from rest_framework_simplejwt.views import TokenObtainPairView
from django_tenants.utils import tenant_context
from django.http import Http404
from .models import Client, Domain

class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        # Extract tenant subdomain from the request
        tenant_domain = self.get_tenant_from_request(request)
        tenant_domain+='.localhost'
        try:
            # Fetch the domain object by subdomain
            domain = Domain.objects.get(domain=tenant_domain)
            # Fetch the corresponding tenant (Client) using tenant_id from Domain
            tenant = Client.objects.get(id=domain.tenant_id)
        except Domain.DoesNotExist:
            raise Http404("Domain not found")
        except Client.DoesNotExist:
            raise Http404("Tenant not found")

        # Switch to the tenant schema context
        with tenant_context(tenant):
            response = super().post(request, *args, **kwargs)
        return response

    def get_tenant_from_request(self, request):
        """Extract subdomain from the request."""
        # Example: Extract subdomain from 'ktm-mall.localhost'
        tenant_domain = request.META.get('HTTP_HOST').split('.')[0]  # Get the subdomain part
        return tenant_domain
