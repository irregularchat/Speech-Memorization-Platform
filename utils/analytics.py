# ./utils/analytics.py
import json
import os
from datetime import datetime, timedelta
import statistics
from collections import defaultdict, Counter

class PerformanceAnalytics:
    def __init__(self, user_data_dir="data/user_data/"):
        self.user_data_dir = user_data_dir
        self.analytics_file = os.path.join(user_data_dir, "logs", "performance_analytics.json")
        self.sessions_file = os.path.join(user_data_dir, "logs", "session_history.json")
        self.ensure_directories()
    
    def ensure_directories(self):
        """Ensure required directories exist."""
        os.makedirs(os.path.dirname(self.analytics_file), exist_ok=True)
    
    def load_analytics_data(self):
        """Load analytics data from file."""
        if os.path.exists(self.analytics_file):
            try:
                with open(self.analytics_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return self._get_default_analytics()
        return self._get_default_analytics()
    
    def _get_default_analytics(self):
        """Get default analytics structure."""
        return {
            'total_sessions': 0,
            'total_practice_time': 0,  # in minutes
            'total_words_practiced': 0,
            'average_accuracy': 0,
            'accuracy_trend': [],  # last 30 sessions
            'daily_stats': {},
            'weekly_stats': {},
            'monthly_stats': {},
            'text_performance': {},  # performance per text
            'improvement_rate': 0,
            'streak_days': 0,
            'best_session': {'accuracy': 0, 'date': None},
            'last_updated': datetime.now().isoformat()
        }
    
    def save_analytics_data(self, data):
        """Save analytics data to file."""
        try:
            data['last_updated'] = datetime.now().isoformat()
            with open(self.analytics_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except IOError as e:
            print(f"Error saving analytics data: {e}")
    
    def log_session(self, session_data):
        """Log a practice session."""
        sessions = self.load_session_history()
        
        # Create session record
        session_record = {
            'session_id': len(sessions) + 1,
            'timestamp': datetime.now().isoformat(),
            'text_name': session_data.get('text_name', 'Unknown'),
            'words_practiced': session_data.get('words_practiced', 0),
            'accuracy': session_data.get('accuracy', 0),
            'errors': session_data.get('errors', 0),
            'duration_minutes': session_data.get('duration_minutes', 0),
            'words_per_minute': session_data.get('words_per_minute', 150),
            'mastery_level': session_data.get('mastery_level', 0)
        }
        
        sessions.append(session_record)
        self.save_session_history(sessions)
        self.update_analytics(session_record)
        
        return session_record
    
    def load_session_history(self):
        """Load session history from file."""
        if os.path.exists(self.sessions_file):
            try:
                with open(self.sessions_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []
    
    def save_session_history(self, sessions):
        """Save session history to file."""
        try:
            with open(self.sessions_file, 'w') as f:
                json.dump(sessions, f, indent=2, default=str)
        except IOError as e:
            print(f"Error saving session history: {e}")
    
    def update_analytics(self, session_record):
        """Update analytics with new session data."""
        data = self.load_analytics_data()
        now = datetime.now()
        today = now.strftime('%Y-%m-%d')
        this_week = now.strftime('%Y-W%U')
        this_month = now.strftime('%Y-%m')
        
        # Update totals
        data['total_sessions'] += 1
        data['total_practice_time'] += session_record.get('duration_minutes', 0)
        data['total_words_practiced'] += session_record.get('words_practiced', 0)
        
        # Update accuracy trend (keep last 30 sessions)
        data['accuracy_trend'].append(session_record.get('accuracy', 0))
        if len(data['accuracy_trend']) > 30:
            data['accuracy_trend'] = data['accuracy_trend'][-30:]
        
        # Calculate average accuracy
        if data['accuracy_trend']:
            data['average_accuracy'] = statistics.mean(data['accuracy_trend'])
        
        # Update daily stats
        if today not in data['daily_stats']:
            data['daily_stats'][today] = {
                'sessions': 0, 'accuracy': [], 'words_practiced': 0, 'practice_time': 0
            }
        
        daily = data['daily_stats'][today]
        daily['sessions'] += 1
        daily['accuracy'].append(session_record.get('accuracy', 0))
        daily['words_practiced'] += session_record.get('words_practiced', 0)
        daily['practice_time'] += session_record.get('duration_minutes', 0)
        
        # Update weekly stats
        if this_week not in data['weekly_stats']:
            data['weekly_stats'][this_week] = {
                'sessions': 0, 'avg_accuracy': 0, 'total_words': 0, 'total_time': 0
            }
        
        weekly = data['weekly_stats'][this_week]
        weekly['sessions'] += 1
        weekly['total_words'] += session_record.get('words_practiced', 0)
        weekly['total_time'] += session_record.get('duration_minutes', 0)
        
        # Calculate weekly average accuracy
        weekly_sessions = [s for s in self.load_session_history() 
                          if datetime.fromisoformat(s['timestamp']).strftime('%Y-W%U') == this_week]
        if weekly_sessions:
            weekly['avg_accuracy'] = statistics.mean([s['accuracy'] for s in weekly_sessions])
        
        # Update monthly stats
        if this_month not in data['monthly_stats']:
            data['monthly_stats'][this_month] = {
                'sessions': 0, 'avg_accuracy': 0, 'total_words': 0, 'total_time': 0
            }
        
        monthly = data['monthly_stats'][this_month]
        monthly['sessions'] += 1
        monthly['total_words'] += session_record.get('words_practiced', 0)
        monthly['total_time'] += session_record.get('duration_minutes', 0)
        
        # Update text-specific performance
        text_name = session_record.get('text_name', 'Unknown')
        if text_name not in data['text_performance']:
            data['text_performance'][text_name] = {
                'sessions': 0, 'accuracies': [], 'avg_accuracy': 0, 'best_accuracy': 0
            }
        
        text_perf = data['text_performance'][text_name]
        text_perf['sessions'] += 1
        text_perf['accuracies'].append(session_record.get('accuracy', 0))
        text_perf['avg_accuracy'] = statistics.mean(text_perf['accuracies'])
        text_perf['best_accuracy'] = max(text_perf['accuracies'])
        
        # Update best session
        if session_record.get('accuracy', 0) > data['best_session']['accuracy']:
            data['best_session'] = {
                'accuracy': session_record.get('accuracy', 0),
                'date': session_record['timestamp'],
                'text_name': text_name
            }
        
        # Calculate improvement rate (trend over last 10 sessions)
        if len(data['accuracy_trend']) >= 10:
            recent_avg = statistics.mean(data['accuracy_trend'][-5:])
            older_avg = statistics.mean(data['accuracy_trend'][-10:-5])
            data['improvement_rate'] = recent_avg - older_avg
        
        # Update streak
        data['streak_days'] = self.calculate_streak()
        
        self.save_analytics_data(data)
    
    def calculate_streak(self):
        """Calculate current daily practice streak."""
        sessions = self.load_session_history()
        if not sessions:
            return 0
        
        # Group sessions by date
        sessions_by_date = defaultdict(list)
        for session in sessions:
            date = datetime.fromisoformat(session['timestamp']).strftime('%Y-%m-%d')
            sessions_by_date[date].append(session)
        
        # Calculate streak from today backwards
        streak = 0
        current_date = datetime.now()
        
        while True:
            date_str = current_date.strftime('%Y-%m-%d')
            if date_str in sessions_by_date:
                streak += 1
                current_date -= timedelta(days=1)
            else:
                break
        
        return streak
    
    def get_performance_summary(self, days=30):
        """Get performance summary for the last N days."""
        data = self.load_analytics_data()
        sessions = self.load_session_history()
        
        # Filter sessions to last N days
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_sessions = [
            s for s in sessions 
            if datetime.fromisoformat(s['timestamp']) >= cutoff_date
        ]
        
        if not recent_sessions:
            return None
        
        # Calculate summary statistics
        accuracies = [s['accuracy'] for s in recent_sessions]
        total_words = sum(s['words_practiced'] for s in recent_sessions)
        total_time = sum(s['duration_minutes'] for s in recent_sessions)
        
        # Text performance breakdown
        text_performance = defaultdict(list)
        for session in recent_sessions:
            text_performance[session['text_name']].append(session['accuracy'])
        
        return {
            'period_days': days,
            'total_sessions': len(recent_sessions),
            'total_words_practiced': total_words,
            'total_practice_time': total_time,
            'average_accuracy': statistics.mean(accuracies) if accuracies else 0,
            'best_accuracy': max(accuracies) if accuracies else 0,
            'worst_accuracy': min(accuracies) if accuracies else 0,
            'accuracy_std_dev': statistics.stdev(accuracies) if len(accuracies) > 1 else 0,
            'improvement_trend': self.calculate_improvement_trend(recent_sessions),
            'text_performance': {
                text: {
                    'sessions': len(accs),
                    'avg_accuracy': statistics.mean(accs),
                    'best_accuracy': max(accs)
                } for text, accs in text_performance.items()
            },
            'daily_consistency': len(set(
                datetime.fromisoformat(s['timestamp']).strftime('%Y-%m-%d') 
                for s in recent_sessions
            )),
            'streak_days': data['streak_days']
        }
    
    def calculate_improvement_trend(self, sessions):
        """Calculate improvement trend from sessions."""
        if len(sessions) < 4:
            return 0
        
        # Sort by timestamp
        sessions = sorted(sessions, key=lambda x: x['timestamp'])
        accuracies = [s['accuracy'] for s in sessions]
        
        # Split into first and second half
        mid_point = len(accuracies) // 2
        first_half_avg = statistics.mean(accuracies[:mid_point])
        second_half_avg = statistics.mean(accuracies[mid_point:])
        
        return second_half_avg - first_half_avg
    
    def get_detailed_analytics(self):
        """Get comprehensive analytics data."""
        data = self.load_analytics_data()
        summary_30 = self.get_performance_summary(30)
        summary_7 = self.get_performance_summary(7)
        
        return {
            'overview': {
                'total_sessions': data['total_sessions'],
                'total_practice_time': data['total_practice_time'],
                'total_words_practiced': data['total_words_practiced'],
                'overall_average_accuracy': data['average_accuracy'],
                'current_streak': data['streak_days'],
                'best_session': data['best_session']
            },
            'recent_performance': {
                'last_30_days': summary_30,
                'last_7_days': summary_7
            },
            'trends': {
                'accuracy_trend': data['accuracy_trend'],
                'improvement_rate': data['improvement_rate']
            },
            'text_performance': data['text_performance']
        }