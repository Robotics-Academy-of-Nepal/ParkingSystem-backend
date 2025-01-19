from django.db.models.signals import post_save
from django.dispatch import receiver
from tenant.models import Client
from .services.passcode_service import PasscodeService

@receiver(post_save, sender=Client)
def generate_passcode_on_tenant_creation(sender, instance, created, **kwargs):
    if created:  # Only on tenant creation
        print(f"Generating passcode for tenant {instance.id}")
        PasscodeService.refresh_passcode(instance)
        print(f"Passcode set for tenant {instance.id}: {instance.passcode_code}")
