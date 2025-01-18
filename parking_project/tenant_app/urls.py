from django.urls import path
from .views import *

urlpatterns = [
    path('login/', SuperAdminLoginAPIView.as_view(), name='superadmin-login'),
    path('createuser/', CreateUserView.as_view(), name='create-user'),   
]