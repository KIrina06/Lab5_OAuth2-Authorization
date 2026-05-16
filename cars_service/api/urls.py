from django.urls import path
from .views import health, get_cars, get_car_by_uid, reserve_car, release_car

urlpatterns = [
    path('manage/health', health),
    path('api/v1/cars', get_cars),
    path('api/v1/cars/<uuid:car_uid>', get_car_by_uid),
    path('api/v1/cars/<uuid:car_uid>/reserve', reserve_car),
    path('api/v1/cars/<uuid:car_uid>/release', release_car),
]