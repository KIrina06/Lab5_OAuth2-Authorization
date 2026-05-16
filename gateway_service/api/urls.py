from django.urls import path

from .views import (
    health,
    get_cars,
    rental_collection,
    rental_detail,
    finish_rental,
)

urlpatterns = [
    path('manage/health', health),
    path('api/v1/cars', get_cars),
    path('api/v1/rental', rental_collection),
    path('api/v1/rental/<uuid:rental_uid>', rental_detail),
    path('api/v1/rental/<uuid:rental_uid>/finish', finish_rental),
]