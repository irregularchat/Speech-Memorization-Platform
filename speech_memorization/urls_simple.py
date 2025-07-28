"""
Simplified URL configuration for deployment testing
Removes complex app dependencies that cause import errors
"""
from django.contrib import admin
from django.urls import path
from django.http import JsonResponse

def health_check(request):
    """Simple health check endpoint"""
    return JsonResponse({'status': 'healthy', 'message': 'Speech Memorization Platform - Simple Deployment'})

def home_simple(request):
    """Simple home page"""
    return JsonResponse({'message': 'Welcome to Speech Memorization Platform', 'status': 'running'})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health_check'),
    path('', home_simple, name='home'),
]