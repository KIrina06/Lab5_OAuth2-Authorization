import json
import os
from datetime import datetime

import requests
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from requests.exceptions import RequestException


CARS_SERVICE_URL = os.getenv('CARS_SERVICE_URL', 'http://localhost:8070')
PAYMENT_SERVICE_URL = os.getenv('PAYMENT_SERVICE_URL', 'http://localhost:8050')
RENTAL_SERVICE_URL = os.getenv('RENTAL_SERVICE_URL', 'http://localhost:8060')


def health(request):
    return JsonResponse({"status": "OK"}, status=200)


def auth_headers(request):
    return {
        "Authorization": request.headers.get("Authorization", "")
    }


def get_username(request):
    payload = getattr(request, "jwt_payload", {})
    return payload.get("email") or payload.get("sub")


def get_cars(request):
    response = requests.get(
        f'{CARS_SERVICE_URL}/api/v1/cars',
        params=request.GET,
        headers=auth_headers(request)
    )

    return JsonResponse(response.json(), status=response.status_code)


def build_rental_response(request, rental_data):
    car_response = requests.get(
        f'{CARS_SERVICE_URL}/api/v1/cars/{rental_data["carUid"]}',
        headers=auth_headers(request)
    )

    if car_response.status_code != 200:
        return {
            "rentalUid": rental_data["rentalUid"],
            "carUid": rental_data["carUid"],
            "status": rental_data["status"],
            "dateFrom": rental_data["dateFrom"],
            "dateTo": rental_data["dateTo"],
            "car": {},
            "payment": {}
        }

    car_data = car_response.json()
    payment_data = {}

    try:
        payment_response = requests.get(
            f'{PAYMENT_SERVICE_URL}/api/v1/payment/{rental_data["paymentUid"]}',
            headers=auth_headers(request),
            timeout=3
        )

        if payment_response.status_code == 200:
            payment_data = payment_response.json()

            if rental_data["status"] == "CANCELED" and payment_data.get("status") == "PAID":
                cancel_response = requests.post(
                    f'{PAYMENT_SERVICE_URL}/api/v1/payment/{rental_data["paymentUid"]}/cancel',
                    headers=auth_headers(request),
                    timeout=3
                )

                if cancel_response.status_code == 200:
                    payment_data = cancel_response.json()
    except RequestException:
        payment_data = {}

    return {
        "rentalUid": rental_data["rentalUid"],
        "carUid": rental_data["carUid"],
        "status": rental_data["status"],
        "dateFrom": rental_data["dateFrom"],
        "dateTo": rental_data["dateTo"],
        "car": {
            "carUid": car_data["carUid"],
            "brand": car_data["brand"],
            "model": car_data["model"],
            "registrationNumber": car_data["registrationNumber"]
        },
        "payment": payment_data if payment_data else {}
    }


def get_rentals(request):
    username = get_username(request)

    rental_response = requests.get(
        f'{RENTAL_SERVICE_URL}/api/v1/rental',
        params={"username": username},
        headers=auth_headers(request)
    )

    if rental_response.status_code != 200:
        return JsonResponse(rental_response.json(), status=rental_response.status_code)

    rental_items = rental_response.json().get("items", [])

    result = []
    for rental in rental_items:
        result.append(build_rental_response(request, rental))

    return JsonResponse(result, safe=False, status=200)


def get_rental_by_uid(request, rental_uid):
    username = get_username(request)

    rental_response = requests.get(
        f'{RENTAL_SERVICE_URL}/api/v1/rental/{rental_uid}',
        params={"username": username},
        headers=auth_headers(request)
    )

    if rental_response.status_code != 200:
        return JsonResponse(rental_response.json(), status=rental_response.status_code)

    result = build_rental_response(request, rental_response.json())

    return JsonResponse(result, status=200)


