import json
import uuid

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Payment


def health(request):
    return JsonResponse({"status": "OK"}, status=200)


@csrf_exempt
def create_payment(request):
    if request.method != 'POST':
        return JsonResponse({"message": "Method not allowed"}, status=405)

    try:
        body = json.loads(request.body.decode('utf-8'))
        price = body.get('price')
    except Exception:
        return JsonResponse({"message": "Invalid JSON"}, status=400)

    if price is None:
        return JsonResponse({"message": "price is required"}, status=400)

    payment = Payment.objects.create(
        payment_uid=uuid.uuid4(),
        status='PAID',
        price=price
    )

    return JsonResponse({
        "paymentUid": str(payment.payment_uid),
        "status": payment.status,
        "price": payment.price
    }, status=201)


def get_payment(request, payment_uid):
    try:
        payment = Payment.objects.get(payment_uid=payment_uid)
    except Payment.DoesNotExist:
        return JsonResponse({"message": "Payment not found"}, status=404)

    return JsonResponse({
        "paymentUid": str(payment.payment_uid),
        "status": payment.status,
        "price": payment.price
    }, status=200)


@csrf_exempt
def cancel_payment(request, payment_uid):
    if request.method != 'POST':
        return JsonResponse({"message": "Method not allowed"}, status=405)

    try:
        payment = Payment.objects.get(payment_uid=payment_uid)
    except Payment.DoesNotExist:
        return JsonResponse({"message": "Payment not found"}, status=404)

    payment.status = 'CANCELED'
    payment.save()

    return JsonResponse({
        "paymentUid": str(payment.payment_uid),
        "status": payment.status,
        "price": payment.price
    }, status=200)