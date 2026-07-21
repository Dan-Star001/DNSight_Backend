"""
Users — DRF Views
====================
Authentication views: admin/doctor registration, JWT token with status
enforcement, and user profile retrieval.
"""

from django.utils import datastructures
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.core.cache import cache
from hospitals.views import CACHE_KEY_ADMIN_STATS

from hospitals.models import Hospital
from users.permissions import IsActiveUser
from users.serializers import (AdminRegistrationSerializer,DoctorRegistrationSerializer,UserSerializer,)

User = get_user_model()


class AdminRegistrationView(APIView):
    """POST /api/auth/admin/register/

    Atomically creates a new Hospital and its first Admin user in a single
    database transaction. Returns JWT tokens on success.
    """

    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        try:
            serializer = AdminRegistrationSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data

            # Use request.FILES directly — more reliable with Cloudinary than
            # the InMemoryUploadedFile from serializer validated_data.
            logo_file = request.FILES.get('logo')
            logo_url = None
            if logo_file:
                import cloudinary.uploader
                from rest_framework.exceptions import ValidationError
                try:
                    upload_result = cloudinary.uploader.upload(
                        logo_file,
                        folder='hospital_logos',
                        resource_type='image',
                        timeout=10,
                    )
                    logo_url = upload_result.get('secure_url')
                except Exception as e:
                    raise ValidationError({'logo': f'Image upload failed: {str(e)}'})

            hospital = Hospital.objects.create(
                name=data['hospital_name'],
                logo=logo_url
            )

            user = User.objects.create_user(
                email=data['email'],
                password=data['password'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                hospital=hospital,
                role='ADMIN',
                status='ACTIVE',
                is_staff=True,
            )

            refresh = RefreshToken.for_user(user)

            return Response(
                {
                    'message': 'Hospital and admin account created successfully.',
                    'hospital': {
                        'id': hospital.id,
                        'name': hospital.name,
                    },
                    'user': UserSerializer(user, context={'request': request}).data,
                    'tokens': {
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                    },
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            return Response(
                {"detail": str(e), "traceback": error_details},
                status=status.HTTP_400_BAD_REQUEST
            )


class DoctorRegistrationView(APIView):
    """POST /api/auth/doctor/register/

    Creates a new Doctor user with PENDING status.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = DoctorRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = User.objects.create_user(
            email=data['email'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            hospital_id=data['hospital_id'],
            role='DOCTOR',
            status='PENDING',
        )

        from users.tasks import send_doctor_registration_email
        send_doctor_registration_email.delay(user.email, user.first_name)

        return Response(
            {
                'message': (
                    'Registration successful. Your account is pending '
                    'admin approval.'
                ),
                'user': UserSerializer(user, context={'request': request}).data,
            },
            status=status.HTTP_201_CREATED,
        )


class CustomTokenObtainPairView(TokenObtainPairView):
    """POST /api/auth/token/

    Extends SimpleJWT to enforce that only ACTIVE users can obtain tokens.
    """

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            try:
                # Add select_related to avoid N+1 query on hospital.name
                user = User.objects.select_related('hospital').get(email=request.data.get('email', ''))
            except User.DoesNotExist:
                return response

            if user.status == 'PENDING':
                return Response(
                    {'detail': 'Your account is pending admin approval.'},
                    status=status.HTTP_403_FORBIDDEN,
                )
            elif user.status == 'REJECTED':
                return Response(
                    {'detail': 'Your account has been rejected. Contact support.'},
                    status=status.HTTP_403_FORBIDDEN,
                )

            response.data['user'] = UserSerializer(user, context={'request': request}).data

        return response


class UserProfileView(APIView):
    """GET /api/users/me/

    Returns the full profile of the currently authenticated user.
    """

    permission_classes = [IsAuthenticated, IsActiveUser]

    def get(self, request):
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data)
