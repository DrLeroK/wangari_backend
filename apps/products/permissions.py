# apps/products/permissions.py
from rest_framework import permissions

class IsOwner(permissions.BasePermission):
    """Custom permission to only allow owners (users in 'Owner' group)"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.groups.filter(name='Owner').exists()

class IsWorker(permissions.BasePermission):
    """Custom permission to only allow workers (users in 'Worker' group)"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        # Workers cannot delete
        if request.method == 'DELETE':
            return False
        return request.user.groups.filter(name='Worker').exists()

# Add specific role permissions
class IsChef(permissions.BasePermission):
    """Permission for Chef role"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.groups.filter(name='Chef').exists()

class IsWaiter(permissions.BasePermission):
    """Permission for Waiter role"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.groups.filter(name='Waiter').exists()

class IsCashier(permissions.BasePermission):
    """Permission for Cashier role"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.groups.filter(name='Cashier').exists()

class IsButcher(permissions.BasePermission):
    """Permission for Butcher role"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.groups.filter(name='Butcher').exists()

class IsOwnerOrWorker(permissions.BasePermission):
    """Combined permission that allows both owners and workers"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.groups.filter(name__in=['Owner', 'Worker']).exists()

class IsStaff(permissions.BasePermission):
    """Permission for all staff roles (Owner, Worker, Chef, Waiter, Cashier, Butcher)"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        staff_groups = ['Owner', 'Worker', 'Chef', 'Waiter', 'Cashier', 'Butcher']
        return request.user.groups.filter(name__in=staff_groups).exists()

class IsOrderOwnerOrStaff(permissions.BasePermission):
    """Permission that allows order owners or staff to access order details"""
    def has_object_permission(self, request, view, obj):
        # All staff can access all orders
        staff_groups = ['Owner', 'Worker', 'Chef', 'Waiter', 'Cashier', 'Butcher']
        if request.user.groups.filter(name__in=staff_groups).exists():
            return True
        
        # For orders with user, check if the user owns the order
        if hasattr(obj, 'user') and obj.user == request.user:
            return True
        
        # For orders without user but with customer email, check if email matches
        if hasattr(obj, 'customer_email') and obj.customer_email == request.user.email:
            return True
            
        return False

class CanManageProducts(permissions.BasePermission):
    """Permission for managing products (Owner, Chef, Butcher)"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        allowed_groups = ['Owner', 'Chef', 'Butcher']
        return request.user.groups.filter(name__in=allowed_groups).exists()

class CanManageOrders(permissions.BasePermission):
    """Permission for managing orders (All staff except Butcher)"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        allowed_groups = ['Owner', 'Worker', 'Chef', 'Waiter', 'Cashier']
        return request.user.groups.filter(name__in=allowed_groups).exists()

class CanProcessPhysicalSales(permissions.BasePermission):
    """Permission for processing physical sales (Waiter, Cashier, Owner)"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        allowed_groups = ['Owner', 'Waiter', 'Cashier']
        return request.user.groups.filter(name__in=allowed_groups).exists()
