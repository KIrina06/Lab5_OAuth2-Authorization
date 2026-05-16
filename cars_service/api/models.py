from django.db import models


class Car(models.Model):
    CAR_TYPES = (
        ('SEDAN', 'SEDAN'),
        ('SUV', 'SUV'),
        ('MINIVAN', 'MINIVAN'),
        ('ROADSTER', 'ROADSTER'),
    )

    car_uid = models.UUIDField(unique=True)
    brand = models.CharField(max_length=80)
    model = models.CharField(max_length=80)
    registration_number = models.CharField(max_length=20)
    power = models.IntegerField(null=True, blank=True)
    price = models.IntegerField()
    type = models.CharField(max_length=20, choices=CAR_TYPES)
    availability = models.BooleanField(default=True)

    class Meta:
        db_table = 'cars'

    def __str__(self):
        return f'{self.brand} {self.model}'