import re
import time
from typing import List, Dict, Tuple, Optional
from django.utils import timezone
from .models import Text, WordProgress, PracticeSession, UserTextProgress


class PracticeWordState:
    """Represents the state of a single word during practice"""
    def __init__(self, word: str, index: int, mastery_level: float = 0.0):
        self.word = word.strip()
        self.index = index
        self.mastery_level = mastery_level
        self.is_visible = True
        self.is_current = False
        self.is_completed = False
        self.hint_level = 0  # 0: no hint, 1: first letter, 2: partial word, 3: full word
        self.attempts = 0
        self.time_stuck = 0.0  # seconds stuck on this word
        self.needs_hint = False


class AdaptivePracticeEngine:
    """Manages the adaptive practice session with word-level tracking"""
    
    def __init__(self, text: Text, user, mastery_threshold: float = 0.7):
        self.text = text
        self.user = user
        self.mastery_threshold = mastery_threshold
        self.words = self._parse_text_words()
        self.current_word_index = 0
        self.session_start_time = timezone.now()
        self.word_start_time = None
        self.delay_threshold = 3.0  # seconds before offering hint
        self.pause_threshold = 5.0  # seconds before auto-advancing
        self.practice_session = None
        
    def _parse_text_words(self) -> List[PracticeWordState]:
        """Parse text into individual words with their mastery levels"""
        # Clean text and split into words
        cleaned_text = re.sub(r'[^\w\s\'-]', ' ', self.text.content)
        word_list = [word for word in cleaned_text.split() if word.strip()]
        
        # Get existing word progress
        word_progress_map = {}
        if self.user.is_authenticated:
            progress_entries = WordProgress.objects.filter(
                user=self.user,
                text=self.text
            )
            word_progress_map = {wp.word_index: wp.mastery_level for wp in progress_entries}
        
        # Create practice word states
        practice_words = []
        for i, word in enumerate(word_list):
            mastery = word_progress_map.get(i, 0.0)
            practice_word = PracticeWordState(word, i, mastery)
            practice_words.append(practice_word)
            
        return practice_words
    
    def get_display_text(self, global_mastery_level: float = 0.0) -> str:
        """Generate display text with appropriate word masking"""
        display_parts = []
        
        for word_state in self.words:
            word = word_state.word
            
            # Determine if word should be hidden based on mastery
            should_hide = (
                word_state.mastery_level >= self.mastery_threshold and
                global_mastery_level > 0
            )
            
            # Apply current word highlighting
            if word_state.is_current:
                if word_state.hint_level == 0:
                    if should_hide:
                        word = f'<span class="word-current word-masked" data-index="{word_state.index}">{"_" * len(word)}</span>'
                    else:
                        word = f'<span class="word-current" data-index="{word_state.index}">{word}</span>'
                elif word_state.hint_level == 1:
                    # First letter hint
                    hint = word[0] + "_" * (len(word) - 1)
                    word = f'<span class="word-current word-hint" data-index="{word_state.index}">{hint}</span>'
                elif word_state.hint_level == 2:
                    # Partial word hint (first half)
                    mid = len(word) // 2
                    hint = word[:mid] + "_" * (len(word) - mid)
                    word = f'<span class="word-current word-hint" data-index="{word_state.index}">{hint}</span>'
                else:
                    # Full word revealed
                    word = f'<span class="word-current word-revealed" data-index="{word_state.index}">{word}</span>'
            elif word_state.is_completed:
                word = f'<span class="word-completed" data-index="{word_state.index}">{word}</span>'
            elif should_hide:
                word = f'<span class="word-masked" data-index="{word_state.index}">{"_" * len(word)}</span>'
            else:
                word = f'<span class="word-normal" data-index="{word_state.index}">{word}</span>'
            
            display_parts.append(word)
        
        return ' '.join(display_parts)
    
    def advance_to_word(self, word_index: int) -> Dict:
        """Advance to a specific word and return state information"""
        if word_index >= len(self.words):
            return self._complete_session()
        
        # Mark previous word as completed
        if self.current_word_index < len(self.words):
            self.words[self.current_word_index].is_current = False
            self.words[self.current_word_index].is_completed = True
        
        # Set new current word
        self.current_word_index = word_index
        current_word = self.words[word_index]
        current_word.is_current = True
        current_word.hint_level = 0
        current_word.needs_hint = False
        self.word_start_time = time.time()
        
        return {
            'success': True,
            'current_word': current_word.word,
            'word_index': word_index,
            'display_text': self.get_display_text(),
            'progress': (word_index / len(self.words)) * 100,
            'is_complete': False
        }
    
    def check_word_timing(self) -> Dict:
        """Check if current word needs hints based on timing"""
        if not self.word_start_time or self.current_word_index >= len(self.words):
            return {'needs_hint': False}
        
        current_word = self.words[self.current_word_index]
        time_on_word = time.time() - self.word_start_time
        
        # Update time stuck
        current_word.time_stuck = time_on_word
        
        # Check if hint is needed
        if time_on_word > self.delay_threshold and not current_word.needs_hint:
            current_word.needs_hint = True
            return {
                'needs_hint': True,
                'time_stuck': time_on_word,
                'suggested_hint_level': min(current_word.hint_level + 1, 3),
                'word': current_word.word,
                'word_index': self.current_word_index
            }
        
        # Check if auto-advance is needed
        elif time_on_word > self.pause_threshold:
            return {
                'needs_hint': True,
                'auto_advance': True,
                'time_stuck': time_on_word,
                'word': current_word.word,
                'word_index': self.current_word_index
            }
        
        return {'needs_hint': False, 'time_stuck': time_on_word}
    
    def apply_hint(self, hint_type: str = 'auto') -> Dict:
        """Apply a hint to the current word"""
        if self.current_word_index >= len(self.words):
            return {'success': False, 'error': 'No current word'}
        
        current_word = self.words[self.current_word_index]
        
        if hint_type == 'auto':
            # Automatic hint progression
            current_word.hint_level = min(current_word.hint_level + 1, 3)
        elif hint_type == 'letter':
            current_word.hint_level = max(current_word.hint_level, 1)
        elif hint_type == 'partial':
            current_word.hint_level = max(current_word.hint_level, 2)
        elif hint_type == 'full':
            current_word.hint_level = 3
        
        current_word.needs_hint = False
        current_word.attempts += 1
        
        return {
            'success': True,
            'hint_level': current_word.hint_level,
            'display_text': self.get_display_text(),
            'word': current_word.word,
            'attempts': current_word.attempts
        }
    
    def process_speech_input(self, spoken_text: str) -> Dict:
        """Process speech input and advance practice accordingly"""
        if self.current_word_index >= len(self.words):
            return {'success': False, 'error': 'Practice session complete'}
        
        current_word = self.words[self.current_word_index]
        spoken_words = spoken_text.lower().split()
        expected_word = current_word.word.lower()
        
        # Check if spoken text contains the expected word
        word_found = False
        for spoken_word in spoken_words:
            # Clean spoken word for comparison
            clean_spoken = re.sub(r'[^\w\'-]', '', spoken_word)
            clean_expected = re.sub(r'[^\w\'-]', '', expected_word)
            
            if clean_spoken == clean_expected:
                word_found = True
                break
        
        if word_found:
            # Word correctly spoken - advance
            self._update_word_mastery(current_word, success=True)
            return self.advance_to_word(self.current_word_index + 1)
        else:
            # Word not found or incorrect
            current_word.attempts += 1
            self._update_word_mastery(current_word, success=False)
            
            # Offer hint if struggling
            if current_word.attempts >= 2:
                hint_result = self.apply_hint('auto')
                return {
                    'success': False,
                    'word_found': False,
                    'attempts': current_word.attempts,
                    'hint_applied': True,
                    'hint_level': hint_result['hint_level'],
                    'display_text': hint_result['display_text'],
                    'expected_word': current_word.word,
                    'spoken_text': spoken_text
                }
            
            return {
                'success': False,
                'word_found': False,
                'attempts': current_word.attempts,
                'hint_applied': False,
                'expected_word': current_word.word,
                'spoken_text': spoken_text,
                'display_text': self.get_display_text()
            }
    
    def _update_word_mastery(self, word_state: PracticeWordState, success: bool):
        """Update word mastery level based on performance"""
        if not self.user.is_authenticated:
            return
        
        # Get or create word progress
        word_progress, created = WordProgress.objects.get_or_create(
            user=self.user,
            text=self.text,
            word_index=word_state.index,
            defaults={
                'word_text': word_state.word,
                'mastery_level': 0.0,
                'times_practiced': 0,
                'times_correct': 0
            }
        )
        
        # Update statistics
        word_progress.times_practiced += 1
        if success:
            word_progress.times_correct += 1
        
        # Calculate new mastery level using a learning curve
        accuracy = word_progress.times_correct / word_progress.times_practiced
        practice_factor = min(word_progress.times_practiced / 10.0, 1.0)  # Cap at 10 practices
        
        if success:
            # Increase mastery
            improvement = 0.1 * (1.0 - word_progress.mastery_level) * practice_factor
            word_progress.mastery_level = min(word_progress.mastery_level + improvement, 1.0)
        else:
            # Decrease mastery slightly
            reduction = 0.05 * word_progress.mastery_level
            word_progress.mastery_level = max(word_progress.mastery_level - reduction, 0.0)
        
        # Update spaced repetition fields
        word_progress.last_practiced = timezone.now()
        if success and word_progress.mastery_level > 0.8:
            # Increase interval for well-mastered words
            word_progress.ease_factor = min(word_progress.ease_factor * 1.1, 3.0)
        elif not success:
            # Decrease interval for struggling words
            word_progress.ease_factor = max(word_progress.ease_factor * 0.9, 1.0)
        
        word_progress.save()
        
        # Update word state
        word_state.mastery_level = word_progress.mastery_level
    
    def _complete_session(self) -> Dict:
        """Complete the practice session and return results"""
        session_duration = (timezone.now() - self.session_start_time).total_seconds()
        
        # Calculate session statistics
        total_words = len(self.words)
        completed_words = sum(1 for word in self.words if word.is_completed)
        total_attempts = sum(word.attempts for word in self.words)
        successful_attempts = sum(1 for word in self.words if word.is_completed and word.attempts <= 2)
        
        accuracy = (successful_attempts / max(completed_words, 1)) * 100
        words_per_minute = (completed_words / max(session_duration / 60, 0.1))
        
        # Update user progress
        if self.user.is_authenticated:
            user_progress, created = UserTextProgress.objects.get_or_create(
                user=self.user,
                text=self.text
            )
            
            user_progress.total_sessions += 1
            user_progress.total_practice_time += session_duration / 60  # in minutes
            user_progress.best_accuracy = max(user_progress.best_accuracy, accuracy)
            user_progress.last_practiced = timezone.now()
            user_progress.save()
        
        return {
            'success': True,
            'is_complete': True,
            'session_complete': True,
            'statistics': {
                'total_words': total_words,
                'completed_words': completed_words,
                'accuracy': accuracy,
                'words_per_minute': words_per_minute,
                'duration_seconds': session_duration,
                'total_attempts': total_attempts,
                'hints_used': sum(1 for word in self.words if word.hint_level > 0)
            }
        }
    
    def get_session_state(self) -> Dict:
        """Get current session state for frontend"""
        return {
            'current_word_index': self.current_word_index,
            'total_words': len(self.words),
            'display_text': self.get_display_text(),
            'current_word': self.words[self.current_word_index].word if self.current_word_index < len(self.words) else None,
            'progress_percentage': (self.current_word_index / len(self.words)) * 100,
            'session_duration': (timezone.now() - self.session_start_time).total_seconds(),
            'is_complete': self.current_word_index >= len(self.words)
        }