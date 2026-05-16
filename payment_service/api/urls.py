from django.urls import path
from .views import health, create_payment, get_payment, cancel_payment

urlpatterns = [
    path('manage/health', health),
    path('api/v1/payment', create_payment),
    path('api/v1/payment/<uuid:payment_uid>', get_payment),
    path('api/v1/payment/<uuid:payment_uid>/cancel', cancel_payment),
]