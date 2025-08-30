from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from memorization.models import Text

class Command(BaseCommand):
    help = 'Create demo texts for testing different practice modes'
    
    def handle(self, *args, **options):
        # Get or create demo user
        demo_user, created = User.objects.get_or_create(
            username='demo',
            defaults={
                'email': 'demo@example.com',
                'first_name': 'Demo',
                'last_name': 'User'
            }
        )
        
        # Sample texts for different practice modes
        demo_texts = [
            {
                'title': 'The Gettysburg Address',
                'content': 'Four score and seven years ago our fathers brought forth on this continent, a new nation, conceived in Liberty, and dedicated to the proposition that all men are created equal. Now we are engaged in a great civil war, testing whether that nation, or any nation so conceived and so dedicated, can long endure. We are met on a great battle-field of that war. We have come to dedicate a portion of that field, as a final resting place for those who here gave their lives that that nation might live. It is altogether fitting and proper that we should do this.',
                'description': 'Abraham Lincoln\'s famous speech delivered during the American Civil War at the dedication of the Soldiers\' National Cemetery in Gettysburg, Pennsylvania.',
                'difficulty': 'intermediate',
                'tags': 'historical, american, speech, civil war'
            },
            {
                'title': 'I Have a Dream (Excerpt)',
                'content': 'I have a dream that one day this nation will rise up and live out the true meaning of its creed: "We hold these truths to be self-evident, that all men are created equal." I have a dream that one day on the red hills of Georgia, the sons of former slaves and the sons of former slave owners will be able to sit down together at the table of brotherhood. I have a dream that one day even the state of Mississippi, a state sweltering with the heat of injustice, sweltering with the heat of oppression, will be transformed into an oasis of freedom and justice.',
                'description': 'Excerpt from Martin Luther King Jr.\'s iconic speech delivered during the March on Washington for Jobs and Freedom in 1963.',
                'difficulty': 'advanced',
                'tags': 'civil rights, american, dream, equality, historical'
            },
            {
                'title': 'Army Values',
                'content': 'Loyalty. Bear true faith and allegiance to the U.S. Constitution, the Army, your unit and other Soldiers. Duty. Fulfill your obligations. Respect. Treat people as they should be treated. Selfless Service. Put the welfare of the Nation, the Army and your subordinates before your own. Honor. Live up to Army values. Integrity. Do what\'s right, legally and morally. Personal Courage. Face fear, danger or adversity physical or moral.',
                'description': 'The seven core values that guide every soldier in the United States Army.',
                'difficulty': 'beginner',
                'tags': 'military, army, values, character'
            },
            {
                'title': 'To Be Or Not To Be',
                'content': 'To be or not to be, that is the question: Whether \'tis nobler in the mind to suffer the slings and arrows of outrageous fortune, or to take arms against a sea of troubles and, by opposing, end them. To die—to sleep, no more; and by a sleep to say we end the heartache and the thousand natural shocks that flesh is heir to: \'tis a consummation devoutly to be wished.',
                'description': 'The famous soliloquy from William Shakespeare\'s play Hamlet, Act 3, Scene 1.',
                'difficulty': 'advanced',
                'tags': 'shakespeare, literature, soliloquy, hamlet'
            },
            {
                'title': 'The Star-Spangled Banner',
                'content': 'O say can you see, by the dawn\'s early light, What so proudly we hailed at the twilight\'s last gleaming, Whose broad stripes and bright stars through the perilous fight, O\'er the ramparts we watched, were so gallantly streaming? And the rocket\'s red glare, the bombs bursting in air, Gave proof through the night that our flag was still there; O say does that star-spangled banner yet wave O\'er the land of the free and the home of the brave?',
                'description': 'The national anthem of the United States, written by Francis Scott Key.',
                'difficulty': 'intermediate',
                'tags': 'national anthem, patriotic, american, song'
            }
        ]
        
        created_count = 0
        
        for text_data in demo_texts:
            text, created = Text.objects.get_or_create(
                title=text_data['title'],
                defaults={
                    'content': text_data['content'],
                    'description': text_data['description'],
                    'difficulty': text_data['difficulty'],
                    'tags': text_data['tags'],
                    'is_public': True,
                    'created_by': demo_user
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created text: {text.title}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Text already exists: {text.title}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} demo texts')
        )