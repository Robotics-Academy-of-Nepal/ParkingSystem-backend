from celery import shared_task
from datetime import datetime, timedelta
from tenant.models import Client  # Assuming Client model holds tenant details
from .services.passcode_service import PasscodeService  # Import the generate_passcode function
from django_tenants.utils import schema_context

@shared_task
def refresh_passcodes():
    tenants = Client.objects.all()  # Fetch all tenants
    for tenant in tenants:
        with schema_context(tenant.schema_name):  # Switch to tenant schema
            tenant.set_passcode()
            
            # Now the passcode is stored in the Passcode model, no need to store in tenant
            # You may want to log the passcode refresh or do something else here if necessary
            print(f"Passcode for tenant {tenant} refreshed: {tenant.passcode}, expires at {tenant.passcode_expires_at}")