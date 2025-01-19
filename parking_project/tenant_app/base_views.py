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
        subdomain = request.get_host().split(':')[0]  # Get host without port
        try:
            # Get tenant schema by subdomain
            domain = Domain.objects.get(domain=subdomain)
            tenant = Client.objects.get(id=domain.tenant_id)
            return tenant.schema_name  # Assuming `Client` model has `schema_name`
        except Client.DoesNotExist:
            raise Http404("Tenant not found")
