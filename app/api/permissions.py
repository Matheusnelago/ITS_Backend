from rest_framework import permissions
from ..models import UserRole


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        # Check if user is a superuser
        if request.user and request.user.is_superuser:
            return True
        try:
            user_role = UserRole.objects.get(user=request.user)
            return user_role.role == 'admin'
        except UserRole.DoesNotExist:
            return False

class IsTicketManagement(permissions.BasePermission):
    def has_permission(self, request, view):
        try:
            user_role = UserRole.objects.get(user=request.user)
            return user_role.role == ['admin', 'ministry', 'officer']
        except UserRole.DoesNotExist:
            return False
class IsTicket(permissions.BasePermission):
    def has_permission(self, request, view):
        try:
            user_role = UserRole.objects.get(user=request.user)
            return user_role.role == ['officer']
        except UserRole.DoesNotExist:
            return False

class IsOfficer(permissions.BasePermission):
    def has_permission(self, request, view):
        try:
            user_role = UserRole.objects.get(user=request.user)
            return user_role.role == 'officer'
        except UserRole.DoesNotExist:
            return False

class IsJudiciary(permissions.BasePermission):
    def has_permission(self, request, view):
        try:
            user_role = UserRole.objects.get(user=request.user)
            return user_role.role == 'judiciary'
        except UserRole.DoesNotExist:
            return False

class IsMinistry(permissions.BasePermission):
    def has_permission(self, request, view):
        try:
            user_role = UserRole.objects.get(user=request.user)
            return user_role.role == 'ministry'
        except UserRole.DoesNotExist:
            return False

class IsNaTISAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        # Allow superusers to access NaTIS admin endpoints
        if request.user and request.user.is_superuser:
            return True
        try:
            user_role = UserRole.objects.get(user=request.user)
            return user_role.role == 'natisadmin'
        except UserRole.DoesNotExist:
            return False

class IsOfficer(permissions.BasePermission):
    def has_permission(self, request, view):
        try:
            user_role = UserRole.objects.get(user=request.user)
            return user_role.role == 'officer'
        except UserRole.DoesNotExist:
            return False
