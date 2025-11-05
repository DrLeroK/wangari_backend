from django.urls import path
from .views import (
    UserListView, UserDetailView,
    RegisterView, UpdateProfileView,
    DeleteAccountView, LogoutView,
    CustomTokenObtainPairView, VerifyEmailView, 
    ResendOTPView, UserProfileView, LoyaltyProfileView,
    AdminLoyaltyUsersView, AdminLoyaltyStatsView,
    AdminUpdateUserPointsView
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

    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('loyalty-profile/', LoyaltyProfileView.as_view(), name='loyalty-profile'),

    path('admin/loyalty-users/', AdminLoyaltyUsersView.as_view(), name='admin-loyalty-users'),
    path('admin/loyalty-stats/', AdminLoyaltyStatsView.as_view(), name='admin-loyalty-stats'),
    path('admin/users/<int:user_id>/update-points/', AdminUpdateUserPointsView.as_view(), name='admin-update-points'),

]


