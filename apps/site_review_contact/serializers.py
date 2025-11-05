from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import SiteReview, ContactSubmission


User = get_user_model()



class SiteReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_initials = serializers.SerializerMethodField()
    
    class Meta:
        model = SiteReview
        fields = [
            'id', 'user', 'user_name', 'user_email', 'user_initials',
            'rating', 'title', 'comment', 'is_approved', 'is_featured',
            'admin_response', 'admin_response_date', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at', 'admin_response_date']
    
    def get_user_initials(self, obj):
        if obj.user:
            first_initial = obj.user.first_name[0] if obj.user.first_name else ''
            last_initial = obj.user.last_name[0] if obj.user.last_name else ''
            return f"{first_initial}{last_initial}".upper()
        return "A"  # Anonymous
    
    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
        return super().create(validated_data)


class SiteReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteReview
        fields = ['rating', 'title', 'comment']
    
    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
        return super().create(validated_data)


class ContactSubmissionSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    contact_type_display = serializers.CharField(source='get_contact_type_display', read_only=True)
    days_open = serializers.ReadOnlyField()
    
    class Meta:
        model = ContactSubmission
        fields = [
            'id', 'full_name', 'email', 'phone', 'subject', 'message',
            'contact_type', 'contact_type_display', 'status', 'status_display',
            'admin_notes', 'admin_response', 'assigned_to', 'assigned_to_name',
            'ip_address', 'user_agent', 'days_open',
            'created_at', 'updated_at', 'resolved_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'resolved_at']


class ContactSubmissionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactSubmission
        fields = ['full_name', 'email', 'phone', 'subject', 'message', 'contact_type']
    
    def create(self, validated_data):
        request = self.context.get('request')
        contact = ContactSubmission.objects.create(**validated_data)
        
        # Capture request metadata
        if request:
            contact.ip_address = self.get_client_ip(request)
            contact.user_agent = request.META.get('HTTP_USER_AGENT', '')
            contact.save()
        
        return contact
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class AdminSiteReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = SiteReview
        fields = '__all__'


class AdminContactSubmissionSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    
    class Meta:
        model = ContactSubmission
        fields = '__all__'