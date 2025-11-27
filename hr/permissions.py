# hr/permissions.py
from rest_framework import permissions

class IsHR(permissions.BasePermission):
    """Allow only HR and management roles."""
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and getattr(user, 'role', None) in ('hr','management'))

class IsTL(permissions.BasePermission):
    """Allow only TL (team lead)."""
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and getattr(user, 'role', None) == 'tl')
