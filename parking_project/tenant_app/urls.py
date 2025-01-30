from django.urls import path,include
from .views import *
from rest_framework.routers import DefaultRouter
from .views import UserViewSet
from rest_framework.authtoken.views import obtain_auth_token

router=DefaultRouter()
router.register(r'users',UserViewSet,basename='user')
router.register(r'parking-details',ParkingDetailsViewSet,basename='parking-details')


urlpatterns = [
    path('', include(router.urls)),
    path('token/', obtain_auth_token, name='api_token_auth'),
    path('changeBaseRate/', ChangeBaseRateView.as_view(), name='change-base-rate'),
    path('refreshPasscode/', RefreshPasscodeView.as_view(), name='refresh-passcode'),
    path('checkin/', CheckinView.as_view(), name='checkin'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('print/',PrintImageView.as_view(),name='print'),
    path('sync-database/', DatabaseSyncView.as_view(), name='sync-database'),
]