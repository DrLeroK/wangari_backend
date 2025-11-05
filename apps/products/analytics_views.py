# apps/products/analytics_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .permissions import IsOwner
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import timedelta, datetime
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from .models import Order, OrderItem, Product, Category
from apps.user_management.models import User
import json

class OwnerAnalyticsView(APIView):
    permission_classes = [IsAuthenticated, IsOwner]
    
    def get(self, request):
        try:
            # Get time period from query params (default: 30 days)
            days = int(request.GET.get('days', 30))
            start_date = timezone.now() - timedelta(days=days)
            
            # print(f"Analytics request: {days} days from {start_date}")
            
            analytics_data = {
                'time_period': f'last_{days}_days',
                'summary': self.get_summary_stats(start_date),
                'revenue_analytics': self.get_revenue_analytics(start_date),
                'order_analytics': self.get_order_analytics(start_date),
                'product_analytics': self.get_product_analytics(start_date),
                'customer_analytics': self.get_customer_analytics(start_date),
                'time_based_analytics': self.get_time_based_analytics(days)
            }
            
            # print(f"Analytics data prepared: {analytics_data['summary']}")
            
            return Response(analytics_data)
            
        except Exception as e:
            # print(f"Analytics error: {str(e)}")
            return Response(
                {'error': f'Failed to generate analytics: {str(e)}'}, 
                status=500
            )
    
    def get_summary_stats(self, start_date):
        """Get overall summary statistics"""
        try:
            total_orders = Order.objects.filter(created_at__gte=start_date)
            completed_orders = total_orders.filter(status='completed')
            
            # Use total_amount + delivery_fee for final total
            total_revenue = sum(
                order.total_amount + order.delivery_fee 
                for order in completed_orders
            )
            
            # print(f"Summary stats - Total orders: {total_orders.count()}, Revenue: {total_revenue}")
            
            return {
                'total_revenue': float(total_revenue),
                'total_orders': total_orders.count(),
                'completed_orders': completed_orders.count(),
                'average_order_value': float(completed_orders.aggregate(
                    avg=Avg('total_amount')
                )['avg'] or 0),
                'online_orders': total_orders.filter(order_type='online').count(),
                'offline_orders': total_orders.filter(order_type='offline').count(),
                'new_customers': User.objects.filter(
                    date_joined__gte=start_date,
                    is_staff=False
                ).count()
            }
        except Exception as e:
            # print(f" Summary stats error: {str(e)}")
            return {
                'total_revenue': 0,
                'total_orders': 0,
                'completed_orders': 0,
                'average_order_value': 0,
                'online_orders': 0,
                'offline_orders': 0,
                'new_customers': 0
            }
    
    def get_revenue_analytics(self, start_date):
        """Get revenue breakdown and trends"""
        try:
            orders = Order.objects.filter(
                created_at__gte=start_date,
                status='completed'
            )
            
            # Calculate revenue for each order type
            online_revenue = sum(
                order.total_amount + order.delivery_fee 
                for order in orders.filter(order_type='online')
            )
            
            offline_revenue = sum(
                order.total_amount + order.delivery_fee 
                for order in orders.filter(order_type='offline')
            )
            
            # Calculate revenue by fulfillment method
            pickup_revenue = sum(
                order.total_amount + order.delivery_fee 
                for order in orders.filter(fulfillment_method='pickup')
            )
            
            delivery_revenue = sum(
                order.total_amount + order.delivery_fee 
                for order in orders.filter(fulfillment_method='delivery')
            )
            
            total_revenue = online_revenue + offline_revenue
            
            return {
                'by_order_type': {
                    'online': float(online_revenue),
                    'offline': float(offline_revenue)
                },
                'by_fulfillment': {
                    'pickup': float(pickup_revenue),
                    'delivery': float(delivery_revenue)
                },
                'total_revenue': float(total_revenue)
            }
        except Exception as e:
            # print(f" Revenue analytics error: {str(e)}")
            return {
                'by_order_type': {'online': 0, 'offline': 0},
                'by_fulfillment': {'pickup': 0, 'delivery': 0},
                'total_revenue': 0
            }
    
    def get_order_analytics(self, start_date):
        """Get order statistics and trends"""
        try:
            orders = Order.objects.filter(created_at__gte=start_date)
            
            # Order status distribution
            status_distribution = list(orders.values('status').annotate(
                count=Count('id')
            ).order_by('-count'))
            
            # Order type distribution
            type_distribution = list(orders.values('order_type').annotate(
                count=Count('id')
            ))
            
            # Average preparation time for completed orders
            avg_prep_time = orders.filter(
                status='completed'
            ).aggregate(
                avg=Avg('estimated_preparation_time')
            )['avg'] or 0
            
            completion_rate = (
                (orders.filter(status='completed').count() / orders.count() * 100) 
                if orders.count() > 0 else 0
            )
            
            return {
                'status_distribution': status_distribution,
                'type_distribution': type_distribution,
                'average_preparation_time': avg_prep_time,
                'completion_rate': completion_rate
            }
        except Exception as e:
            # print(f"Order analytics error: {str(e)}")
            return {
                'status_distribution': [],
                'type_distribution': [],
                'average_preparation_time': 0,
                'completion_rate': 0
            }
    
    def get_product_analytics(self, start_date):
        """Get product performance analytics"""
        try:
            # Top selling products
            top_products = list(OrderItem.objects.filter(
                order__created_at__gte=start_date,
                order__status='completed'
            ).values(
                'product__name', 'product__category__name'
            ).annotate(
                total_quantity=Sum('quantity'),
                total_revenue=Sum('unit_price') * Sum('quantity')  # Calculate revenue manually
            ).order_by('-total_quantity')[:10])
            
            # Fix the total_revenue calculation for each product
            for product in top_products:
                product['total_revenue'] = float(product['total_revenue'] or 0)
            
            # Category performance
            category_performance = list(OrderItem.objects.filter(
                order__created_at__gte=start_date,
                order__status='completed'
            ).values('product__category__name').annotate(
                total_orders=Count('order', distinct=True),
                total_quantity=Sum('quantity')
            ).order_by('-total_quantity'))
            
            # Calculate revenue for each category
            for category in category_performance:
                category_revenue = OrderItem.objects.filter(
                    order__created_at__gte=start_date,
                    order__status='completed',
                    product__category__name=category['product__category__name']
                ).aggregate(
                    revenue=Sum('unit_price') * Sum('quantity')
                )['revenue'] or 0
                category['total_revenue'] = float(category_revenue)
            
            # Low stock alerts
            low_stock_products = list(Product.objects.filter(
                stock_quantity__lte=5,
                is_active=True
            ).values('name', 'stock_quantity', 'category__name').order_by('stock_quantity')[:10])
            
            total_products_sold = OrderItem.objects.filter(
                order__created_at__gte=start_date,
                order__status='completed'
            ).aggregate(total=Sum('quantity'))['total'] or 0
            
            return {
                'top_products': top_products,
                'category_performance': category_performance,
                'low_stock_alerts': low_stock_products,
                'total_products_sold': total_products_sold
            }
        except Exception as e:
            # print(f"Product analytics error: {str(e)}")
            return {
                'top_products': [],
                'category_performance': [],
                'low_stock_alerts': [],
                'total_products_sold': 0
            }
    
    def get_customer_analytics(self, start_date):
        """Get customer behavior analytics"""
        try:
            # Customer loyalty - top customers by order count
            loyal_customers = User.objects.filter(
                orders__created_at__gte=start_date,
                orders__status='completed',
                is_staff=False
            ).annotate(
                order_count=Count('orders')
            ).filter(order_count__gte=1).order_by('-order_count')[:10]
            
            # Calculate total spent for each customer
            top_customers_data = []
            for customer in loyal_customers:
                customer_orders = Order.objects.filter(
                    user=customer,
                    created_at__gte=start_date,
                    status='completed'
                )
                total_spent = sum(
                    order.total_amount + order.delivery_fee 
                    for order in customer_orders
                )
                
                top_customers_data.append({
                    'name': f"{customer.first_name} {customer.last_name}",
                    'email': customer.email,
                    'order_count': customer.order_count,
                    'total_spent': float(total_spent),
                    'loyalty_points': customer.loyalty_points
                })
            
            # New vs returning customers
            total_customers = User.objects.filter(
                orders__created_at__gte=start_date,
                orders__status='completed',
                is_staff=False
            ).distinct().count()
            
            # For simplicity, consider all as new customers in this period
            new_customers = total_customers
            returning_customers = 0
            
            return {
                'top_customers': top_customers_data,
                'customer_breakdown': {
                    'new_customers': new_customers,
                    'returning_customers': returning_customers,
                    'total_customers': total_customers
                },
                'average_customer_value': self.get_average_customer_value(start_date)
            }
        except Exception as e:
            # print(f" Customer analytics error: {str(e)}")
            return {
                'top_customers': [],
                'customer_breakdown': {
                    'new_customers': 0,
                    'returning_customers': 0,
                    'total_customers': 0
                },
                'average_customer_value': 0
            }
    
    def get_average_customer_value(self, start_date):
        """Calculate average customer lifetime value"""
        try:
            customers = User.objects.filter(
                orders__created_at__gte=start_date,
                orders__status='completed',
                is_staff=False
            ).distinct()
            
            total_revenue = 0
            for customer in customers:
                customer_orders = Order.objects.filter(
                    user=customer,
                    created_at__gte=start_date,
                    status='completed'
                )
                total_revenue += sum(
                    order.total_amount + order.delivery_fee 
                    for order in customer_orders
                )
            
            return float(total_revenue / customers.count()) if customers.count() > 0 else 0
        except:
            return 0
    
    def get_time_based_analytics(self, days):
        """Get time-based analytics (daily, weekly, monthly)"""
        try:
            if days <= 7:
                return self.get_daily_analytics(days)
            elif days <= 30:
                return self.get_weekly_analytics(days)
            else:
                return self.get_monthly_analytics(days)
        except Exception as e:
            # print(f" Time-based analytics error: {str(e)}")
            return {
                'period': 'daily',
                'data': []
            }
    
    def get_daily_analytics(self, days):
        """Get daily revenue and order data"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        daily_orders = Order.objects.filter(
            created_at__gte=start_date,
            status='completed'
        )
        
        # Group by date manually
        dates = {}
        for order in daily_orders:
            date_str = order.created_at.strftime('%Y-%m-%d')
            if date_str not in dates:
                dates[date_str] = {
                    'revenue': 0,
                    'orders': 0,
                    'order_values': []
                }
            
            order_total = order.total_amount + order.delivery_fee
            dates[date_str]['revenue'] += float(order_total)
            dates[date_str]['orders'] += 1
            dates[date_str]['order_values'].append(float(order_total))
        
        # Convert to list format
        daily_data = []
        for date_str, data in sorted(dates.items()):
            avg_order_value = sum(data['order_values']) / len(data['order_values']) if data['order_values'] else 0
            daily_data.append({
                'date': date_str,
                'revenue': data['revenue'],
                'orders': data['orders'],
                'avg_order_value': avg_order_value
            })
        
        return {
            'period': 'daily',
            'data': daily_data
        }
    
    def get_weekly_analytics(self, days):
        """Get weekly revenue and order data"""
        weekly_orders = Order.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=days),
            status='completed'
        )
        
        # Group by week manually
        weeks = {}
        for order in weekly_orders:
            week_str = order.created_at.strftime('%Y-%W')  # Year-Week number
            if week_str not in weeks:
                weeks[week_str] = {
                    'revenue': 0,
                    'orders': 0,
                    'order_values': []
                }
            
            order_total = order.total_amount + order.delivery_fee
            weeks[week_str]['revenue'] += float(order_total)
            weeks[week_str]['orders'] += 1
            weeks[week_str]['order_values'].append(float(order_total))
        
        # Convert to list format
        weekly_data = []
        for week_str, data in sorted(weeks.items()):
            avg_order_value = sum(data['order_values']) / len(data['order_values']) if data['order_values'] else 0
            weekly_data.append({
                'week': week_str,
                'revenue': data['revenue'],
                'orders': data['orders'],
                'avg_order_value': avg_order_value
            })
        
        return {
            'period': 'weekly',
            'data': weekly_data
        }
    
    def get_monthly_analytics(self, days):
        """Get monthly revenue and order data"""
        monthly_orders = Order.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=days),
            status='completed'
        )
        
        # Group by month manually
        months = {}
        for order in monthly_orders:
            month_str = order.created_at.strftime('%Y-%m')
            if month_str not in months:
                months[month_str] = {
                    'revenue': 0,
                    'orders': 0,
                    'order_values': []
                }
            
            order_total = order.total_amount + order.delivery_fee
            months[month_str]['revenue'] += float(order_total)
            months[month_str]['orders'] += 1
            months[month_str]['order_values'].append(float(order_total))
        
        # Convert to list format
        monthly_data = []
        for month_str, data in sorted(months.items()):
            avg_order_value = sum(data['order_values']) / len(data['order_values']) if data['order_values'] else 0
            monthly_data.append({
                'month': month_str,
                'revenue': data['revenue'],
                'orders': data['orders'],
                'avg_order_value': avg_order_value
            })
        
        return {
            'period': 'monthly',
            'data': monthly_data
        }


class ExportAnalyticsView(APIView):
    permission_classes = [IsAuthenticated, IsOwner]
    
    def get(self, request):
        """Export analytics data as JSON"""
        try:
            days = int(request.GET.get('days', 30))
            start_date = timezone.now() - timedelta(days=days)
            
            analytics_view = OwnerAnalyticsView()
            analytics_data = {
                'time_period': f'last_{days}_days',
                'summary': analytics_view.get_summary_stats(start_date),
                'revenue_analytics': analytics_view.get_revenue_analytics(start_date),
                'order_analytics': analytics_view.get_order_analytics(start_date),
                'product_analytics': analytics_view.get_product_analytics(start_date),
                'customer_analytics': analytics_view.get_customer_analytics(start_date),
                'time_based_analytics': analytics_view.get_time_based_analytics(days)
            }
            
            response = Response(analytics_data)
            response['Content-Disposition'] = f'attachment; filename="analytics_{days}_days.json"'
            return response
            
        except Exception as e:
            return Response(
                {'error': f'Failed to export analytics: {str(e)}'}, 
                status=500
            )