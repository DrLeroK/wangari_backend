from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


User = get_user_model()


class SiteReview(models.Model):
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='site_reviews'
    )
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars"
    )
    title = models.CharField(max_length=200, help_text="Brief title for the review")
    comment = models.TextField(help_text="Detailed review comment")
    is_approved = models.BooleanField(default=True, help_text="Whether the review is approved to show on site")
    is_featured = models.BooleanField(default=False, help_text="Featured reviews show in prominent places")
    is_active = models.BooleanField(default=True)
    
    # Admin response to the review
    admin_response = models.TextField(blank=True, help_text="Admin response to this review")
    admin_response_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Site Review"
        verbose_name_plural = "Site Reviews"
    
    def __str__(self):
        user_info = self.user.email if self.user else "Anonymous"
        return f"Site Review by {user_info} - {self.rating} stars"
    
    def save(self, *args, **kwargs):
        # Update admin response date if response is added/modified
        if self.admin_response and not self.admin_response_date:
            self.admin_response_date = timezone.now()
        elif not self.admin_response:
            self.admin_response_date = None
            
        super().save(*args, **kwargs)


class ContactSubmission(models.Model):
    CONTACT_CHOICES = [
        ('general', 'General Inquiry'),
        ('reservation', 'Table Reservation'),
        ('catering', 'Catering Service'),
        ('complaint', 'Complaint'),
        ('compliment', 'Compliment'),
        ('suggestion', 'Suggestion'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    # Contact Information
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    
    # Submission Details
    subject = models.CharField(max_length=200)
    message = models.TextField()
    contact_type = models.CharField(max_length=20, choices=CONTACT_CHOICES, default='general')
    
    # Admin Management
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    admin_notes = models.TextField(blank=True, help_text="Internal notes for admin")
    admin_response = models.TextField(blank=True, help_text="Response sent to customer")
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_contacts'
    )
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Contact Submission"
        verbose_name_plural = "Contact Submissions"
    
    def __str__(self):
        return f"Contact from {self.full_name} - {self.subject}"
    
    def save(self, *args, **kwargs):
        # Set resolved_at when status changes to resolved
        if self.status == 'resolved' and not self.resolved_at:
            self.resolved_at = timezone.now()
        elif self.status != 'resolved':
            self.resolved_at = None
            
        super().save(*args, **kwargs)
    
    @property
    def is_new(self):
        return self.status == 'new'
    
    @property
    def days_open(self):
        if self.resolved_at:
            return (self.resolved_at - self.created_at).days
        return (timezone.now() - self.created_at).days