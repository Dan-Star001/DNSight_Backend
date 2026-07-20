# Import Celery app on Django startup so that @shared_task decorators
# in tasks.py are registered when the worker starts.
from DNSight_Backend.celery import app as celery_app

__all__ = ('celery_app',)
