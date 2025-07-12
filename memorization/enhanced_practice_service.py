import re
import time
import random
from typing import List, Dict, Tuple, Optional, Set
from django.utils import timezone
from datetime import timedelta
from .models import (Text, WordProgress, PracticeSession, UserTextProgress, 
                     PracticePattern, DelayedRecallSession, WordRevealSession)


class EnhancedPracticeWordState:
    """Enhanced state management for individual words during practice"""
    
    def __init__(self, word: str, index: int, mastery_level: float = 0.0):
        self.word = word.strip()
        self.index = index
        self.mastery_level = mastery_level
        
        # Display state
        self.is_visible = True
        self.is_current = False
        self.is_completed = False
        self.is_problem_word = False
        self.is_auto_hidden = False
        
        # Hint system
        self.hint_level = 0  # 0: no hint, 1: first letter, 2: partial word, 3: full word
        self.hint_type = None  # 'letter', 'partial', 'context', 'audio'
        
        # Timing and performance
        self.attempts = 0
        self.response_time = 0.0
        self.time_stuck = 0.0
        self.needs_hint = False
        self.auto_hide_timeout = None
        
        # Context information
        self.surrounding_words = []
        self.sentence_position = None
        self.difficulty_factors = []


class PracticePatternDetector:
    """Identifies and tracks difficult patterns in text memorization"""
    
    def __init__(self, text: Text, user):
        self.text = text
        self.user = user
        self.words = text.content.split()
        self.patterns = []
        
    def detect_patterns(self, session_data: Dict) -> List[PracticePattern]:
        """Detect various difficulty patterns from session performance"""
        patterns = []
        
        # Word sequence difficulties
        patterns.extend(self._detect_word_sequences(session_data))
        
        # Sentence start problems
        patterns.extend(self._detect_sentence_starts(session_data))
        
        # Paragraph transitions
        patterns.extend(self._detect_paragraph_transitions(session_data))
        
        # Long word difficulties
        patterns.extend(self._detect_long_words(session_data))
        
        # Similar word confusion
        patterns.extend(self._detect_similar_words(session_data))
        
        return patterns
    
    def _detect_word_sequences(self, session_data: Dict) -> List[PracticePattern]:
        """Detect sequences of words that are consistently difficult"""
        patterns = []
        difficult_sequences = []
        current_sequence = []
        
        for i, word_data in enumerate(session_data.get('word_performance', [])):
            if word_data.get('attempts', 0) > 2 or word_data.get('response_time', 0) > 3.0:
                current_sequence.append(i)
            else:
                if len(current_sequence) >= 3:  # Sequence of 3+ difficult words
                    difficult_sequences.append(current_sequence)
                current_sequence = []
        
        # Add final sequence if applicable
        if len(current_sequence) >= 3:
            difficult_sequences.append(current_sequence)
        
        for sequence in difficult_sequences:
            pattern, created = PracticePattern.objects.get_or_create(
                user=self.user,
                text=self.text,
                pattern_type='word_sequence',
                start_word_index=sequence[0],
                defaults={
                    'end_word_index': sequence[-1],
                    'difficulty_score': self._calculate_sequence_difficulty(sequence, session_data),
                    'context_words': [self.words[i] for i in sequence],
                }
            )
            if not created:
                pattern.frequency_encountered += 1
                pattern.save()
            patterns.append(pattern)
        
        return patterns
    
    def _detect_sentence_starts(self, session_data: Dict) -> List[PracticePattern]:
        """Detect difficulties with sentence beginnings"""
        patterns = []
        sentences = re.split(r'[.!?]+', self.text.content)
        
        # Find word indices that start sentences
        sentence_starts = []
        word_index = 0
        for sentence in sentences:
            sentence_words = sentence.strip().split()
            if sentence_words:
                sentence_starts.append(word_index)
            word_index += len(sentence_words)
        
        # Check performance at sentence starts
        for start_index in sentence_starts:
            if start_index < len(session_data.get('word_performance', [])):
                word_data = session_data['word_performance'][start_index]
                if word_data.get('attempts', 0) > 2:
                    pattern, created = PracticePattern.objects.get_or_create(
                        user=self.user,
                        text=self.text,
                        pattern_type='sentence_start',
                        start_word_index=start_index,
                        defaults={
                            'end_word_index': start_index,
                            'difficulty_score': min(word_data.get('attempts', 0) / 5.0, 1.0),
                        }
                    )
                    if not created:
                        pattern.frequency_encountered += 1
                        pattern.save()
                    patterns.append(pattern)
        
        return patterns
    
    def _detect_paragraph_transitions(self, session_data: Dict) -> List[PracticePattern]:
        """Detect difficulties with paragraph transitions"""
        patterns = []
        paragraphs = self.text.content.split('\n\n')
        
        # Find paragraph transition points
        word_index = 0
        for i, paragraph in enumerate(paragraphs[:-1]):  # All but last paragraph
            paragraph_words = paragraph.split()
            word_index += len(paragraph_words)
            
            # Check performance around transition (last word of paragraph, first of next)
            transition_range = range(max(0, word_index - 2), min(len(self.words), word_index + 2))
            difficulty_sum = 0
            for idx in transition_range:
                if idx < len(session_data.get('word_performance', [])):
                    word_data = session_data['word_performance'][idx]
                    difficulty_sum += word_data.get('attempts', 0)
            
            if difficulty_sum > 6:  # Threshold for transition difficulty
                pattern, created = PracticePattern.objects.get_or_create(
                    user=self.user,
                    text=self.text,
                    pattern_type='paragraph_transition',
                    start_word_index=word_index - 1,
                    defaults={
                        'end_word_index': word_index + 1,
                        'difficulty_score': min(difficulty_sum / 10.0, 1.0),
                    }
                )
                if not created:
                    pattern.frequency_encountered += 1
                    pattern.save()
                patterns.append(pattern)
        
        return patterns
    
    def _detect_long_words(self, session_data: Dict) -> List[PracticePattern]:
        """Detect difficulties with long words"""
        patterns = []
        
        for i, word in enumerate(self.words):
            if len(word) >= 8:  # Consider words 8+ characters as long
                if i < len(session_data.get('word_performance', [])):
                    word_data = session_data['word_performance'][i]
                    if word_data.get('attempts', 0) > 2 or word_data.get('response_time', 0) > 4.0:
                        pattern, created = PracticePattern.objects.get_or_create(
                            user=self.user,
                            text=self.text,
                            pattern_type='long_words',
                            start_word_index=i,
                            defaults={
                                'end_word_index': i,
                                'difficulty_score': min(word_data.get('attempts', 0) / 4.0, 1.0),
                                'context_words': [word],
                            }
                        )
                        if not created:
                            pattern.frequency_encountered += 1
                            pattern.save()
                        patterns.append(pattern)
        
        return patterns
    
    def _detect_similar_words(self, session_data: Dict) -> List[PracticePattern]:
        """Detect confusion between similar words"""
        patterns = []
        
        # Group similar words (by length and first letter)
        word_groups = {}
        for i, word in enumerate(self.words):
            key = (len(word), word[0].lower() if word else '')
            if key not in word_groups:
                word_groups[key] = []
            word_groups[key].append((i, word))
        
        # Find groups with multiple difficult words
        for group in word_groups.values():
            if len(group) >= 2:
                difficult_words = []
                for word_index, word in group:
                    if word_index < len(session_data.get('word_performance', [])):
                        word_data = session_data['word_performance'][word_index]
                        if word_data.get('attempts', 0) > 2:
                            difficult_words.append((word_index, word))
                
                if len(difficult_words) >= 2:
                    # Create pattern for similar word confusion
                    start_idx = min(idx for idx, _ in difficult_words)
                    end_idx = max(idx for idx, _ in difficult_words)
                    
                    pattern, created = PracticePattern.objects.get_or_create(
                        user=self.user,
                        text=self.text,
                        pattern_type='similar_words',
                        start_word_index=start_idx,
                        defaults={
                            'end_word_index': end_idx,
                            'difficulty_score': len(difficult_words) / len(group),
                            'context_words': [word for _, word in difficult_words],
                        }
                    )
                    if not created:
                        pattern.frequency_encountered += 1
                        pattern.save()
                    patterns.append(pattern)
        
        return patterns
    
    def _calculate_sequence_difficulty(self, sequence: List[int], session_data: Dict) -> float:
        """Calculate difficulty score for a word sequence"""
        total_attempts = 0
        total_time = 0.0
        
        for idx in sequence:
            if idx < len(session_data.get('word_performance', [])):
                word_data = session_data['word_performance'][idx]
                total_attempts += word_data.get('attempts', 0)
                total_time += word_data.get('response_time', 0)
        
        # Normalize to 0-1 scale
        attempt_score = min(total_attempts / (len(sequence) * 3), 1.0)
        time_score = min(total_time / (len(sequence) * 3.0), 1.0)
        
        return (attempt_score + time_score) / 2


