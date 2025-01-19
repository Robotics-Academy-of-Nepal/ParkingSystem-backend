from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.timezone import now

class User(AbstractUser):
    ROLE_CHOICES = [
        ('SUPERADMIN', 'Super Admin'),
        ('STAFF', 'Staff/Operator'),
    ]
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default='STAFF')
    phone = models.CharField(max_length=15, null=True, blank = True)
    address = models.TextField(null=True,blank=True)

    def is_superadmin(self):
        return self.role == 'SUPERADMIN'

    
class ParkingRates(models.Model):
    tenant=models.ForeignKey('tenant.Client',on_delete=models.CASCADE)
    two_wheeler_rate=models.DecimalField(max_digits=10,decimal_places=2,default=0)
    four_wheeler_rate=models.DecimalField(max_digits=10,decimal_places=2,default=0)
    heavy_vehicle_rate=models.DecimalField(max_digits=10,decimal_places=2,default=0)