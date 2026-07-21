"""
Patients — DRF Views
=======================
Full CRUD for patients with multi-tenant isolation, search, and pagination.
"""

from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import filters, viewsets
from rest_framework.permissions import IsAuthenticated

from django_filters.rest_framework import DjangoFilterBackend

from analytics.mixins import log_action
from patients.models import Patient
from patients.serializers import (
    PatientCreateUpdateSerializer,
    PatientDetailSerializer,
    PatientListSerializer,
)
from users.permissions import IsActiveUser

# Cache key template — shared with hospitals.views
CACHE_KEY_ADMIN_STATS = 'admin_stats_hospital_{hospital_id}'


class PatientViewSet(viewsets.ModelViewSet):
    """Full CRUD for patients with multi-tenant isolation, search, and
    pagination. Uses a lightweight serializer for list views and a full
    serializer with nested assessments for detail views.
    """

    permission_classes = [IsAuthenticated, IsActiveUser]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['first_name', 'last_name', 'id']
    filterset_fields = ['status', 'gender', 'primary_doctor']

    def get_queryset(self):
        """Tenant-scoped queryset with optimized joins."""
        qs = (
            Patient.objects
            .filter(hospital_id=self.request.user.hospital_id)
            .select_related('hospital', 'primary_doctor')
        )
        if self.action == 'list':
            qs = qs.prefetch_related('assessments')
        return qs

    def get_serializer_class(self):
        if self.action == 'list':
            return PatientListSerializer
        elif self.action in ('create', 'update', 'partial_update'):
            return PatientCreateUpdateSerializer
        return PatientDetailSerializer

    def get_object(self):
        """Override to add prefetch_related for the detail view."""
        obj = super().get_object()
        if self.action == 'retrieve':
            obj = (
                Patient.objects
                .filter(id=obj.id)
                .select_related('hospital', 'primary_doctor')
                .prefetch_related('assessments')
                .first()
            )
        return obj

    @method_decorator(cache_page(60))
    def list(self, request, *args, **kwargs):
        """Cached patient table (60 seconds)."""
        return super().list(request, *args, **kwargs)

    @method_decorator(cache_page(60))
    def retrieve(self, request, *args, **kwargs):
        """Cached patient profile modal (60 seconds)."""
        return super().retrieve(request, *args, **kwargs)

    def perform_create(self, serializer):
        """Auto-set the hospital from the authenticated user."""
        kwargs = {'hospital': self.request.user.hospital}
        if self.request.user.role == 'DOCTOR':
            kwargs['primary_doctor'] = self.request.user
        
        patient = serializer.save(**kwargs)
        log_action(
            self.request,
            action='Created patient record',
            details={
                'patient_id': patient.id,
                'patient_name': f'{patient.first_name} {patient.last_name}',
            },
        )

    def perform_update(self, serializer):
        patient = serializer.save()
        log_action(
            self.request,
            action='Updated patient record',
            details={'patient_id': patient.id},
        )
