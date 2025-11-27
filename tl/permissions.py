# tl/permissions.py
from rest_framework import permissions


class IsTL(permissions.BasePermission):
    """Allow only Team Leaders."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "tl")
