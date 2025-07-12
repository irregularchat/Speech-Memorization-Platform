from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import os
from memorization.models import Text


class Command(BaseCommand):
    help = 'Import existing texts from data/pre_texts/ directory'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Username to assign as creator of imported texts (will create if not exists)',
            default='admin'
        )

    def handle(self, *args, **options):
        username = options['user']
        
        # Get or create user
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': f'{username}@example.com',
                'is_staff': True,
                'is_superuser': True
            }
        )
        
        if created:
            user.set_password('admin123')  # Default password
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f'Created user: {username} (password: admin123)')
            )
        
        # Import texts
        texts_dir = 'data/pre_texts/'
        if not os.path.exists(texts_dir):
            self.stdout.write(
                self.style.ERROR(f'Directory {texts_dir} does not exist')
            )
            return
        
        imported_count = 0
        for filename in os.listdir(texts_dir):
            if filename.endswith('.txt'):
                filepath = os.path.join(texts_dir, filename)
                title = filename[:-4].replace('_', ' ').title()
                
                # Check if text already exists
                if Text.objects.filter(title=title).exists():
                    self.stdout.write(
                        self.style.WARNING(f'Text "{title}" already exists, skipping...')
                    )
                    continue
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                    
                    # Create description based on filename
                    if 'military' in filename.lower():
                        description = 'Military creed for memorization and recitation practice'
                        difficulty = 'intermediate'
                        tags = 'military, creed, honor'
                    elif 'speech' in filename.lower():
                        description = 'Historical speech for oratory practice'
                        difficulty = 'advanced'
                        tags = 'speech, oratory, historical'
                    else:
                        description = f'Text imported from {filename}'
                        difficulty = 'beginner'
                        tags = 'general, practice'
                    
                    # Create text object
                    text = Text.objects.create(
                        title=title,
                        content=content,
                        description=description,
                        tags=tags,
                        difficulty=difficulty,
                        created_by=user,
                        is_public=True
                    )
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'Imported: "{title}" ({text.word_count} words)')
                    )
                    imported_count += 1
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error importing {filename}: {e}')
                    )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully imported {imported_count} texts')
        )