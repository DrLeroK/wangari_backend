from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Admin configuration for custom User model"""

    # Fields to display in the list view
    list_display = ('email', 'first_name', 'last_name', 'phone_number', 
                   'is_email_verified', 'is_active', 'is_staff', 'date_joined')
    
    # Fields that can be clicked to edit
    list_display_links = ('email',)
    
    # Fields to filter by in the right sidebar
    list_filter = ('is_email_verified', 'is_active', 'is_staff', 'is_superuser', 'date_joined')
    
    # Fields to search by
    search_fields = ('email', 'first_name', 'last_name', 'phone_number')
    
    # Default ordering
    ordering = ('-date_joined',)
    
    # Fieldsets for the edit form
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'phone_number')}),
        (_('Verification'), {'fields': ('is_email_verified', 'email_verification_otp', 'otp_created_at')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    # Fieldsets for the add form
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'phone_number', 'password1', 'password2'),
        }),
    )
    
    # Readonly fields
    readonly_fields = ('last_login', 'date_joined', 'otp_created_at')

    def get_readonly_fields(self, request, obj=None):
        """Make email readonly when editing existing user"""
        if obj:  # editing an existing object
            return self.readonly_fields + ('email',)
        return self.readonly_fields










# from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin
# from .models import User


# class CustomUserAdmin(UserAdmin):
#     # The forms to add and change user instances
#     model = User
#     list_display = ('email', 'phone_number', 'first_name', 'last_name', 'is_staff')
#     list_filter = ('is_staff', 'is_superuser', 'is_active')
#     fieldsets = (
#         (None, {'fields': ('email', 'password')}),
#         ('Personal info', {'fields': ('first_name', 'last_name', 'phone_number')}),
#         ('Permissions', {
#             'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
#         }),
#         ('Important dates', {'fields': ('last_login', 'date_joined')}),
#     )
#     add_fieldsets = (
#         (None, {
#             'classes': ('wide',),
#             'fields': (
#                 'email', 
#                 'phone_number', 
#                 'first_name', 
#                 'last_name', 
#                 'password1', 
#                 'password2',
#                 'is_staff',
#                 'is_active'
#             )}
#         ),
#     )
#     search_fields = ('email', 'phone_number', 'first_name', 'last_name')
#     ordering = ('email',)
#     filter_horizontal = ('groups', 'user_permissions',)
    
#     # To use the same phone number validation as in the serializer
#     def save_model(self, request, obj, form, change):
#         from .serializers import RegisterSerializer
#         serializer = RegisterSerializer(data={
#             'email': obj.email,
#             'phone_number': obj.phone_number,
#             'first_name': obj.first_name,
#             'last_name': obj.last_name,
#             'password': obj.password,
#             'password2': obj.password
#         })
        
#         if not change:  # Only validate phone number on creation
#             serializer.validate_phone_number(obj.phone_number)
        
#         super().save_model(request, obj, form, change)
#         if not change:  # Only set password on creation
#             obj.set_password(obj.password)
#             obj.save()

# # Register the custom User model with the custom admin interface
# admin.site.register(User, CustomUserAdmin)
