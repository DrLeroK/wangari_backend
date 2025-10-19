from rest_framework import serializers
from django.contrib.auth.models import User, Group
from .models import Category, Product, Review, Cart, CartItem, Order, OrderItem, ActivityLog



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
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'stock_quantity', 
            'category', 'category_name', 'product_type', 'image', 
            'is_active', 'show', 'is_spicy', 'average_rating', 'review_count',
            'created_at', 'updated_at'
        ]


class ProductListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    average_rating = serializers.ReadOnlyField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'category_name',
            'product_type', 'image', 'stock_quantity', 'average_rating',
            'is_spicy'
        ]



class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = Review
        fields = [
            'id', 'product', 'user', 'user_name', 'user_email', 'rating',
            'comment', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'product', 'created_at', 'updated_at']  # Make product read-only
    
    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value
    
    # Remove the create method since we're handling it in the view
    


# class ReviewSerializer(serializers.ModelSerializer):
#     user_name = serializers.CharField(source='user.get_full_name', read_only=True)
#     user_email = serializers.CharField(source='user.email', read_only=True)
    
#     class Meta:
#         model = Review
#         fields = [
#             'id', 'product', 'user', 'user_name', 'user_email', 'rating',
#             'comment', 'is_active', 'created_at', 'updated_at'
#         ]
#         read_only_fields = ['user', 'created_at', 'updated_at']
    
#     def validate_rating(self, value):
#         if value < 1 or value > 5:
#             raise serializers.ValidationError("Rating must be between 1 and 5.")
#         return value
    
#     def create(self, validated_data):
#         validated_data['user'] = self.context['request'].user
#         return super().create(validated_data)


class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(source='product.price', read_only=True, max_digits=10, decimal_places=2)
    product_image = serializers.ImageField(source='product.image', read_only=True)
    total_price = serializers.ReadOnlyField()
    
    class Meta:
        model = CartItem
        fields = [
            'id', 'product', 'product_name', 'product_price', 'product_image',
            'quantity', 'special_instructions', 'total_price', 'created_at'
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
    special_instructions = serializers.CharField(required=False, allow_blank=True)


class UpdateCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['quantity', 'special_instructions']


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_image = serializers.ImageField(source='product.image', read_only=True)
    total_price = serializers.ReadOnlyField()
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'product_name', 'product_image', 'quantity', 
            'unit_price', 'special_instructions', 'total_price'
        ]
        read_only_fields = ['unit_price']



class OrderItemCreateSerializer(serializers.Serializer):
    product = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
    special_instructions = serializers.CharField(required=False, allow_blank=True, default='')
    
    def validate_product(self, value):
        # Ensure product exists
        try:
            product = Product.objects.get(id=value)
            return value
        except Product.DoesNotExist:
            raise serializers.ValidationError(f"Product with ID {value} does not exist.")


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    final_total = serializers.ReadOnlyField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'user', 'customer_name', 'customer_phone', 'customer_email',
            'order_type', 'fulfillment_method', 'status', 'total_amount', 
            'delivery_fee', 'final_total', 'delivery_address', 'notes', 
            'estimated_preparation_time', 'ready_at', 'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['order_number', 'user', 'total_amount', 'delivery_fee', 'created_at', 'updated_at']



# class OrderCreateSerializer(serializers.ModelSerializer):
#     # Remove the items field from serializer and handle it manually
#     class Meta:
#         model = Order
#         fields = [
#             'customer_name', 'customer_phone', 'customer_email',
#             'order_type', 'fulfillment_method', 'delivery_address', 'notes'
#         ]
    
#     def create(self, validated_data):
#         # Get items from request data directly
#         request = self.context.get('request')
#         items_data = request.data.get('items', [])
        
#         if not items_data:
#             raise serializers.ValidationError({
#                 'items': 'At least one item is required to create an order.'
#             })
        
#         # Set user if authenticated
#         if request and request.user.is_authenticated:
#             validated_data['user'] = request.user
        
#         # Create order
#         order = Order.objects.create(**validated_data)
#         total_amount = 0
        
