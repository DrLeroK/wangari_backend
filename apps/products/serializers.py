from rest_framework import serializers
from django.contrib.auth.models import User, Group
from .models import Category, Product, Review, Cart, CartItem, Order, OrderItem, ActivityLog
from django.utils import timezone
from decimal import Decimal



class UserSerializer(serializers.ModelSerializer):
    groups = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='name'
    )
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'groups']
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }


class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(source='products.count', read_only=True)
    
    class Meta:
        model = Category
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    average_rating = serializers.ReadOnlyField()
    review_count = serializers.ReadOnlyField()
    is_weight_based = serializers.ReadOnlyField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'pricing_type', 'available_weights',
            'stock_quantity', 'category', 'category_name', 'product_type', 'image', 
            'is_active', 'show', 'is_spicy', 'average_rating', 'review_count',
            'is_weight_based', 'created_at', 'updated_at'
        ]


class ProductListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    average_rating = serializers.ReadOnlyField()
    is_weight_based = serializers.ReadOnlyField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'pricing_type', 'available_weights',
            'category_name', 'product_type', 'image', 'stock_quantity', 'average_rating',
            'is_spicy', 'is_weight_based'
        ]


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = Review
        fields = [
            'id', 'product', 'product_name', 'user', 'user_name', 'user_email', 'rating',
            'comment', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'product', 'created_at', 'updated_at']
    
    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value
    

class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(source='product.price', read_only=True, max_digits=10, decimal_places=2)
    product_image = serializers.ImageField(source='product.image', read_only=True)
    product_pricing_type = serializers.CharField(source='product.pricing_type', read_only=True)
    product_is_weight_based = serializers.BooleanField(source='product.is_weight_based', read_only=True)
    product_available_weights = serializers.ListField(source='product.available_weights', read_only=True)
    total_price = serializers.ReadOnlyField()
    
    class Meta:
        model = CartItem
        fields = [
            'id', 'product', 'product_name', 'product_price', 'product_image',
            'quantity', 'weight_kg', 'special_instructions', 'total_price',
            'product_pricing_type', 'product_is_weight_based', 'product_available_weights',
            'created_at'
        ]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.ReadOnlyField()
    total_quantity = serializers.ReadOnlyField()
    
    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'total_price', 'total_quantity', 'created_at', 'updated_at']
        read_only_fields = ['user']


class AddToCartSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, default=1)
    weight_kg = serializers.DecimalField(
        max_digits=6, 
        decimal_places=3, 
        min_value=Decimal('0.001'),
        required=False,
        allow_null=True
    )
    special_instructions = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        product_id = attrs.get('product_id')
        weight_kg = attrs.get('weight_kg')
        
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found")
        
        # Validate weight for weight-based products
        if product.is_weight_based:
            if weight_kg is None:
                raise serializers.ValidationError({
                    'weight_kg': 'Weight is required for weight-based products'
                })
            
            # Validate against available weights
            if product.available_weights:
                if float(weight_kg) not in [float(w) for w in product.available_weights]:
                    raise serializers.ValidationError({
                        'weight_kg': f'Weight must be one of: {", ".join(map(str, product.available_weights))}kg'
                    })
        else:
            # For non-weight-based products, ensure no weight is provided
            if weight_kg is not None:
                raise serializers.ValidationError({
                    'weight_kg': 'Weight should not be provided for non-weight-based products'
                })
        
        return attrs


class UpdateCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['quantity', 'special_instructions']




