from django.db import migrations
import uuid


def create_initial_car(apps, schema_editor):
    Car = apps.get_model('api', 'Car')

    Car.objects.get_or_create(
        car_uid=uuid.UUID("109b42f3-198d-4c89-9276-a7520a7120ab"),
        defaults={
            "brand": "Mercedes Benz",
            "model": "GLA 250",
            "registration_number": "ЛО777Х799",
            "power": 249,
            "type": "SEDAN",
            "price": 3500,
            "availability": True,
        }
    )


def delete_initial_car(apps, schema_editor):
    Car = apps.get_model('api', 'Car')
    Car.objects.filter(
        car_uid=uuid.UUID("109b42f3-198d-4c89-9276-a7520a7120ab")
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_initial_car, delete_initial_car),
    ]