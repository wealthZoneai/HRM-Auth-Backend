"""
WSGI config for HRM project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise
from pathlib import Path

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HRM.settings')

# Get the Django WSGI application
django_app = get_wsgi_application()

# Wrap with WhiteNoise for static files
application = WhiteNoise(
    django_app,
    root=os.path.join(Path(__file__).resolve().parent.parent, 'staticfiles'),
    prefix='static/'
)

# Add additional directories to the WhiteNoise application
application.add_files(os.path.join(Path(__file__).resolve().parent.parent, 'static'), prefix='static/')
