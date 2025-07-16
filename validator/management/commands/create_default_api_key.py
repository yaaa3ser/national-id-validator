"""
Management command to create a default API key for testing and development.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from authentication.models import APIKey


class Command(BaseCommand):
    help = 'Create a default API key for testing and development'

    def add_arguments(self, parser):
        parser.add_argument(
            '--name',
            type=str,
            default='Default API Key',
            help='Name for the API key'
        )
        parser.add_argument(
            '--user',
            type=str,
            default='admin',
            help='Username to associate with the API key'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force creation even if key already exists'
        )

    def handle(self, *args, **options):
        name = options['name']
        username = options['user']
        force = options['force']
        
        # Check if default API key already exists
        default_api_key = getattr(settings, 'DEFAULT_API_KEY', None)
        if default_api_key and not force:
            existing_key = APIKey.objects.filter(key=default_api_key).first()
            if existing_key:
                self.stdout.write(
                    self.style.WARNING(
                        f'Default API key already exists: {existing_key.name} '
                        f'(ID: {existing_key.id})'
                    )
                )
                return
        
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
            user.set_password('admin123')  # Default password for development
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f'Created user: {username}')
            )
        
        # Create API key
        api_key_data = {
            'name': name,
            'user': user,
            'rate_limit_per_minute': 1000,
            'rate_limit_per_hour': 10000,
            'rate_limit_per_day': 100000,
            'description': 'Default API key for development and testing'
        }
        
        # Use default key if specified in settings
        if default_api_key:
            api_key_data['key'] = default_api_key
        
        api_key = APIKey.objects.create(**api_key_data)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created API key: {api_key.name}\n'
                f'Key: {api_key.key}\n'
                f'User: {user.username}\n'
                f'Rate limits: {api_key.rate_limit_per_minute}/min, '
                f'{api_key.rate_limit_per_hour}/hour, '
                f'{api_key.rate_limit_per_day}/day'
            )
        )
        
        # Display usage instructions
        self.stdout.write(
            self.style.HTTP_INFO(
                '\nUsage instructions:\n'
                f'curl -H "X-API-Key: {api_key.key}" \\\n'
                '     -H "Content-Type: application/json" \\\n'
                '     -d \'{"national_id": "29001011234567"}\' \\\n'
                '     http://localhost:8000/api/v1/validate/\n'
            )
        )
