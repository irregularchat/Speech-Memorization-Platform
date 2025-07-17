from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password


class Command(BaseCommand):
    help = 'Create a default user for the application'

    def handle(self, *args, **options):
        # Check if admin user already exists
        if User.objects.filter(username='admin').exists():
            self.stdout.write(
                self.style.WARNING('Admin user already exists')
            )
            return

        # Create admin user
        user = User.objects.create(
            username='admin',
            email='admin@example.com',
            password=make_password('admin123'),  # Change this password!
            is_staff=True,
            is_superuser=True
        )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created admin user: {user.username}')
        )
        self.stdout.write(
            self.style.WARNING('Default password is "admin123" - please change it immediately!')
        ) 