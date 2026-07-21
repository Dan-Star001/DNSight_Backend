"""
Patients — DRF Serializers
=============================
Lightweight list, full detail, and write serializers for patient management.
"""

from rest_framework import serializers

from patients.models import Patient


class PatientListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for patient list views. Excludes heavy JSON
    fields (medical_history, contact_info) and nested assessments."""

    doctor_name = serializers.SerializerMethodField()
    assessments = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = [
            'id', 'first_name', 'last_name', 'date_of_birth',
            'gender', 'email', 'phone_number', 'status', 'primary_doctor', 'doctor_name',
            'created_at', 'assessments', 'medical_history'
        ]
        read_only_fields = ['id', 'created_at']

    def get_doctor_name(self, obj) -> str | None:
        if obj.primary_doctor:
            return f'{obj.primary_doctor.first_name} {obj.primary_doctor.last_name}'
        return None

    def get_assessments(self, obj):
        from assessments.serializers import AssessmentSerializer
        assessments = list(obj.assessments.all())[:1]
        return AssessmentSerializer(assessments, many=True).data


class PatientDetailSerializer(serializers.ModelSerializer):
    """Full patient profile serializer including nested assessments for the
    detail view. Used with ``prefetch_related('assessments')``."""

    doctor_name = serializers.SerializerMethodField()
    assessments = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = [
            'id', 'hospital', 'primary_doctor', 'doctor_name',
            'first_name', 'last_name', 'date_of_birth', 'gender',
            'email', 'phone_number', 'contact_info', 'medical_history',
            'status', 'created_at', 'assessments',
        ]
        read_only_fields = ['id', 'hospital', 'created_at']

    def get_doctor_name(self, obj) -> str | None:
        if obj.primary_doctor:
            return f'{obj.primary_doctor.first_name} {obj.primary_doctor.last_name}'
        return None

    def get_assessments(self, obj):
        """Return the most recent 10 assessments without hitting the DB, leveraging the prefetched
        queryset."""
        from assessments.serializers import AssessmentSerializer

        assessments = list(obj.assessments.all())[:10]
        return AssessmentSerializer(assessments, many=True).data


class PatientCreateUpdateSerializer(serializers.ModelSerializer):
    """Write serializer for creating/updating patients. The hospital field is
    auto-set from the authenticated user's hospital in the view."""

    class Meta:
        model = Patient
        fields = [
            'id', 'first_name', 'last_name', 'date_of_birth', 'gender',
            'email', 'phone_number', 'contact_info', 'medical_history',
            'status', 'primary_doctor', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']
