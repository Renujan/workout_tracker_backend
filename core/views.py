"""
Health-check view for load balancers and system monitoring.
GET /api/v1/health/
"""

import time
from django.db import connection
from django.http import JsonResponse
from django.views import View


class HealthCheckView(View):
    """GET /api/v1/health/ — system status, database ping, and latency."""
    def get(self, request):
        db_status = 'ok'
        db_latency_ms = 0.0
        try:
            start = time.time()
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1;')
            db_latency_ms = round((time.time() - start) * 1000, 2)
        except Exception as e:
            db_status = f'error: {str(e)}'

        is_healthy = db_status == 'ok'
        return JsonResponse({
            'status': 'healthy' if is_healthy else 'degraded',
            'version': '1.1.0',
            'app': 'ProgressX API',
            'database': {
                'status': db_status,
                'latency_ms': db_latency_ms,
            },
        }, status=200 if is_healthy else 503)
