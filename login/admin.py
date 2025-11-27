# login/admin.py
from django.contrib import admin
from .models import User, PasswordResetOTP

admin.site.register(User)
admin.site.register(PasswordResetOTP)
