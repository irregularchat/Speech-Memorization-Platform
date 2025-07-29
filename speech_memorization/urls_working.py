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

# Add memorization URLs with fallbacks for missing views
try:
    # Import memorization views if available
    from memorization import views as memorization_views
    # Add text management URLs
    urlpatterns.extend([
        path('texts/', memorization_views.text_list, name='text_list'),
        path('texts/create/', memorization_views.create_text, name='create_text'),
        path('texts/<int:text_id>/', memorization_views.text_detail, name='text_detail'),
        path('texts/<int:text_id>/edit/', memorization_views.edit_text, name='edit_text'),
    ])
    # Include full memorization URLs
    urlpatterns.append(path('', include('memorization.urls')))
except ImportError:
    # Add fallback URLs for text_list and other common references
    def text_list_fallback(request):
        return JsonResponse({
            'message': 'Text management in demo mode',
            'texts': [
                {'id': 1, 'title': 'Demo Text 1', 'description': 'Sample memorization text'},
                {'id': 2, 'title': 'Demo Text 2', 'description': 'Another sample text'},
            ],
            'note': 'Full functionality requires database setup'
        })
    
    def text_create_fallback(request):
        return JsonResponse({'message': 'Text creation available in full deployment'})
    
    urlpatterns.extend([
        path('texts/', text_list_fallback, name='text_list'),
        path('texts/create/', text_create_fallback, name='create_text'),
    ])

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)