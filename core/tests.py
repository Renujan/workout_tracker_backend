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
