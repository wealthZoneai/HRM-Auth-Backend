from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Create an HR user with name Raviteja'

    def handle(self, *args, **options):
        username = 'Raviteja'
        email = 'raviteja@example.com'
        password = 'Ravi@123'
        first_name = 'Raviteja'
        last_name = ''

        # Check if user already exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'HR User "{username}" already exists!')
            )
            return

        # Create HR user (staff but not superuser)
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        user.is_staff = True
        user.save()

        self.stdout.write(
            self.style.SUCCESS(
                f'✓ HR User created successfully!\n'
                f'  Username: {username}\n'
                f'  Email: {email}\n'
                f'  Password: {password}\n'
                f'  Role: HR (Staff)'
            )
        )
