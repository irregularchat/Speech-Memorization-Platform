"""
Ultra-minimal URL configuration for testing
"""

from django.http import JsonResponse
from django.urls import path

def health_check(request):
    return JsonResponse({'status': 'healthy', 'message': 'Django test deployment working'})

def home_test(request):
    return JsonResponse({'message': 'Speech Memorization Platform - Test Deployment'})

urlpatterns = [
    path('health/', health_check, name='health'),
    path('', home_test, name='home'),
]