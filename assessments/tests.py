"""
Unit and Integration Tests for Assessments App
===============================================
Tests:
- 3-tier clinical risk classification logic
- Serializer validation (including physiological cross-field check: ONSET_AGE <= AGE)
- Assessment model persistence including LR, KNN, and GNB scores
- Multi-tenant isolation for assessment retrieval
"""

from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient, APIRequestFactory

from assessments.models import Assessment
from assessments.serializers import AssessmentSerializer, PredictionInputSerializer
from hospitals.models import Hospital
from patients.models import Patient

User = get_user_model()


class AssessmentRiskLevelTest(TestCase):
    """Verifies the three-tier clinical risk classification."""

    def test_risk_level_boundaries(self):
        # Low: < 30%
        self.assertEqual(Assessment.compute_risk_level(0.0), 'LOW')
        self.assertEqual(Assessment.compute_risk_level(29.99), 'LOW')

        # Medium: 30% - 70%
        self.assertEqual(Assessment.compute_risk_level(30.0), 'MEDIUM')
        self.assertEqual(Assessment.compute_risk_level(50.0), 'MEDIUM')
        self.assertEqual(Assessment.compute_risk_level(69.99), 'MEDIUM')

        # High: >= 70%
        self.assertEqual(Assessment.compute_risk_level(70.0), 'HIGH')
        self.assertEqual(Assessment.compute_risk_level(85.5), 'HIGH')
        self.assertEqual(Assessment.compute_risk_level(100.0), 'HIGH')


