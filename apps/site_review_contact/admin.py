from django.contrib import admin
from .models import SiteReview, ContactSubmission

@admin.register(SiteReview)
class SiteReviewAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'rating', 'is_approved', 'is_featured', 'is_active', 'created_at']
    list_filter = ['is_approved', 'is_featured', 'is_active', 'rating', 'created_at']
    search_fields = ['title', 'comment', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at', 'admin_response_date']
    fieldsets = (
        ('Review Information', {
            'fields': ('user', 'rating', 'title', 'comment')
        }),
        ('Moderation', {
            'fields': ('is_approved', 'is_featured', 'is_active')
        }),
        ('Admin Response', {
            'fields': ('admin_response', 'admin_response_date'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(ContactSubmission)
class ContactSubmissionAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'subject', 'contact_type', 'status', 'created_at', 'is_new']
    list_filter = ['status', 'contact_type', 'created_at', 'assigned_to']
    search_fields = ['full_name', 'email', 'subject', 'message']
    readonly_fields = ['created_at', 'updated_at', 'resolved_at', 'ip_address', 'user_agent', 'days_open']
    fieldsets = (
        ('Contact Information', {
            'fields': ('full_name', 'email', 'phone')
        }),
        ('Submission Details', {
            'fields': ('subject', 'message', 'contact_type')
        }),
        ('Admin Management', {
            'fields': ('status', 'admin_notes', 'admin_response', 'assigned_to')
        }),
        ('Metadata', {
            'fields': ('ip_address', 'user_agent', 'created_at', 'updated_at', 'resolved_at', 'days_open'),
            'classes': ('collapse',)
        }),
    )
    
    def is_new(self, obj):
        return obj.status == 'new'
    is_new.boolean = True
    is_new.short_description = 'New'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('assigned_to')