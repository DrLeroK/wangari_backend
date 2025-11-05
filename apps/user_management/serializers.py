from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .utils import send_verification_email
from django.contrib.auth import authenticate

User = get_user_model()



class UserSerializer(serializers.ModelSerializer):
    is_admin = serializers.BooleanField(source='is_superuser', read_only=True)
    groups = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()
    is_worker = serializers.SerializerMethodField()
    
    # ADD THESE NEW FIELDS FOR SPECIFIC ROLES
    is_chef = serializers.SerializerMethodField()
    is_waiter = serializers.SerializerMethodField()
    is_cashier = serializers.SerializerMethodField()
    is_butcher = serializers.SerializerMethodField()
    
    loyalty_tier = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 
            'first_name', 
            'last_name', 
            'email', 
            'phone_number',
            'is_staff',
            'is_superuser',
            'is_admin',
            'is_active',
            'is_email_verified',
            'groups',
            'is_owner',
            'is_worker',
            # ADD THE NEW ROLE FIELDS
            'is_chef',
            'is_waiter', 
            'is_cashier',
            'is_butcher',
            'loyalty_points',
            'loyalty_tier'
        ]
        read_only_fields = ['id', 'loyalty_points']

    def get_groups(self, obj):
        return [group.name for group in obj.groups.all()]

    def get_is_owner(self, obj):
        return obj.groups.filter(name='Owner').exists()

    def get_is_worker(self, obj):
        return obj.groups.filter(name='Worker').exists()
    
    # ADD THESE NEW METHODS
    def get_is_chef(self, obj):
        return obj.groups.filter(name='Chef').exists()
    
    def get_is_waiter(self, obj):
        return obj.groups.filter(name='Waiter').exists()
    
    def get_is_cashier(self, obj):
        return obj.groups.filter(name='Cashier').exists()
    
    def get_is_butcher(self, obj):
        return obj.groups.filter(name='Butcher').exists()
    
    def get_loyalty_tier(self, obj):
        return obj.get_loyalty_tier()
    

    

class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    phone_number = serializers.CharField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = [
            'first_name', 
            'last_name', 
            'email', 
            'phone_number', 
            'password',
            'password2'
        ]

    # validation to check if both passwords match
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )
        return attrs

    # validation to check if phone number is in correct format
    def validate_phone_number(self, value):
        import re
        if not re.match(r'^\+?1?\d{9,15}$', value):
            raise serializers.ValidationError(
                "Phone number must be in format: '+999999999'."
            )
        return value
    

    def create(self, validated_data):
        # Remove password2 before creating user
        validated_data.pop('password2')
        user = User.objects.create(
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone_number=validated_data['phone_number'],
            is_active=False,  # User not active until email verified
        )
        user.set_password(validated_data['password'])
        user.save()
        
        # Send verification email
        send_verification_email(user)
        
        return user



class VerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(max_length=6, required=True)
    
    def validate(self, attrs):
        email = attrs.get('email')
        otp = attrs.get('otp')
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
        
        from .utils import is_otp_valid
        if not is_otp_valid(user, otp):
            raise serializers.ValidationError("Invalid or expired OTP.")
            
        attrs['user'] = user
        return attrs



class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    
    def validate(self, attrs):
        email = attrs.get('email')
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
            
        attrs['user'] = user
        return attrs
    
    
# Working Custom Token Serializer
# ==============================================================================



class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email'
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        try:
            # Use email as username for parent class
            attrs['username'] = email
            
            # Let parent class handle the main validation
            data = super().validate(attrs)
            
            # Add user data to response
            user_serializer = UserSerializer(self.user)
            data['user'] = user_serializer.data
            
            # Add additional user information with ALL roles
            data.update({
                'is_admin': self.user.is_superuser,
                'email': self.user.email,
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'groups': [group.name for group in self.user.groups.all()],
                # ALL ROLE BOOLEANS
                'is_owner': self.user.groups.filter(name='Owner').exists(),
                'is_worker': self.user.groups.filter(name='Worker').exists(),
                'is_chef': self.user.groups.filter(name='Chef').exists(),
                'is_waiter': self.user.groups.filter(name='Waiter').exists(),
                'is_cashier': self.user.groups.filter(name='Cashier').exists(),
                'is_butcher': self.user.groups.filter(name='Butcher').exists(),
                'is_staff': self.user.is_staff,
            })
            
            return data
            
        except Exception as e:
            print(f"Login error: {str(e)}")
            raise
