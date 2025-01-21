from django.db import models
from django_tenants.models import TenantMixin, DomainMixin
import uuid
from datetime import timedelta, timezone, date
def generate_passcode():
    return str(uuid.uuid4())[:8]
class Client(TenantMixin):
    name=models.CharField(max_length=100)
    paid_until=models.DateField()
    created_on=models.DateField(auto_now_add=True)
    auto_create_schema=True
    # passcode=models.CharField(max_length=100,null=True, blank=True)
    passcode = models.CharField(max_length=100, default = generate_passcode)
    # passcode_expires_at=models.DateTimeField(null=True, blank=True)
    passcode_expires_at = models.DateField()
    def __str__(self):
        return self.name
    
    def set_passcode(self):
        """Generate a passcode using UUID and set its expiration."""
        # Generate a passcode using UUID (v4)
        self.passcode = generate_passcode() # Take the first 8 characters of the UUID
        # self.passcode_expires_at = timezone.now() + timedelta(day=1)
        self.passcode_expires_at = date.today() + timedelta(days=1)
        self.save()

    def is_passcode_valid(self):
        """Check if the passcode is valid."""
        return self.passcode_expires_at > date.today() if self.passcode else False
    
class Domain(DomainMixin):
    pass