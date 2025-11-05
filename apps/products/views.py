from rest_framework import generics, status, filters
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import date, timedelta
from django.contrib.auth import get_user_model


from .models import Category, Product, Review, Cart, CartItem, Order, OrderItem, ActivityLog
from .serializers import (
    CategorySerializer, ProductSerializer, ProductListSerializer,
    ReviewSerializer, CartSerializer, CartItemSerializer,
    AddToCartSerializer, UpdateCartItemSerializer,
    OrderSerializer, OrderCreateSerializer, StockUpdateSerializer,
    ActivityLogSerializer
)

# from .permissions import IsOwnerOrWorker, IsOwner, IsWorker, IsOrderOwnerOrStaff

from .permissions import (IsStaff, IsOwner, IsChef, IsWaiter, 
                        IsCashier, IsButcher, CanManageProducts, 
                        CanManageOrders, CanProcessPhysicalSales, 
                        IsOwnerOrWorker, IsOrderOwnerOrStaff)

from .services import LoyaltyService

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


User = get_user_model()



############ Activity Log Helper Function ############

def log_activity(user, action, model_name, object_id='', description='', old_value='', new_value='', request=None):
    ip_address = request.META.get('REMOTE_ADDR') if request else None
    ActivityLog.objects.create(
        user=user,
        action=action,
        model_name=model_name,
        object_id=object_id,
        description=description,
        old_value=old_value,
        new_value=new_value,
        ip_address=ip_address
    )


################## Public Views (No authentication required) ######################


class CategoryListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = CategorySerializer
    
    def get_queryset(self):
        return Category.objects.filter(is_active=True).annotate(
            product_count=Count('products')
        ).order_by('name')


class ProductListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = ProductListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'category__name']
    ordering_fields = ['price', 'name', 'created_at', 'average_rating']
    ordering = ['name']
    
    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True, show=True, stock_quantity__gt=0)
        
        # Filter by category
        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Filter by product type
        product_type = self.request.query_params.get('type')
        if product_type:
            queryset = queryset.filter(product_type=product_type)
        
        is_spicy = self.request.query_params.get('spicy')
        if is_spicy and is_spicy.lower() == 'true':
            queryset = queryset.filter(is_spicy=True)
        
        return queryset


class ProductDetailView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = ProductSerializer
    queryset = Product.objects.filter(is_active=True, show=True)


class ProductReviewsView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = ReviewSerializer
    
    def get_queryset(self):

        if getattr(self, 'swagger_fake_view', False):
            return Review.objects.none()
        
        product_id = self.kwargs['pk']
        return Review.objects.filter(product_id=product_id, is_active=True).select_related('user')



