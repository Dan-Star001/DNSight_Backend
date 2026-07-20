"""Assessments — Django Admin Configuration"""

from django.contrib import admin

from assessments.models import Assessment


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'doctor', 'risk_score', 'risk_level', 'confirmed_outcome', 'created_at')
    list_filter = ('risk_level', 'confirmed_outcome')
    search_fields = ('patient__first_name', 'patient__last_name')
    readonly_fields = ('clinical_data', 'risk_score', 'risk_level', 'knn_score', 'gnb_score', 'prediction_confidence')
