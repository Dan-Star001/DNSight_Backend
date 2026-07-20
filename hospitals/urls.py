"""
Hospitals — URL Configuration
================================
Admin management, hospital analytics, and doctor dashboard endpoints.
"""

from django.urls import path

from hospitals.views import AdminViewSet, DoctorStatsView

urlpatterns = [
    path('admin/doctors/', AdminViewSet.as_view({'get': 'list'}), name='admin-doctors-list'),
    path(
        'admin/doctors/<int:pk>/approve/',
        AdminViewSet.as_view({'patch': 'approve'}),
        name='admin-doctor-approve',
    ),
    path(
        'admin/doctors/<int:pk>/reject/',
        AdminViewSet.as_view({'patch': 'reject'}),
        name='admin-doctor-reject',
    ),
    path('admin/stats/', AdminViewSet.as_view({'get': 'stats'}), name='admin-stats'),
    path('doctor/stats/', DoctorStatsView.as_view(), name='doctor-stats'),
]
