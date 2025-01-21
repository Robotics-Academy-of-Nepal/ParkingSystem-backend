from rest_framework import serializers
from .models import User,ParkingDetails
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)  # Ensure password is write-only
    # is_superadmin=serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'password', 'email', 'first_name', 'last_name',
            'phone', 'address', 'role'
        ]
    def create(self, validated_data):
        # Create user with hashed password
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
    
    def get_is_superadmin(self, obj):
        # Method to get the is_superadmin field
        return obj.is_superadmin()
    
class BaseRateSerializer(serializers.Serializer):
    two_wheeler_rate = serializers.DecimalField(max_digits=10,decimal_places=2,required=False)
    four_wheeler_rate = serializers.DecimalField(max_digits=10,decimal_places=2,required=False)
    heavy_vehicle_rate = serializers.DecimalField(max_digits=10,decimal_places=2,required=False)
    
    def validate(self, data):
        # Ensure at least one rate is provided
        if not any(data.values()):
            raise serializers.ValidationError("At least one rate must be provided.")
        return data
    
class ParkingDetailsSerializer(serializers.ModelSerializer):
    checkedin_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    checkedout_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)

    class Meta:
        model = ParkingDetails
        fields = [
            'receipt_id', 'vehicle_number', 'vehicle_type', 'checkin_time',
            'checkedin_by', 'checkout_time', 'checkedout_by', 'amount', 'total_time'
        ]

    def validate(self, data):
        # Custom validation logic for parking details
        if 'checkout_time' in data and not data.get('checkedout_by'):
            raise serializers.ValidationError("Checked-out time requires a checked-out user.")
        return data