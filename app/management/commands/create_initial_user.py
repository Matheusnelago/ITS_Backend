from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from app.models import UserRole

User = get_user_model()

class Command(BaseCommand):
    help = 'Create an initial admin user if none exists'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='Username for the admin user',
        )
        parser.add_argument(
            '--password',
            type=str,
            default='admin123',
            help='Password for the admin user',
        )

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']

        # Check if any superuser exists
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write(self.style.WARNING('Admin user(s) already exist. No new user created.'))
            return

        # Create superuser
        user = User.objects.create_superuser(
            username=username,
            email='admin@example.com',
            password=password
        )

        # Create UserRole with admin role
        UserRole.objects.create(
            user=user,
            role='admin',
            is_active=True
        )

        self.stdout.write(self.style.SUCCESS(f'Successfully created admin user: {username}'))
        self.stdout.write(self.style.SUCCESS(f'Password: {password}'))
        self.stdout.write(self.style.WARNING('Please change the password in production!'))

