from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class WorkerPayment(models.Model):
    PAYMENT_TYPES = [
        ('salary', 'Salary'),
        ('bonus', 'Bonus'),
        ('advance', 'Advance'),
        ('overtime', 'Overtime'),
        ('other', 'Other'),
    ]
    
    worker = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='payments_received'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES, default='salary')
    notes = models.TextField(blank=True)
    paid_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='payments_made',
        help_text="Manager who processed this payment"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-payment_date', '-created_at']
        verbose_name = 'Worker Payment'
        verbose_name_plural = 'Worker Payments'

    def __str__(self):
        return f"{self.worker.get_full_name()} - ${self.amount} - {self.payment_date}"

    @property
    def worker_name(self):
        return self.worker.get_full_name() or self.worker.email

    @property
    def paid_by_name(self):
        return self.paid_by.get_full_name() or self.paid_by.email
  