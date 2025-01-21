from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from .views import *
from django.shortcuts import render
from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


urlpatterns = [
    path('admin/', admin.site.urls), 
    path('', index),
    path('api/', include('tenant_app.urls')),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
