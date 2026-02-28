from django.urls import path, re_path
from app.views import *
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


urlpatterns = [
    path('auth/login/', LoginAPIView.as_view(), name='token_obtain_pair'),
    path('auth/me/', MeView.as_view(), name='me'),
    path('auth/refresh/', RefreshAPIView.as_view(), name='token_refresh'),
    path('auth/logout/', LogoutAPIView.as_view(), name='logout'),
    path('website/', WebsiteListAPIView.as_view(), name='website'),
    path('website/<int:pk>/', WebsiteDetailAPIView.as_view(), name='website_detail'),

]