@csrf_exempt
def create_rental(request):
    if request.method != 'POST':
        return JsonResponse({"message": "Method not allowed"}, status=405)

    username = get_username(request)

    try:
        body = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({"message": "Invalid JSON"}, status=400)

    car_uid = body.get("carUid")
    date_from_raw = body.get("dateFrom")
    date_to_raw = body.get("dateTo")

    if not car_uid or not date_from_raw or not date_to_raw:
        return JsonResponse({"message": "carUid, dateFrom and dateTo are required"}, status=400)

    car_response = requests.get(
        f'{CARS_SERVICE_URL}/api/v1/cars/{car_uid}',
        headers=auth_headers(request)
    )

    if car_response.status_code != 200:
        return JsonResponse({"message": "Car not found"}, status=404)

    car_data = car_response.json()
    is_available = car_data.get("available", car_data.get("availability"))

    if not is_available:
        return JsonResponse({"message": "Car is not available"}, status=409)

    reserve_response = requests.post(
        f'{CARS_SERVICE_URL}/api/v1/cars/{car_uid}/reserve',
        headers=auth_headers(request)
    )

    if reserve_response.status_code != 200:
        return JsonResponse({"message": "Cannot reserve car"}, status=409)

    date_from = datetime.strptime(date_from_raw, "%Y-%m-%d")
    date_to = datetime.strptime(date_to_raw, "%Y-%m-%d")
    days = abs((date_to - date_from).days)
    total_price = days * car_data["price"]

    try:
        payment_response = requests.post(
            f'{PAYMENT_SERVICE_URL}/api/v1/payment',
            json={"price": total_price},
            headers=auth_headers(request),
            timeout=3
        )
    except RequestException:
        requests.post(
            f'{CARS_SERVICE_URL}/api/v1/cars/{car_uid}/release',
            headers=auth_headers(request)
        )
        return JsonResponse({"message": "Payment Service unavailable"}, status=503)

    if payment_response.status_code != 201:
        requests.post(
            f'{CARS_SERVICE_URL}/api/v1/cars/{car_uid}/release',
            headers=auth_headers(request)
        )
        return JsonResponse({"message": "Payment Service unavailable"}, status=503)

    payment_data = payment_response.json()

    rental_response = requests.post(
        f'{RENTAL_SERVICE_URL}/api/v1/rental/create',
        json={
            "username": username,
            "paymentUid": payment_data["paymentUid"],
            "carUid": car_uid,
            "dateFrom": date_from_raw,
            "dateTo": date_to_raw
        },
        headers=auth_headers(request)
    )

    if rental_response.status_code != 201:
        requests.post(
            f'{CARS_SERVICE_URL}/api/v1/cars/{car_uid}/release',
            headers=auth_headers(request)
        )
        requests.post(
            f'{PAYMENT_SERVICE_URL}/api/v1/payment/{payment_data["paymentUid"]}/cancel',
            headers=auth_headers(request)
        )
        return JsonResponse({"message": "Cannot create rental"}, status=500)

    rental_data = rental_response.json()

    return JsonResponse({
        "rentalUid": rental_data["rentalUid"],
        "carUid": rental_data["carUid"],
        "status": rental_data["status"],
        "dateFrom": rental_data["dateFrom"],
        "dateTo": rental_data["dateTo"],
        "payment": {
            "paymentUid": payment_data["paymentUid"],
            "status": payment_data["status"],
            "price": payment_data["price"]
        }
    }, status=200)


@csrf_exempt
def cancel_rental(request, rental_uid):
    if request.method != 'DELETE':
        return JsonResponse({"message": "Method not allowed"}, status=405)

    username = get_username(request)

    rental_response = requests.get(
        f'{RENTAL_SERVICE_URL}/api/v1/rental/{rental_uid}',
        params={"username": username},
        headers=auth_headers(request)
    )

    if rental_response.status_code != 200:
        return JsonResponse(rental_response.json(), status=rental_response.status_code)

    rental_data = rental_response.json()

    requests.post(
        f'{CARS_SERVICE_URL}/api/v1/cars/{rental_data["carUid"]}/release',
        headers=auth_headers(request)
    )

    try:
        requests.post(
            f'{PAYMENT_SERVICE_URL}/api/v1/payment/{rental_data["paymentUid"]}/cancel',
            headers=auth_headers(request),
            timeout=3
        )
    except RequestException:
        pass

    requests.delete(
        f'{RENTAL_SERVICE_URL}/api/v1/rental/{rental_uid}/cancel',
        params={"username": username},
        headers=auth_headers(request)
    )

    return HttpResponse(status=204)


@csrf_exempt
def finish_rental(request, rental_uid):
    if request.method != 'POST':
        return JsonResponse({"message": "Method not allowed"}, status=405)

    username = get_username(request)

    rental_response = requests.get(
        f'{RENTAL_SERVICE_URL}/api/v1/rental/{rental_uid}',
        params={"username": username},
        headers=auth_headers(request)
    )

    if rental_response.status_code != 200:
        return JsonResponse(rental_response.json(), status=rental_response.status_code)

    rental_data = rental_response.json()

    requests.post(
        f'{CARS_SERVICE_URL}/api/v1/cars/{rental_data["carUid"]}/release',
        headers=auth_headers(request)
    )

    requests.post(
        f'{RENTAL_SERVICE_URL}/api/v1/rental/{rental_uid}/finish',
        params={"username": username},
        headers=auth_headers(request)
    )

    return HttpResponse(status=204)


@csrf_exempt
def rental_collection(request):
    if request.method == 'GET':
        return get_rentals(request)

    if request.method == 'POST':
        return create_rental(request)

    return JsonResponse({"message": "Method not allowed"}, status=405)


@csrf_exempt
def rental_detail(request, rental_uid):
    if request.method == 'GET':
        return get_rental_by_uid(request, rental_uid)

    if request.method == 'DELETE':
        return cancel_rental(request, rental_uid)

    return JsonResponse({"message": "Method not allowed"}, status=405)