#         for item_data in items_data:
#             product_id = item_data.get('product')
#             quantity = item_data.get('quantity')
            
#             if not product_id or not quantity:
#                 continue
                
#             try:
#                 product = Product.objects.get(id=product_id)
#             except Product.DoesNotExist:
#                 continue
            
#             # Check stock
#             if product.stock_quantity < quantity:
#                 raise serializers.ValidationError({
#                     'error': f'Insufficient stock for {product.name}'
#                 })
            
#             # Create order item
#             OrderItem.objects.create(
#                 order=order,
#                 product=product,
#                 quantity=quantity,
#                 unit_price=product.price,
#                 special_instructions=item_data.get('special_instructions', '')
#             )
            
#             # Update product stock
#             product.stock_quantity -= quantity
#             product.save()
            
#             total_amount += quantity * product.price
        
#         # Update order total
#         order.total_amount = total_amount
#         order.save()
        
#         return order


class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemCreateSerializer(many=True, write_only=True, required=False)
    
    class Meta:
        model = Order
        fields = [
            'customer_name', 'customer_phone', 'customer_email',
            'order_type', 'fulfillment_method', 'delivery_address', 'notes',
            'items'  # Include items field for write operations
        ]
    
    def create(self, validated_data):
        # Get items from validated data or request data
        items_data = validated_data.pop('items', [])
        request = self.context.get('request')
        
        if not items_data and request:
            # Fallback to request data if items not in validated_data
            items_data = request.data.get('items', [])
        
        if not items_data:
            raise serializers.ValidationError({
                'items': 'At least one item is required to create an order.'
            })
        
        # Set user if authenticated
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
        
        # Create order
        order = Order.objects.create(**validated_data)
        total_amount = 0
        
        for item_data in items_data:
            product_id = item_data.get('product')
            quantity = item_data.get('quantity')
            
            if not product_id or not quantity:
                continue
                
            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                continue
            
            # Check stock
            if product.stock_quantity < quantity:
                raise serializers.ValidationError({
                    'error': f'Insufficient stock for {product.name}'
                })
            
            # Create order item
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                unit_price=product.price,
                special_instructions=item_data.get('special_instructions', '')
            )
            
            # Update product stock
            product.stock_quantity -= quantity
            product.save()
            
            total_amount += quantity * product.price
        
        # Update order total
        order.total_amount = total_amount
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



























# from rest_framework import serializers
# from django.contrib.auth.models import User, Group
# from .models import Category, Product, Review, Cart, CartItem, Order, OrderItem, ActivityLog

# class UserSerializer(serializers.ModelSerializer):
#     groups = serializers.SlugRelatedField(
#         many=True,
#         read_only=True,
#         slug_field='name'
#     )
    
#     class Meta:
#         model = User
#         fields = ['id', 'email', 'first_name', 'last_name', 'groups']
#         extra_kwargs = {
#             'email': {'required': True},
#             'first_name': {'required': True},
#             'last_name': {'required': True},
#         }

# class CategorySerializer(serializers.ModelSerializer):
#     product_count = serializers.IntegerField(source='products.count', read_only=True)
    
#     class Meta:
#         model = Category
#         fields = '__all__'

# class ProductSerializer(serializers.ModelSerializer):
#     category_name = serializers.CharField(source='category.name', read_only=True)
#     average_rating = serializers.ReadOnlyField()
#     review_count = serializers.ReadOnlyField()
    
#     class Meta:
#         model = Product
#         fields = [
#             'id', 'name', 'description', 'price', 'stock_quantity', 
#             'category', 'category_name', 'product_type', 'image', 
#             'is_active', 'show', 'is_spicy', 'average_rating', 'review_count',
#             'created_at', 'updated_at'
#         ]

# class ProductListSerializer(serializers.ModelSerializer):
#     category_name = serializers.CharField(source='category.name', read_only=True)
#     average_rating = serializers.ReadOnlyField()
    
#     class Meta:
#         model = Product
#         fields = [
#             'id', 'name', 'description', 'price', 'category_name',
#             'product_type', 'image', 'stock_quantity', 'average_rating',
#             'is_spicy'
#         ]

