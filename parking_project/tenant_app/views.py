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
from django.db import transaction
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action,api_view
from rest_framework.authtoken.models import Token
from django.db.models import Count, F, Q,Sum
from django.db.models.functions import TruncHour,TruncDate
from datetime import timedelta, datetime
import pandas as pd
from pytz import timezone

local_tz = timezone('Asia/Kathmandu')



class UserViewSet(ViewSet):
    @action(detail=False, methods=['POST'], url_path='login')
    def login(self,request):
        username = request.data.get('username')
        password = request.data.get('password')
        print(request.data)
        print("view",username)
        print("view",password)
        tenant_schema=self.get_tenant_schema_from_request(request)
        with tenant_schema(tenant_schema):
            # Authenticate the user 
            user = authenticate(request,username=username, password=password)
            print("view",user)
            serializer=UserSerializer(user)
            # Check if authentication was successful
            if user and user.is_superadmin():  # Check if its superadmin
                # Generate token
                token, created = Token.objects.get_or_create(user=user)
                return Response(
                    {
                        'token': token.key,
                        'is_superadmin': True,
                        'user': serializer.data,
                    },
                    status=status.HTTP_200_OK
                )
            elif user:  # for users other than superadmin
                # Generate token
                token, created = Token.objects.get_or_create(user=user)
                return Response(
                    {
                        'token': token.key,
                        'is_superadmin': False,
                        'user': serializer.data,
                    },
                    status=status.HTTP_200_OK
                )
            # Return error if authentication fails
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


    @action(detail=False, methods=['POST'], url_path='create-user', permission_classes=[IsAuthenticated, IsSuperAdmin])
    def create_user(self, request):
        tenant_schema = self.get_tenant_schema_from_request(request)

        if not tenant_schema:
            return Response({"detail": "Tenant not found."}, status=status.HTTP_400_BAD_REQUEST)
        
        with schema_context(tenant_schema):
            serializer = UserSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['GET'], url_path='get-user-info')
    def get_user_info(self, request):
        token = self.request.headers.get('Authorization').split(' ')[1]
        user = Token.objects.get(key=token).user
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['GET'], url_path='list-users', permission_classes=[IsAuthenticated, IsSuperAdmin])
    def list_users(self, request):
        # tenant_schema = self.get_tenant_schema_from_request(request)

        # if not tenant_schema:
        #     return Response({"detail": "Tenant not found."}, status=status.HTTP_400_BAD_REQUEST)
        
        # with schema_context(tenant_schema):
        users = User.objects.filter(role="STAFF")
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    def get_tenant_schema_from_request(self, request):
        # subdomain = request.tenant # Get host without port
        subdomain = request.META.get('HTTP_TENANT')
        domain = Domain.objects.select_related('tenant').get(domain=subdomain)        
        return domain.tenant.schema_name     
    

