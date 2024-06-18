from django.urls import path
from .views import LoanCreateView, LoanPaymentsView, UpdatePaymentPrincipalView

urlpatterns = [
    path('loans/', LoanCreateView.as_view(), name='loan-create'),
    path('loans/<int:loan_id>/payments/', LoanPaymentsView.as_view(), name='loan-payments'),
    path('payments/<int:payment_id>/', UpdatePaymentPrincipalView.as_view(), name='update-payment-principal'),
]