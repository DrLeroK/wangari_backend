# apps/products/services.py
from django.db import transaction
from django.utils import timezone
from .models import Order, ActivityLog
from apps.user_management.models import User

class LoyaltyService:
    @staticmethod
    def process_order_loyalty_points(order):
        """
        Process loyalty points for an order
        - Online orders over $700 get 1 point automatically
        - Only process when order status changes to completed
        """
        # print(f" Processing loyalty points for order {order.order_number}")
        # print(f"   - Order type: {order.order_type}")
        # print(f"   - Order status: {order.status}")
        # print(f"   - Total amount: ${order.total_amount}")
        # print(f"   - User: {order.user}")
        
        # Check if order qualifies for loyalty points
        if (order.order_type == 'online' and 
            order.user and 
            order.total_amount >= 700 and
            order.status == 'completed'):
            
            # print(f"Order qualifies for loyalty points!")
            
            # Check if points were already awarded for this order
            if not ActivityLog.objects.filter(
                action='loyalty_points_awarded', 
                object_id=str(order.id),
                model_name='Order'
            ).exists():
                
                # print(f" Awarding 1 point to user {order.user.email}")
                
                with transaction.atomic():
                    # Add 1 point to user
                    old_points = order.user.loyalty_points
                    order.user.loyalty_points += 1
                    order.user.save()
                    
                    # Log the activity
                    ActivityLog.objects.create(
                        user=order.user,
                        action='loyalty_points_awarded',
                        model_name='Order',
                        object_id=str(order.id),
                        description=f'Loyalty points awarded for order {order.order_number} (${order.total_amount})',
                        old_value=str(old_points),
                        new_value=str(order.user.loyalty_points),
                        ip_address=None
                    )
                    
                    # print(f" Successfully awarded 1 point! User now has {order.user.loyalty_points} points")
                    return True
            else:
                print(f" Points already awarded for this order")
        else:
            # print(f" Order doesn't qualify for loyalty points:")
            if order.order_type != 'online':
                print("   - Not an online order")
            if not order.user:
                print("   - No user associated with order")
            if order.total_amount < 700:
                print(f"   - Order amount ${order.total_amount} is less than $700")
            if order.status != 'completed':
                print("   - Order status is not 'completed'")
        
        return False
    
    @staticmethod
    def get_user_loyalty_summary(user):
        """Get loyalty summary for a user"""
        # Count qualifying orders for this user
        qualifying_orders = Order.objects.filter(
            user=user,
            order_type='online',
            total_amount__gte=700,
            status='completed'
        ).count()
        
        return {
            'points': user.loyalty_points,
            'tier': LoyaltyService.get_tier(user.loyalty_points),
            'next_tier': LoyaltyService.get_next_tier_info(user.loyalty_points),
            'qualifying_orders_count': qualifying_orders,
            'points_per_order': 1  # Fixed rate
        }
    
    @staticmethod
    def get_tier(points):
        if points >= 100:
            return "Gold"
        elif points >= 60:
            return "Silver"
        elif points >= 35:
            return "Bronze"
        else:
            return "Member"
    
    @staticmethod
    def get_next_tier_info(current_points):
        if current_points >= 100:
            return {'tier': 'Max', 'points_needed': 0}
        elif current_points >= 60:
            return {'tier': 'Gold', 'points_needed': 100 - current_points}
        elif current_points >= 35:
            return {'tier': 'Silver', 'points_needed': 60 - current_points}
        else:
            return {'tier': 'Bronze', 'points_needed': 35 - current_points}

