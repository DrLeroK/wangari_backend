from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import WorkerPayment

User = get_user_model()

class WorkerSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    groups = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='name'
    )

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 'groups']

class WorkerPaymentSerializer(serializers.ModelSerializer):
    worker_name = serializers.CharField(source='worker.get_full_name', read_only=True)
    worker_email = serializers.CharField(source='worker.email', read_only=True)
    paid_by_name = serializers.CharField(source='paid_by.get_full_name', read_only=True)
    payment_type_display = serializers.CharField(source='get_payment_type_display', read_only=True)

    class Meta:
        model = WorkerPayment
        fields = [
            'id', 'worker', 'worker_name', 'worker_email', 'amount', 
            'payment_date', 'payment_type', 'payment_type_display', 'notes',
            'paid_by', 'paid_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['paid_by', 'created_at', 'updated_at']


class WorkerPaymentCreateSerializer(serializers.ModelSerializer):
    worker = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(
            groups__name__in=['Worker', 'Waiter', 'Chef', 'Cashier', 'Butcher', 'Owner']
        ).distinct()
    )

    class Meta:
        model = WorkerPayment
        fields = [
            'worker', 'amount', 'payment_date', 'payment_type', 'notes'
        ]

    def validate_worker(self, value):
        # Ensure the selected user is actually a staff member
        staff_groups = ['Worker', 'Waiter', 'Chef', 'Cashier', 'Butcher', 'Owner']
        if not value.groups.filter(name__in=staff_groups).exists():
            raise serializers.ValidationError("Selected user is not a staff member.")
        return value

    def create(self, validated_data):
        # Automatically set the paid_by field to the current user
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['paid_by'] = request.user
        return super().create(validated_data)
    

class PaymentStatsSerializer(serializers.Serializer):
    total_paid = serializers.DecimalField(max_digits=12, decimal_places=2)
    payment_count = serializers.IntegerField()
    average_payment = serializers.DecimalField(max_digits=10, decimal_places=2)
    workers_paid = serializers.IntegerField()
    
    # Payment type breakdown
    salary_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    bonus_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    advance_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    overtime_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    other_total = serializers.DecimalField(max_digits=12, decimal_places=2)