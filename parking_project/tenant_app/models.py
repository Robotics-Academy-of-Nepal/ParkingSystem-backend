from django.contrib.auth.models import AbstractUser
from django.db import models

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
