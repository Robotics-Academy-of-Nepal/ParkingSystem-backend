from rest_framework.views import APIView
from django.http import Http404
from tenant.models import Client, Domain
# Base class for views that require tenant context
class TenantAPIView(APIView):
    def get_tenant_schema_from_request(self, request):
        """
        Extract tenant schema from the request. 
        Example: Extract tenant schema from subdomain.
        """
        # subdomain = request.tenant # Get host without port
        subdomain = request.META.get('HTTP_TENANT')
        domain = Domain.objects.select_related('tenant').get(domain=subdomain)        
        return domain.tenant.schema_name     
      
