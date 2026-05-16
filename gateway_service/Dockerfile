FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY gateway_service /app

EXPOSE 8080

CMD ["sh", "-c", "sleep 12 && python manage.py runserver 0.0.0.0:8080"]