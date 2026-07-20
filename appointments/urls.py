"""
Appointments — URL Configuration
====================================
Appointment scheduling CRUD via DRF router.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from appointments.views import AppointmentViewSet

router = DefaultRouter()
router.register(r'appointments', AppointmentViewSet, basename='appointment')

urlpatterns = [
    path('', include(router.urls)),
]
