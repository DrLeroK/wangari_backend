from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model

from .models import WorkerPayment
from .serializers import (
    WorkerPaymentSerializer, WorkerPaymentCreateSerializer,
    WorkerSerializer, PaymentStatsSerializer
)
from apps.products.permissions import IsStaff, IsOwnerOrWorker

User = get_user_model()


class WorkerListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsStaff]
    serializer_class = WorkerSerializer
    
    def get_queryset(self):
        # Get only staff users (workers, waiters, chefs, etc.) without duplicates
        staff_groups = ['Worker', 'Waiter', 'Chef', 'Cashier', 'Butcher', 'Owner']
        return User.objects.filter(
            groups__name__in=staff_groups
        ).distinct().order_by('first_name', 'last_name')
    

class WorkerPaymentListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsStaff]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return WorkerPaymentCreateSerializer
        return WorkerPaymentSerializer

    def get_queryset(self):
        queryset = WorkerPayment.objects.all()
        
        # Filter by worker
        worker_id = self.request.query_params.get('worker')
        if worker_id:
            queryset = queryset.filter(worker_id=worker_id)
        
        # Filter by payment type
        payment_type = self.request.query_params.get('payment_type')
        if payment_type:
            queryset = queryset.filter(payment_type=payment_type)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(payment_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(payment_date__lte=end_date)
        
        # Filter by this week
        this_week = self.request.query_params.get('this_week')
        if this_week and this_week.lower() == 'true':
            today = timezone.now().date()
            start_of_week = today - timedelta(days=today.weekday())
            queryset = queryset.filter(payment_date__gte=start_of_week)
        
        # Filter by this month
        this_month = self.request.query_params.get('this_month')
        if this_month and this_month.lower() == 'true':
            today = timezone.now().date()
            start_of_month = today.replace(day=1)
            queryset = queryset.filter(payment_date__gte=start_of_month)
        
        return queryset

    def perform_create(self, serializer):
        serializer.save()

class WorkerPaymentDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsStaff]
    serializer_class = WorkerPaymentSerializer
    queryset = WorkerPayment.objects.all()

class PaymentStatsView(APIView):
    permission_classes = [IsAuthenticated, IsStaff]
    
    def get(self, request):
        # Get date filters from query params
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        this_week = request.query_params.get('this_week')
        this_month = request.query_params.get('this_month')
        
        queryset = WorkerPayment.objects.all()
        
        # Apply date filters
        if start_date:
            queryset = queryset.filter(payment_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(payment_date__lte=end_date)
        
        if this_week and this_week.lower() == 'true':
            today = timezone.now().date()
            start_of_week = today - timedelta(days=today.weekday())
            queryset = queryset.filter(payment_date__gte=start_of_week)
        
        if this_month and this_month.lower() == 'true':
            today = timezone.now().date()
            start_of_month = today.replace(day=1)
            queryset = queryset.filter(payment_date__gte=start_of_month)
        
        # Calculate stats
        total_paid = queryset.aggregate(Sum('amount'))['amount__sum'] or 0
        payment_count = queryset.count()
        average_payment = queryset.aggregate(Avg('amount'))['amount__avg'] or 0
        workers_paid = queryset.values('worker').distinct().count()
        
        # Payment type breakdown
        salary_total = queryset.filter(payment_type='salary').aggregate(Sum('amount'))['amount__sum'] or 0
        bonus_total = queryset.filter(payment_type='bonus').aggregate(Sum('amount'))['amount__sum'] or 0
        advance_total = queryset.filter(payment_type='advance').aggregate(Sum('amount'))['amount__sum'] or 0
        overtime_total = queryset.filter(payment_type='overtime').aggregate(Sum('amount'))['amount__sum'] or 0
        other_total = queryset.filter(payment_type='other').aggregate(Sum('amount'))['amount__sum'] or 0
        
        stats = {
            'total_paid': total_paid,
            'payment_count': payment_count,
            'average_payment': average_payment,
            'workers_paid': workers_paid,
            'salary_total': salary_total,
            'bonus_total': bonus_total,
            'advance_total': advance_total,
            'overtime_total': overtime_total,
            'other_total': other_total,
        }
        
        serializer = PaymentStatsSerializer(stats)
        return Response(serializer.data)

class RecentPaymentsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsStaff]
    serializer_class = WorkerPaymentSerializer
    
    def get_queryset(self):
        return WorkerPayment.objects.all().order_by('-payment_date', '-created_at')[:10]