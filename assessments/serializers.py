"""
Assessments — DRF Serializers
================================
Covers assessment read display, ML prediction input validation, and
clinician feedback for model retraining.
"""

from rest_framework import serializers

from assessments.models import Assessment
from patients.models import Patient


class AssessmentSerializer(serializers.ModelSerializer):
    """Read serializer for assessment records."""

    patient_name = serializers.SerializerMethodField()
    doctor_name = serializers.SerializerMethodField()

    class Meta:
        model = Assessment
        fields = [
            'id', 'patient', 'patient_name', 'doctor', 'doctor_name',
            'clinical_data', 'risk_score', 'risk_level',
            'knn_score', 'gnb_score',
            'prediction_confidence', 'ai_treatment_suggestion',
            'confirmed_outcome', 'created_at',
        ]
        read_only_fields = fields

    def get_patient_name(self, obj) -> str | None:
        if obj.patient:
            return f'{obj.patient.first_name} {obj.patient.last_name}'
        return None

    def get_doctor_name(self, obj) -> str | None:
        if obj.doctor:
            return f'{obj.doctor.first_name} {obj.doctor.last_name}'
        return None


class PredictionInputSerializer(serializers.Serializer):
    """Write-only serializer that validates inbound clinical data for the ML
    prediction endpoint. Field names match the ML service's expected schema."""

    patient_id = serializers.CharField(max_length=50)

    # Clinical features — must match the ML service ClinicalData model
    AGE = serializers.FloatField()
    SEX = serializers.IntegerField()
    BMI = serializers.FloatField()
    SP = serializers.FloatField()
    BP = serializers.FloatField()
    HbA1c = serializers.FloatField()
    FPS = serializers.FloatField()
    PPS = serializers.FloatField()
    FAMILY_HO = serializers.IntegerField()
    SMOKING = serializers.IntegerField()
    ONSET_AGE = serializers.FloatField()

    def validate_patient_id(self, value):
        """Ensure the patient exists and belongs to the current user's hospital."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if not Patient.objects.filter(
                id=value,
                hospital_id=request.user.hospital_id,
            ).exists():
                raise serializers.ValidationError(
                    'Patient not found in your hospital.'
                )
        return value


class FeedbackSerializer(serializers.Serializer):
    """Accepts clinician feedback on an assessment outcome for model
    retraining purposes."""

    confirmed_outcome = serializers.ChoiceField(
        choices=['CONFIRMED_YES', 'CONFIRMED_NO'],
    )
