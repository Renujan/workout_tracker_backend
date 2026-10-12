"""
Basic API tests for the users app.
Run: python manage.py test users
"""

from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status


class AuthAPITestCase(TestCase):
    """Test JWT register, login, and profile endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.register_url = '/api/v1/auth/register/'
        self.login_url = '/api/v1/auth/login/'
        self.profile_url = '/api/v1/users/profile/'

    # ── Registration ──────────────────────────────────────────────────────────
    def test_register_creates_user_and_returns_jwt(self):
        payload = {
            'username': 'testuser',
            'email': 'test@progressx.app',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'strongpass123',
            'password2': 'strongpass123',
        }
        res = self.client.post(self.register_url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', res.data)
        self.assertIn('refresh', res.data)
        self.assertEqual(res.data['user']['username'], 'testuser')
        self.assertTrue(User.objects.filter(username='testuser').exists())

    def test_register_password_mismatch_returns_400(self):
        payload = {
            'username': 'baduser',
            'email': 'bad@progressx.app',
            'password': 'pass1234',
            'password2': 'different',
        }
        res = self.client.post(self.register_url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # ── Login ─────────────────────────────────────────────────────────────────
    def test_login_returns_jwt_tokens(self):
        User.objects.create_user(username='loginuser', password='gym12345')
        res = self.client.post(self.login_url, {'username': 'loginuser', 'password': 'gym12345'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('access', res.data)
        self.assertIn('refresh', res.data)

    def test_login_wrong_password_returns_401(self):
        User.objects.create_user(username='user2', password='correct')
        res = self.client.post(self.login_url, {'username': 'user2', 'password': 'wrong'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    # ── Profile ───────────────────────────────────────────────────────────────
    def test_profile_requires_authentication(self):
        res = self.client.get(self.profile_url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_can_get_profile(self):
        user = User.objects.create_user(username='profileuser', password='gym12345')
        self.client.force_authenticate(user=user)
        res = self.client.get(self.profile_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['username'], 'profileuser')

    # ── Password Change ───────────────────────────────────────────────────────
    def test_authenticated_user_can_change_password(self):
        user = User.objects.create_user(username='pwduser', password='oldpass123')
        self.client.force_authenticate(user=user)
        url = '/api/v1/auth/password/change/'
        payload = {
            'old_password': 'oldpass123',
            'new_password': 'newstrongpass456',
            'new_password_confirm': 'newstrongpass456',
        }
        res = self.client.post(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.check_password('newstrongpass456'))

    def test_change_password_wrong_old_password_fails(self):
        user = User.objects.create_user(username='pwduser2', password='oldpass123')
        self.client.force_authenticate(user=user)
        url = '/api/v1/auth/password/change/'
        payload = {
            'old_password': 'wrongpassword',
            'new_password': 'newstrongpass456',
            'new_password_confirm': 'newstrongpass456',
        }
        res = self.client.post(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