class CreateReviewView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ReviewSerializer
    
    def get_serializer_context(self):
        # Add product to serializer context
        context = super().get_serializer_context()
        product_id = self.kwargs['pk']
        product = get_object_or_404(Product, id=product_id, is_active=True)
        context['product'] = product
        return context
    
    def create(self, request, *args, **kwargs):
        product = self.get_serializer_context()['product']
        
        # Check if user already reviewed this product
        if Review.objects.filter(product=product, user=request.user).exists():
            return Response(
                {"detail": "You have already reviewed this product."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().create(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        product = self.get_serializer_context()['product']
        review = serializer.save(product=product, user=self.request.user)



####################### Cart Views ########################

class CartView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CartSerializer
    
    def get_object(self):
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart



class AddToCartView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = AddToCartSerializer(data=request.data)
        if serializer.is_valid():
            product_id = serializer.validated_data['product_id']
            quantity = serializer.validated_data['quantity']
            weight_kg = serializer.validated_data.get('weight_kg')
            special_instructions = serializer.validated_data.get('special_instructions', '')
            
            product = get_object_or_404(Product, id=product_id, is_active=True, show=True)
            
            # FIXED: Check stock for BOTH product types
            if product.is_weight_based:
                # For weight-based products: check weight availability
                if weight_kg and product.stock_quantity < weight_kg:
                    return Response(
                        {'error': f'Insufficient stock. Only {product.stock_quantity}kg available.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                # For fixed-price products: check quantity availability
                if product.stock_quantity < quantity:
                    return Response(
                        {'error': f'Insufficient stock. Only {product.stock_quantity} available.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            cart, created = Cart.objects.get_or_create(user=request.user)
            
            # For weight-based products, use weight_kg in the lookup
            if product.is_weight_based and weight_kg:
                lookup_params = {
                    'cart': cart,
                    'product': product,
                    'weight_kg': weight_kg
                }
            else:
                lookup_params = {
                    'cart': cart,
                    'product': product
                }
            
            # Check if item already in cart with same weight
            cart_item, created = CartItem.objects.get_or_create(
                **lookup_params,
                defaults={
                    'quantity': quantity,
                    'weight_kg': weight_kg,
                    'special_instructions': special_instructions
                }
            )
            
            if not created:
                cart_item.quantity += quantity
                if special_instructions:
                    cart_item.special_instructions = special_instructions
                cart_item.save()
            
            return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpdateCartItemView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UpdateCartItemSerializer
    queryset = CartItem.objects.all()
    
    def get_queryset(self):

        if getattr(self, 'swagger_fake_view', False):
            return CartItem.objects.none()
        return CartItem.objects.filter(cart__user=self.request.user)
    
    def perform_update(self, serializer):
        cart_item = self.get_object()
        old_quantity = cart_item.quantity
        
        updated_item = serializer.save()
        
        # Check stock availability
        if updated_item.quantity > updated_item.product.stock_quantity:
            raise serializers.ValidationError({
                'quantity': f'Only {updated_item.product.stock_quantity} available in stock.'
            })
        
        # log_activity(
        #     user=self.request.user,
        #     action='update',
        #     model_name='CartItem',
        #     object_id=str(updated_item.id),
        #     description=f'Cart item updated: {updated_item.product.name}',
        #     old_value=f"Quantity: {old_quantity}",
        #     new_value=f"Quantity: {updated_item.quantity}",
        #     request=self.request
        # )



class RemoveFromCartView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = CartItem.objects.all()
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return CartItem.objects.none()
        return CartItem.objects.filter(cart__user=self.request.user)
    
    def perform_destroy(self, instance):
        log_activity(
            user=self.request.user,
            action='delete',
            model_name='CartItem',
            object_id=str(instance.id),
            description=f'Item removed from cart: {instance.product.name}',
            old_value=f"Quantity: {instance.quantity}",
            request=self.request
        )
        instance.delete()



class ClearCartView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        cart = get_object_or_404(Cart, user=request.user)
        items_count = cart.items.count()
        
        # log_activity(
        #     user=request.user,
        #     action='delete',
        #     model_name='Cart',
        #     object_id=str(cart.id),
        #     description='Cart cleared',
        #     old_value=f"Items: {items_count}",
        #     request=request
        # )
        
        cart.items.all().delete()
        return Response({'detail': 'Cart cleared successfully.'}, status=status.HTTP_200_OK)




##################### Order Views #####################

class CreateOrderView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = OrderCreateSerializer
    
    def create(self, request, *args, **kwargs):
        # If user is authenticated, we can use their cart
        if request.user.is_authenticated and not request.user.groups.filter(name__in=['Worker', 'Owner']).exists():
            return self.create_from_cart(request)
        else:
            return super().create(request, *args, **kwargs)
        
    def create_from_cart(self, request):
        cart = get_object_or_404(Cart, user=request.user)
        if cart.items.count() == 0:
            return Response(
                {'error': 'Cart is empty.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Prepare order data from cart including new fields
        order_data = {
            'customer_name': f"{request.user.first_name} {request.user.last_name}",
            'customer_email': request.user.email,
            'customer_phone': getattr(request.user, 'phone_number', ''),
            'order_type': 'online',
            'fulfillment_method': request.data.get('fulfillment_method', 'pickup'),
            'delivery_address': request.data.get('delivery_address', ''),
            'notes': request.data.get('notes', ''),
            'pickup_time': request.data.get('pickup_time'),
            'delivery_time': request.data.get('delivery_time'),
            'payment_confirmation': request.FILES.get('payment_confirmation'),
            'items': []
        }
        
        # FIXED: Prepare items from cart with weight_kg
        for cart_item in cart.items.all():
            item_data = {
                'product': cart_item.product.id,
                'quantity': cart_item.quantity,
                'special_instructions': cart_item.special_instructions
            }
            
            # ADD THIS: Include weight_kg for weight-based products
            if cart_item.product.is_weight_based and cart_item.weight_kg:
                item_data['weight_kg'] = float(cart_item.weight_kg)
            
            order_data['items'].append(item_data)
        
        serializer = self.get_serializer(data=order_data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        
        # Log the order creation activity
        user_for_log = request.user if request.user.is_authenticated else None
        log_activity(
            user=user_for_log,
            action='create',
            model_name='Order',
            object_id=str(order.id),
            description=f'Online order created: {order.order_number}',
            new_value=f"Status: {order.status}, Total: ${order.final_total}, Type: {order.order_type}, Method: {order.fulfillment_method}",
            request=request
        )
        
        # Clear the cart after successful order
        cart.items.all().delete()
        
        headers = self.get_success_headers(serializer.data)
        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )


class UserOrderListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer
    
    def get_queryset(self):
        return Order.objects.filter(
            Q(user=self.request.user) | Q(customer_email=self.request.user.email)
        ).order_by('-created_at')


class OrderDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated, IsOrderOwnerOrStaff]
    serializer_class = OrderSerializer
    queryset = Order.objects.all()



################## Admin Views (Owner and Worker permissions) ######################

class AdminCategoryListCreateView(generics.ListCreateAPIView):
    # permission_classes = [IsAuthenticated, IsOwnerOrWorker]
    permission_classes = [IsAuthenticated, CanManageProducts]
    serializer_class = CategorySerializer
    queryset = Category.objects.all()
    
    def perform_create(self, serializer):
        category = serializer.save()
        log_activity(
            user=self.request.user,
            action='create',
            model_name='Category',
            object_id=str(category.id),
            description=f'Category created: {category.name}',
            new_value=category.name,
            request=self.request
        )


class AdminCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    # permission_classes = [IsAuthenticated, IsOwnerOrWorker]
    permission_classes = [IsAuthenticated, CanManageProducts]
    serializer_class = CategorySerializer
    queryset = Category.objects.all()
    
    def perform_update(self, serializer):
        old_name = self.get_object().name
        category = serializer.save()
        log_activity(
            user=self.request.user,
            action='update',
            model_name='Category',
            object_id=str(category.id),
            description=f'Category updated: {old_name} -> {category.name}',
            old_value=old_name,
            new_value=category.name,
            request=self.request
        )
    
    def perform_destroy(self, instance):
        log_activity(
            user=self.request.user,
            action='delete',
            model_name='Category',
            object_id=str(instance.id),
            description=f'Category deleted: {instance.name}',
            old_value=instance.name,
            request=self.request
        )
        instance.delete()


class AdminProductListCreateView(generics.ListCreateAPIView):
    # permission_classes = [IsAuthenticated, IsOwnerOrWorker]
    permission_classes = [IsAuthenticated, CanManageProducts]
    serializer_class = ProductSerializer
    queryset = Product.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'category__name']
    ordering_fields = ['price', 'name', 'created_at', 'stock_quantity']
    
    def perform_create(self, serializer):
        product = serializer.save()
        log_activity(
            user=self.request.user,
            action='create',
            model_name='Product',
            object_id=str(product.id),
            description=f'Product created: {product.name}',
            new_value=product.name,
            request=self.request
        )


class AdminProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    # permission_classes = [IsAuthenticated, IsOwnerOrWorker]
    permission_classes = [IsAuthenticated, CanManageProducts]
    serializer_class = ProductSerializer
    queryset = Product.objects.all()
    
    def perform_update(self, serializer):
        product = self.get_object()
        old_name = product.name
        old_stock = product.stock_quantity
        
        updated_product = serializer.save()
        
        # Log stock changes if any
        if old_stock != updated_product.stock_quantity:
            action = 'stock_add' if updated_product.stock_quantity > old_stock else 'stock_reduce'
            log_activity(
                user=self.request.user,
                action=action,
                model_name='Product',
                object_id=str(updated_product.id),
                description=f'Product stock updated: {updated_product.name}',
                old_value=str(old_stock),
                new_value=str(updated_product.stock_quantity),
                request=self.request
            )
        else:
            log_activity(
                user=self.request.user,
                action='update',
                model_name='Product',
                object_id=str(updated_product.id),
                description=f'Product updated: {old_name} -> {updated_product.name}',
                old_value=old_name,
                new_value=updated_product.name,
                request=self.request
            )
    
    def perform_destroy(self, instance):
        log_activity(
            user=self.request.user,
            action='delete',
            model_name='Product',
            object_id=str(instance.id),
            description=f'Product deleted: {instance.name}',
            old_value=instance.name,
            request=self.request
        )
        instance.delete()



class UpdateProductStockView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrWorker]
    
    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        serializer = StockUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            quantity = serializer.validated_data['quantity']
            action = serializer.validated_data['action']
            reason = serializer.validated_data.get('reason', '')
            
            old_stock = product.stock_quantity
            
            if action == 'add':
                product.stock_quantity += quantity
                log_action = 'stock_add'
                action_description = 'added to'
            else:  # reduce
                if product.stock_quantity < quantity:
                    return Response(
                        {'error': 'Insufficient stock'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                product.stock_quantity -= quantity
                log_action = 'stock_reduce'
                action_description = 'reduced from'
            
            product.save()
            
            # Log the activity
            description = f"Stock {action_description} {product.name}"
            if reason:
                description += f" - Reason: {reason}"
                
            log_activity(
                user=request.user,
                action=log_action,
                model_name='Product',
                object_id=str(product.id),
                description=description,
                old_value=str(old_stock),
                new_value=str(product.stock_quantity),
                request=request
            )
            
            return Response(ProductSerializer(product).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class AdminOrderListView(generics.ListAPIView):
    # permission_classes = [IsAuthenticated, IsOwnerOrWorker]
    permission_classes = [IsAuthenticated, CanManageOrders]
    serializer_class = OrderSerializer
    queryset = Order.objects.all()
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'total_amount', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = Order.objects.all()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by order type
        order_type = self.request.query_params.get('order_type')
        if order_type:
            queryset = queryset.filter(order_type=order_type)
        
        # Filter by fulfillment method
        fulfillment_method = self.request.query_params.get('fulfillment_method')
        if fulfillment_method:
            queryset = queryset.filter(fulfillment_method=fulfillment_method)
        
        return queryset
    


class AdminOrderDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated, IsOwnerOrWorker]
    serializer_class = OrderSerializer
    queryset = Order.objects.all()
    
    def perform_update(self, serializer):
        order = self.get_object()
        old_status = order.status
        
        # Handle payment verification separately if it's in the request
        request_data = self.request.data.copy()
        payment_verified = request_data.pop('payment_verified', None)
        
        updated_order = serializer.save()
        
        # Handle payment verification
        if payment_verified is not None:
            if payment_verified and not updated_order.payment_verified:
                # Verify payment
                updated_order.payment_verified = True
                updated_order.payment_verified_by = self.request.user
                updated_order.payment_verified_at = timezone.now()
            elif not payment_verified and updated_order.payment_verified:
                # Unverify payment
                updated_order.payment_verified = False
                updated_order.payment_verified_by = None
                updated_order.payment_verified_at = None
            updated_order.save()
        
        # Update ready_at time if status changed to ready
        if updated_order.status == 'ready' and not updated_order.ready_at:
            updated_order.ready_at = timezone.now()
            updated_order.save()
        
        # Process loyalty points when order status changes to completed
        if (old_status != 'completed' and 
            updated_order.status == 'completed'):
            
            print(f" Order {updated_order.order_number} status changed to completed")
            print(f"   Processing loyalty points...")
            
            # Process loyalty points
            points_awarded = LoyaltyService.process_order_loyalty_points(updated_order)
            
            if points_awarded:
                print(f" Loyalty points awarded successfully!")
            else:
                print(f" No loyalty points awarded")
        
        # Log status change
        if old_status != updated_order.status:
            log_activity(
                user=self.request.user,
                action='order_status',
                model_name='Order',
                object_id=str(updated_order.id),
                description=f'Order status changed: {updated_order.order_number}',
                old_value=old_status,
                new_value=updated_order.status,
                request=self.request
            )
        
        # Log payment verification if changed
        if payment_verified is not None:
            action = 'verified' if payment_verified else 'unverified'
            log_activity(
                user=self.request.user,
                action='update',
                model_name='Order',
                object_id=str(updated_order.id),
                description=f'Payment {action} for order: {updated_order.order_number}',
                old_value=str(not payment_verified),
                new_value=str(payment_verified),
                request=self.request
            )


#################### Additional Admin Actions ####################

class CreatePhysicalSaleView(generics.CreateAPIView):
    # permission_classes = [IsAuthenticated, IsOwnerOrWorker]
    permission_classes = [IsAuthenticated, CanProcessPhysicalSales]
    serializer_class = OrderCreateSerializer
    
    def create(self, request, *args, **kwargs):
        # Force order type to offline for physical sales
        request.data['order_type'] = 'offline'
        
        # Auto-fill customer information from the worker
        if not request.data.get('customer_name'):
            request.data['customer_name'] = f"Table {request.data.get('table_number', 'N/A')} - {request.user.get_full_name()}"
        if not request.data.get('customer_email'):
            request.data['customer_email'] = request.user.email
        if not request.data.get('customer_phone'):
            request.data['customer_phone'] = 'N/A'
        
        return super().create(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        order = serializer.save()
        
        # Log the physical sale creation activity
        log_activity(
            user=self.request.user,
            action='physical_sale',
            model_name='Order',
            object_id=str(order.id),
            description=f'Physical sale created: {order.order_number} for Table {order.table_number}',
            new_value=f"Status: {order.status}, Total: ${order.final_total}, Table: {order.table_number}, Worker: {self.request.user.get_full_name()}",
            request=self.request
        )




class ActivityLogListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsOwnerOrWorker]
    serializer_class = ActivityLogSerializer
    queryset = ActivityLog.objects.all()
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        queryset = ActivityLog.objects.all()
        
        # Filter by action
        action = self.request.query_params.get('action')
        if action:
            queryset = queryset.filter(action=action)
        
        # Filter by user
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(timestamp__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__date__lte=end_date)
        
        return queryset



############### Additional admin management views ###############

class LowStockProductsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsOwnerOrWorker]
    serializer_class = ProductSerializer
    
    def get_queryset(self):
        threshold = self.request.query_params.get('threshold', 10)
        return Product.objects.filter(
            stock_quantity__lte=int(threshold), 
            is_active=True
        ).order_by('stock_quantity')


class TodayOrdersView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsOwnerOrWorker]
    serializer_class = OrderSerializer
    
    def get_queryset(self):
        today = timezone.now().date()
        return Order.objects.filter(created_at__date=today)


class OrderStatsView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrWorker]
    
    def get(self, request):
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        # Today's stats
        today_orders = Order.objects.filter(created_at__date=today)
        yesterday_orders = Order.objects.filter(created_at__date=yesterday)
        
        stats = {
            # Today's orders
            'total_orders_today': today_orders.count(),
            'pending_orders': Order.objects.filter(status='pending').count(),
            'completed_orders_today': today_orders.filter(status='completed').count(),
            'pickup_orders_today': today_orders.filter(fulfillment_method='pickup').count(),
            'delivery_orders_today': today_orders.filter(fulfillment_method='delivery').count(),
            
            # Revenue
            'revenue_today': sum(order.final_total for order in today_orders),
            'revenue_yesterday': sum(order.final_total for order in yesterday_orders),
            
            # Products
            'low_stock_products': Product.objects.filter(stock_quantity__lte=5, is_active=True).count(),
            'out_of_stock_products': Product.objects.filter(stock_quantity=0, is_active=True).count(),
            'total_products': Product.objects.filter(is_active=True).count(),
            
            # Order status breakdown
            'orders_by_status': {
                status[1]: Order.objects.filter(status=status[0]).count()
                for status in Order.STATUS_CHOICES
            }
        }
        
        return Response(stats)


################# Review Management Views ################


class ReviewManagementView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsOwnerOrWorker]
    serializer_class = ReviewSerializer
    queryset = Review.objects.all()
    
    def get_queryset(self):
        queryset = Review.objects.select_related('user', 'product').order_by('-created_at')
        
        # Filter by is_active status
        is_active = self.request.query_params.get('is_active')
        if is_active:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Filter by product
        product_id = self.request.query_params.get('product')
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        
        # Filter by rating
        rating = self.request.query_params.get('rating')
        if rating:
            queryset = queryset.filter(rating=rating)
        
        return queryset

class ToggleReviewStatusView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrWorker]
    
    def post(self, request, pk):
        review = get_object_or_404(Review, pk=pk)
        old_status = review.is_active
        review.is_active = not review.is_active
        review.save()
        
        action = 'activated' if review.is_active else 'deactivated'
        log_activity(
            user=request.user,
            action='update',
            model_name='Review',
            object_id=str(review.id),
            description=f'Review {action} for {review.product.name}',
            old_value=f"Active: {old_status}",
            new_value=f"Active: {review.is_active}",
            request=request
        )
        
        return Response({
            'detail': f'Review {action} successfully.',
            'is_active': review.is_active
        })


class EnhancedOrderStatsView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrWorker]
    
    def get(self, request):
        today = date.today()
        yesterday = today - timedelta(days=1)
        last_month = today - timedelta(days=30)
        
        # Today's stats
        today_orders = Order.objects.filter(created_at__date=today)
        yesterday_orders = Order.objects.filter(created_at__date=yesterday)
        last_month_orders = Order.objects.filter(created_at__date__gte=last_month)
        
        # Calculate growth
        revenue_today = sum(order.final_total for order in today_orders)
        revenue_yesterday = sum(order.final_total for order in yesterday_orders)
        
        monthly_growth = 0
        if revenue_yesterday > 0:
            monthly_growth = ((revenue_today - revenue_yesterday) / revenue_yesterday) * 100
        
        stats = {
            # Revenue
            'revenue_today': revenue_today,
            'revenue_yesterday': revenue_yesterday,
            'monthly_growth': round(monthly_growth, 1),
            
            # Orders
            'total_orders_today': today_orders.count(),
            'pending_orders': Order.objects.filter(status='pending').count(),
            'completed_orders_today': today_orders.filter(status='completed').count(),
            
            # Products
            'low_stock_products': Product.objects.filter(stock_quantity__lte=5, is_active=True).count(),
            'out_of_stock_products': Product.objects.filter(stock_quantity=0, is_active=True).count(),
            'total_products': Product.objects.filter(is_active=True).count(),
            'total_categories': Category.objects.filter(is_active=True).count(),
            
            # Order status breakdown
            'orders_by_status': {
                status[1]: Order.objects.filter(status=status[0]).count()
                for status in Order.STATUS_CHOICES
            }
        }
        
        return Response(stats)



# apps/products/views.py - ADD THIS VIEW

class RoleSpecificDashboardData(APIView):
    permission_classes = [IsAuthenticated, IsStaff]
    
    def get(self, request):
        user = request.user
        role = self.get_user_role(user)
        
        # Get today's date for filtering
        today = timezone.now().date()
        
        data = {
            'role': role,
            'user': {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email
            },
            'stats': self.get_role_stats(role, today)
        }
        
        return Response(data)
    
    def get_user_role(self, user):
        """Determine user's specific role"""
        if user.is_superuser or user.groups.filter(name='Owner').exists():
            return 'owner'
        elif user.groups.filter(name='Chef').exists():
            return 'chef'
        elif user.groups.filter(name='Waiter').exists():
            return 'waiter'
        elif user.groups.filter(name='Cashier').exists():
            return 'cashier'
        elif user.groups.filter(name='Butcher').exists():
            return 'butcher'
        elif user.groups.filter(name='Worker').exists():
            return 'worker'
        return 'customer'
    
    def get_role_stats(self, role, today):
        """Get statistics specific to each role"""
        today_orders = Order.objects.filter(created_at__date=today)
        
        if role == 'owner':
            return {
                'totalRevenue': float(sum(order.final_total for order in today_orders)),
                'totalOrders': today_orders.count(),
                'pendingOrders': Order.objects.filter(status='pending').count(),
                'completedOrders': today_orders.filter(status='completed').count(),
                'lowStockProducts': Product.objects.filter(stock_quantity__lte=5, is_active=True).count(),
            }
        
        elif role == 'chef':
            return {
                'pendingOrders': Order.objects.filter(status='pending').count(),
                'preparingOrders': Order.objects.filter(status='preparing').count(),
                'readyOrders': Order.objects.filter(status='ready').count(),
                'totalOrders': Order.objects.filter(status__in=['pending', 'preparing']).count(),
            }
        
        elif role == 'waiter':
            return {
                'activeOrders': Order.objects.filter(status__in=['pending', 'preparing', 'ready']).count(),
                'readyOrders': Order.objects.filter(status='ready').count(),
                'physicalSalesToday': Order.objects.filter(
                    order_type='offline', 
                    created_at__date=today
                ).count(),
            }
        
        elif role == 'cashier':
            return {
                'totalRevenue': float(sum(order.final_total for order in today_orders)),
                'pendingPayments': Order.objects.filter(status='pending', payment_verified=False).count(),
                'completedTransactions': today_orders.filter(status='completed').count(),
            }
        
        elif role == 'butcher':
            # Count meat-related products (you might want to adjust this logic)
            meat_products = Product.objects.filter(
                name__icontains='meat', 
                is_active=True
            ).count()
            
            return {
                'meatProducts': meat_products,
                'lowStockItems': Product.objects.filter(stock_quantity__lte=3, is_active=True).count(),
                'totalInventory': Product.objects.filter(is_active=True).count(),
            }
        
        else:  # worker or fallback
            return {
                'pendingOrders': Order.objects.filter(status='pending').count(),
                'activeTasks': 5,
            }



########################################################################