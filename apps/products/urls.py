from django.urls import path
from . import views

urlpatterns = [
    # Public routes (No authentication required)
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('products/', views.ProductListView.as_view(), name='product-list'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),
    path('products/<int:pk>/reviews/', views.ProductReviewsView.as_view(), name='product-reviews'),
    
    # Cart routes (Authenticated customers only)
    path('cart/', views.CartView.as_view(), name='cart-detail'),
    path('cart/add/', views.AddToCartView.as_view(), name='add-to-cart'),
    path('cart/items/<int:pk>/', views.UpdateCartItemView.as_view(), name='update-cart-item'),
    path('cart/items/<int:pk>/remove/', views.RemoveFromCartView.as_view(), name='remove-cart-item'),
    path('cart/clear/', views.ClearCartView.as_view(), name='clear-cart'),
    
    # Order routes
    path('orders/create/', views.CreateOrderView.as_view(), name='create-order'),
    path('orders/my-orders/', views.UserOrderListView.as_view(), name='user-orders'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order-detail'),
    
    # Review routes
    path('reviews/product/<int:pk>/create/', views.CreateReviewView.as_view(), name='create-review'),
    
    # Admin routes (Owner and Worker permissions)
    path('admin/categories/', views.AdminCategoryListCreateView.as_view(), name='admin-category-list'),
    path('admin/categories/<int:pk>/', views.AdminCategoryDetailView.as_view(), name='admin-category-detail'),
    path('admin/products/', views.AdminProductListCreateView.as_view(), name='admin-product-list'),
    path('admin/products/<int:pk>/', views.AdminProductDetailView.as_view(), name='admin-product-detail'),
    path('admin/products/<int:pk>/update-stock/', views.UpdateProductStockView.as_view(), name='update-product-stock'),
    path('admin/orders/', views.AdminOrderListView.as_view(), name='admin-order-list'),
    path('admin/orders/<int:pk>/', views.AdminOrderDetailView.as_view(), name='admin-order-detail'),
    path('admin/physical-sale/', views.CreatePhysicalSaleView.as_view(), name='create-physical-sale'),
    path('admin/activity-logs/', views.ActivityLogListView.as_view(), name='activity-logs'),
    path('admin/reviews/', views.ReviewManagementView.as_view(), name='review-management'),
    path('admin/reviews/<int:pk>/toggle/', views.ToggleReviewStatusView.as_view(), name='toggle-review-status'),
    
    # Additional admin management routes
    path('admin/low-stock-products/', views.LowStockProductsView.as_view(), name='low-stock-products'),
    path('admin/today-orders/', views.TodayOrdersView.as_view(), name='today-orders'),
    path('admin/stats/', views.OrderStatsView.as_view(), name='order-stats'),

    # Enhanced stats view
    path('admin/stats/', views.EnhancedOrderStatsView.as_view(), name='admin-stats'),
]