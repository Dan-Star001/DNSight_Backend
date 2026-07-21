#!/usr/bin/env bash

# Start the Celery worker in the background
celery -A DNSight_Backend worker --pool=solo --loglevel=info &

# Start the Django Web Service in the foreground
gunicorn DNSight_Backend.wsgi:application --workers 1 --threads 2 --timeout 180
