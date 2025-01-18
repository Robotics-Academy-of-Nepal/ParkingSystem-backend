from django.core.management.base import BaseCommand
from django_tenants.utils import schema_context
from tenant_app.models import User
from django.contrib.auth.hashers import make_password
  
class Command(BaseCommand):
    help = "Create Super Admin if not already created"
    
    def add_arguments(self, parser):
        parser.add_argument('schema', type=str, help='The schema name where the superadmin will be created')


    def handle(self, *args, **options):
        schema=options['schema']
        username = "superadmin"
        password = "superadmin"
        role = "SUPERADMIN"
        
        with schema_context(schema):
            if not User.objects.filter(username=username).exists():
                User.objects.create_superuser(
                    username=username,
                    password=password,
                    email= "superadmin@gmail.com",
                    role = role
                )
                self.stdout.write(self.style.SUCCESS("Super Admin Created Successfully"))
            else:
                self.stdout.write(self.style.WARNING("Super Admin already exists."))