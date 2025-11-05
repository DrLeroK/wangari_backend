from django.urls import path
from . import views

app_name = 'payroll'

urlpatterns = [
    path('workers/', views.WorkerListView.as_view(), name='worker-list'),
    path('payments/', views.WorkerPaymentListCreateView.as_view(), name='payment-list-create'),
    path('payments/<int:pk>/', views.WorkerPaymentDetailView.as_view(), name='payment-detail'),
    path('stats/', views.PaymentStatsView.as_view(), name='payment-stats'),
    path('recent-payments/', views.RecentPaymentsView.as_view(), name='recent-payments'),
]