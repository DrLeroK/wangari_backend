import os
from .base import *

# Security
DEBUG = False
# ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com', 'api.yourdomain.com']
ALLOWED_HOSTS = ['*']
SECRET_KEY = os.environ['SECRET_KEY']


# Database
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': os.environ['DB_NAME'],
#         'USER': os.environ['DB_USER'],
#         'PASSWORD': os.environ['DB_PASS'],
#         'HOST': os.environ['DB_HOST'],
#         'PORT': os.environ.get('DB_PORT', '5432'),
#     }
# }


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}



# Correct Static Files Configuration
STATIC_URL = '/static/'
STATIC_ROOT = '/home/pldassociationor/public_html/static_3'  # Changed to public_html
STATICFILES_DIRS = []

# Media Files
MEDIA_URL = '/media/'
MEDIA_ROOT = '/home/pldassociationor/wangari_backend/media'

# For production
FRONTEND_URL = os.getenv('FRONTEND_URL', 'https://wan-deployment-frontend.vercel.app')
DOMAIN = os.getenv('DOMAIN', 'wan-deployment-frontend.vercel.app')
# FRONTEND_URL = 'https://www.pldassociation.org'
# DOMAIN = 'pldassociation.org'  # or 'www.pldassociation.org'
SITE_NAME = 'Wangari Restaurant'


# Security headers
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# CORS - restrict to your frontend domain
# CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_ALL_ORIGINS = True
# CORS_ALLOWED_ORIGINS = [
#     "https://yourdomain.com",
#     "https://www.yourdomain.com",
#     "https://your-vercel-app.vercel.app",
# ]


# Email - use real SMTP in production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
