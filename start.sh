#!/usr/bin/env bash

# Start the Celery worker in the background
celery -A DNSight_Backend worker --loglevel=info &

# Start the Django Web Service in the foreground
gunicorn DNSight_Backend.wsgi:application
