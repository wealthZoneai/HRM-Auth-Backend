import os
import django

def create_superuser():
    # Set up Django environment
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HRM.settings')
    django.setup()
    
    from django.contrib.auth import get_user_model
    
    # Get the User model
    User = get_user_model()
    
    # Create or update the superuser
    user, created = User.objects.get_or_create(
        username='Raviteja',
        defaults={
            'email': 'hr@example.com',
            'is_staff': True,
            'is_superuser': True,
            'role': 'hr'
        }
    )
    
    # Set the password
    if user:
        user.set_password('Ravi@123')
        user.save()
        print("Superuser 'Raviteja' has been created/updated successfully!")
    else:
        print("Failed to create/update superuser.")

if __name__ == "__main__":
    create_superuser()
