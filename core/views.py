"""
Lightweight health-check view for load balancers / uptime monitors.
GET /api/v1/health/ → { "status": "ok", "version": "1.0" }
"""

from django.http import JsonResponse
from django.views import View


class HealthCheckView(View):
    def get(self, request):
        return JsonResponse({'status': 'ok', 'version': '1.0', 'app': 'ProgressX API'})
