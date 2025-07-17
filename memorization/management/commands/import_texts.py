from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import os
from memorization.models import Text


class Command(BaseCommand):
    help = 'Import existing texts from data/pre_texts/ directory and add military creeds'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Username to assign as creator of imported texts (will create if not exists)',
            default='admin'
        )
        parser.add_argument(
            '--military-only',
            action='store_true',
            help='Only import military creeds, skip file imports'
        )

    def handle(self, *args, **options):
        username = options['user']
        military_only = options['military_only']
        
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
        
        # Import military creeds first
        self._import_military_creeds(user)
        
        # Skip file imports if military-only flag is set
        if military_only:
            return
        
        # Import texts
        texts_dir = 'data/pre_texts/'
        if not os.path.exists(texts_dir):
            self.stdout.write(
                self.style.WARNING(f'Directory {texts_dir} does not exist, skipping file imports')
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
    
    def _import_military_creeds(self, user):
        """Import military creeds as default content"""
        military_creeds = {
            "US Army Creed": {
                "content": """I am an American Soldier.
I am a warrior and a member of a team.
I serve the people of the United States, and live the Army Values.
I will always place the mission first.
I will never accept defeat.
I will never quit.
I will never leave a fallen comrade.
I am disciplined, physically and mentally tough, trained and proficient in my warrior tasks and drills.
I always maintain my arms, my equipment and myself.
I am an expert and I am a professional.
I stand ready to deploy, engage, and destroy, the enemies of the United States of America in close combat.
I am a guardian of freedom and the American way of life.
I am an American Soldier.""",
                "description": "The official creed of the United States Army, emphasizing the core values and responsibilities of every soldier.",
                "difficulty": "intermediate"
            },
            "US Navy Creed": {
                "content": """I am a United States Sailor.
I will support and defend the Constitution of the United States of America and I will obey the orders of those appointed over me.
I represent the fighting spirit of the Navy and those who have gone before me to defend freedom and democracy around the world.
I proudly serve my country's Navy combat team with Honor, Courage and Commitment.
I am committed to excellence and the fair treatment of all.""",
                "description": "The creed of the United States Navy, highlighting honor, courage, and commitment to service.",
                "difficulty": "intermediate"
            },
            "US Air Force Creed": {
                "content": """I am an American Airman.
I am a warrior.
I have answered my nation's call.
I am an American Airman.
My mission is to fly, fight, and win.
I am faithful to a proud heritage, a tradition of honor, and a legacy of valor.
I am an American Airman.
Guardian of freedom and justice, my nation's sword and shield, its sentry and avenger.
I defend my country with my life.
I am an American Airman.
Wingman, leader, warrior.
I will never leave an Airman behind, I will never falter, and I will not fail.""",
                "description": "The Airman's Creed of the United States Air Force, emphasizing the warrior spirit and commitment to excellence.",
                "difficulty": "intermediate"
            },
            "US Marine Corps Creed": {
                "content": """My rifle and I know that what counts in war is not the rounds we fire, the noise of our burst, nor the smoke we make.
We know that it is the hits that count.
We will hit.
My rifle is human, even as I, because it is my life.
Thus, I will learn it as a brother.
I will learn its weaknesses, its strength, its parts, its accessories, its sights and its barrel.
I will keep my rifle clean and ready, even as I am clean and ready.
We will become part of each other.
We will.
Before God, I swear this creed.
My rifle and I are the defenders of my country.
We are the masters of our enemy.
We are the saviors of my life.
So be it, until victory is America's and there is no enemy, but peace!""",
                "description": "The Rifleman's Creed of the United States Marine Corps, emphasizing the sacred bond between Marine and rifle.",
                "difficulty": "advanced"
            },
            "US Coast Guard Creed": {
                "content": """I am proud to be a United States Coast Guardsman.
I revere that long line of expert seamen who by their devotion to duty and sacrifice of self have made it possible for me to be a member of a service honored and respected, in peace and in war, throughout the world.
I never, by word or deed, will bring reproach upon the fair name of my service.
I will cheerfully and willingly obey all lawful orders.
I will always be on time to relieve, and shall endeavor to do more, rather than less, than my share.
I will always be at my station, alert and attending to my duties.
I shall, so conduct myself at all times that others will be proud to say, 'That man is a Coast Guardsman.'""",
                "description": "The creed of the United States Coast Guard, emphasizing honor, duty, and service above self.",
                "difficulty": "intermediate"
            }
        }
        
        imported_creeds = 0
        for title, creed_data in military_creeds.items():
            # Check if creed already exists
            if Text.objects.filter(title=title).exists():
                self.stdout.write(
                    self.style.WARNING(f'Military creed "{title}" already exists, skipping...')
                )
                continue
            
            try:
                text = Text.objects.create(
                    title=title,
                    content=creed_data["content"],
                    description=creed_data["description"],
                    tags="military, creed, honor, service",
                    difficulty=creed_data["difficulty"],
                    created_by=user,
                    is_public=True
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'Added military creed: "{title}" ({text.word_count} words)')
                )
                imported_creeds += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error adding military creed {title}: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully imported {imported_creeds} military creeds')
        )