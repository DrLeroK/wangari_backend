import random
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

def generate_otp():
    """Generate a 6-digit OTP"""
    return str(random.randint(100000, 999999))

def send_verification_email(user):
    """Send OTP verification email to user"""
    # Generate OTP
    otp = generate_otp()
    
    # Save OTP to user model
    user.email_verification_otp = otp
    user.otp_created_at = timezone.now()
    user.save()
    
    # Send email
    subject = 'Verify Your Email - Wangari Restaurant'
    message = f'''
    Hello {user.first_name},
    
    Thank you for registering with Wangari Restaurant!
    
    Your OTP for email verification is: {otp}
    
    This OTP will expire in 10 minutes.
    
    If you didn't create an account, please ignore this email.
    
    Best regards,
    Wangari Restaurant Team
    '''
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )
    
    return otp

def is_otp_valid(user, otp):
    """Check if OTP is valid and not expired"""
    if not user.otp_created_at or not user.email_verification_otp:
        return False
        
    # Check if OTP matches
    if user.email_verification_otp != otp:
        return False
        
    # Check if OTP is expired (10 minutes)
    expiry_time = user.otp_created_at + timedelta(minutes=10)
    if timezone.now() > expiry_time:
        return False
        
    return True