class ChangeBaseRateView(TenantAPIView):
    permission_classes = [IsAuthenticated]  # Ensure only superadmins can access this view
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
                    if not tenant.is_passcode_valid():
                       return Response({"detail": "passcode expired."}, status=status.HTTP_400_BAD_REQUEST)
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
        
        print(tenant_schema)
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
            
            
class CheckinView(TenantAPIView):
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access this view

    def post(self, request):
        # Validate incoming data with the serializer
        serializer = ParkingDetailsSerializer(data=request.data)
        
        if serializer.is_valid():
            # Extract validated data
            receipt_id = serializer.validated_data.get('receipt_id')
            vehicle_number = serializer.validated_data.get('vehicle_number')
            vehicle_type = serializer.validated_data.get('vehicle_type')
            checkin_time = serializer.validated_data.get('checkin_time')
            checkedin_by = serializer.validated_data.get('checkedin_by').id
            
            # Get tenant schema from request
            tenant_schema = self.get_tenant_schema_from_request(request)
            
            # Check if tenant schema exists
            if not tenant_schema:
                return Response({"detail": "Tenant not found."}, status=status.HTTP_400_BAD_REQUEST)

            # Ensure checkedin_by is a valid user
            try:
                user = User.objects.get(id=checkedin_by)
            except User.DoesNotExist:
                return Response({"detail": "User doesn't exist."}, status=status.HTTP_404_NOT_FOUND)

            # Use schema context for the tenant-specific database operations
            with schema_context(tenant_schema):
                try:
                    # Use transaction to ensure atomic operations
                    with transaction.atomic():
                        # Create the parking details entry
                        checkin_details = ParkingDetails.objects.create(
                            receipt_id=receipt_id,
                            vehicle_number=vehicle_number,
                            vehicle_type=vehicle_type,
                            checkin_time=checkin_time,
                            checkedin_by=user
                        )
                        
                        # Return a success response with created data
                        return Response(
                            {"detail": "Check-in successful", "data": ParkingDetailsSerializer(checkin_details).data},
                            status=status.HTTP_201_CREATED
                        )
                except Exception as e:
                    return Response({"detail": f"Error creating check-in: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            # Return validation errors if serializer is not valid
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        
class CheckoutView(TenantAPIView):
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access this view

    def post(self, request):
        
        receipt_id = request.data.get("receipt_id")
        
        tenant_schema = self.get_tenant_schema_from_request(request)

        if not tenant_schema:
            return Response({"detail": "Tenant not found."}, status=status.HTTP_400_BAD_REQUEST)

        with schema_context(tenant_schema):
            try:
                # Fetch the existing parking details by receipt number
                parking_details = ParkingDetails.objects.get(receipt_id=receipt_id)
                print(parking_details)
                if parking_details.checkout_time:
                    return Response({"detail": "Vehicle already checked out."}, status=status.HTTP_400_BAD_REQUEST)
            except ValidationError as e:
                 # Handle validation errors and send them to the frontend
                return Response({"error": e.message_dict}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({"detail": "Parking details not found."}, status=status.HTTP_404_NOT_FOUND)
            # Pass the existing instance to the serializer for updating
            serializer = ParkingDetailsSerializer(parking_details, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()  # Save the updated instance
                return Response({"detail": "Checkout successful","data":serializer.data}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



# def generate_hour_ranges(start_time, end_time):
#     """Generate hour ranges from start_time to end_time."""
#     return pd.date_range(start=start_time, end=end_time, freq="h").to_pydatetime().tolist()

# def format_hour_range(hour):
#     """Format hour range as 8-9, 9-10, etc."""
#     start_hour = hour.hour
#     end_hour = (hour + timedelta(hours=1)).hour
#     return f"{start_hour}-{end_hour}"

# def get_parking_data(days=1):
#     # Calculate the start and end date
#     end_datetime = datetime.now()
#     start_datetime = end_datetime - timedelta(days=days)
    
#     # Define the time range (8:00 to 20:00)
#     start_time = start_datetime.replace(hour=8, minute=0, second=0, microsecond=0)
#     end_time = start_datetime.replace(hour=20, minute=0, second=0, microsecond=0)
#     print(f"Start datetime: {start_datetime}, End datetime: {end_datetime}")

#     # Generate the complete hour ranges for the given time
#     hour_ranges = generate_hour_ranges(start_time, end_time)
#     hour_ranges = [hour.astimezone(local_tz) for hour in hour_ranges]       
#     # Query the parking data
#     parking_data = (
#         ParkingDetails.objects.filter(
#             Q(checkin_time__date__gte=start_datetime.date()) &
#             (
#                 Q(checkin_time__time__range=("08:00:00", "20:00:00")) |
#                 Q(checkout_time__time__range=("08:00:00", "20:00:00"))
#             )
#         )
#         .annotate(hour_range=TruncHour('checkin_time'))
#         .values('hour_range', 'vehicle_type')
#         .annotate(
#             total_entries=Count('id', filter=Q(checkin_time__isnull=False)),
#             total_exits=Count('id', filter=Q(checkout_time__isnull=False)),
#         )
#     )
#     print(parking_data)

#     # Convert query result to a dictionary for easier processing
#     parking_data_dict = {}
#     for record in parking_data:
#         # Format the hour_range to match the generated hour ranges
#         formatted_hour = format_hour_range(record['hour_range'])
#         key = (formatted_hour, record['vehicle_type'])
#         parking_data_dict[key] = {
#             'total_entries': record['total_entries'],
#             'total_exits': record['total_exits']
#         }
#     print(parking_data_dict)
#     # Fill in missing hour ranges and vehicle types
#     vehicle_types = ['TWO_WHEELER', 'FOUR_WHEELER', 'HEAVY_VEHICLE']
#     result = []
#     for hour in hour_ranges:
#         formatted_hour = format_hour_range(hour)  # Match the format
#         for vehicle_type in vehicle_types:
#             key = (formatted_hour, vehicle_type)
#             data = parking_data_dict.get(key, {'total_entries': 0, 'total_exits': 0})
#             result.append({
#                 'hour_range': formatted_hour,
#                 'vehicle_type': vehicle_type,
#                 'total_entries': data['total_entries'],
#                 'total_exits': data['total_exits']
#             })
#     print(result)
#     return result

# class ParkingDetailsView(TenantAPIView):
#     permission_classes = [IsAuthenticated,IsSuperAdmin]  # Ensure only authenticated users can access this view
#     def get(self,request):
#         """
#         API to get parking data for graphs. 
#         Allows filtering based on days (1, 7, or 30).
#         """
#         # Extract 'days' parameter from request query, default to 1 if not provided
#         days = int(request.query_params.get('days', 1))  # Default to 1 day
#         print(f'days {days}')
#         # Validate days to ensure it's one of 1, 7, or 30
#         if days not in [1, 7, 30]:
#             return Response({"error": "Invalid 'days' value. Allowed values are 1, 7, or 30."}, status=400)
        
#         # Fetch the data
#         data = get_parking_data(days)
#         return Response(data)
    


class ParkingDetailsViewSet(ViewSet):
    permission_classes = [IsAuthenticated,IsSuperAdmin]  # Ensure only authenticated users can access this view
    
    @action(detail=False, methods=['GET'], url_path='get-details')
    def get_details(self, request):
        # Extract 'days' parameter from request query, default to 1 if not provided
        days = int(request.query_params.get('days', 1))  # Default to 1 day
        
        # Validate days to ensure it's one of 1, 7, or 30
        if days not in [1, 7, 30]:
            return Response({"error": "Invalid 'days' value. Allowed values are 1, 7, or 30."}, status=400)
        
        # Fetch the aggregated data
        data = self.get_aggregated_parking_data(days)
        
        # Return the data in the format expected for displaying in three boxes
        return Response(data)
    
    """
    Fetch parking data for graphs. Allows filtering based on days (1, 7, or 30).
    """
    # Extract 'days' parameter from request query, default to 1 if not provided
    @action(detail=False, methods=['GET'], url_path='get-graph-details')
    def get_graph_details(self, request):
        days = int(request.query_params.get('days', 1))  # Default to 1 day
        print(f'days {days}')
        
        # Validate days to ensure it's one of 1, 7, or 30
        if days not in [1, 7, 30]:
            return Response({"error": "Invalid 'days' value. Allowed values are 1, 7, or 30."}, status=400)
        
        # Calculate the start and end date
        end_datetime = datetime.now()
        
        
        # Calculate start date based on 'days' parameter and set to 8:00 AM
        start_datetime = end_datetime - timedelta(days=days-1)
        start_datetime = start_datetime.replace(hour=8, minute=0, second=0, microsecond=0)
        
        # Define the end time (today at 8:00 PM)
        end_time = start_datetime.replace(hour=20, minute=0, second=0, microsecond=0)
        print(f"Start datetime: {start_datetime}, End datetime: {end_datetime}")

        # Generate the complete hour ranges for the given time
        hour_ranges = self.generate_hour_ranges(start_datetime, end_time)
        hour_ranges = [hour.astimezone(local_tz) for hour in hour_ranges]

        # Query the parking data
        parking_data = (
            ParkingDetails.objects.filter(
                Q(checkin_time__date__gte=start_datetime.date()) &
                (
                    Q(checkin_time__time__range=("08:00:00", "20:00:00")) |
                    Q(checkout_time__time__range=("08:00:00", "20:00:00"))
                )
            )
            .annotate(hour_range=TruncHour('checkin_time'))
            .values('hour_range', 'vehicle_type')
            .annotate(
                total_entries=Count('id', filter=Q(checkin_time__isnull=False)),
                total_exits=Count('id', filter=Q(checkout_time__isnull=False)),
            )
        )
        print(parking_data)

        # Convert query result to a dictionary for easier processing
        parking_data_dict = {}
        for record in parking_data:
            # Format the hour_range to match the generated hour ranges
            formatted_hour = self.format_hour_range(record['hour_range'])
            key = (formatted_hour, record['vehicle_type'])
            parking_data_dict[key] = {
                'total_entries': record['total_entries'],
                'total_exits': record['total_exits']
            }
        print(parking_data_dict)

        # Fill in missing hour ranges and vehicle types
        vehicle_types = ['TWO_WHEELER', 'FOUR_WHEELER', 'HEAVY_VEHICLE']
        result = []
        for hour in hour_ranges:
            formatted_hour = self.format_hour_range(hour)  # Match the format
            for vehicle_type in vehicle_types:
                key = (formatted_hour, vehicle_type)
                data = parking_data_dict.get(key, {'total_entries': 0, 'total_exits': 0})
                result.append({
                    'hour_range': formatted_hour,
                    'vehicle_type': vehicle_type,
                    'total_entries': data['total_entries'],
                    'total_exits': data['total_exits']
                })
        print(result)
        return Response(result)
    def generate_hour_ranges(self, start_time, end_time):
        """Generate hour ranges from start_time to end_time."""
        return pd.date_range(start=start_time, end=end_time, freq="h").to_pydatetime().tolist()

    def format_hour_range(self, hour):
        """Format hour range as 8-9, 9-10, etc."""
        start_hour = hour.hour
        end_hour = (hour + timedelta(hours=1)).hour
        return f"{start_hour}-{end_hour}"
    
    def get_aggregated_parking_data(self,days=1):
        """Fetch total entries, exits, and collections aggregated for 1, 7, or 30 days."""
        
        # Calculate the date range
        end_datetime = datetime.now()
        start_datetime = end_datetime - timedelta(days=days-1)
        start_datetime = start_datetime.replace(hour=8, minute=0, second=0, microsecond=0)
        print(start_datetime)
        # Query the parking data for the given date range
        parking_data = (
            ParkingDetails.objects.filter(
                Q(checkin_time__gte=start_datetime) | Q(checkout_time__gte=start_datetime)
            )
            .annotate(day=TruncDate('checkin_time'))  # Truncate the checkin time to the date
            .values('day')
            .annotate(
                total_entries=Count('id', filter=Q(checkin_time__isnull=False)),
                total_exits=Count('id', filter=Q(checkout_time__isnull=False)),
                total_collections=Sum('amount')
            )
        )
        print(parking_data)
        # Calculate the aggregated totals
        total_entries = sum(record['total_entries'] for record in parking_data)
        total_exits = sum(record['total_exits'] for record in parking_data)
        total_collections = sum(record['total_collections'] or 0 for record in parking_data)

        return {
            "total_entries": total_entries,
            "total_exits": total_exits,
            "total_collections": total_collections
        }

    
        