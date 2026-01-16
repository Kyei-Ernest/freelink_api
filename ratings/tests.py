from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from jobs.models import Job
from contracts.models import Contract
from .models import Rating

User = get_user_model()


class RatingModelTests(TestCase):
    """Tests for Rating model."""

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
        self.job = Job.objects.create(
            client=self.client_user,
            title='Test Job',
            description='Test description',
            budget=100.00,
            freelancer=self.freelancer_user,
            status='completed',
        )

    def test_create_rating(self):
        """Test creating a rating."""
        rating = Rating.objects.create(
            job=self.job,
            reviewer=self.client_user,
            reviewee=self.freelancer_user,
            rating=5,
            comment='Excellent work!',
        )
        self.assertEqual(rating.rating, 5)
        self.assertEqual(rating.reviewer, self.client_user)
        self.assertEqual(rating.reviewee, self.freelancer_user)

    def test_rating_validation_min(self):
        """Test that rating cannot be less than 1."""
        rating = Rating(
            job=self.job,
            reviewer=self.client_user,
            reviewee=self.freelancer_user,
            rating=0,
        )
        with self.assertRaises(Exception):
            rating.full_clean()

    def test_rating_validation_max(self):
        """Test that rating cannot be more than 5."""
        rating = Rating(
            job=self.job,
            reviewer=self.client_user,
            reviewee=self.freelancer_user,
            rating=6,
        )
        with self.assertRaises(Exception):
            rating.full_clean()

    def test_rating_str(self):
        """Test rating string representation."""
        rating = Rating.objects.create(
            job=self.job,
            reviewer=self.client_user,
            reviewee=self.freelancer_user,
            rating=4,
        )
        self.assertIn('freelancer@example.com', str(rating))
        self.assertIn('4/5', str(rating))
