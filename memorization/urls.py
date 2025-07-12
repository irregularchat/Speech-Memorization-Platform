from django.urls import path
from . import views, practice_views, ai_practice_views

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
    
    # Enhanced practice
    path('practice/<int:text_id>/enhanced/', practice_views.practice_text_enhanced, name='practice_text_enhanced'),
    
    # Practice AJAX endpoints
    path('api/practice/start/', practice_views.start_adaptive_session, name='start_adaptive_session'),
    path('api/practice/speech/', ai_practice_views.process_ai_speech_input, name='process_speech_input'),
    path('api/practice/hint/', practice_views.request_hint, name='request_hint'),
    path('api/practice/advance/', practice_views.advance_word, name='advance_word'),
    path('api/practice/timing/', practice_views.check_word_timing, name='check_word_timing'),
    path('api/practice/complete/', practice_views.complete_adaptive_session, name='complete_adaptive_session'),
    path('api/practice/state/', practice_views.get_session_state, name='get_session_state'),
    
    # AI Speech endpoints
    path('api/practice/pronunciation-feedback/', ai_practice_views.get_ai_pronunciation_feedback, name='get_ai_pronunciation_feedback'),
    path('api/practice/test-microphone/', ai_practice_views.test_microphone_quality, name='test_microphone_quality'),
    
    # Text management AJAX endpoints
    path('api/texts/create/', views.create_text_ajax, name='create_text_ajax'),
]