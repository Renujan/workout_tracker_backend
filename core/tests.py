"""
Tests for core app endpoints and middleware.
"""
from django.test import TestCase, Client


class CoreMiddlewareAndHealthCheckTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_health_check_endpoint(self):
        res = self.client.get('/api/v1/health/')
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['app'], 'ProgressX API')
        self.assertIn('database', data)

    def test_request_timing_middleware_header(self):
        res = self.client.get('/api/v1/health/')
        self.assertIn('X-Process-Time-Ms', res.headers)
        # Value should be a valid float string
        duration = float(res.headers['X-Process-Time-Ms'])
        self.assertGreaterEqual(duration, 0.0)

    def test_user_data_export_archive(self):
        from django.contrib.auth.models import User
        from rest_framework.test import APIClient
        user = User.objects.create_user(username='exportuser', password='password123')
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        res = api_client.get('/api/v1/export/userdata/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('export_metadata', res.data)
        self.assertEqual(res.data['export_metadata']['username'], 'exportuser')
        self.assertIn('workouts', res.data)
        self.assertIn('nutrition', res.data)
        self.assertIn('progress', res.data)
