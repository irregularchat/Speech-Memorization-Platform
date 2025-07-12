# memorization/services.py
"""
Services for spaced repetition and memorization logic.
Migrated from utils/ to Django service layer.
"""

import re
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from django.utils import timezone
from django.contrib.auth.models import User

from .models import Text, WordProgress, PracticeSession, UserTextProgress


class SpacedRepetitionService:
    """
    Service for managing spaced repetition algorithm (SM-2 based).
    Migrated from utils/spaced_repetition.py
    """
    
    def __init__(self, user: User):
        self.user = user
    
    def extract_words(self, text: str) -> List[str]:
        """Extract words from text, filtering out punctuation and short words."""
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        return [word for word in words if len(word) > 2]  # Filter out short words
    
    def get_stop_words(self) -> set:
        """Get common stop words that shouldn't be tracked for memorization."""
        return {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
            'after', 'above', 'below', 'between', 'among', 'under', 'over',
            'a', 'an', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she',
            'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your',
            'his', 'her', 'its', 'our', 'their', 'is', 'am', 'are', 'was', 'were',
            'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can'
        }
    
    def update_word_performance(self, text: Text, word: str, word_position: int, correct: bool) -> WordProgress:
        """
        Update performance data for a specific word using Anki SM-2 algorithm.
        """
        word_lower = word.lower().strip()
        
        # Skip stop words
        if word_lower in self.get_stop_words():
            return None
        
        # Get or create word progress
        word_progress, created = WordProgress.objects.get_or_create(
            user=self.user,
            text=text,
            word=word_lower,
            word_position=word_position,
            defaults={
                'next_review': timezone.now(),
                'easiness_factor': 2.5,
                'repetition': 0,
                'interval': 1,
            }
        )
        
        # Update attempts
        word_progress.total_attempts += 1
        
        if correct:
            word_progress.correct_attempts += 1
            word_progress.repetition += 1
            
            # SM-2 algorithm implementation
            if word_progress.repetition == 1:
                word_progress.interval = 1
            elif word_progress.repetition == 2:
                word_progress.interval = 6
            else:
                word_progress.interval = int(word_progress.interval * word_progress.easiness_factor)
            
            # Update easiness factor
            accuracy = word_progress.accuracy / 100  # Convert to 0-1 scale
            quality = min(5, max(0, int(accuracy * 5)))  # 0-5 scale
            
            ef = word_progress.easiness_factor
            ef = ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
            word_progress.easiness_factor = max(1.3, ef)
            
            # Update mastery level
            if accuracy >= 0.9 and word_progress.repetition >= 3:
                word_progress.mastery_level = min(5, word_progress.mastery_level + 1)
        else:
            # Reset on failure
            word_progress.repetition = 0
            word_progress.interval = 1
            word_progress.easiness_factor = max(1.3, word_progress.easiness_factor - 0.2)
            word_progress.mastery_level = max(0, word_progress.mastery_level - 1)
        
        # Calculate next review date
        next_review = timezone.now() + timedelta(days=word_progress.interval)
        word_progress.next_review = next_review
        
        word_progress.save()
        return word_progress
    
    def get_mastered_words(self, text: Text, mastery_threshold: int = 3) -> List[str]:
        """Get list of words that have reached mastery threshold."""
        mastered_words = WordProgress.objects.filter(
            user=self.user,
            text=text,
            mastery_level__gte=mastery_threshold
        ).values_list('word', flat=True)
        
        return list(mastered_words)
    
    def get_words_for_review(self, text: Text = None) -> List[WordProgress]:
        """Get words that are due for review."""
        queryset = WordProgress.objects.filter(
            user=self.user,
            next_review__lte=timezone.now()
        )
        
        if text:
            queryset = queryset.filter(text=text)
        
        return list(queryset.order_by('next_review'))
    
    def apply_spaced_repetition(self, text: Text, mastery_percentage: int = 0) -> str:
        """Apply spaced repetition by hiding mastered words based on percentage."""
        if mastery_percentage == 0:
            return text.content
        
        words = text.content.split()
        mastered_words = self.get_mastered_words(text)
        
        if not mastered_words:
            return text.content
        
        # Calculate how many words to hide based on mastery percentage
        num_to_hide = int(len(mastered_words) * (mastery_percentage / 100))
        words_to_hide = mastered_words[:num_to_hide]
        
        # Replace mastered words with blanks
        result_words = []
        for word in words:
            clean_word = re.sub(r'[^\w]', '', word.lower())
            if clean_word in words_to_hide:
                # Create blank with same length
                blank = '_' * len(clean_word)
                # Preserve punctuation
                result_word = re.sub(r'\w+', blank, word)
                result_words.append(result_word)
            else:
                result_words.append(word)
        
        return ' '.join(result_words)
    
    def get_text_statistics(self, text: Text) -> Dict:
        """Get detailed statistics for words in the text."""
        words = self.extract_words(text.content)
        word_progresses = WordProgress.objects.filter(user=self.user, text=text)
        
        stats = {
            'total_words': len(set(words)),  # Unique words only
            'tracked_words': word_progresses.count(),
            'mastered_words': word_progresses.filter(mastery_level__gte=3).count(),
            'words_due_review': word_progresses.filter(next_review__lte=timezone.now()).count(),
            'average_mastery': 0,
            'word_details': []
        }
        
        if word_progresses.exists():
            # Calculate average mastery
            total_mastery = sum(wp.mastery_level for wp in word_progresses)
            stats['average_mastery'] = total_mastery / word_progresses.count()
            
            # Get word details
            for wp in word_progresses:
                stats['word_details'].append({
                    'word': wp.word,
                    'mastery_level': wp.mastery_level,
                    'accuracy': wp.accuracy,
                    'total_attempts': wp.total_attempts,
                    'next_review': wp.next_review.isoformat()
                })
        
        return stats


