"""
Celery Application Configuration for DNSight Backend
=====================================================
Auto-discovers tasks from all installed Django apps and configures the
Celery application instance used by workers.
"""

import os

from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DNSight_Backend.settings')

app = Celery('DNSight_Backend')

# Read config from Django settings, using the CELERY_ namespace so that
# all Celery-related settings in settings.py must be prefixed with CELERY_.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks.py files in all installed Django apps.
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Diagnostic task for verifying Celery connectivity."""
    print(f'Request: {self.request!r}')
