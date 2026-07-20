"""
Users — DRF Serializers
=========================
Covers user profile display and auth registration workflows.
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from hospitals.models import Hospital

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Read-only serializer for user profile data. Never exposes the password."""

    hospital_name = serializers.CharField(source='hospital.name', read_only=True)
    hospital_logo = serializers.URLField(source='hospital.logo', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name',
            'role', 'status', 'hospital', 'hospital_name', 'hospital_logo',
            'date_joined',
        ]
        read_only_fields = fields


class AdminRegistrationSerializer(serializers.Serializer):
    """Handles the transactional creation of a Hospital + Admin user.
    Accepts hospital name alongside standard user fields."""

    hospital_name = serializers.CharField(max_length=255)
    logo = serializers.FileField(required=False, allow_null=True)
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value.lower()


class DoctorRegistrationSerializer(serializers.Serializer):
    """Registers a new doctor under an existing hospital.
    The doctor starts with PENDING status and must be approved by an admin."""

    hospital_id = serializers.CharField(max_length=50)
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value.lower()

    def validate_hospital_id(self, value):
        if not Hospital.objects.filter(id=value).exists():
            raise serializers.ValidationError('Hospital not found.')
        return value