# class ReviewSerializer(serializers.ModelSerializer):
#     user_name = serializers.CharField(source='user.get_full_name', read_only=True)
#     user_email = serializers.CharField(source='user.email', read_only=True)
    
#     class Meta:
#         model = Review
#         fields = [
#             'id', 'product', 'user', 'user_name', 'user_email', 'rating',
#             'comment', 'is_active', 'created_at', 'updated_at'
#         ]
#         read_only_fields = ['user', 'created_at', 'updated_at']
    
#     def validate_rating(self, value):
#         if value < 1 or value > 5:
#             raise serializers.ValidationError("Rating must be between 1 and 5.")
#         return value
    
#     def create(self, validated_data):
#         validated_data['user'] = self.context['request'].user
#         return super().create(validated_data)

# class CartItemSerializer(serializers.ModelSerializer):
#     product_name = serializers.CharField(source='product.name', read_only=True)
#     product_price = serializers.DecimalField(source='product.price', read_only=True, max_digits=10, decimal_places=2)
#     product_image = serializers.ImageField(source='product.image', read_only=True)
#     total_price = serializers.ReadOnlyField()
    
#     class Meta:
#         model = CartItem
#         fields = [
#             'id', 'product', 'product_name', 'product_price', 'product_image',
#             'quantity', 'special_instructions', 'total_price', 'created_at'
#         ]

# class CartSerializer(serializers.ModelSerializer):
#     items = CartItemSerializer(many=True, read_only=True)
#     total_price = serializers.ReadOnlyField()
#     total_quantity = serializers.ReadOnlyField()
    
#     class Meta:
#         model = Cart
#         fields = ['id', 'user', 'items', 'total_price', 'total_quantity', 'created_at', 'updated_at']
#         read_only_fields = ['user']

# class AddToCartSerializer(serializers.Serializer):
#     product_id = serializers.IntegerField()
#     quantity = serializers.IntegerField(min_value=1, default=1)
#     special_instructions = serializers.CharField(required=False, allow_blank=True)

# class UpdateCartItemSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = CartItem
#         fields = ['quantity', 'special_instructions']

# class OrderItemSerializer(serializers.ModelSerializer):
#     product_name = serializers.CharField(source='product.name', read_only=True)
#     product_image = serializers.ImageField(source='product.image', read_only=True)
#     total_price = serializers.ReadOnlyField()
    
#     class Meta:
#         model = OrderItem
#         fields = [
#             'id', 'product', 'product_name', 'product_image', 'quantity', 
#             'unit_price', 'special_instructions', 'total_price'
#         ]
#         read_only_fields = ['unit_price']

# # SIMPLE FIX: Use a basic serializer for order creation

# # class OrderItemCreateSerializer(serializers.Serializer):
# #     product = serializers.IntegerField()
# #     quantity = serializers.IntegerField(min_value=1)
# #     special_instructions = serializers.CharField(required=False, allow_blank=True)

# class OrderItemCreateSerializer(serializers.Serializer):
#     product = serializers.IntegerField()
#     quantity = serializers.IntegerField(min_value=1)
#     special_instructions = serializers.CharField(required=False, allow_blank=True, default='')
    
#     def validate_product(self, value):
#         # Ensure product exists
#         try:
#             product = Product.objects.get(id=value)
#             return value
#         except Product.DoesNotExist:
#             raise serializers.ValidationError(f"Product with ID {value} does not exist.")


# class OrderSerializer(serializers.ModelSerializer):
#     items = OrderItemSerializer(many=True, read_only=True)
#     final_total = serializers.ReadOnlyField()
    
#     class Meta:
#         model = Order
#         fields = [
#             'id', 'order_number', 'user', 'customer_name', 'customer_phone', 'customer_email',
#             'order_type', 'fulfillment_method', 'status', 'total_amount', 
#             'delivery_fee', 'final_total', 'delivery_address', 'notes', 
#             'estimated_preparation_time', 'ready_at', 'items', 'created_at', 'updated_at'
#         ]
#         read_only_fields = ['order_number', 'user', 'total_amount', 'delivery_fee', 'created_at', 'updated_at']




