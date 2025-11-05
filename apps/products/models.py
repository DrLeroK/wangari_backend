from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import json

User = get_user_model()

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Product(models.Model):
    FOOD = 'food'
    DRINK = 'drink'
    DESSERT = 'dessert'
    PRODUCT_TYPE_CHOICES = [
        (FOOD, 'Food'),
        (DRINK, 'Drink'),
        (DESSERT, 'Dessert'),
    ]
    
    PRICING_TYPE_CHOICES = [
        ('fixed', 'Fixed Price'),
        ('per_kg', 'Per Kilogram'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Price per kg for food items, fixed price for drinks/desserts"
    )
    
    # New fields for weight-based pricing
    pricing_type = models.CharField(
        max_length=10,
        choices=PRICING_TYPE_CHOICES,
        default='fixed',
        help_text="Whether price is per kg or fixed"
    )
    
    available_weights = models.JSONField(
        default=list,
        blank=True,
        help_text="Available weight increments in kg (e.g., [0.25, 0.5, 0.75, 1.0])"
    )
    
    stock_quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    product_type = models.CharField(max_length=10, choices=PRODUCT_TYPE_CHOICES, default=FOOD)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    show = models.BooleanField(default=True)
    is_spicy = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    @property
    def is_weight_based(self):
        """Check if product uses weight-based pricing"""
        return self.pricing_type == 'per_kg' and self.product_type == self.FOOD
    
    def calculate_price(self, quantity=1, weight_kg=None):
        """Calculate price based on quantity and weight"""
        if self.is_weight_based and weight_kg is not None:
            return self.price * Decimal(str(weight_kg))
        else:
            return self.price * quantity
    
    def save(self, *args, **kwargs):
        # Set default available weights for food items with per_kg pricing
        if self.is_weight_based and not self.available_weights:
            self.available_weights = [0.25, 0.5, 0.75, 1.0, 1.5, 2.0]
        super().save(*args, **kwargs)
    
    @property
    def average_rating(self):
        reviews = self.reviews.filter(is_active=True)
        if reviews.exists():
            return round(sum(review.rating for review in reviews) / reviews.count(), 1)
        return 0
    
    @property
    def review_count(self):
        return self.reviews.filter(is_active=True).count()
    
    class Meta:
        ordering = ['-created_at']


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['product', 'user']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.product.name} - {self.rating}"


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())
    
    @property
    def total_quantity(self):
        return sum(item.quantity for item in self.items.all())
    
    def __str__(self):
        return f"Cart - {self.user.email}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    
    # Weight field for weight-based products
    weight_kg = models.DecimalField(
        max_digits=6, 
        decimal_places=3,  # Allows up to 999.999 kg with 3 decimal precision
        null=True, 
        blank=True,
        validators=[MinValueValidator(Decimal('0.001'))],  # Minimum 1 gram
        help_text="Weight in kg for weight-based products"
    )
    
    special_instructions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def total_price(self):
        """Calculate total price considering weight for weight-based products"""
        if self.product.is_weight_based and self.weight_kg:
            return self.weight_kg * self.product.price
        else:
            return self.quantity * self.product.price
    
    class Meta:
        unique_together = ['cart', 'product', 'weight_kg']
    
    def __str__(self):
        if self.product.is_weight_based and self.weight_kg:
            return f"{self.weight_kg}kg x {self.product.name}"
        else:
            return f"{self.quantity} x {self.product.name}"


class Order(models.Model):
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    PREPARING = 'preparing'
    READY = 'ready'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'
    
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (CONFIRMED, 'Confirmed'),
        (PREPARING, 'Preparing'),
        (READY, 'Ready'),
        (COMPLETED, 'Completed'),
        (CANCELLED, 'Cancelled'),
    ]
    
    ONLINE = 'online'
    OFFLINE = 'offline'
    
    ORDER_TYPE_CHOICES = [
        (ONLINE, 'Online'),
        (OFFLINE, 'Offline'),
    ]
    
    PICKUP = 'pickup'
    DELIVERY = 'delivery'
    
    FULFILLMENT_CHOICES = [
        (PICKUP, 'Pick Up'),
        (DELIVERY, 'Delivery'),
    ]
    
    order_number = models.CharField(max_length=20, unique=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    customer_name = models.CharField(max_length=200)
    customer_phone = models.CharField(max_length=15)
    customer_email = models.EmailField()
    order_type = models.CharField(max_length=10, choices=ORDER_TYPE_CHOICES, default=ONLINE)
    fulfillment_method = models.CharField(max_length=10, choices=FULFILLMENT_CHOICES, default=PICKUP)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_address = models.TextField(blank=True)

    # added fields for payment confirmation and scheduling
    pickup_time = models.DateTimeField(null=True, blank=True, help_text="Scheduled pickup time")
    delivery_time = models.DateTimeField(null=True, blank=True, help_text="Scheduled delivery time")
    payment_confirmation = models.ImageField(
        upload_to='payment_confirmations/', 
        null=True, 
        blank=True,
        help_text="Screenshot of payment confirmation"
    )
    payment_verified = models.BooleanField(default=False, help_text="Whether payment has been verified by admin")
    payment_verified_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='verified_payments',
        help_text="Staff member who verified the payment"
    )
    payment_verified_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When payment was verified"
    )

    table_number = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        help_text="Table number for physical sales"
    )

    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=60)
    notes = models.TextField(blank=True)
    estimated_preparation_time = models.IntegerField(default=50, help_text="Estimated preparation time in minutes")
    ready_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Order {self.order_number}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        
        # Calculate delivery fee
        if self.fulfillment_method == self.DELIVERY:
            self.delivery_fee = Decimal('59.99')  # Fixed delivery fee
        else:
            self.delivery_fee = Decimal('0.00')
            
        super().save(*args, **kwargs)
    
    def generate_order_number(self):
        return f"ORD{timezone.now().strftime('%Y%m%d%H%M%S')}{self.id or ''}"
    
    @property
    def final_total(self):
        return self.total_amount + self.delivery_fee
    
    class Meta:
        ordering = ['-created_at']


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    
    # Weight field for weight-based products
    weight_kg = models.DecimalField(
        max_digits=6, 
        decimal_places=3,
        null=True, 
        blank=True,
        validators=[MinValueValidator(Decimal('0.001'))],
        help_text="Weight in kg for weight-based products"
    )
    
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    special_instructions = models.TextField(blank=True)
    
    def __str__(self):
        if self.product.is_weight_based and self.weight_kg:
            return f"{self.weight_kg}kg x {self.product.name}"
        else:
            return f"{self.quantity} x {self.product.name}"
    
    @property
    def total_price(self):
        """Calculate total price considering weight"""
        if self.product.is_weight_based and self.weight_kg:
            return self.weight_kg * self.unit_price
        else:
            return self.quantity * self.unit_price


class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('stock_add', 'Stock Add'),
        ('stock_reduce', 'Stock Reduce'),
        ('order_status', 'Order Status Change'),
        ('physical_sale', 'Physical Sale'),
        ('user_login', 'User Login'),
        ('user_logout', 'User Logout'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100, blank=True)
    description = models.TextField()
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        user_info = self.user.email if self.user else 'System'
        return f"{user_info} - {self.action} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
    
    class Meta:
        ordering = ['-timestamp']
