from django.db import models


class Rental(models.Model):
    RENTAL_STATUSES = (
        ('IN_PROGRESS', 'IN_PROGRESS'),
        ('FINISHED', 'FINISHED'),
        ('CANCELED', 'CANCELED'),
    )

    rental_uid = models.UUIDField(unique=True)
    username = models.CharField(max_length=80)
    payment_uid = models.UUIDField()
    car_uid = models.UUIDField()
    date_from = models.DateTimeField()
    date_to = models.DateTimeField()
    status = models.CharField(max_length=20, choices=RENTAL_STATUSES)

    class Meta:
        db_table = 'rental'

    def __str__(self):
        return f'{self.username} - {self.rental_uid}'