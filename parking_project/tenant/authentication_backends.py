from django.contrib.auth.backends import ModelBackend
from django_tenants.utils import tenant_context
from django.http import Http404
from .models import Client, Domain
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
User = get_user_model()

class TenantAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        # tenant = self.get_tenant_schema(request)  # Get the full tenant object
               
        # if request.tenant:
        #     # Use tenant context to authenticate user within the tenant's schema
        #     with tenant_context(request.tenant.schema_name):  # Pass the entire tenant object here
                
        #         # Manually query the user model for authentication
        #         try:
        #             # user = User.objects.get(username=username)  # Query user in the tenant's schema
        #             # print("user", user)
        #             # print("password",password)
        #             # if user.check_password(password):  # Check the password manually
        #             #     print("user after password", user)
        #             #     print("password",password)
        #             #     return user  # Return the authenticated user
        #             user=super().authenticate(request, username=username, password=password)
        #             return user
        #             # else:
        #             #     return None  # Invalid password
        #         except User.DoesNotExist:
        #             return None  # User not found
        
        user=super().authenticate(request, username=username, password=password)
        return user
        # return None

    # def get_tenant_schema(self, request):
    #     """Extract tenant schema based on subdomain."""
    #     subdomain = request.get_host().split(':')[0]  # Get host, without port if present
    #     print(subdomain)
    #     tenant = self.get_tenant_by_subdomain(subdomain)
    #     return tenant  # Return the full tenant object (not just schema_name)

    # def get_tenant_by_subdomain(self, subdomain):
    #     """Fetch tenant object by subdomain."""
    #     try:
    #         # Look up the domain by subdomain
    #         domain = Domain.objects.select_related('tenant').get(domain=subdomain)
    #         # Use the tenant_id from the domain to fetch the corresponding tenant (Client)
    #         tenant = domain.tenant
    #         return tenant  # Return the full tenant object (Client)
    #     except Domain.DoesNotExist:
    #         raise Http404("Tenant not found")
    #     except Client.DoesNotExist:
    #         raise Http404("Tenant not found")
