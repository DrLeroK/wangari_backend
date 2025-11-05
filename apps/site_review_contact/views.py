from rest_framework import generics, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
# from django_filters.rest_framework import DjangoFilterBackend
# from rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta

from .models import SiteReview, ContactSubmission
from .serializers import (
    SiteReviewSerializer, SiteReviewCreateSerializer,
    ContactSubmissionSerializer, ContactSubmissionCreateSerializer,
    AdminSiteReviewSerializer, AdminContactSubmissionSerializer
)
from apps.products.permissions import IsOwnerOrWorker, IsOwner, IsWorker
from apps.products.models import ActivityLog


def log_activity(user, action, model_name, object_id='', description='', old_value='', new_value='', request=None):
    ip_address = request.META.get('REMOTE_ADDR') if request else None
    ActivityLog.objects.create(
        user=user,
        action=action,
        model_name=model_name,
        object_id=object_id,
        description=description,
        old_value=old_value,
        new_value=new_value,
        ip_address=ip_address
    )



# Public Views (No authentication required)
class SiteReviewListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = SiteReviewSerializer
    
    def get_queryset(self):
        return SiteReview.objects.filter(
            is_approved=True, 
            is_active=True
        ).select_related('user').order_by('-is_featured', '-created_at')


class CreateSiteReviewView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = SiteReviewCreateSerializer
    
    def perform_create(self, serializer):
        review = serializer.save()
        
        # Log activity
        user_for_log = self.request.user if self.request.user.is_authenticated else None
        log_activity(
            user=user_for_log,
            action='create',
            model_name='SiteReview',
            object_id=str(review.id),
            description=f'Site review submitted: {review.title}',
            new_value=f"Rating: {review.rating}, Approved: {review.is_approved}",
            request=self.request
        )


class CreateContactSubmissionView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = ContactSubmissionCreateSerializer
    
    def perform_create(self, serializer):
        contact = serializer.save()
        
        # Log activity
        log_activity(
            user=None,
            action='create',
            model_name='ContactSubmission',
            object_id=str(contact.id),
            description=f'Contact form submitted: {contact.subject}',
            new_value=f"Type: {contact.contact_type}, Status: {contact.status}",
            request=self.request
        )


# Admin Views (Owner and Worker permissions)
class AdminSiteReviewListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsOwnerOrWorker]
    serializer_class = AdminSiteReviewSerializer
    # filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_approved', 'is_featured', 'is_active', 'rating']
    search_fields = ['title', 'comment', 'user__email', 'user__first_name', 'user__last_name']
    ordering_fields = ['created_at', 'updated_at', 'rating']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return SiteReview.objects.all().select_related('user')


class AdminSiteReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsOwnerOrWorker]
    serializer_class = AdminSiteReviewSerializer
    queryset = SiteReview.objects.all()
    
    def perform_update(self, serializer):
        old_review = self.get_object()
        old_approved = old_review.is_approved
        old_featured = old_review.is_featured
        
        review = serializer.save()
        
        # Log changes
        changes = []
        if old_approved != review.is_approved:
            changes.append(f"Approved: {old_approved} → {review.is_approved}")
        if old_featured != review.is_featured:
            changes.append(f"Featured: {old_featured} → {review.is_featured}")
        
        if changes:
            log_activity(
                user=self.request.user,
                action='update',
                model_name='SiteReview',
                object_id=str(review.id),
                description=f'Site review updated: {review.title}',
                old_value=", ".join([f"Approved: {old_approved}", f"Featured: {old_featured}"]),
                new_value=", ".join(changes),
                request=self.request
            )
    
    def perform_destroy(self, instance):
        log_activity(
            user=self.request.user,
            action='delete',
            model_name='SiteReview',
            object_id=str(instance.id),
            description=f'Site review deleted: {instance.title}',
            old_value=f"Rating: {instance.rating}, Title: {instance.title}",
            request=self.request
        )
        instance.delete()


class ToggleSiteReviewApprovalView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrWorker]
    
    def post(self, request, pk):
        review = generics.get_object_or_404(SiteReview, pk=pk)
        old_status = review.is_approved
        review.is_approved = not review.is_approved
        review.save()
        
        action = 'approved' if review.is_approved else 'unapproved'
        log_activity(
            user=request.user,
            action='update',
            model_name='SiteReview',
            object_id=str(review.id),
            description=f'Site review {action}: {review.title}',
            old_value=f"Approved: {old_status}",
            new_value=f"Approved: {review.is_approved}",
            request=request
        )
        
        return Response({
            'detail': f'Review {action} successfully.',
            'is_approved': review.is_approved
        })



