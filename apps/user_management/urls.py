from django.urls import path
from .views import (
    UserListView, UserDetailView,
    RegisterView, UpdateProfileView,
    DeleteAccountView, LogoutView,
    CustomTokenObtainPairView, VerifyEmailView, 
    ResendOTPView
)

urlpatterns = [
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/me/', UserDetailView.as_view(), name='user-detail'),
    path('register/', RegisterView.as_view(), name='register'),

    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend-otp'),
    
    path('update/', UpdateProfileView.as_view(), name='update-profile'),
    path('delete/', DeleteAccountView.as_view(), name='delete-account'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),

]


