"""
Assessments — DRF Views
==========================
ML prediction requests, patient assessment history, and clinician feedback.
"""

import requests as http_client
from django.conf import settings
from django.core.cache import cache
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from analytics.mixins import log_action
from assessments.models import Assessment
from assessments.serializers import (
    AssessmentSerializer,
    FeedbackSerializer,
    PredictionInputSerializer,
)
from assessments.tasks import generate_ai_treatment_suggestion
from users.permissions import IsActiveUser

# Cache key template — shared with hospitals.views
CACHE_KEY_ADMIN_STATS = 'admin_stats_hospital_{hospital_id}'


class AssessmentViewSet(viewsets.ViewSet):
    """Handles ML prediction requests, patient assessment history, and
    clinician feedback for model retraining.
    """

    permission_classes = [IsAuthenticated, IsActiveUser]

    @action(detail=False, methods=['post'], url_path='predict')
    def predict(self, request):
        """POST /api/assessments/predict/

        Accepts clinical data, calls the ML microservice synchronously,
        saves the Assessment record, fires an async Celery task for the LLM
        treatment suggestion, and returns the result immediately.
        """
        serializer = PredictionInputSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        ml_payload = {
            'AGE': data['AGE'],
            'SEX': data['SEX'],
            'BMI': data['BMI'],
            'SP': data['SP'],
            'BP': data['BP'],
            'HbA1c': data['HbA1c'],
            'FPS': data['FPS'],
            'PPS': data['PPS'],
            'FAMILY_HO': data['FAMILY_HO'],
            'SMOKING': data['SMOKING'],
            'ONSET_AGE': data['ONSET_AGE'],
        }

        ml_service_url = getattr(
            settings, 'ML_SERVICE_URL', 'https://ml-service-sgvf.onrender.com',
        )

        try:
            ml_response = http_client.post(
                f'{ml_service_url}/predict',
                json=ml_payload,
                timeout=180,
            )
            ml_response.raise_for_status()
            ml_result = ml_response.json()
        except http_client.exceptions.RequestException as exc:
            import logging
            logger = logging.getLogger(__name__)
            logger.error('ML service call failed: %s', str(exc))
            return Response(
                {'detail': 'ML prediction service is currently unavailable.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        risk_score = ml_result.get('risk_score', 0)
        confidence = ml_result.get('probability', 0)
        knn_score = ml_result.get('knn_score')
        gnb_score = ml_result.get('gnb_score')
        risk_level = Assessment.compute_risk_level(risk_score)

        assessment = Assessment.objects.create(
            patient_id=data['patient_id'],
            doctor=request.user,
            clinical_data=ml_payload,
            risk_score=risk_score,
            risk_level=risk_level,
            prediction_confidence=confidence,
            knn_score=knn_score,
            gnb_score=gnb_score,
        )

        try:
            generate_ai_treatment_suggestion.delay(assessment.id)
        except Exception as exc:
            pass

        log_action(
            request,
            action='Ran ML risk assessment',
            details={
                'assessment_id': assessment.id,
                'patient_id': data['patient_id'],
                'risk_score': risk_score,
                'risk_level': risk_level,
            },
        )

        return Response(
            AssessmentSerializer(assessment).data,
            status=status.HTTP_201_CREATED,
        )

    def list(self, request, patient_id=None):
        """GET /api/patients/<patient_id>/assessments/

        Returns all assessments for a specific patient, tenant-scoped.
        """
        queryset = (
            Assessment.objects
            .filter(
                patient_id=patient_id,
                patient__hospital_id=request.user.hospital_id,
            )
            .select_related('patient', 'doctor')
        )
        serializer = AssessmentSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """GET /api/assessments/<id>/
        
        Fetches a single assessment for polling.
        """
        try:
            assessment = Assessment.objects.select_related('patient', 'doctor').get(
                id=pk,
                patient__hospital_id=request.user.hospital_id,
            )
        except Assessment.DoesNotExist:
            return Response(
                {'detail': 'Assessment not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = AssessmentSerializer(assessment)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'], url_path='feedback')
    def feedback(self, request, pk=None):
        """PATCH /api/assessments/<id>/feedback/

        Updates the confirmed_outcome field for model retraining.
        """
        serializer = FeedbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            assessment = (
                Assessment.objects
                .select_related('patient')
                .get(
                    id=pk,
                    patient__hospital_id=request.user.hospital_id,
                )
            )
        except Assessment.DoesNotExist:
            return Response(
                {'detail': 'Assessment not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        assessment.confirmed_outcome = serializer.validated_data['confirmed_outcome']
        assessment.save(update_fields=['confirmed_outcome'])

        log_action(
            request,
            action='Submitted assessment feedback',
            details={
                'assessment_id': assessment.id,
                'confirmed_outcome': assessment.confirmed_outcome,
            },
        )

        return Response(AssessmentSerializer(assessment).data)
