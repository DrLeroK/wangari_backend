from rest_framework import permissions

class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners (users in 'Owner' group)
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Check if user is in Owner group
        return request.user.groups.filter(name='Owner').exists()


class IsWorker(permissions.BasePermission):
    """
    Custom permission to only allow workers (users in 'Worker' group)
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Workers cannot delete
        if request.method == 'DELETE':
            return False
        
        # Check if user is in Worker group
        return request.user.groups.filter(name='Worker').exists()


class IsOwnerOrWorker(permissions.BasePermission):
    """
    Combined permission that allows both owners and workers
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Check if user is in either Owner or Worker group
        return request.user.groups.filter(name__in=['Owner', 'Worker']).exists()


class IsOrderOwnerOrStaff(permissions.BasePermission):
    """
    Permission that allows order owners or staff to access order details
    """
    def has_object_permission(self, request, view, obj):
        # Staff (owners/workers) can access all orders
        if request.user.groups.filter(name__in=['Owner', 'Worker']).exists():
            return True
        
        # For orders with user, check if the user owns the order
        if hasattr(obj, 'user') and obj.user == request.user:
            return True
        
        # For orders without user but with customer email, check if email matches
        if hasattr(obj, 'customer_email') and obj.customer_email == request.user.email:
            return True
            
        return False



















# from rest_framework import permissions


# class IsOwner(permissions.BasePermission):
#     """
#     Custom permission to only allow owners to delete items.
#     Owners are users in the 'Owner' group.
#     """
#     def has_permission(self, request, view):
#         if not request.user.is_authenticated:
#             return False
        
#         # For safe methods (GET, HEAD, OPTIONS), allow both workers and owners
#         if request.method in permissions.SAFE_METHODS:
#             return request.user.groups.filter(name__in=['Owner', 'Worker']).exists()
        
#         # For DELETE method, only allow owners
#         if request.method == 'DELETE':
#             return request.user.groups.filter(name='Owner').exists()
        
#         # For other methods (POST, PUT, PATCH), allow both workers and owners
#         return request.user.groups.filter(name__in=['Owner', 'Worker']).exists()


# class IsWorker(permissions.BasePermission):
#     """
#     Custom permission to only allow workers (no delete access).
#     Workers are users in the 'Worker' group.
#     """
#     def has_permission(self, request, view):
#         if not request.user.is_authenticated:
#             return False
        
#         # Workers cannot delete
#         if request.method == 'DELETE':
#             return False
        
#         # Workers can do everything else
#         return request.user.groups.filter(name='Worker').exists()


# class IsOwnerOrWorker(permissions.BasePermission):
#     """
#     Combined permission that allows both owners and workers with different privileges.
#     """
#     def has_permission(self, request, view):
#         if not request.user.is_authenticated:
#             return False
        
#         # Check if user is in either Owner or Worker group
#         is_owner = request.user.groups.filter(name='Owner').exists()
#         is_worker = request.user.groups.filter(name='Worker').exists()
        
#         if not (is_owner or is_worker):
#             return False
        
#         # Owners can do everything
#         if is_owner:
#             return True
        
#         # Workers cannot delete
#         if request.method == 'DELETE':
#             return False
        
#         # Workers can do everything else
#         return True


# class NoDjangoAdminAccess(permissions.BasePermission):
#     """
#     Prevent access to Django admin for specific groups.
#     """
#     def has_permission(self, request, view):
#         # This is for API views only, Django admin access is controlled separately
#         return True


# class IsCustomer(permissions.BasePermission):
#     """
#     Permission for regular customers (not workers or owners)
#     """
#     def has_permission(self, request, view):
#         if not request.user.is_authenticated:
#             return False
        
#         # Customers are users not in Worker or Owner groups
#         is_worker_or_owner = request.user.groups.filter(name__in=['Worker', 'Owner']).exists()
#         return not is_worker_or_owner


# class IsOrderOwnerOrStaff(permissions.BasePermission):
#     """
#     Permission that allows order owners or staff to access order details
#     """
#     def has_object_permission(self, request, view, obj):
#         if request.user.is_staff or request.user.groups.filter(name__in=['Owner', 'Worker']).exists():
#             return True
        
#         # For orders with user, check if the user owns the order
#         if hasattr(obj, 'user') and obj.user == request.user:
#             return True
        
#         # For orders without user but with customer email, check if email matches
#         if hasattr(obj, 'customer_email') and obj.customer_email == request.user.email:
#             return True
            
#         return False