# # class OrderCreateSerializer(serializers.ModelSerializer):
# #     items = OrderItemCreateSerializer(many=True)
    
# #     class Meta:
# #         model = Order
# #         fields = [
# #             'customer_name', 'customer_phone', 'customer_email',
# #             'order_type', 'fulfillment_method', 'delivery_address', 'notes', 'items'
# #         ]
    
# #     def validate(self, data):
# #         # Validate delivery address for delivery orders
# #         if data.get('fulfillment_method') == Order.DELIVERY and not data.get('delivery_address'):
# #             raise serializers.ValidationError({
# #                 'delivery_address': 'Delivery address is required for delivery orders.'
# #             })
        
# #         # Validate items
# #         if not data.get('items'):
# #             raise serializers.ValidationError({
# #                 'items': 'At least one item is required to create an order.'
# #             })
        
# #         return data
    
# #     def create(self, validated_data):
# #         items_data = validated_data.pop('items')
# #         request = self.context.get('request')
        
# #         # Set user if authenticated
# #         if request and request.user.is_authenticated:
# #             validated_data['user'] = request.user
        
# #         # Create order first
# #         order = Order.objects.create(**validated_data)
# #         total_amount = 0
        
# #         for item_data in items_data:
# #             # Get product by ID
# #             product_id = item_data['product']
# #             try:
# #                 product = Product.objects.get(id=product_id)
# #             except Product.DoesNotExist:
# #                 raise serializers.ValidationError({
# #                     'error': f'Product with ID {product_id} does not exist.'
# #                 })
            
# #             quantity = item_data['quantity']
# #             unit_price = product.price
            
# #             # Check stock availability
# #             if product.stock_quantity < quantity:
# #                 raise serializers.ValidationError({
# #                     'error': f'Insufficient stock for {product.name}. Available: {product.stock_quantity}, Requested: {quantity}'
# #                 })
            
# #             # Create order item
# #             OrderItem.objects.create(
# #                 order=order,
# #                 product=product,
# #                 quantity=quantity,
# #                 unit_price=unit_price,
# #                 special_instructions=item_data.get('special_instructions', '')
# #             )
            
# #             # Update product stock
# #             product.stock_quantity -= quantity
# #             product.save()
            
# #             total_amount += quantity * unit_price
        
# #         # Update order total
# #         order.total_amount = total_amount
# #         order.save()
        
# #         return order





# # class OrderCreateSerializer(serializers.ModelSerializer):
# #     items = OrderItemCreateSerializer(many=True)
    
# #     class Meta:
# #         model = Order
# #         fields = [
# #             'customer_name', 'customer_phone', 'customer_email',
# #             'order_type', 'fulfillment_method', 'delivery_address', 'notes', 'items'
# #         ]
    
# #     def validate(self, data):
# #         # Validate delivery address for delivery orders
# #         if data.get('fulfillment_method') == Order.DELIVERY and not data.get('delivery_address'):
# #             raise serializers.ValidationError({
# #                 'delivery_address': 'Delivery address is required for delivery orders.'
# #             })
        
# #         # Validate items
# #         if not data.get('items'):
# #             raise serializers.ValidationError({
# #                 'items': 'At least one item is required to create an order.'
# #             })
        
# #         return data
    
# #     def create(self, validated_data):
# #         items_data = validated_data.pop('items')
# #         request = self.context.get('request')
        
# #         # Set user if authenticated
# #         if request and request.user.is_authenticated:
# #             validated_data['user'] = request.user
        
# #         order = Order.objects.create(**validated_data)
# #         total_amount = 0
        
# #         for item_data in items_data:
# #             # Get product by ID
# #             product_id = item_data['product']
# #             product = Product.objects.get(id=product_id)  # Already validated to exist
            
# #             quantity = item_data['quantity']
# #             unit_price = product.price
            
# #             # Check stock availability
# #             if product.stock_quantity < quantity:
# #                 raise serializers.ValidationError({
# #                     'error': f'Insufficient stock for {product.name}. Available: {product.stock_quantity}, Requested: {quantity}'
# #                 })
            
