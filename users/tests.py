from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token

User = get_user_model()


class UserRegistrationTests(APITestCase):
    """Tests for user registration endpoint."""

    def test_register_freelancer_success(self):
        """Test successful freelancer registration."""
        data = {
            'full_name': 'Test Freelancer',
            'email': 'freelancer@example.com',
            'phone': '+233201234567',
            'country': 'GH',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'is_freelancer': True,
            'is_client': False,
        }
        response = self.client.post('/api/users/register/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='freelancer@example.com').exists())

    def test_register_client_success(self):
        """Test successful client registration."""
        data = {
            'full_name': 'Test Client',
            'email': 'client@example.com',
            'phone': '+233209876543',
            'country': 'GH',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'is_freelancer': False,
            'is_client': True,
        }
        response = self.client.post('/api/users/register/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='client@example.com').exists())

    def test_register_password_mismatch(self):
        """Test registration fails with mismatched passwords."""
        data = {
            'full_name': 'Test User',
            'email': 'user@example.com',
            'phone': '+233201111111',
            'country': 'GH',
            'password': 'testpass123',
            'password_confirm': 'differentpass',
            'is_freelancer': True,
            'is_client': False,
        }
        response = self.client.post('/api/users/register/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_email(self):
        """Test registration fails with duplicate email."""
        User.objects.create_user(
            full_name='Existing User',
            email='existing@example.com',
            phone='+233202222222',
            password='testpass123',
        )
        data = {
            'full_name': 'New User',
            'email': 'existing@example.com',
            'phone': '+233203333333',
            'country': 'GH',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'is_freelancer': True,
            'is_client': False,
        }
        response = self.client.post('/api/users/register/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_both_freelancer_and_client(self):
        """Test registration fails when both is_freelancer and is_client are True."""
        data = {
            'full_name': 'Test User',
            'email': 'both@example.com',
            'phone': '+233204444444',
            'country': 'GH',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'is_freelancer': True,
            'is_client': True,
        }
        response = self.client.post('/api/users/register/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserLoginTests(APITestCase):
    """Tests for user login endpoint."""

    def setUp(self):
        self.user = User.objects.create_user(
            full_name='Test User',
            email='testuser@example.com',
            phone='+233205555555',
            password='testpass123',
            is_freelancer=True,
        )

    def test_login_success(self):
        """Test successful login."""
        data = {
            'username': 'testuser@example.com',
            'password': 'testpass123',
        }
        response = self.client.post('/api/users/login/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_login_wrong_password(self):
        """Test login fails with wrong password."""
        data = {
            'username': 'testuser@example.com',
            'password': 'wrongpass',
        }
        response = self.client.post('/api/users/login/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_nonexistent_user(self):
        """Test login fails with nonexistent user."""
        data = {
            'username': 'noone@example.com',
            'password': 'testpass123',
        }
        response = self.client.post('/api/users/login/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserModelTests(TestCase):
    """Tests for User model."""

    def test_create_user(self):
        """Test creating a user."""
        user = User.objects.create_user(
            full_name='Test User',
            email='modeltest@example.com',
            phone='+233206666666',
            password='testpass123',
        )
        self.assertEqual(user.email, 'modeltest@example.com')
        self.assertEqual(user.full_name, 'Test User')
        self.assertTrue(user.check_password('testpass123'))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        """Test creating a superuser."""
        admin = User.objects.create_superuser(
            full_name='Admin User',
            email='admin@example.com',
            phone='+233207777777',
            password='adminpass123',
        )
        self.assertEqual(admin.email, 'admin@example.com')
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)

    def test_user_str(self):
        """Test user string representation."""
        user = User.objects.create_user(
            full_name='String Test',
            email='strtest@example.com',
            phone='+233208888888',
            password='testpass123',
        )
        self.assertEqual(str(user), 'String Test (strtest@example.com)')
