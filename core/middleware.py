"""
Core API performance and telemetry middleware.
"""
import time


class RequestTimingMiddleware:
    """
    Measures the execution time of incoming requests and attaches
    the duration in milliseconds as a response header (X-Process-Time-Ms).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)
        duration_ms = round((time.time() - start_time) * 1000, 2)
        response['X-Process-Time-Ms'] = str(duration_ms)
        return response
