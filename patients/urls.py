"""
Patients — URL Configuration
===============================
Patient CRUD via DRF router.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from patients.views import PatientViewSet

router = DefaultRouter()
router.register(r'patients', PatientViewSet, basename='patient')

urlpatterns = [
    path('', include(router.urls)),
]
