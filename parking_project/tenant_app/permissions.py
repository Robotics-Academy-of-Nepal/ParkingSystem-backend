from rest_framework.permissions import BasePermission

class IsSuperAdmin(BasePermission):
    """
    Custom permission to allow only superadmins.
    """
    def has_permission(self, request, view):
        # Check if the user is authenticated and is a superadmin
        return request.user.is_authenticated and request.user.role == "SUPERADMIN"
