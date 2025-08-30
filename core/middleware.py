"""
Custom middleware for debugging CSRF issues on Cloud Run
"""

import logging
from django.http import HttpResponse
import json

logger = logging.getLogger(__name__)

class CSRFDebugMiddleware:
    """Middleware to debug CSRF issues"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Log request details before processing
        if request.method == 'POST' and '/login/' in request.path:
            debug_info = {
                'path': request.path,
                'method': request.method,
                'cookies': dict(request.COOKIES),
                'headers': {k: v for k, v in request.META.items() if k.startswith('HTTP_')},
                'is_secure': request.is_secure(),
                'host': request.get_host(),
                'origin': request.META.get('HTTP_ORIGIN'),
                'referer': request.META.get('HTTP_REFERER'),
                'csrf_cookie': request.COOKIES.get('csrftoken'),
                'csrf_header': request.META.get('HTTP_X_CSRFTOKEN'),
                'post_data': dict(request.POST) if request.method == 'POST' else {},
            }
            
            logger.error(f"CSRF DEBUG - Login attempt: {json.dumps(debug_info, default=str)}")
            
            # Check if CSRF token is missing entirely
            has_csrf_cookie = 'csrftoken' in request.COOKIES
            has_csrf_form = 'csrfmiddlewaretoken' in request.POST
            has_csrf_header = 'HTTP_X_CSRFTOKEN' in request.META
            
            logger.error(f"CSRF tokens present - Cookie: {has_csrf_cookie}, Form: {has_csrf_form}, Header: {has_csrf_header}")

        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        """Log CSRF-related exceptions"""
        if 'CSRF' in str(exception):
            logger.error(f"CSRF Exception: {exception}")
            logger.error(f"Request details: {request.META}")
        return None