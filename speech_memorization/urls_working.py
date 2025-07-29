"""
Working URL configuration for Speech Memorization Platform
Includes core functionality with graceful handling of missing components
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

# Import core views (these should work with graceful fallbacks)
from core import views as core_views

# Health check function
def health_check(request):
    """Health check endpoint for monitoring"""
    return JsonResponse({
        'status': 'healthy', 
        'message': 'Speech Memorization Platform - Full Application',
        'version': '1.0',
        'django': 'running'
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Health check
    path('health/', health_check, name='health_check'),
    
    # Core application views
    path('', core_views.home, name='home'),
    path('about/', core_views.about, name='about'),
    path('analytics/', core_views.analytics, name='analytics'),
    
    # Authentication
    path('login/', core_views.demo_login, name='login'),
    path('logout/', core_views.demo_logout, name='logout'),
    
    # API endpoints (should work with demo data)
    path('api/update-mastery/', core_views.update_mastery_level, name='update_mastery_level'),
    path('api/start-session/', core_views.start_practice_session, name='start_practice_session'),
    path('api/complete-session/', core_views.complete_practice_session, name='complete_practice_session'),
]

# Only include memorization URLs if the app is properly configured
try:
    # Test if memorization app can be imported
    from memorization import urls as memorization_urls
    urlpatterns.append(path('practice/', include('memorization.urls')))
except ImportError:
    # Add a fallback practice URL that shows demo content
    def practice_fallback(request):
        return JsonResponse({
            'message': 'Practice features available in demo mode',
            'note': 'Full practice functionality requires database setup'
        })
    urlpatterns.append(path('practice/', practice_fallback, name='practice_fallback'))

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)