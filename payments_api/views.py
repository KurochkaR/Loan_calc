
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Payment
from .serializers import PaymentSerializer, LoanSerializer

from .utils import generate_payment_schedule, recalculate_payments


class LoanCreateView(APIView):

    def post(self, request):
        serializer = LoanSerializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.save()
            generate_payment_schedule(instance)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoanPaymentsView(generics.ListAPIView):
    serializer_class = PaymentSerializer

    def get_queryset(self):
        loan_id = self.kwargs['loan_id']
        return Payment.objects.filter(loan_id=loan_id)


class UpdatePaymentPrincipalView(APIView):
    def put(self, request, payment_id):
        try:
            payment = Payment.objects.get(id=payment_id)
        except ObjectDoesNotExist:
            return Response({'error': 'Payment not found'}, status=status.HTTP_404_NOT_FOUND)

        original_principal = payment.principal_payment
        serializer = PaymentSerializer(payment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        new_principal = serializer.validated_data.get('principal_payment', original_principal)
        if new_principal != original_principal:
            recalculate_payments(payment)

        return Response(serializer.data)

    def perform_update(self, serializer):
        serializer.save()