class PredictionInputValidationTest(TestCase):
    """Verifies data validation in PredictionInputSerializer."""

    def setUp(self):
        self.hospital = Hospital.objects.create(name='City Hospital')
        self.doctor = User.objects.create_user(
            email='dr.test@cityhospital.org',
            password='TestPassword123!',
            first_name='John',
            last_name='Doe',
            hospital=self.hospital,
            role='DOCTOR',
            status='ACTIVE',
        )
        self.patient = Patient.objects.create(
            first_name='Alice',
            last_name='Smith',
            date_of_birth='1980-01-01',
            gender='FEMALE',
            hospital=self.hospital,
        )
        self.valid_data = {
            'patient_id': str(self.patient.id),
            'AGE': 55.0,
            'SEX': 1,
            'BMI': 28.5,
            'SP': 130.0,
            'BP': 85.0,
            'HbA1c': 7.2,
            'FPS': 140.0,
            'PPS': 180.0,
            'FAMILY_HO': 1,
            'SMOKING': 0,
            'ONSET_AGE': 45.0,
        }

    def test_valid_clinical_data(self):
        factory = APIRequestFactory()
        request = factory.post('/api/assessments/predict/')
        request.user = self.doctor

        serializer = PredictionInputSerializer(
            data=self.valid_data,
            context={'request': request},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_onset_age_exceeding_current_age_rejected(self):
        invalid_data = self.valid_data.copy()
        invalid_data['AGE'] = 40.0
        invalid_data['ONSET_AGE'] = 50.0  # Invalid: Onset age > current age

        factory = APIRequestFactory()
        request = factory.post('/api/assessments/predict/')
        request.user = self.doctor

        serializer = PredictionInputSerializer(
            data=invalid_data,
            context={'request': request},
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('ONSET_AGE', serializer.errors)
        self.assertIn("Age at diabetes onset cannot exceed the patient's current age.", str(serializer.errors['ONSET_AGE']))

    def test_negative_or_zero_age_rejected(self):
        invalid_data = self.valid_data.copy()
        invalid_data['AGE'] = -5.0

        factory = APIRequestFactory()
        request = factory.post('/api/assessments/predict/')
        request.user = self.doctor

        serializer = PredictionInputSerializer(
            data=invalid_data,
            context={'request': request},
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('AGE', serializer.errors)

    def test_patient_cross_tenant_rejected(self):
        other_hospital = Hospital.objects.create(name='Other Hospital')
        other_doctor = User.objects.create_user(
            email='dr.other@otherhospital.org',
            password='TestPassword123!',
            first_name='Bob',
            last_name='Jones',
            hospital=other_hospital,
            role='DOCTOR',
        )

        factory = APIRequestFactory()
        request = factory.post('/api/assessments/predict/')
        request.user = other_doctor  # Doctor from other hospital

        serializer = PredictionInputSerializer(
            data=self.valid_data,
            context={'request': request},
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('patient_id', serializer.errors)


class AssessmentModelAndSerializationTest(TestCase):
    """Verifies Assessment persistence with all 3 ML model scores and multi-tenant isolation."""

    def setUp(self):
        self.hospital_a = Hospital.objects.create(name='Hospital Alpha')
        self.hospital_b = Hospital.objects.create(name='Hospital Beta')

        self.doctor_a = User.objects.create_user(
            email='doctor.a@alpha.org',
            password='Password123!',
            first_name='Alpha',
            last_name='Doctor',
            hospital=self.hospital_a,
            role='DOCTOR',
            status='ACTIVE',
        )
        self.patient_a = Patient.objects.create(
            first_name='Patient',
            last_name='Alpha',
            date_of_birth='1975-05-15',
            gender='MALE',
            hospital=self.hospital_a,
        )

    def test_assessment_creation_with_all_three_scores(self):
        assessment = Assessment.objects.create(
            patient=self.patient_a,
            doctor=self.doctor_a,
            clinical_data={'AGE': 50, 'ONSET_AGE': 40},
            risk_score=75.5,
            risk_level=Assessment.compute_risk_level(75.5),
            prediction_confidence=0.82,
            knn_score=78.0,
            gnb_score=68.0,
            lr_score=74.2,
        )

        retrieved = Assessment.objects.get(id=assessment.id)
        self.assertEqual(retrieved.risk_level, 'HIGH')
        self.assertEqual(retrieved.knn_score, 78.0)
        self.assertEqual(retrieved.gnb_score, 68.0)
        self.assertEqual(retrieved.lr_score, 74.2)

        serializer = AssessmentSerializer(retrieved)
        data = serializer.data
        self.assertEqual(data['knn_score'], 78.0)
        self.assertEqual(data['gnb_score'], 68.0)
        self.assertEqual(data['lr_score'], 74.2)
        self.assertEqual(data['risk_level'], 'HIGH')
        self.assertEqual(data['patient_name'], 'Patient Alpha')
        self.assertEqual(data['doctor_name'], 'Alpha Doctor')

    @patch('assessments.views.generate_ai_treatment_suggestion.delay')
    @patch('assessments.views.http_client.post')
    def test_predict_view_end_to_end_persistence(self, mock_post, mock_celery):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'success',
            'knn_score': 91.3,
            'gnb_score': 58.72,
            'lr_score': 77.2,
            'risk_score': 76.75,
            'probability': 0.7675,
            'prediction': 1,
            'risk_category': 'HIGH',
        }
        mock_post.return_value = mock_response

        client = APIClient()
        client.force_authenticate(user=self.doctor_a)

        payload = {
            'patient_id': str(self.patient_a.id),
            'AGE': 55.0,
            'SEX': 1,
            'BMI': 28.5,
            'SP': 130.0,
            'BP': 85.0,
            'HbA1c': 7.2,
            'FPS': 140.0,
            'PPS': 180.0,
            'FAMILY_HO': 1,
            'SMOKING': 0,
            'ONSET_AGE': 45.0,
        }

        response = client.post('/api/assessments/predict/', payload, format='json')
        self.assertEqual(response.status_code, 201)
        resp_data = response.json()

        self.assertEqual(resp_data['knn_score'], 91.3)
        self.assertEqual(resp_data['gnb_score'], 58.72)
        self.assertEqual(resp_data['lr_score'], 77.2)
        self.assertEqual(resp_data['risk_score'], 76.75)
        self.assertEqual(resp_data['risk_level'], 'HIGH')

        # Verify DB record
        created_assessment = Assessment.objects.get(id=resp_data['id'])
        self.assertEqual(created_assessment.lr_score, 77.2)
        self.assertEqual(created_assessment.knn_score, 91.3)
        self.assertEqual(created_assessment.gnb_score, 58.72)
        self.assertEqual(created_assessment.risk_level, 'HIGH')

    def test_predict_view_rejects_invalid_onset_age(self):
        client = APIClient()
        client.force_authenticate(user=self.doctor_a)

        payload = {
            'patient_id': str(self.patient_a.id),
            'AGE': 45.0,
            'SEX': 1,
            'BMI': 28.5,
            'SP': 130.0,
            'BP': 85.0,
            'HbA1c': 7.2,
            'FPS': 140.0,
            'PPS': 180.0,
            'FAMILY_HO': 1,
            'SMOKING': 0,
            'ONSET_AGE': 55.0,  # Invalid: onset > age
        }

        response = client.post('/api/assessments/predict/', payload, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('ONSET_AGE', response.json())