# #             # Create order item
# #             OrderItem.objects.create(
# #                 order=order,
# #                 product=product,
# #                 quantity=quantity,
# #                 unit_price=unit_price,
# #                 special_instructions=item_data.get('special_instructions', '')
# #             )
            
# #             # Update product stock
# #             product.stock_quantity -= quantity
# #             product.save()
            
# #             total_amount += quantity * unit_price
        
# #         order.total_amount = total_amount
# #         order.save()
        
# #         return order





# class OrderCreateSerializer(serializers.ModelSerializer):
#     # Remove the items field from serializer and handle it manually
#     class Meta:
#         model = Order
#         fields = [
#             'customer_name', 'customer_phone', 'customer_email',
#             'order_type', 'fulfillment_method', 'delivery_address', 'notes'
#         ]
    
#     def create(self, validated_data):
#         # Get items from request data directly
#         request = self.context.get('request')
#         items_data = request.data.get('items', [])
        
#         if not items_data:
#             raise serializers.ValidationError({
#                 'items': 'At least one item is required to create an order.'
#             })
        
#         # Set user if authenticated
#         if request and request.user.is_authenticated:
#             validated_data['user'] = request.user
        
#         # Create order
#         order = Order.objects.create(**validated_data)
#         total_amount = 0
        
#         for item_data in items_data:
#             product_id = item_data.get('product')
#             quantity = item_data.get('quantity')
            
#             if not product_id or not quantity:
#                 continue
                
#             try:
#                 product = Product.objects.get(id=product_id)
#             except Product.DoesNotExist:
#                 continue
            
#             # Check stock
#             if product.stock_quantity < quantity:
#                 raise serializers.ValidationError({
#                     'error': f'Insufficient stock for {product.name}'
#                 })
            
#             # Create order item
#             OrderItem.objects.create(
#                 order=order,
#                 product=product,
#                 quantity=quantity,
#                 unit_price=product.price,
#                 special_instructions=item_data.get('special_instructions', '')
#             )
            
#             # Update product stock
#             product.stock_quantity -= quantity
#             product.save()
            
#             total_amount += quantity * product.price
        
#         # Update order total
#         order.total_amount = total_amount
#         order.save()
        
#         return order





# class StockUpdateSerializer(serializers.Serializer):
#     quantity = serializers.IntegerField(min_value=1)
#     action = serializers.ChoiceField(choices=['add', 'reduce'])
#     reason = serializers.CharField(max_length=200, required=False)

# class ActivityLogSerializer(serializers.ModelSerializer):
#     user_name = serializers.CharField(source='user.get_full_name', read_only=True)
#     user_email = serializers.CharField(source='user.email', read_only=True)
#     action_display = serializers.CharField(source='get_action_display', read_only=True)
    
#     class Meta:
#         model = ActivityLog
#         fields = [
#             'id', 'user', 'user_name', 'user_email', 'action', 'action_display',
#             'model_name', 'object_id', 'description', 'old_value',
#             'new_value', 'ip_address', 'timestamp'
#         ]




























# from rest_framework import serializers
# from django.contrib.auth.models import User, Group
# from .models import Category, Product, Review, Cart, CartItem, Order, OrderItem, ActivityLog



# class UserSerializer(serializers.ModelSerializer):
#     groups = serializers.SlugRelatedField(
#         many=True,
#         read_only=True,
#         slug_field='name'
#     )
    
#     class Meta:
#         model = User
#         fields = ['id', 'email', 'first_name', 'last_name', 'groups']
#         extra_kwargs = {
#             'email': {'required': True},
#             'first_name': {'required': True},
#             'last_name': {'required': True},
#         }


# class CategorySerializer(serializers.ModelSerializer):
#     product_count = serializers.IntegerField(source='products.count', read_only=True)
    
#     class Meta:
#         model = Category
#         fields = '__all__'


# class ProductSerializer(serializers.ModelSerializer):
#     category_name = serializers.CharField(source='category.name', read_only=True)
#     average_rating = serializers.ReadOnlyField()
#     review_count = serializers.ReadOnlyField()
    
