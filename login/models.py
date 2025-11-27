# login/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import datetime


class User(AbstractUser):
    ROLE_CHOICES = [
        ('management', 'Management'),
        ('hr', 'HR'),
        ('tl', 'Team Leader'),
        ('employee', 'Employee'),
        ('intern', 'Intern'),
    ]
    role = models.CharField(
        max_length=20, choices=ROLE_CHOICES, default='employee')

    def __str__(self):
        return f"{self.username} ({self.role})"


class PasswordResetOTP(models.Model):
    user = models.ForeignKey('login.User', on_delete=models.CASCADE)
    otp = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_expired(self):
        return timezone.now() > self.created_at + datetime.timedelta(minutes=10)

    def __str__(self):
        return f"{self.user.username} - OTP {self.otp}"
