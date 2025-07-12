"""
URL configuration for speech_memorization project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

from core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Core views
    path('', core_views.home, name='home'),
    path('practice/<int:text_id>/', core_views.practice_text, name='practice_text'),
    path('analytics/', core_views.analytics, name='analytics'),
    # Include memorization app URLs
    path('', include('memorization.urls')),
    path('about/', core_views.about, name='about'),
    
    # AJAX endpoints
    path('api/update-mastery/', core_views.update_mastery_level, name='update_mastery_level'),
    path('api/start-session/', core_views.start_practice_session, name='start_practice_session'),
    path('api/complete-session/', core_views.complete_practice_session, name='complete_practice_session'),
    
    # Authentication
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', auth_views.LoginView.as_view(template_name='registration/signup.html'), name='signup'),
    
    # App includes (for future development)
    # path('api/v1/', include('api.urls')),
    # path('users/', include('users.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