#     class Meta:
#         model = Product
#         fields = [
#             'id', 'name', 'description', 'price', 'stock_quantity', 
#             'category', 'category_name', 'product_type', 'image', 
#             'is_active', 'show',
#             'is_spicy', 'average_rating', 'review_count',
#             'created_at', 'updated_at'
#         ]


# class ProductListSerializer(serializers.ModelSerializer):
#     category_name = serializers.CharField(source='category.name', read_only=True)
#     average_rating = serializers.ReadOnlyField()
    
#     class Meta:
#         model = Product
#         fields = [
#             'id', 'name', 'description', 'price', 'category_name',
#             'product_type', 'image', 'stock_quantity', 'average_rating',
#             'is_spicy'
#         ]


# class ReviewSerializer(serializers.ModelSerializer):
#     user_name = serializers.CharField(source='user.get_full_name', read_only=True)
#     user_email = serializers.CharField(source='user.email', read_only=True)
    
#     class Meta:
#         model = Review
#         fields = [
#             'id', 'product', 'user', 'user_name', 'user_email', 'rating',
#             'comment', 'is_active', 'created_at', 'updated_at'
#         ]
#         read_only_fields = ['user', 'created_at', 'updated_at']
    
#     def validate_rating(self, value):
#         if value < 1 or value > 5:
#             raise serializers.ValidationError("Rating must be between 1 and 5.")
#         return value
    
#     def create(self, validated_data):
#         validated_data['user'] = self.context['request'].user
#         return super().create(validated_data)


# class CartItemSerializer(serializers.ModelSerializer):
#     product_name = serializers.CharField(source='product.name', read_only=True)
#     product_price = serializers.DecimalField(source='product.price', read_only=True, max_digits=10, decimal_places=2)
#     product_image = serializers.ImageField(source='product.image', read_only=True)
#     total_price = serializers.ReadOnlyField()
    
#     class Meta:
#         model = CartItem
#         fields = [
#             'id', 'product', 'product_name', 'product_price', 'product_image',
#             'quantity', 'special_instructions', 'total_price', 'created_at'
#         ]


# class CartSerializer(serializers.ModelSerializer):
#     items = CartItemSerializer(many=True, read_only=True)
#     total_price = serializers.ReadOnlyField()
#     total_quantity = serializers.ReadOnlyField()
    
#     class Meta:
#         model = Cart
#         fields = ['id', 'user', 'items', 'total_price', 'total_quantity', 'created_at', 'updated_at']
#         read_only_fields = ['user']


# class AddToCartSerializer(serializers.Serializer):
#     product_id = serializers.IntegerField()
#     quantity = serializers.IntegerField(min_value=1, default=1)
#     special_instructions = serializers.CharField(required=False, allow_blank=True)


# class UpdateCartItemSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = CartItem
#         fields = ['quantity', 'special_instructions']




# # class OrderItemSerializer(serializers.ModelSerializer):
# #     product_name = serializers.CharField(source='product.name', read_only=True)
# #     product_image = serializers.ImageField(source='product.image', read_only=True)
# #     total_price = serializers.ReadOnlyField()
    
# #     class Meta:
# #         model = OrderItem
# #         fields = ['id', 'product', 'product_name', 'product_image', 'quantity', 'unit_price', 'special_instructions', 'total_price']



# class OrderItemSerializer(serializers.ModelSerializer):
#     product_name = serializers.CharField(source='product.name', read_only=True)
#     product_image = serializers.ImageField(source='product.image', read_only=True)
#     total_price = serializers.ReadOnlyField()
    
#     class Meta:
#         model = OrderItem
#         fields = [
#             'id', 'product', 'product_name', 'product_image', 'quantity', 
#             'unit_price', 'special_instructions', 'total_price'
#         ]
#         extra_kwargs = {
#             'product': {'required': True},
#             'quantity': {'required': True},
#             'unit_price': {'read_only': True}  # This should be set automatically
#         }




