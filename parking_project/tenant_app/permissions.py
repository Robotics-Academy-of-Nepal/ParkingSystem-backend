from rest_framework.permissions import BasePermission
from tenant.models import Domain
from django_tenants.utils import schema_context
class IsSuperAdmin(BasePermission):
    """
    Custom permission to allow only superadmins.
    """
    def has_permission(self, request, view):
        schema_name = self.get_tenant_schema_from_request(request)
        with schema_context(schema_name):
            # Check if the user is authenticated and is a superadmin
            return request.user.is_authenticated and request.user.role == "SUPERADMIN"
    
    def get_tenant_schema_from_request(self, request):
        """
        Extract tenant schema from the request. 
        Example: Extract tenant schema from subdomain.
        """
        # subdomain = request.tenant # Get host without port
        subdomain = request.META.get('HTTP_TENANT')
        domain = Domain.objects.select_related('tenant').get(domain=subdomain)        
        return domain.tenant.schema_name 