import json
import uuid

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_date
from django.utils import timezone

from .models import Rental

def health(request):
    return JsonResponse({"status": "OK"}, status=200)


def rental_to_json(rental):
    return {
        "rentalUid": str(rental.rental_uid),
        "username": rental.username,
        "paymentUid": str(rental.payment_uid),
        "carUid": str(rental.car_uid),
        "dateFrom": rental.date_from.strftime('%Y-%m-%d'),
        "dateTo": rental.date_to.strftime('%Y-%m-%d'),
        "status": rental.status,
    }


def get_rentals(request):
    username = request.GET.get('username')

    if not username:
        return JsonResponse({"message": "username is required"}, status=400)

    rentals = Rental.objects.filter(username=username)

    return JsonResponse({
        "items": [rental_to_json(rental) for rental in rentals]
    }, status=200)


def get_rental_by_uid(request, rental_uid):
    username = request.GET.get('username')

    if not username:
        return JsonResponse({"message": "username is required"}, status=400)

    try:
        rental = Rental.objects.get(rental_uid=rental_uid, username=username)
    except Rental.DoesNotExist:
        return JsonResponse({"message": "Rental not found"}, status=404)

    return JsonResponse(rental_to_json(rental), status=200)


@csrf_exempt
def create_rental(request):
    if request.method != 'POST':
        return JsonResponse({"message": "Method not allowed"}, status=405)

    try:
        body = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({"message": "Invalid JSON"}, status=400)

    required_fields = ['username', 'paymentUid', 'carUid', 'dateFrom', 'dateTo']

    for field in required_fields:
        if field not in body:
            return JsonResponse({"message": f"{field} is required"}, status=400)

    date_from = parse_date(body['dateFrom'])
    date_to = parse_date(body['dateTo'])

    if date_from is None or date_to is None:
        return JsonResponse({"message": "Invalid date format. Use YYYY-MM-DD"}, status=400)

    date_from = timezone.make_aware(
        timezone.datetime.combine(date_from, timezone.datetime.min.time())
    )
    date_to = timezone.make_aware(
        timezone.datetime.combine(date_to, timezone.datetime.min.time())
    )

    rental = Rental.objects.create(
        rental_uid=uuid.uuid4(),
        username=body['username'],
        payment_uid=body['paymentUid'],
        car_uid=body['carUid'],
        date_from=date_from,
        date_to=date_to,
        status='IN_PROGRESS'
    )

    return JsonResponse(rental_to_json(rental), status=201)


@csrf_exempt
def finish_rental(request, rental_uid):
    if request.method != 'POST':
        return JsonResponse({"message": "Method not allowed"}, status=405)

    username = request.GET.get('username')

    if not username:
        return JsonResponse({"message": "username is required"}, status=400)

    try:
        rental = Rental.objects.get(rental_uid=rental_uid, username=username)
    except Rental.DoesNotExist:
        return JsonResponse({"message": "Rental not found"}, status=404)

    rental.status = 'FINISHED'
    rental.save()

    return JsonResponse(rental_to_json(rental), status=200)


@csrf_exempt
def cancel_rental(request, rental_uid):
    if request.method != 'DELETE':
        return JsonResponse({"message": "Method not allowed"}, status=405)

    username = request.GET.get('username')

    if not username:
        return JsonResponse({"message": "username is required"}, status=400)

    try:
        rental = Rental.objects.get(rental_uid=rental_uid, username=username)
    except Rental.DoesNotExist:
        return JsonResponse({"message": "Rental not found"}, status=404)

    rental.status = 'CANCELED'
    rental.save()

    return JsonResponse(rental_to_json(rental), status=200)