class ToggleSiteReviewFeaturedView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrWorker]
    
    def post(self, request, pk):
        review = generics.get_object_or_404(SiteReview, pk=pk)
        old_status = review.is_featured
        review.is_featured = not review.is_featured
        review.save()
        
        action = 'featured' if review.is_featured else 'unfeatured'
        log_activity(
            user=request.user,
            action='update',
            model_name='SiteReview',
            object_id=str(review.id),
            description=f'Site review {action}: {review.title}',
            old_value=f"Featured: {old_status}",
            new_value=f"Featured: {review.is_featured}",
            request=request
        )
        
        return Response({
            'detail': f'Review {action} successfully.',
            'is_featured': review.is_featured
        })


class AdminContactSubmissionListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsOwnerOrWorker]
    serializer_class = AdminContactSubmissionSerializer
    # filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'contact_type']
    search_fields = ['full_name', 'email', 'subject', 'message']
    ordering_fields = ['created_at', 'updated_at', 'resolved_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return ContactSubmission.objects.all().select_related('assigned_to')



class AdminContactSubmissionDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated, IsOwnerOrWorker]
    serializer_class = AdminContactSubmissionSerializer
    queryset = ContactSubmission.objects.all()
    
    def perform_update(self, serializer):
        old_contact = self.get_object()
        old_status = old_contact.status
        
        contact = serializer.save()
        
        # Log status changes
        if old_status != contact.status:
            log_activity(
                user=self.request.user,
                action='update',
                model_name='ContactSubmission',
                object_id=str(contact.id),
                description=f'Contact submission status updated: {contact.subject}',
                old_value=f"Status: {old_status}",
                new_value=f"Status: {contact.status}",
                request=self.request
            )


class UpdateContactStatusView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrWorker]
    
    def post(self, request, pk):
        contact = generics.get_object_or_404(ContactSubmission, pk=pk)
        new_status = request.data.get('status')
        
        if new_status not in dict(ContactSubmission.STATUS_CHOICES):
            return Response(
                {'error': 'Invalid status'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_status = contact.status
        contact.status = new_status
        contact.save()
        
        log_activity(
            user=request.user,
            action='update',
            model_name='ContactSubmission',
            object_id=str(contact.id),
            description=f'Contact submission status changed: {contact.subject}',
            old_value=f"Status: {old_status}",
            new_value=f"Status: {contact.status}",
            request=request
        )
        
        return Response({
            'detail': f'Contact status updated to {new_status} successfully.',
            'status': contact.status
        })


class SiteReviewStatsView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrWorker]
    
    def get(self, request):
        total_reviews = SiteReview.objects.count()
        approved_reviews = SiteReview.objects.filter(is_approved=True).count()
        featured_reviews = SiteReview.objects.filter(is_featured=True).count()
        average_rating = SiteReview.objects.filter(is_approved=True).aggregate(
            avg_rating=Avg('rating')
        )['avg_rating'] or 0
        
        # Rating distribution
        rating_distribution = SiteReview.objects.filter(is_approved=True).values(
            'rating'
        ).annotate(count=Count('id')).order_by('rating')
        
        # Recent activity
        last_week = timezone.now() - timedelta(days=7)
        recent_reviews = SiteReview.objects.filter(created_at__gte=last_week).count()
        
        stats = {
            'total_reviews': total_reviews,
            'approved_reviews': approved_reviews,
            'pending_approval': total_reviews - approved_reviews,
            'featured_reviews': featured_reviews,
            'average_rating': round(average_rating, 1),
            'recent_reviews_7_days': recent_reviews,
            'rating_distribution': list(rating_distribution),
        }
        
        return Response(stats)


class ContactStatsView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrWorker]
    
    def get(self, request):
        total_contacts = ContactSubmission.objects.count()
        new_contacts = ContactSubmission.objects.filter(status='new').count()
        
        # Status distribution
        status_distribution = ContactSubmission.objects.values(
            'status'
        ).annotate(count=Count('id')).order_by('status')
        
        # Contact type distribution
        type_distribution = ContactSubmission.objects.values(
            'contact_type'
        ).annotate(count=Count('id')).order_by('contact_type')
        
        # Recent activity
        last_week = timezone.now() - timedelta(days=7)
        recent_contacts = ContactSubmission.objects.filter(created_at__gte=last_week).count()
        
        stats = {
            'total_contacts': total_contacts,
            'new_contacts': new_contacts,
            'recent_contacts_7_days': recent_contacts,
            'status_distribution': list(status_distribution),
            'type_distribution': list(type_distribution),
        }
        
        return Response(stats)