class TextComparisonService:
    """
    Service for comparing transcribed text with original text.
    Migrated from utils/text_parser.py
    """
    
    @staticmethod
    def clean_word(word: str) -> str:
        """Clean word by removing punctuation and normalizing."""
        return re.sub(r'[^\w]', '', word).lower()
    
    @staticmethod
    def compare_texts(transcribed_text: str, original_text: str) -> Dict:
        """Compare transcribed text with the original text and highlight differences."""
        differences = []
        original_words = original_text.split()
        transcribed_words = transcribed_text.split()
        
        # Compare word by word, accounting for different lengths
        max_length = max(len(original_words), len(transcribed_words))
        
        for i in range(max_length):
            original_word = original_words[i] if i < len(original_words) else ""
            transcribed_word = transcribed_words[i] if i < len(transcribed_words) else ""
            
            # Clean words for comparison
            clean_original = TextComparisonService.clean_word(original_word)
            clean_transcribed = TextComparisonService.clean_word(transcribed_word)
            
            if clean_original != clean_transcribed:
                differences.append((original_word, transcribed_word))
        
        return {
            'total_words': len(original_words),
            'errors': len(differences),
            'differences': differences,
            'accuracy': ((len(original_words) - len(differences)) / len(original_words) * 100) if original_words else 0
        }


class PracticeSessionService:
    """
    Service for managing practice sessions.
    Migrated from utils/analytics.py
    """
    
    def __init__(self, user: User):
        self.user = user
    
    def create_session(self, text: Text, session_type: str = 'full_text') -> PracticeSession:
        """Create a new practice session."""
        session = PracticeSession.objects.create(
            user=self.user,
            text=text,
            session_type=session_type,
            started_at=timezone.now()
        )
        return session
    
    def complete_session(
        self,
        session: PracticeSession,
        transcribed_text: str,
        words_per_minute: int,
        mastery_level_used: int,
        duration_seconds: int
    ) -> PracticeSession:
        """Complete a practice session with results."""
        
        # Compare texts
        comparison = TextComparisonService.compare_texts(transcribed_text, session.text.content)
        
        # Update session
        session.words_practiced = comparison['total_words']
        session.words_correct = comparison['total_words'] - comparison['errors']
        session.accuracy_percentage = comparison['accuracy']
        session.duration_seconds = duration_seconds
        session.words_per_minute = words_per_minute
        session.mastery_level_used = mastery_level_used
        session.transcription = transcribed_text
        session.differences = comparison['differences']
        session.completed_at = timezone.now()
        session.save()
        
        # Update spaced repetition data
        sr_service = SpacedRepetitionService(self.user)
        original_words = session.text.content.split()
        transcribed_words = transcribed_text.split()
        
        for i, original_word in enumerate(original_words):
            if i < len(transcribed_words):
                transcribed_word = transcribed_words[i]
                clean_original = TextComparisonService.clean_word(original_word)
                clean_transcribed = TextComparisonService.clean_word(transcribed_word)
                correct = clean_original == clean_transcribed
                sr_service.update_word_performance(session.text, clean_original, i, correct)
        
        # Update user text progress
        self._update_user_text_progress(session)
        
        return session
    
    def _update_user_text_progress(self, session: PracticeSession):
        """Update overall progress for a user on a specific text."""
        progress, created = UserTextProgress.objects.get_or_create(
            user=self.user,
            text=session.text,
            defaults={
                'preferred_words_per_minute': session.words_per_minute,
                'preferred_session_duration': session.duration_seconds,
            }
        )
        
        # Update metrics
        progress.total_sessions += 1
        progress.total_practice_time += session.duration_seconds
        
        if session.accuracy_percentage > progress.best_accuracy:
            progress.best_accuracy = session.accuracy_percentage
        
        # Calculate new average accuracy
        sessions = PracticeSession.objects.filter(user=self.user, text=session.text)
        total_accuracy = sum(s.accuracy_percentage for s in sessions)
        progress.average_accuracy = total_accuracy / sessions.count()
        
        # Update mastery percentage based on word progress
        sr_service = SpacedRepetitionService(self.user)
        stats = sr_service.get_text_statistics(session.text)
        if stats['total_words'] > 0:
            progress.overall_mastery_percentage = (stats['mastered_words'] / stats['total_words']) * 100
            progress.words_mastered = stats['mastered_words']
        
        progress.save()