from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.timezone import now,datetime,timedelta
from django.core.exceptions import ValidationError

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
    
    
class ParkingDetails(models.Model):
    VEHICLE_TYPES=[
        ('TWO_WHEELER','Two Wheeler'),
        ('FOUR_WHEELER','Four Wheeler'),
        ('HEAVY_VEHICLE','Heavy Vehicle')
    ]
    receipt_id=models.CharField(max_length=100,blank=False,null=False,unique=True)
    vehicle_number=models.CharField(max_length=100,blank=True,null=True)
    vehicle_type=models.CharField(max_length=100,choices=VEHICLE_TYPES,blank=True,null=True)
    checkin_time=models.DateTimeField(default=now,blank=False,null=False)
    checkedin_by=models.ForeignKey(User,on_delete=models.CASCADE,blank=False,null=False,related_name='checked_in_parkings')
    checkout_time=models.DateTimeField(null=True,blank=True)
    checkedout_by=models.ForeignKey(User,on_delete=models.CASCADE,null=True,blank=True,related_name='checked_out_parkings')
    amount=models.DecimalField(max_digits=10,decimal_places=2,default=0)
    total_time=models.DurationField(null=True,blank=True)
    
    def clean(self):
        # Ensure checkout_time is greater than checkin_time
        if self.checkout_time and self.checkout_time <= self.checkin_time:
            raise ValidationError("Checkout time must be later than check-in time.")
    
    def save(self, *args, **kwargs):
        #perform validation
        self.full_clean()
        # Calculate total_time only if checkout_time is provided
        if self.checkout_time:
            time_difference = self.checkout_time - self.checkin_time
            
            # Cap total_time to 1 day if necessary
            if time_difference >= timedelta(days=1):
                self.total_time = timedelta(days=1)
            else:
                self.total_time = time_difference

        super().save(*args, **kwargs)
    
    