from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from .models import Job, Skill

User = get_user_model()


class JobModelTests(TestCase):
    """Tests for Job model."""

    def setUp(self):
        self.client_user = User.objects.create_user(
            full_name='Test Client',
            email='client@example.com',
            phone='+233201234567',
            password='testpass123',
            is_client=True,
        )
        self.freelancer_user = User.objects.create_user(
            full_name='Test Freelancer',
            email='freelancer@example.com',
            phone='+233209876543',
            password='testpass123',
            is_freelancer=True,
        )

    def test_create_job(self):
        """Test creating a job."""
        job = Job.objects.create(
            client=self.client_user,
            title='Test Job',
            description='Test job description',
            budget=100.00,
        )
        self.assertEqual(job.title, 'Test Job')
        self.assertEqual(job.client, self.client_user)
        self.assertEqual(job.status, 'available')

    def test_job_str(self):
        """Test job string representation."""
        job = Job.objects.create(
            client=self.client_user,
            title='String Test Job',
            description='Description',
            budget=50.00,
        )
        self.assertEqual(str(job), 'String Test Job')


class JobAPITests(APITestCase):
    """Tests for Job API endpoints."""

    def setUp(self):
        self.client_user = User.objects.create_user(
            full_name='API Client',
            email='apiclient@example.com',
            phone='+233201111111',
            password='testpass123',
            is_client=True,
        )
        self.freelancer_user = User.objects.create_user(
            full_name='API Freelancer',
            email='apifreelancer@example.com',
            phone='+233202222222',
            password='testpass123',
            is_freelancer=True,
        )
        self.client_token = Token.objects.create(user=self.client_user)
        self.freelancer_token = Token.objects.create(user=self.freelancer_user)
        self.api_client = APIClient()

    def test_list_jobs_authenticated(self):
        """Test listing jobs as authenticated user."""
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.client_token.key}')
        Job.objects.create(
            client=self.client_user,
            title='Test Job 1',
            description='Description 1',
            budget=100.00,
        )
        response = self.api_client.get('/api/jobs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle paginated response
        if 'results' in response.data:
            self.assertEqual(len(response.data['results']), 1)
        else:
            self.assertEqual(len(response.data), 1)

    def test_create_job_as_client(self):
        """Test creating a job as client."""
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.client_token.key}')
        data = {
            'title': 'New Job',
            'description': 'Job description',
            'budget': '150.00',
        }
        response = self.api_client.post('/api/jobs/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Job.objects.count(), 1)
        self.assertEqual(Job.objects.first().client, self.client_user)

    def test_create_job_as_freelancer_fails(self):
        """Test that freelancers cannot create jobs."""
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.freelancer_token.key}')
        data = {
            'title': 'Freelancer Job',
            'description': 'Should fail',
            'budget': '100.00',
        }
        response = self.api_client.post('/api/jobs/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_jobs_unauthenticated(self):
        """Test listing jobs without authentication fails."""
        response = self.api_client.get('/api/jobs/')
        # DRF with SessionAuthentication returns 403 for unauthenticated requests
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])


class SkillModelTests(TestCase):
    """Tests for Skill model."""

    def test_create_skill(self):
        """Test creating a skill."""
        skill = Skill.objects.create(name='Python')
        self.assertEqual(skill.name, 'Python')
        self.assertEqual(str(skill), 'Python')

    def test_skill_unique_name(self):
        """Test that skill names are unique."""
        Skill.objects.create(name='Django')
        with self.assertRaises(Exception):
            Skill.objects.create(name='Django')