# class OrderSerializer(serializers.ModelSerializer):
#     items = OrderItemSerializer(many=True, read_only=True)
#     # status_display = serializers.CharField(source='get_status_display', read_only=True)
#     # order_type_display = serializers.CharField(source='get_order_type_display', read_only=True)
#     # fulfillment_method_display = serializers.CharField(source='get_fulfillment_method_display', read_only=True)
#     final_total = serializers.ReadOnlyField()
    
#     class Meta:
#         model = Order

#         # fields = [
#         #     'id', 'order_number', 'user', 'customer_name', 'customer_phone', 'customer_email',
#         #     'order_type', 'order_type_display', 'fulfillment_method', 'fulfillment_method_display',
#         #     'status', 'status_display', 'total_amount', 'delivery_fee', 'final_total',
#         #     'delivery_address', 'notes', 'estimated_preparation_time', 'ready_at',
#         #     'items', 'created_at', 'updated_at'
#         # ]

#         fields = [
#             'id', 'order_number', 'user', 'customer_name', 'customer_phone', 'customer_email',
#             'order_type', 'fulfillment_method', 'status', 'total_amount', 
#             'delivery_fee', 'final_total', 'delivery_address', 'notes', 
#             'estimated_preparation_time', 'ready_at', 'items', 'created_at', 'updated_at'
#         ]

#         read_only_fields = ['order_number', 'user', 'total_amount', 'delivery_fee', 'created_at', 'updated_at']



# # class OrderCreateSerializer(serializers.ModelSerializer):
# #     items = OrderItemSerializer(many=True)
    
# #     class Meta:
# #         model = Order
# #         fields = [
# #             'customer_name', 'customer_phone', 'customer_email',
# #             'order_type', 'fulfillment_method', 'delivery_address', 'notes', 'items'
# #         ]
    
# #     def validate(self, data):
# #         # Validate delivery address for delivery orders
# #         if data.get('fulfillment_method') == Order.DELIVERY and not data.get('delivery_address'):
# #             raise serializers.ValidationError({
# #                 'delivery_address': 'Delivery address is required for delivery orders.'
# #             })
        
# #         # Validate items
# #         if not data.get('items'):
# #             raise serializers.ValidationError({
# #                 'items': 'At least one item is required to create an order.'
# #             })
        
# #         return data
    
# #     def create(self, validated_data):
# #         items_data = validated_data.pop('items')
# #         request = self.context.get('request')
        
# #         # Set user if authenticated
# #         if request and request.user.is_authenticated:
# #             validated_data['user'] = request.user
        
# #         order = Order.objects.create(**validated_data)
# #         total_amount = 0
# #         max_preparation_time = 0
        
# #         for item_data in items_data:
# #             product = item_data['product']
# #             quantity = item_data['quantity']
# #             unit_price = product.price
            
# #             # Check stock availability
# #             if product.stock_quantity < quantity:
# #                 raise serializers.ValidationError({
# #                     'error': f'Insufficient stock for {product.name}. Available: {product.stock_quantity}, Requested: {quantity}'
# #                 })
            
# #             # Create order item
# #             OrderItem.objects.create(
# #                 order=order,
# #                 product=product,
# #                 quantity=quantity,
# #                 unit_price=unit_price,
# #                 special_instructions=item_data.get('special_instructions', '')
# #             )
            
# #             # Update product stock
# #             product.stock_quantity -= quantity
# #             product.save()
            
# #             total_amount += quantity * unit_price
            
# #             # Track maximum preparation time
# #             # if product.preparation_time > max_preparation_time:
# #             #     max_preparation_time = product.preparation_time
        
# #         order.total_amount = total_amount
# #         # order.estimated_preparation_time = max_preparation_time
# #         order.save()
        
# #         # Log activity
# #         user = request.user if request and request.user.is_authenticated else None
# #         self.log_order_activity(user, order, items_data)
        
# #         return order
    
# #     def log_order_activity(self, user, order, items_data):
# #         from .models import ActivityLog
        
# #         action = 'physical_sale' if order.order_type == Order.OFFLINE else 'create'
# #         description = f"{order.order_type.title()} order created: {order.order_number}"
        
