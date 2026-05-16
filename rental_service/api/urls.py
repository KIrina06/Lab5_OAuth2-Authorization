from django.urls import path
from .views import health, get_rentals, get_rental_by_uid, create_rental, finish_rental, cancel_rental

urlpatterns = [
    path('manage/health', health),
    path('api/v1/rental', get_rentals),
    path('api/v1/rental/<uuid:rental_uid>', get_rental_by_uid),
    path('api/v1/rental/create', create_rental),
    path('api/v1/rental/<uuid:rental_uid>/finish', finish_rental),
    path('api/v1/rental/<uuid:rental_uid>/cancel', cancel_rental),
]