class AdvancedPracticeEngine:
    """Enhanced practice engine with word reveal, delayed recall, and pattern detection"""
    
    def __init__(self, text: Text, user, practice_mode: str = 'adaptive'):
        self.text = text
        self.user = user
        self.practice_mode = practice_mode
        self.words = self._parse_text_words()
        self.session_data = {
            'word_performance': [],
            'patterns_detected': [],
            'hints_used': 0,
            'auto_hides_triggered': 0,
        }
        
        # Practice configuration
        self.current_word_index = 0
        self.session_start_time = timezone.now()
        self.word_start_time = None
        
        # Advanced features
        self.reveal_session = None
        self.delayed_recall_session = None
        self.pattern_detector = PracticePatternDetector(text, user)
        
        # Timing thresholds
        self.hint_threshold = 3.0  # seconds
        self.auto_hide_threshold = 5.0  # seconds
        self.mastery_threshold = 0.8
        
    def _parse_text_words(self) -> List[EnhancedPracticeWordState]:
        """Parse text into enhanced word states"""
        cleaned_text = re.sub(r'[^\w\s\'-]', ' ', self.text.content)
        word_list = [word for word in cleaned_text.split() if word.strip()]
        
        # Get existing word progress
        word_progress_map = {}
        if self.user.is_authenticated:
            progress_entries = WordProgress.objects.filter(
                user=self.user,
                text=self.text
            )
            for wp in progress_entries:
                word_progress_map[wp.word_index] = {
                    'mastery_level': wp.mastery_level,
                    'is_problem_word': wp.is_problem_word,
                    'average_response_time': wp.average_response_time,
                }
        
        # Create enhanced word states
        practice_words = []
        for i, word in enumerate(word_list):
            progress_data = word_progress_map.get(i, {})
            word_state = EnhancedPracticeWordState(
                word, i, progress_data.get('mastery_level', 0.0)
            )
            word_state.is_problem_word = progress_data.get('is_problem_word', False)
            practice_words.append(word_state)
        
        return practice_words
    
    def start_word_reveal_session(self, config: Dict) -> WordRevealSession:
        """Start a progressive word reveal session"""
        self.reveal_session = WordRevealSession.objects.create(
            user=self.user,
            text=self.text,
            reveal_strategy=config.get('strategy', 'progressive'),
            reveal_percentage=config.get('reveal_percentage', 0.1),
            increment_percentage=config.get('increment_percentage', 0.1),
            auto_hide_enabled=config.get('auto_hide_enabled', True),
            hide_delay_seconds=config.get('hide_delay_seconds', 3),
            fade_duration_seconds=config.get('fade_duration_seconds', 2),
        )
        
        # Calculate initial reveal set
        self._update_word_reveal_state()
        return self.reveal_session
    
    def start_delayed_recall_session(self, config: Dict) -> DelayedRecallSession:
        """Start a delayed recall session"""
        self.delayed_recall_session = DelayedRecallSession.objects.create(
            user=self.user,
            text=self.text,
            delay_minutes=config.get('delay_minutes', 15),
            reveal_percentage=config.get('reveal_percentage', 0.3),
            auto_hide_enabled=config.get('auto_hide_enabled', True),
            auto_hide_delay=config.get('auto_hide_delay', 5),
        )
        
        # Select words for recall based on mastery level
        self._select_recall_words()
        return self.delayed_recall_session
    
    def _update_word_reveal_state(self):
        """Update which words are visible based on reveal session configuration"""
        if not self.reveal_session:
            return
        
        visible_words = self.reveal_session.calculate_next_reveal_set()
        self.reveal_session.currently_visible_words = visible_words
        self.reveal_session.save()
        
        # Update word visibility
        for i, word_state in enumerate(self.words):
            word_state.is_visible = i in visible_words
    
    def _select_recall_words(self):
        """Select words for delayed recall based on difficulty and mastery"""
        if not self.delayed_recall_session:
            return
        
        # Prioritize problem words and low-mastery words
        word_scores = []
        for i, word_state in enumerate(self.words):
            score = 1.0 - word_state.mastery_level  # Lower mastery = higher score
            if word_state.is_problem_word:
                score += 0.5
            word_scores.append((i, score))
        
        # Sort by score and select top percentage
        word_scores.sort(key=lambda x: x[1], reverse=True)
        num_to_select = int(len(self.words) * self.delayed_recall_session.reveal_percentage)
        selected_indices = [idx for idx, _ in word_scores[:num_to_select]]
        
        self.delayed_recall_session.words_to_recall = selected_indices
        self.delayed_recall_session.save()
    
    def get_enhanced_display_text(self) -> str:
        """Generate display text with advanced hiding/revealing logic"""
        display_parts = []
        
        for word_state in self.words:
            word = word_state.word
            classes = ['word']
            
            # Apply reveal session logic
            if self.reveal_session and not word_state.is_visible:
                word = "_" * len(word)
                classes.append('word-hidden')
            
            # Apply delayed recall logic
            if (self.delayed_recall_session and 
                self.delayed_recall_session.is_recall_phase and
                word_state.index in self.delayed_recall_session.words_to_recall):
                if not word_state.is_completed:
                    word = "_" * len(word)
                    classes.append('word-recall-target')
            
            # Current word highlighting
            if word_state.is_current:
                classes.append('word-current')
                
                # Apply hints
                if word_state.hint_level == 1:
                    word = word[0] + "_" * (len(word) - 1)
                    classes.append('word-hint-letter')
                elif word_state.hint_level == 2:
                    mid = len(word) // 2
                    word = word[:mid] + "_" * (len(word) - mid)
                    classes.append('word-hint-partial')
                elif word_state.hint_level == 3:
                    classes.append('word-hint-full')
            
            # Problem word highlighting
            if word_state.is_problem_word:
                classes.append('word-problem')
            
            # Completed word
            if word_state.is_completed:
                classes.append('word-completed')
            
            # Auto-hidden word
            if word_state.is_auto_hidden:
                classes.append('word-auto-hidden')
                word = "_" * len(word)
            
            display_parts.append(
                f'<span class="{" ".join(classes)}" data-index="{word_state.index}">{word}</span>'
            )
        
        return ' '.join(display_parts)
    
    def process_word_timing(self, word_index: int) -> Dict:
        """Process timing for auto-hide and hint suggestions"""
        if word_index >= len(self.words):
            return {'action': 'none'}
        
        word_state = self.words[word_index]
        current_time = time.time()
        
        if not self.word_start_time:
            self.word_start_time = current_time
            return {'action': 'none'}
        
        time_on_word = current_time - self.word_start_time
        word_state.time_stuck = time_on_word
        
        # Check for hint threshold
        if time_on_word > self.hint_threshold and not word_state.needs_hint:
            word_state.needs_hint = True
            return {
                'action': 'suggest_hint',
                'word_index': word_index,
                'time_stuck': time_on_word,
                'suggested_hint_level': min(word_state.hint_level + 1, 3)
            }
        
        # Check for auto-hide (if enabled)
        if (self.reveal_session and 
            self.reveal_session.auto_hide_enabled and
            time_on_word > self.reveal_session.hide_delay_seconds and
            not word_state.is_auto_hidden):
            
            word_state.is_auto_hidden = True
            self.session_data['auto_hides_triggered'] += 1
            return {
                'action': 'auto_hide',
                'word_index': word_index,
                'fade_duration': self.reveal_session.fade_duration_seconds
            }
        
        # Check for auto-advance threshold
        if time_on_word > self.auto_hide_threshold:
            return {
                'action': 'suggest_advance',
                'word_index': word_index,
                'time_stuck': time_on_word
            }
        
        return {'action': 'none', 'time_stuck': time_on_word}
    
    def apply_intelligent_hint(self, word_index: int, hint_type: str = 'auto') -> Dict:
        """Apply contextual hints based on word characteristics and user history"""
        if word_index >= len(self.words):
            return {'success': False, 'error': 'Invalid word index'}
        
        word_state = self.words[word_index]
        word = word_state.word
        
        if hint_type == 'auto':
            # Intelligent hint selection based on word characteristics
            if len(word) <= 3:
                hint_type = 'full'  # Short words get full reveal
            elif word_state.is_problem_word:
                hint_type = 'context'  # Problem words get context hints
            elif word_state.attempts >= 2:
                hint_type = 'partial'  # Multiple attempts get partial reveal
            else:
                hint_type = 'letter'  # Default to letter hint
        
        # Apply the hint
        if hint_type == 'letter':
            word_state.hint_level = max(word_state.hint_level, 1)
            hint_text = word[0] + "_" * (len(word) - 1)
        elif hint_type == 'partial':
            word_state.hint_level = max(word_state.hint_level, 2)
            mid = len(word) // 2
            hint_text = word[:mid] + "_" * (len(word) - mid)
        elif hint_type == 'context':
            word_state.hint_level = max(word_state.hint_level, 2)
            # Provide surrounding words as context
            context_start = max(0, word_index - 2)
            context_end = min(len(self.words), word_index + 3)
            context_words = [self.words[i].word for i in range(context_start, context_end) if i != word_index]
            hint_text = f"Context: ...{' '.join(context_words[:2])} __ {' '.join(context_words[2:])}..."
        elif hint_type == 'full':
            word_state.hint_level = 3
            hint_text = word
        else:
            return {'success': False, 'error': 'Invalid hint type'}
        
        word_state.hint_type = hint_type
        word_state.needs_hint = False
        word_state.attempts += 1
        self.session_data['hints_used'] += 1
        
        return {
            'success': True,
            'hint_level': word_state.hint_level,
            'hint_type': hint_type,
            'hint_text': hint_text,
            'display_text': self.get_enhanced_display_text()
        }
    
    def complete_session_with_analysis(self) -> Dict:
        """Complete session and provide detailed analysis"""
        session_duration = (timezone.now() - self.session_start_time).total_seconds()
        
        # Detect patterns from this session
        detected_patterns = self.pattern_detector.detect_patterns(self.session_data)
        
        # Calculate comprehensive statistics
        total_words = len(self.words)
        completed_words = sum(1 for word in self.words if word.is_completed)
        problem_words_identified = sum(1 for word in self.words if word.is_problem_word)
        
        # Performance metrics
        accuracy = (completed_words / total_words) * 100 if total_words > 0 else 0
        words_per_minute = (completed_words / max(session_duration / 60, 0.1))
        
        # Problem area analysis
        problem_areas = []
        for pattern in detected_patterns:
            problem_areas.append({
                'type': pattern.pattern_type,
                'start_index': pattern.start_word_index,
                'end_index': pattern.end_word_index,
                'difficulty_score': pattern.difficulty_score,
                'words': pattern.context_words,
            })
        
        # Update reveal session if active
        if self.reveal_session:
            self.reveal_session.total_rounds_completed += 1
            self.reveal_session.total_practice_time += int(session_duration)
            self.reveal_session.completed_at = timezone.now()
            self.reveal_session.save()
        
        # Update delayed recall session if active
        if self.delayed_recall_session:
            self.delayed_recall_session.is_completed = True
            self.delayed_recall_session.completed_at = timezone.now()
            self.delayed_recall_session.save()
        
        return {
            'success': True,
            'session_complete': True,
            'statistics': {
                'total_words': total_words,
                'completed_words': completed_words,
                'accuracy': accuracy,
                'words_per_minute': words_per_minute,
                'duration_seconds': session_duration,
                'hints_used': self.session_data['hints_used'],
                'auto_hides_triggered': self.session_data['auto_hides_triggered'],
                'problem_words_identified': problem_words_identified,
            },
            'analysis': {
                'problem_areas': problem_areas,
                'patterns_detected': len(detected_patterns),
                'recommendations': self._generate_recommendations(detected_patterns),
            }
        }
    
    def _generate_recommendations(self, patterns: List[PracticePattern]) -> List[str]:
        """Generate practice recommendations based on detected patterns"""
        recommendations = []
        
        if any(p.pattern_type == 'word_sequence' for p in patterns):
            recommendations.append("Focus on practicing word sequences that consistently cause difficulty")
        
        if any(p.pattern_type == 'sentence_start' for p in patterns):
            recommendations.append("Practice sentence beginnings separately to improve flow")
        
        if any(p.pattern_type == 'long_words' for p in patterns):
            recommendations.append("Break down long words into syllables for easier memorization")
        
        if any(p.pattern_type == 'similar_words' for p in patterns):
            recommendations.append("Use distinctive memory techniques for similar-sounding words")
        
        if any(p.difficulty_score > 0.7 for p in patterns):
            recommendations.append("Consider using delayed recall sessions for high-difficulty areas")
        
        return recommendations