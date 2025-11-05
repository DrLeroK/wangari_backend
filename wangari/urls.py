"""
URL configuration for wangari project.
"""


from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from django.conf import settings
from django.conf.urls.static import static


from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.views.generic import RedirectView


schema_view = get_schema_view(
    openapi.Info(
        title="Wangari Restaurant Website",
        default_version='v1',
        description="API documentation for Wangari Restaurant",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('user_management/', include('apps.user_management.urls')),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    path('products/', include('apps.products.urls')),

    path('site-review-contact/', include('apps.site_review_contact.urls')),
    path('payroll/', include('apps.payroll.urls')),
    # path('contact_review/', include('apps.contact_review.urls')),
    # path('payments/', include('apps.payments.urls')),

    # Djoser endpoints for password reset
    path('auth/', include('djoser.urls')),  # Main Djoser endpoints
    path('auth/', include('djoser.urls.jwt')),  # JWT-specific endpoints

    # Documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
