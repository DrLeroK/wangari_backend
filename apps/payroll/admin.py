from django.contrib import admin
from .models import WorkerPayment

@admin.register(WorkerPayment)
class WorkerPaymentAdmin(admin.ModelAdmin):
    list_display = ['worker', 'amount', 'payment_date', 'payment_type', 'paid_by', 'created_at']
    list_filter = ['payment_type', 'payment_date', 'created_at']
    search_fields = ['worker__first_name', 'worker__last_name', 'worker__email', 'notes']
    date_hierarchy = 'payment_date'
    ordering = ['-payment_date', '-created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('worker', 'paid_by')