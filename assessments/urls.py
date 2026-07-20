"""
Assessments — URL Configuration
===================================
ML prediction, patient assessment history, and feedback endpoints.
"""

from django.urls import path

from assessments.views import AssessmentViewSet

urlpatterns = [
    path(
        'assessments/predict/',
        AssessmentViewSet.as_view({'post': 'predict'}),
        name='assessment-predict',
    ),
    path(
        'patients/<str:patient_id>/assessments/',
        AssessmentViewSet.as_view({'get': 'list'}),
        name='patient-assessments',
    ),
    path(
        'assessments/<int:pk>/',
        AssessmentViewSet.as_view({'get': 'retrieve'}),
        name='assessment-detail',
    ),
    path(
        'assessments/<int:pk>/feedback/',
        AssessmentViewSet.as_view({'patch': 'feedback'}),
        name='assessment-feedback',
    ),
]
