"""
Assessments — Django ORM Models
=================================
ML prediction records with clinical data, risk scores, and AI-generated
treatment suggestions.
"""

from django.conf import settings
from django.db import models


class Assessment(models.Model):
    """Stores the result of a single ML-powered diabetic neuropathy risk
    assessment, including raw clinical inputs, the computed risk score,
    and an optional AI-generated treatment suggestion."""

    RISK_LEVEL_CHOICES = [
        ('LOW', 'Low'),
        ('MODERATE', 'Moderate'),
        ('HIGH', 'High'),
        ('VERY_HIGH', 'Very High'),
    ]
    OUTCOME_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED_YES', 'Confirmed Yes'),
        ('CONFIRMED_NO', 'Confirmed No'),
    ]

    id = models.BigAutoField(primary_key=True)
    patient = models.ForeignKey(
        'patients.Patient',
        on_delete=models.CASCADE,
        related_name='assessments',
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assessments',
    )
    clinical_data = models.JSONField(
        help_text='Raw clinical input: AGE, SEX, BMI, HbA1c, etc.',
    )
    risk_score = models.FloatField(
        help_text='ML-predicted risk score (0-100).',
    )
    risk_level = models.CharField(
        max_length=20,
        choices=RISK_LEVEL_CHOICES,
    )
    prediction_confidence = models.FloatField(
        help_text='Model prediction confidence/probability (0-1).',
    )
    knn_score = models.FloatField(
        null=True,
        blank=True,
        help_text='KNN model risk score (0-100).',
    )
    gnb_score = models.FloatField(
        null=True,
        blank=True,
        help_text='Gaussian Naive Bayes model risk score (0-100).',
    )
    ai_treatment_suggestion = models.TextField(
        blank=True,
        null=True,
        help_text='LLM-generated treatment recommendation (populated async).',
    )
    confirmed_outcome = models.CharField(
        max_length=20,
        choices=OUTCOME_CHOICES,
        default='PENDING',
        help_text='Clinician-confirmed outcome for model retraining.',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Assessment #{self.id} — {self.patient_id} ({self.risk_level})'

    @staticmethod
    def compute_risk_level(risk_score: float) -> str:
        """Deterministic mapping from a 0-100 risk score to a categorical
        risk level label."""
        if risk_score < 25:
            return 'LOW'
        elif risk_score < 50:
            return 'MODERATE'
        elif risk_score < 75:
            return 'HIGH'
        else:
            return 'VERY_HIGH'
