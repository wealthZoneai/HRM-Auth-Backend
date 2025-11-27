# emp/permissions.py
from rest_framework import permissions
import logging
logger = logging.getLogger(__name__)


class IsHROrManagement(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        ok = bool(user and user.is_authenticated and getattr(
            user, 'role', None) in ('hr', 'management'))
        if not ok:
            logger.info("Permission denied for user=%s role=%s path=%s", getattr(
                user, 'id', None), getattr(user, 'role', None), request.path)
        return ok


class IsTLorHRorOwner(permissions.BasePermission):
    """
    TL or HR or the owner (employee) can access/modify.
    For leave objects, TL is manager of the profile (profile.manager == user)
    """

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if getattr(user, 'role', None) in ('hr', 'management'):
            return True
        if getattr(user, 'role', None) == 'tl':
            try:
                profile = getattr(obj, 'profile', None) or obj
                owner_user = getattr(profile, 'user', None)
                return owner_user and getattr(owner_user.employeeprofile, 'manager', None) == user
            except Exception:
                return False
        # owner fallback
        try:
            profile = getattr(obj, 'profile', None)
            if profile:
                return profile.user == user
            owner_user = getattr(obj, 'user', None)
            return owner_user == user
        except Exception:
            return False