class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_image = serializers.ImageField(source='product.image', read_only=True)
    product_pricing_type = serializers.CharField(source='product.pricing_type', read_only=True)
    product_is_weight_based = serializers.BooleanField(source='product.is_weight_based', read_only=True)
    product_price_per_kg = serializers.DecimalField(
        source='product.price', 
        read_only=True, 
        max_digits=10, 
        decimal_places=2,
        help_text="Base price per kg for weight-based products"
    )
    total_price = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'product_name', 'product_image', 'quantity', 
            'weight_kg', 'unit_price', 'special_instructions', 'total_price',
            'product_pricing_type', 'product_is_weight_based', 'product_price_per_kg'
        ]
        read_only_fields = ['unit_price']
    
    def get_total_price(self, obj):
        """Calculate total price correctly for both weight-based and fixed-price items"""
        if obj.product.is_weight_based and obj.weight_kg:
            # For weight-based: total = weight_kg × product.price (base price)
            return obj.weight_kg * obj.product.price
        else:
            # For fixed-price: total = quantity × unit_price
            return obj.quantity * obj.unit_price



class OrderItemCreateSerializer(serializers.Serializer):
    product = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
    weight_kg = serializers.DecimalField(
        max_digits=6, 
        decimal_places=3, 
        min_value=Decimal('0.001'),
        required=False,
        allow_null=True  # Add this
    )
    special_instructions = serializers.CharField(required=False, allow_blank=True, default='')
    
    def validate_product(self, value):
        try:
            product = Product.objects.get(id=value)
            return value
        except Product.DoesNotExist:
            raise serializers.ValidationError(f"Product with ID {value} does not exist.")
    
    def validate(self, attrs):
        product_id = attrs.get('product')
        weight_kg = attrs.get('weight_kg')
        
        # print(f" DEBUG OrderItemCreateSerializer.validate()")
        # print(f"   product_id: {product_id}, weight_kg: {weight_kg}, type: {type(weight_kg)}")
        
        try:
            product = Product.objects.get(id=product_id)
            # print(f"  Product found: {product.name}")
            # print(f"  Product is_weight_based: {product.is_weight_based}")
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found")
        
        # Validate weight for weight-based products
        if product.is_weight_based:
            print(f"  Checking weight for weight-based product")
            if weight_kg is None:
                # print(f"  Weight is None for weight-based product")
                raise serializers.ValidationError({
                    'weight_kg': 'Weight is required for weight-based products'
                })
            else:
                print(f"  Weight provided: {weight_kg}")
        else:
            # print(f"   Checking weight for NON-weight-based product")
            if weight_kg is not None:
                # print(f"   Weight should be None but got: {weight_kg}")
                raise serializers.ValidationError({
                    'weight_kg': 'Weight should not be provided for non-weight-based products'
                })
            else:
                print(f"  No weight for non-weight-based product (correct)")
        
        # print(f"  Validation passed")
        return attrs


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    final_total = serializers.ReadOnlyField()
    worker_name = serializers.CharField(source='user.get_full_name', read_only=True)
    worker_email = serializers.CharField(source='user.email', read_only=True)
    verified_by_name = serializers.CharField(source='payment_verified_by.get_full_name', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'user', 'customer_name', 'customer_phone', 'customer_email',
            'order_type', 'fulfillment_method', 'status', 'total_amount', 
            'delivery_fee', 'final_total', 'delivery_address', 'notes', 
            'estimated_preparation_time', 'ready_at', 'items', 
            'pickup_time', 'delivery_time', 'payment_confirmation', 'payment_verified',
            'payment_verified_by', 'payment_verified_at', 'verified_by_name',
            'table_number', 'worker_name', 'worker_email',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['order_number', 'user', 'total_amount', 'delivery_fee', 
                          'payment_verified_by', 'payment_verified_at',
                          'created_at', 'updated_at']


class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemCreateSerializer(many=True, write_only=True, required=False)
    pickup_time = serializers.DateTimeField(required=False, allow_null=True)
    delivery_time = serializers.DateTimeField(required=False, allow_null=True)
    payment_confirmation = serializers.ImageField(required=False, allow_null=True)
    table_number = serializers.CharField(required=False, allow_blank=True, max_length=20)
    
    class Meta:
        model = Order
        fields = [
            'customer_name', 'customer_phone', 'customer_email',
            'order_type', 'fulfillment_method', 'delivery_address', 'notes',
            'pickup_time', 'delivery_time', 'payment_confirmation',
            'table_number', 'items'
        ]
    
    def validate(self, data):
        # ... (keep your existing validation logic) ...
        return data
    
    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        request = self.context.get('request')
        
        if not items_data and request:
            items_data = request.data.get('items', [])
        
        if not items_data:
            raise serializers.ValidationError({
                'items': 'At least one item is required to create an order.'
            })
        
        # Set user if authenticated
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
        
        # For physical sales (offline orders), auto-generate customer info from worker
        if validated_data.get('order_type') == 'offline' and request and request.user.is_authenticated:
            table_number = validated_data.get('table_number', 'N/A')
            worker_name = request.user.get_full_name() or request.user.email
            
            # Auto-generate customer information
            if not validated_data.get('customer_name'):
                validated_data['customer_name'] = f"Table {table_number} - {worker_name}"
            if not validated_data.get('customer_email'):
                validated_data['customer_email'] = request.user.email
            if not validated_data.get('customer_phone'):
                validated_data['customer_phone'] = 'N/A'
        
        # Create order
        order = Order.objects.create(**validated_data)
        total_amount = 0
        
        for item_data in items_data:
            product_id = item_data.get('product')
            quantity = item_data.get('quantity')
            weight_kg = item_data.get('weight_kg')
            
            if not product_id or not quantity:
                continue
                
            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                continue
            
            # FIXED: Check stock for BOTH product types
            if product.is_weight_based and weight_kg:
                # For weight-based products: check weight availability
                if product.stock_quantity < weight_kg:
                    raise serializers.ValidationError({
                        'error': f'Insufficient stock for {product.name}. Available: {product.stock_quantity}kg, Requested: {weight_kg}kg'
                    })
            else:
                # For fixed-price products: check quantity availability
                if product.stock_quantity < quantity:
                    raise serializers.ValidationError({
                        'error': f'Insufficient stock for {product.name}. Available: {product.stock_quantity}'
                    })
            
            # FIXED: Store the base product price in unit_price, not the calculated price
            if product.is_weight_based and weight_kg:
                # For weight-based: unit_price = product.price (base price per kg)
                unit_price = product.price
                # For weight-based: total_price = weight_kg × unit_price
                total_price = weight_kg * unit_price
            else:
                # For fixed-price: unit_price = product.price
                unit_price = product.price
                # For fixed-price: total_price = quantity × unit_price
                total_price = unit_price * quantity
            
            # Create order item
            order_item = OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                weight_kg=weight_kg,
                unit_price=unit_price,  # Now storing base price
                special_instructions=item_data.get('special_instructions', '')
            )
            
            # FIXED: Update product stock for BOTH product types
            if product.is_weight_based and weight_kg:
                # For weight-based: subtract the weight from stock
                product.stock_quantity -= weight_kg
            else:
                # For fixed-price: subtract the quantity from stock
                product.stock_quantity -= quantity
            
            product.save()
            
            total_amount += total_price
        
        # Handle file upload for payment confirmation
        payment_confirmation = validated_data.get('payment_confirmation')
        if payment_confirmation:
            order.payment_confirmation = payment_confirmation
        
        # Update order total
        order.total_amount = total_amount
        
        # Auto-verify payment for physical sales
        if validated_data.get('order_type') == 'offline':
            order.payment_verified = False
        
        order.save()
        
        return order

class StockUpdateSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)
    action = serializers.ChoiceField(choices=['add', 'reduce'])
    reason = serializers.CharField(max_length=200, required=False)


class ActivityLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = ActivityLog
        fields = [
            'id', 'user', 'user_name', 'user_email', 'action', 'action_display',
            'model_name', 'object_id', 'description', 'old_value',
            'new_value', 'ip_address', 'timestamp'
        ]

##################################################################
