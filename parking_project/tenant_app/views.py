from django.shortcuts import render
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response    
from rest_framework import status
from tenant.authentication_backends import TenantAuthBackend
from .serializers import UserSerializer
from tenant.models import Client,Domain
from django.http import Http404
from django_tenants.utils import schema_context
# Create your views here.
class SuperAdminLoginAPIView(APIView):
    def post(self, request):
        # Get the username and password from the request data
        username = request.data.get('username')
        password = request.data.get('password')
        print(request.data)
        print("view",username)
        print("view",password)
        # Authenticate the user (superadmin)
        tenant_auth_backend = TenantAuthBackend()
        user = tenant_auth_backend.authenticate(request,username=username, password=password)
        print("view",user)
        # Check if authentication was successful
        if user and user.is_superadmin():  # Ensure it's the superadmin
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token

            return Response({
                'refresh': str(refresh),
                'access': str(access_token),
            }, status=status.HTTP_200_OK)
        
        # Return error if authentication fails
        return Response({
            'error': 'Invalid credentials or not a superadmin'
        }, status=status.HTTP_401_UNAUTHORIZED)
        
class CreateUserView(APIView):
    def post(self, request):
        # Extract tenant schema (e.g., from subdomain or request headers)
        tenant_schema = self.get_tenant_schema_from_request(request)

        if not tenant_schema:
            return Response({"detail": "Tenant not found."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Switch to tenant schema and create the user
        with schema_context(tenant_schema):
            serializer = UserSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()  # This saves the user in the current tenant schema
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_tenant_schema_from_request(self, request):
        """
        Extract tenant schema from the request. This is just an example,
        you can customize this method to fetch the schema based on subdomain, headers, etc.
        """
        # Example: Extract tenant schema from subdomain
        host = request.get_host().split(':')[0]  # Get host without port
        subdomain = host.split('.')[0] +'.localhost' # Extract subdomain part
        try:
            # Get tenant schema by subdomain
            domain=Domain.objects.get(domain=subdomain)
            tenant = Client.objects.get(id=domain.tenant_id)
            return tenant.schema_name  # Assuming `Client` model has `schema_name`
        except Client.DoesNotExist:
            raise Http404("Tenant not found")