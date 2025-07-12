from django.urls import path
from . import views

urlpatterns = [
    # Text management
    path('texts/', views.text_list, name='text_list'),
    path('texts/create/', views.create_text, name='create_text'),
    path('texts/upload/', views.upload_text_file, name='upload_text_file'),
    path('texts/<int:text_id>/', views.text_detail, name='text_detail'),
    path('texts/<int:text_id>/edit/', views.edit_text, name='edit_text'),
    path('texts/<int:text_id>/delete/', views.delete_text, name='delete_text'),
    path('texts/<int:text_id>/duplicate/', views.duplicate_text, name='duplicate_text'),
    path('texts/<int:text_id>/toggle-visibility/', views.toggle_text_visibility, name='toggle_text_visibility'),
    
    # AJAX endpoints
    path('api/texts/create/', views.create_text_ajax, name='create_text_ajax'),
]