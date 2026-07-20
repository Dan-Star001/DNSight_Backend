"""
Hospitals — DRF Views
========================
Admin-only endpoints for managing doctors and viewing hospital-wide analytics.
All queries are implicitly scoped to the admin's hospital_id.
"""

import logging

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import transaction
from django.db.models import Avg, Count, Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from analytics.mixins import log_action
from appointments.models import Appointment
from assessments.models import Assessment
from patients.models import Patient
from users.permissions import IsAdmin
from users.serializers import UserSerializer

logger = logging.getLogger(__name__)

User = get_user_model()

# Cache key templates — parameterized by hospital ID for tenant isolation
CACHE_KEY_ADMIN_STATS = 'admin_stats_hospital_{hospital_id}'
CACHE_TTL = 300  # 5 minutes


class AdminViewSet(viewsets.ViewSet):
    """Admin-only endpoints for managing doctors and viewing hospital analytics."""

    permission_classes = [IsAuthenticated, IsAdmin]

    def list(self, request):
        """GET /api/admin/doctors/

        Lists all doctors in the admin's hospital with optional status filtering.
        """
        queryset = (
            User.objects
            .filter(
                hospital_id=request.user.hospital_id,
                role='DOCTOR',
            )
            .select_related('hospital')
            .only(
                'id', 'email', 'first_name', 'last_name',
                'role', 'status', 'date_joined', 'hospital__name',
            )
        )

        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter.upper())

        serializer = UserSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'], url_path='approve')
    def approve(self, request, pk=None):
        """PATCH /api/admin/doctors/<id>/approve/"""
        return self._update_doctor_status(request, pk, 'ACTIVE', 'approved')

    @action(detail=True, methods=['patch'], url_path='reject')
    def reject(self, request, pk=None):
        """PATCH /api/admin/doctors/<id>/reject/"""
        return self._update_doctor_status(request, pk, 'REJECTED', 'rejected')

    @transaction.atomic
    def _update_doctor_status(self, request, pk, new_status, action_verb):
        """Shared helper for approve/reject actions."""
        try:
            doctor = (
                User.objects
                .select_for_update()
                .get(
                    id=pk,
                    hospital_id=request.user.hospital_id,
                    role='DOCTOR',
                )
            )
        except User.DoesNotExist:
            return Response(
                {'detail': 'Doctor not found in your hospital.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        doctor.status = new_status
        doctor.save(update_fields=['status'])

        log_action(
            request,
            action=f'{action_verb.capitalize()} doctor account',
            details={
                'doctor_id': doctor.id,
                'doctor_email': doctor.email,
                'new_status': new_status,
            },
        )

        return Response(
            {
                'message': f'Doctor has been {action_verb}.',
                'user': UserSerializer(doctor).data,
            },
        )

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """GET /api/admin/stats/

        Hospital-wide analytics via DB aggregation, wrapped in 5-min cache.
        """
        hospital_id = request.user.hospital_id
        cache_key = CACHE_KEY_ADMIN_STATS.format(hospital_id=hospital_id)

        cached_stats = cache.get(cache_key)
        if cached_stats is not None:
            return Response(cached_stats)

        doctor_stats = (
            User.objects
            .filter(hospital_id=hospital_id, role='DOCTOR')
            .aggregate(
                total=Count('id'),
                active=Count('id', filter=Q(status='ACTIVE')),
                pending=Count('id', filter=Q(status='PENDING')),
                rejected=Count('id', filter=Q(status='REJECTED')),
            )
        )

        patient_stats = (
            Patient.objects
            .filter(hospital_id=hospital_id)
            .aggregate(
                total=Count('id'),
                active=Count('id', filter=Q(status='ACTIVE')),
                inactive=Count('id', filter=Q(status='INACTIVE')),
            )
        )

        assessment_stats = (
            Assessment.objects
            .filter(patient__hospital_id=hospital_id)
            .aggregate(
                total=Count('id'),
                avg_risk_score=Avg('risk_score'),
                low_risk=Count('id', filter=Q(risk_level='LOW')),
                moderate_risk=Count('id', filter=Q(risk_level='MODERATE')),
                high_risk=Count('id', filter=Q(risk_level='HIGH')),
                very_high_risk=Count('id', filter=Q(risk_level='VERY_HIGH')),
            )
        )

        appointment_stats = (
            Appointment.objects
            .filter(doctor__hospital_id=hospital_id)
            .aggregate(
                total=Count('id'),
                scheduled=Count('id', filter=Q(status='SCHEDULED')),
                completed=Count('id', filter=Q(status='COMPLETED')),
                cancelled=Count('id', filter=Q(status='CANCELLED')),
            )
        )

        stats_data = {
            'doctors': doctor_stats,
            'patients': patient_stats,
            'assessments': assessment_stats,
            'appointments': appointment_stats,
        }

        cache.set(cache_key, stats_data, CACHE_TTL)

        return Response(stats_data)


class DoctorStatsView(APIView):
    """GET /api/doctor/stats/

    Returns patient, appointment, and assessment statistics
    scoped to the currently authenticated doctor.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        doctor = request.user
        hospital_id = doctor.hospital_id
        
        cache_key = f'doctor_stats_{doctor.id}'
        cached_stats = cache.get(cache_key)
        if cached_stats is not None:
            return Response(cached_stats)


        patient_stats = (
            Patient.objects
            .filter(hospital_id=hospital_id, primary_doctor=doctor)
            .aggregate(
                total=Count('id'),
                active=Count('id', filter=Q(status='ACTIVE')),
                inactive=Count('id', filter=Q(status='INACTIVE')),
            )
        )

        assessment_stats = (
            Assessment.objects
            .filter(doctor=doctor)
            .aggregate(
                total=Count('id'),
                avg_risk_score=Avg('risk_score'),
                low_risk=Count('id', filter=Q(risk_level='LOW')),
                moderate_risk=Count('id', filter=Q(risk_level='MODERATE')),
                high_risk=Count('id', filter=Q(risk_level='HIGH')),
                very_high_risk=Count('id', filter=Q(risk_level='VERY_HIGH')),
            )
        )

        appointment_stats = (
            Appointment.objects
            .filter(doctor=doctor)
            .aggregate(
                total=Count('id'),
                scheduled=Count('id', filter=Q(status='SCHEDULED')),
                completed=Count('id', filter=Q(status='COMPLETED')),
                cancelled=Count('id', filter=Q(status='CANCELLED')),
            )
        )

        stats_data = {
            'patients': patient_stats,
            'assessments': assessment_stats,
            'appointments': appointment_stats,
        }

        cache.set(cache_key, stats_data, CACHE_TTL)

        return Response(stats_data)
