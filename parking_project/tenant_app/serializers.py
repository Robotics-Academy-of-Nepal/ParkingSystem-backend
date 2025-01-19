from rest_framework import serializers
from .models import User
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)  # Ensure password is write-only

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
    
class BaseRateSerializer(serializers.Serializer):
    two_wheeler_rate = serializers.DecimalField(max_digits=10,decimal_places=2,required=False)
    four_wheeler_rate = serializers.DecimalField(max_digits=10,decimal_places=2,required=False)
    heavy_vehicle_rate = serializers.DecimalField(max_digits=10,decimal_places=2,required=False)