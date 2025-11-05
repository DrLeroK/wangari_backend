from rest_framework import generics, permissions, status
from rest_framework.response import Response

from rest_framework.views import APIView
from .serializers import (UserSerializer, RegisterSerializer, 
                          CustomTokenObtainPairSerializer, VerifyEmailSerializer, 
                          ResendOTPSerializer)
from .models import User
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.views import TokenObtainPairView

from .utils import send_verification_email
from django.contrib.auth import authenticate
from django.db.models import Q

from apps.products.services import LoyaltyService
from apps.products.models import Order

from apps.products.views import log_activity
from apps.products.permissions import IsOwnerOrWorker
# from .permissions import IsOwnerOrWorker

import logging

logger = logging.getLogger(__name__)



# ========================================================================= #
# User Management Views
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        # Generates standard HTTP headers for a successful resource creation response
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    

class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            user.is_email_verified = True
            user.is_active = True  # Activate user account
            user.email_verification_otp = None  # Clear OTP
            user.otp_created_at = None
            user.save()
            
            return Response(
                {"detail": "Email verified successfully. You can now login."},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResendOTPView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            send_verification_email(user)
            
            return Response(
                {"detail": "OTP sent successfully. Please check your email."},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]


class UserDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

class UserProfileView(generics.RetrieveAPIView):
    """
    Extended user profile with loyalty information
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer
    
    def get_object(self):
        return self.request.user
    

class UpdateProfileView(generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

class LoyaltyProfileView(APIView):
    """
    Detailed loyalty profile for authenticated users
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        loyalty_summary = LoyaltyService.get_user_loyalty_summary(user)
        
        # Get user's completed orders that qualified for points
        qualifying_orders = Order.objects.filter(
            user=user,
            order_type='online',
            total_amount__gte=700,
            status='completed'
        ).order_by('-created_at')
        
        response_data = {
            'user': UserSerializer(user).data,
            'loyalty_summary': loyalty_summary,
            'qualifying_orders_count': qualifying_orders.count(),
            'recent_qualifying_orders': [
                {
                    'order_number': order.order_number,
                    'total_amount': float(order.total_amount),
                    'created_at': order.created_at,
                    'points_earned': 1
                }
                for order in qualifying_orders[:5]  # Last 5 orders
            ]
        }
        
        return Response(response_data)


class AdminLoyaltyUsersView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrWorker]
    serializer_class = UserSerializer
    
    def get_queryset(self):
        queryset = User.objects.all().order_by('-loyalty_points')
        
        # Filters
        tier = self.request.query_params.get('tier')
        points_min = self.request.query_params.get('points_min')
        points_max = self.request.query_params.get('points_max')
        search = self.request.query_params.get('search')
        sort_by = self.request.query_params.get('sort_by', 'points_desc')
        
        if tier:
            if tier == 'Gold':
                queryset = queryset.filter(loyalty_points__gte=100)
            elif tier == 'Silver':
                queryset = queryset.filter(loyalty_points__gte=60, loyalty_points__lt=100)
            elif tier == 'Bronze':
                queryset = queryset.filter(loyalty_points__gte=35, loyalty_points__lt=60)
            elif tier == 'Member':
                queryset = queryset.filter(loyalty_points__lt=35)
        
        if points_min:
            queryset = queryset.filter(loyalty_points__gte=int(points_min))
        
        if points_max:
            queryset = queryset.filter(loyalty_points__lte=int(points_max))
        
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search)
            )
        
        # Sorting
        if sort_by == 'points_asc':
            queryset = queryset.order_by('loyalty_points')
        elif sort_by == 'name_asc':
            queryset = queryset.order_by('first_name', 'last_name')
        elif sort_by == 'name_desc':
            queryset = queryset.order_by('-first_name', '-last_name')
        elif sort_by == 'recent_activity':
            # You might want to sort by last order date
            queryset = queryset.order_by('-date_joined')
        else:  # points_desc
            queryset = queryset.order_by('-loyalty_points')
        
        return queryset

class AdminLoyaltyStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrWorker]
    
    def get(self, request):
        total_users = User.objects.count()
        gold_users = User.objects.filter(loyalty_points__gte=100).count()
        silver_users = User.objects.filter(loyalty_points__gte=60, loyalty_points__lt=100).count()
        bronze_users = User.objects.filter(loyalty_points__gte=35, loyalty_points__lt=65).count()
        
        stats = {
            'total_users': total_users,
            'gold_users': gold_users,
            'silver_users': silver_users,
            'bronze_users': bronze_users,
        }
        
        return Response(stats)

class AdminUpdateUserPointsView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrWorker]
    
    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            action = request.data.get('action')  # 'add' or 'subtract'
            points = int(request.data.get('points', 0))
            reason = request.data.get('reason', '')
            
            if action == 'add':
                user.loyalty_points += points
            elif action == 'subtract':
                user.loyalty_points = max(0, user.loyalty_points - points)
            
            user.save()
            
            # Log the activity
            log_activity(
                user=request.user,
                action='loyalty_points',
                model_name='User',
                object_id=str(user.id),
                description=f'Admin {action}ed {points} points: {reason}',
                old_value=str(user.loyalty_points - (points if action == 'add' else -points)),
                new_value=str(user.loyalty_points),
                request=request
            )
            
            return Response({
                'success': True,
                'loyalty_points': user.loyalty_points
            })
            
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=400)
        

class DeleteAccountView(generics.DestroyAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

class LogoutView(generics.GenericAPIView):
    """
    Secure logout endpoint that blacklists refresh tokens
    and clears client-side tokens.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = None
    swagger_schema = None

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            
            if refresh_token:
                try:
                    token = RefreshToken(refresh_token)
                    token.blacklist()
                    logger.info(f"User {request.user.id} logged out successfully")
                except TokenError as e:
                    logger.warning(f"Invalid refresh token during logout: {e}")
                    # Continue with logout even if token is invalid

            response = Response(
                {"detail": "Successfully logged out."},
                status=status.HTTP_200_OK
            )
            
            # Clear cookies if used
            response.delete_cookie('access_token')
            response.delete_cookie('refresh_token')
            
            # Security headers
            response['Cache-Control'] = 'no-store'
            response['X-Content-Type-Options'] = 'nosniff'
            
            return response
            
        except Exception as e:
            logger.error(f"Logout error for user {request.user.id}: {e}")
            return Response(
                {"detail": "Failed to logout."},
                status=status.HTTP_400_BAD_REQUEST
            )




# Custom Token Obtain Pair View that uses email instead of username

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        try:
            logger.info(f"[LOGIN] Login attempt for email: {request.data.get('email')}")
            response = super().post(request, *args, **kwargs)
            logger.info("[LOGIN] Login successful")
            return response
        except Exception as e:
            logger.error(f"[LOGIN] Login view error: {str(e)}", exc_info=True)
            return Response(
                {"detail": "Login service temporarily unavailable."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )