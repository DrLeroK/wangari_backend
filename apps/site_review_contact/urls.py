from django.urls import path
from . import views

urlpatterns = [
    # Public routes
    path('site-reviews/', views.SiteReviewListView.as_view(), name='site-review-list'),
    path('site-reviews/create/', views.CreateSiteReviewView.as_view(), name='create-site-review'),
    path('contact/create/', views.CreateContactSubmissionView.as_view(), name='create-contact'),
    
    # Admin routes - Site Reviews
    path('admin/site-reviews/', views.AdminSiteReviewListView.as_view(), name='admin-site-review-list'),
    path('admin/site-reviews/<int:pk>/', views.AdminSiteReviewDetailView.as_view(), name='admin-site-review-detail'),
    path('admin/site-reviews/<int:pk>/toggle-approval/', views.ToggleSiteReviewApprovalView.as_view(), name='toggle-site-review-approval'),
    path('admin/site-reviews/<int:pk>/toggle-featured/', views.ToggleSiteReviewFeaturedView.as_view(), name='toggle-site-review-featured'),
    path('admin/site-reviews/stats/', views.SiteReviewStatsView.as_view(), name='site-review-stats'),
    
    # Admin routes - Contact Submissions
    path('admin/contacts/', views.AdminContactSubmissionListView.as_view(), name='admin-contact-list'),
    path('admin/contacts/<int:pk>/', views.AdminContactSubmissionDetailView.as_view(), name='admin-contact-detail'),
    path('admin/contacts/<int:pk>/update-status/', views.UpdateContactStatusView.as_view(), name='update-contact-status'),
    path('admin/contacts/stats/', views.ContactStatsView.as_view(), name='contact-stats'),
]