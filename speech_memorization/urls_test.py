"""
Ultra-minimal URL configuration for testing
"""

from django.http import JsonResponse
from django.urls import path

def health_check(request):
    return JsonResponse({'status': 'healthy', 'message': 'Django test deployment working'})

def home_test(request):
    return JsonResponse({'message': 'Speech Memorization Platform - Test Deployment'})

def simple_test(request):
    """Ultra simple test that should always work"""
    return JsonResponse({'test': 'success', 'django': 'working'})

urlpatterns = [
    path('health/', health_check, name='health'),
    path('simple/', simple_test, name='simple'),
    path('', home_test, name='home'),
]