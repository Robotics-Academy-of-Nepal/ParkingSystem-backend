import uuid
from datetime import timedelta
from django.utils.timezone import now
from tenant.models import Client

class PasscodeService:
    @staticmethod
    def generate_passcode():
    # Generate a random UUID and convert it to a string
        passcode = str(uuid.uuid4())[:8]  # Take the first 8 characters of the UUID
        return passcode
    
    @staticmethod
    def refresh_passcode(tenant):
        """
        Generate or refresh the passcode for a tenant.
        """
        new_passcode = PasscodeService.generate_passcode()
        expiry_time = now() + timedelta(hours=24)  # Set expiration for 24 hours
        
        # Set the passcode for the client (tenant)
        tenant.set_passcode()  # This will automatically generate the passcode and set expiration time
        tenant.passcode = new_passcode
        tenant.passcode_expires_at = expiry_time
        tenant.save()
        return tenant
