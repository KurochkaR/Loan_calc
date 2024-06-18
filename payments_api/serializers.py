from rest_framework import serializers

from .models import Loan, Payment


class PaymentSerializer(serializers.ModelSerializer):
    date = serializers.DateField(source='payment_date')
    principal = serializers.DecimalField(source='principal_payment', max_digits=10, decimal_places=2)
    interest = serializers.DecimalField(source='interest_payment', max_digits=10, decimal_places=2)

    class Meta:
        model = Payment
        fields = ['id', 'date', 'principal', 'interest']


class LoanSerializer(serializers.ModelSerializer):
    payments = PaymentSerializer(many=True, read_only=True)
    loan_start_date = serializers.DateField(input_formats=['%d-%m-%Y', '%Y-%m-%d'])

    class Meta:
        model = Loan
        fields = ['id', 'amount', 'loan_start_date', 'number_of_payments', 'periodicity', 'interest_rate', 'payments']