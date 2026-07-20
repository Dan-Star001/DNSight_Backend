"""
Hospitals — DRF Serializers
==============================
Basic hospital CRUD serializer.
"""

from rest_framework import serializers

from hospitals.models import Hospital


class HospitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = ['id', 'name', 'logo', 'created_at']
        read_only_fields = ['id', 'created_at']
