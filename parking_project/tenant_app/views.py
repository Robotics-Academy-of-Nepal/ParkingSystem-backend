from django.shortcuts import render
from .base_views import TenantAPIView 
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response    
from rest_framework import status
from tenant.authentication_backends import TenantAuthBackend
from .serializers import *
from tenant.models import Client,Domain
from django.http import Http404
from django_tenants.utils import schema_context
from .models import *
from rest_framework.permissions import IsAuthenticated
from .permissions import IsSuperAdmin
from .services.passcode_service import PasscodeService
# Create your views here.
class LoginAPIView(TenantAPIView):
    def post(self, request):
        # Get the username and password from the request data
        username = request.data.get('username')
        password = request.data.get('password')
        print(request.data)
        print("view",username)
        print("view",password)
        # Authenticate the user 
        tenant_auth_backend = TenantAuthBackend()
        user = tenant_auth_backend.authenticate(request,username=username, password=password)
        print("view",user)
        # Check if authentication was successful
        if user and user.is_superadmin():  # Check if its superadmin
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token

            return Response({
                'refresh': str(refresh),
                'access': str(access_token),
                'is_superadmin': True
            }, status=status.HTTP_200_OK)
        elif user: #for users other than superadmin
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token

            return Response({
                'refresh': str(refresh),
                'access': str(access_token),
                'is_superadmin': False
            }, status=status.HTTP_200_OK)
            
            
            
        # Return error if authentication fails
        return Response({
            'error': 'Invalid credentials'
        }, status=status.HTTP_401_UNAUTHORIZED)
        
class CreateUserView(TenantAPIView):
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

    
        
class UserListView(TenantAPIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]  # Enforce authentication and custom permission
    def get(self, request):
        # Extract tenant schema (e.g., from subdomain or request headers)
        tenant_schema = self.get_tenant_schema_from_request(request)

        if not tenant_schema:
            return Response({"detail": "Tenant not found."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Switch to tenant schema and fetch users
        with schema_context(tenant_schema):
            users = User.objects.filter(role="STAFF")  # Query users in the current tenant schema
            serializer = UserSerializer(users, many=True)
            return Response(serializer.data)
        
    

class ChangeBaseRateView(TenantAPIView):
    def post(self,request):
        serializer=BaseRateSerializer(data=request.data)
        if serializer.is_valid():
            two_wheeler_rate=serializer.validated_data.get('two_wheeler_rate')
            four_wheeler_rate=serializer.validated_data.get('four_wheeler_rate')
            heavy_vehicle_rate=serializer.validated_data.get('heavy_vehicle_rate')
            passcode=request.data.get('passcode')
            
            tenant_schema=self.get_tenant_schema_from_request(request)
            
            if not tenant_schema:
                return Response({"detail":"Tenant not found."},status=status.HTTP_400_BAD_REQUEST)
            
            with schema_context(tenant_schema):
                #validate the passcode
                try:
                    tenant=Client.objects.get(schema_name=tenant_schema)
                    # Check if the passcode matches
                    if tenant.passcode != passcode:
                        return Response({"detail": "Invalid passcode."}, status=status.HTTP_400_BAD_REQUEST)
                    #update the base rates
                    settings,created=ParkingRates.objects.get_or_create(tenant__schema_name=tenant_schema)  
                    
                    if two_wheeler_rate is not None:
                        settings.two_wheeler_rate=two_wheeler_rate
                    if four_wheeler_rate is not None:
                        settings.four_wheeler_rate=four_wheeler_rate
                    if heavy_vehicle_rate is not None:
                        settings.heavy_vehicle_rate=heavy_vehicle_rate
                    settings.save()
                    return Response({"detail":"Base rates updated successfully."},status=status.HTTP_200_OK)
                  
            
                except Client.DoesNotExist:
                    return Response({"detail":"Passcode not found."},status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)   
    
    def get(self,request):
        tenant_schema=self.get_tenant_schema_from_request(request)
        
        if not tenant_schema:
            return Response({"detail":"Tenant not found."},status=status.HTTP_400_BAD_REQUEST)
        
        with schema_context(tenant_schema):
            settings,created=ParkingRates.objects.get_or_create(tenant__schema_name=tenant_schema)
            serializer=BaseRateSerializer(settings)
            return Response(serializer.data)       

class RefreshPasscodeView(TenantAPIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]  # Ensure only superadmins can access this view

    def post(self, request):
        tenant_schema = self.get_tenant_schema_from_request(request)  # Extract tenant schema from request
        
        if not tenant_schema:
            return Response({"detail": "Tenant not found."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Switch to tenant schema to perform tenant-specific operations
        with schema_context(tenant_schema):
            try:
                tenant=Client.objects.get(schema_name=tenant_schema)
                # Refresh the passcode using the service layer
                tenant.set_passcode()
                
                # Return the new passcode and its expiry time
                return Response({
                    "detail": "Passcode refreshed successfully.",
                    "passcode": tenant.passcode,
                    "expiry_time": tenant.passcode_expires_at
                }, status=status.HTTP_200_OK)
            
            except Exception as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
    def get(self,request):
        tenant_schema = self.get_tenant_schema_from_request(request)  # Extract tenant schema from request
        
        if not tenant_schema:
            return Response({"detail": "Tenant not found."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Switch to tenant schema to perform tenant-specific operations
        with schema_context(tenant_schema):
            try:
                tenant=Client.objects.get(schema_name=tenant_schema)
                # Refresh the passcode using the service layer
                
                
                # Return the new passcode and its expiry time
                return Response({
                    "detail": "Get passcode",
                    "passcode": tenant.passcode,
                    "expiry_time": tenant.passcode_expires_at
                }, status=status.HTTP_200_OK)
            
            except Exception as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)