# #         ActivityLog.objects.create(
# #             user=user,
# #             action=action,
# #             model_name='Order',
# #             object_id=str(order.id),
# #             description=description,
# #             new_value=f"Total: ${order.total_amount}, Items: {len(items_data)}, Method: {order.fulfillment_method}"
# #         )



# class OrderItemCreateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = OrderItem
#         fields = ['product', 'quantity', 'special_instructions']
#         extra_kwargs = {
#             'product': {'required': True},
#             'quantity': {'required': True},
#         }

# class OrderCreateSerializer(serializers.ModelSerializer):
#     items = OrderItemCreateSerializer(many=True)
    
#     class Meta:
#         model = Order
#         fields = [
#             'customer_name', 'customer_phone', 'customer_email',
#             'order_type', 'fulfillment_method', 'delivery_address', 'notes', 'items'
#         ]
    
#     def validate(self, data):
#         # Validate delivery address for delivery orders
#         if data.get('fulfillment_method') == Order.DELIVERY and not data.get('delivery_address'):
#             raise serializers.ValidationError({
#                 'delivery_address': 'Delivery address is required for delivery orders.'
#             })
        
#         # Validate items
#         if not data.get('items'):
#             raise serializers.ValidationError({
#                 'items': 'At least one item is required to create an order.'
#             })
        
#         return data
    
#     def create(self, validated_data):
#         items_data = validated_data.pop('items')
#         request = self.context.get('request')
        
#         # Set user if authenticated
#         if request and request.user.is_authenticated:
#             validated_data['user'] = request.user
        
#         order = Order.objects.create(**validated_data)
#         total_amount = 0
        
#         for item_data in items_data:
#             # Get product by ID - this is now just the ID, not the object
#             product_id = item_data['product']
#             try:
#                 product = Product.objects.get(id=product_id)
#             except Product.DoesNotExist:
#                 raise serializers.ValidationError({
#                     'error': f'Product with ID {product_id} does not exist.'
#                 })
            
#             quantity = item_data['quantity']
#             unit_price = product.price
            
#             # Check stock availability
#             if product.stock_quantity < quantity:
#                 raise serializers.ValidationError({
#                     'error': f'Insufficient stock for {product.name}. Available: {product.stock_quantity}, Requested: {quantity}'
#                 })
            
#             # Create order item
#             OrderItem.objects.create(
#                 order=order,
#                 product=product,
#                 quantity=quantity,
#                 unit_price=unit_price,
#                 special_instructions=item_data.get('special_instructions', '')
#             )
            
#             # Update product stock
#             product.stock_quantity -= quantity
#             product.save()
            
#             total_amount += quantity * unit_price
        
#         order.total_amount = total_amount
#         order.save()
        
#         # Log activity
#         user = request.user if request and request.user.is_authenticated else None
#         self.log_order_activity(user, order, items_data)
        
#         return order
    
#     def log_order_activity(self, user, order, items_data):
#         from .models import ActivityLog
        
#         action = 'physical_sale' if order.order_type == Order.OFFLINE else 'create'
#         description = f"{order.order_type.title()} order created: {order.order_number}"
        
#         ActivityLog.objects.create(
#             user=user,
#             action=action,
#             model_name='Order',
#             object_id=str(order.id),
#             description=description,
#             new_value=f"Total: ${order.total_amount}, Items: {len(items_data)}, Method: {order.fulfillment_method}"
#         )

    




# class StockUpdateSerializer(serializers.Serializer):
#     quantity = serializers.IntegerField(min_value=1)
#     action = serializers.ChoiceField(choices=['add', 'reduce'])
#     reason = serializers.CharField(max_length=200, required=False)


# class ActivityLogSerializer(serializers.ModelSerializer):
#     user_name = serializers.CharField(source='user.get_full_name', read_only=True)
#     user_email = serializers.CharField(source='user.email', read_only=True)
#     action_display = serializers.CharField(source='get_action_display', read_only=True)
    
#     class Meta:
#         model = ActivityLog
#         fields = [
#             'id', 'user', 'user_name', 'user_email', 'action', 'action_display',
#             'model_name', 'object_id', 'description', 'old_value',
#             'new_value', 'ip_address', 'timestamp'
#         ]