#emp/validators.py
from django.core.exceptions import ValidationError

def validate_file_size(value):
    limit_mb = 5  # max 5 MB
    if value.size > limit_mb * 1024 * 1024:
        raise ValidationError(f'File too large. Size should not exceed {limit_mb} MB.')

def validate_image_extension(value):
    valid_ext = ['.jpg', '.jpeg', '.png', '.gif', '.pdf']
    import os
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in valid_ext:
        raise ValidationError('Unsupported file extension.')
