from django.http import JsonResponse
from .models import Car
import json
from django.views.decorators.csrf import csrf_exempt


def health(request):
    return JsonResponse({"status": "OK"}, status=200)


def get_cars(request):
    show_all = request.GET.get('showAll', 'false').lower() == 'true'

    if show_all:
        cars = Car.objects.all()
    else:
        cars = Car.objects.filter(availability=True)

    items = []

    for car in cars:
        items.append({
            "carUid": str(car.car_uid),
            "brand": car.brand,
            "model": car.model,
            "registrationNumber": car.registration_number,
            "power": car.power,
            "type": car.type,
            "price": car.price,
            "available": car.availability,
        })

    return JsonResponse({
        "items": items,
        "page": 1,
        "pageSize": len(items),
        "totalElements": len(items)
    }, status=200)

def get_car_by_uid(request, car_uid):
    try:
        car = Car.objects.get(car_uid=car_uid)
    except Car.DoesNotExist:
        return JsonResponse({"message": "Car not found"}, status=404)

    return JsonResponse({
        "carUid": str(car.car_uid),
        "brand": car.brand,
        "model": car.model,
        "registrationNumber": car.registration_number,
        "power": car.power,
        "type": car.type,
        "price": car.price,
        "available": car.availability,
    }, status=200)


@csrf_exempt
def reserve_car(request, car_uid):
    if request.method != 'POST':
        return JsonResponse({"message": "Method not allowed"}, status=405)

    try:
        car = Car.objects.get(car_uid=car_uid)
    except Car.DoesNotExist:
        return JsonResponse({"message": "Car not found"}, status=404)

    if not car.availability:
        return JsonResponse({"message": "Car is not available"}, status=409)

    car.availability = False
    car.save()

    return JsonResponse({
        "carUid": str(car.car_uid),
        "available": car.availability,
    }, status=200)


@csrf_exempt
def release_car(request, car_uid):
    if request.method != 'POST':
        return JsonResponse({"message": "Method not allowed"}, status=405)

    try:
        car = Car.objects.get(car_uid=car_uid)
    except Car.DoesNotExist:
        return JsonResponse({"message": "Car not found"}, status=404)

    car.availability = True
    car.save()

    return JsonResponse({
        "carUid": str(car.car_uid),
        "available": car.availability,
    }, status=200)