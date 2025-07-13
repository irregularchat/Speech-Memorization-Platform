from django.urls import path
from . import views, practice_views, ai_practice_views, enhanced_practice_views

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
    path('practice/<int:text_id>/enhanced/', enhanced_practice_views.enhanced_practice_dashboard, name='enhanced_practice_dashboard'),
    path('practice/<int:text_id>/legacy/', practice_views.practice_text_enhanced, name='practice_text_enhanced'),
    
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
    path('api/practice/streaming-chunk/', ai_practice_views.process_streaming_speech_chunk, name='process_streaming_speech_chunk'),
    path('api/practice/stop-streaming/', ai_practice_views.stop_streaming_session, name='stop_streaming_session'),
    
    # Phrase-based practice endpoints (Natural Speech)
    path('api/practice/phrase/start/', ai_practice_views.start_phrase_practice_session, name='start_phrase_practice_session'),
    path('api/practice/phrase/process/', ai_practice_views.process_phrase_speech, name='process_phrase_speech'),
    path('api/practice/phrase/next/', ai_practice_views.get_next_phrase, name='get_next_phrase'),
    path('api/practice/phrase/complete/', ai_practice_views.complete_phrase_practice_session, name='complete_phrase_practice_session'),
    
    # Enhanced practice API endpoints
    path('api/enhanced/start-word-reveal/', enhanced_practice_views.start_word_reveal_session, name='start_word_reveal_session'),
    path('api/enhanced/start-delayed-recall/', enhanced_practice_views.start_delayed_recall_session, name='start_delayed_recall_session'),
    path('api/enhanced/advance-reveal-round/', enhanced_practice_views.advance_word_reveal_round, name='advance_word_reveal_round'),
    path('api/enhanced/transition-recall/', enhanced_practice_views.transition_to_recall_phase, name='transition_to_recall_phase'),
    path('api/enhanced/process-speech/', enhanced_practice_views.process_enhanced_speech_input, name='process_enhanced_speech_input'),
    path('api/enhanced/apply-hint/', enhanced_practice_views.apply_intelligent_hint, name='apply_intelligent_hint'),
    path('api/enhanced/check-timing/', enhanced_practice_views.check_word_timing, name='check_enhanced_word_timing'),
    path('api/enhanced/complete-session/', enhanced_practice_views.complete_enhanced_session, name='complete_enhanced_session'),
    path('api/enhanced/analytics/<int:text_id>/', enhanced_practice_views.get_practice_analytics, name='get_practice_analytics'),
    path('api/enhanced/recommendations/<int:text_id>/', enhanced_practice_views.get_session_recommendations, name='get_session_recommendations'),
    
    # Text management AJAX endpoints
    path('api/texts/create/', views.create_text_ajax, name='create_text_ajax'),
]