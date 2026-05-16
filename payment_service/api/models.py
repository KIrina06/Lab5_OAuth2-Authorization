from django.db import models


class Payment(models.Model):
    PAYMENT_STATUSES = (
        ('PAID', 'PAID'),
        ('CANCELED', 'CANCELED'),
    )

    payment_uid = models.UUIDField(unique=True)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUSES)
    price = models.IntegerField()

    class Meta:
        db_table = 'payment'

    def __str__(self):
        return f'{self.payment_uid} - {self.status}'