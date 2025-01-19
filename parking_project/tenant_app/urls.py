from django.urls import path
from .views import *

urlpatterns = [
    path('login/', LoginAPIView.as_view(), name='login'),
    path('createuser/', CreateUserView.as_view(), name='create-user'),  
    path('userList/', UserListView.as_view(), name='list-users'),
    path('changeBaseRate/', ChangeBaseRateView.as_view(), name='change-base-rate'),
    path('refreshPasscode/', RefreshPasscodeView.as_view(), name='refresh-passcode'),
]