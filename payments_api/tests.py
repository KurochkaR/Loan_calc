import math
from datetime import timedelta, date, datetime
from decimal import Decimal

from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.test import TestCase

from payments_api.models import Payment, Loan
from payments_api.utils import parse_period, generate_payment_schedule, recalculate_payments


# Create your tests here.

class PaymentScheduleTests(TestCase):

    def setUp(self):
        self.loan = Loan.objects.create(
            amount=Decimal('1000.00'),
            interest_rate=Decimal('0.1'),
            number_of_payments=4,
            loan_start_date=date(2024, 1, 10),
            periodicity='1m'
        )

    def test_generate_payment_schedule(self):
        generate_payment_schedule(self.loan)
        payments = Payment.objects.filter(loan=self.loan).order_by('payment_date')

        self.assertEqual(len(payments), 4)

        amount = self.loan.amount
        interest = self.loan.interest_rate
        payments_count = self.loan.number_of_payments
        start_date = self.loan.loan_start_date
        period_type, period_number, period_length = parse_period(self.loan.periodicity)
        rate = interest * Decimal(period_length)
        repayment = rate * amount / Decimal(1 - math.pow(1 + rate, -payments_count))

        period_delta_map = {
            'd': lambda start, num: start + timedelta(days=num),
            'w': lambda start, num: start + timedelta(weeks=num),
            'm': lambda start, num: (start.replace(day=1) + timedelta(days=32)).replace(day=start.day)
        }

        for payment in payments:
            interest_payment = amount * rate
            principal_payment = repayment - interest_payment
            payment_date = period_delta_map[period_type](start_date, period_number)

            self.assertEqual(payment.payment_date, payment_date)
            self.assertAlmostEqual(payment.principal_payment, principal_payment, places=2)
            self.assertAlmostEqual(payment.interest_payment, interest_payment, places=2)

            start_date = payment_date
            amount -= principal_payment


class RecalculatePaymentsTest(TestCase):

    def setUp(self):
        self.loan = Loan.objects.create(
            amount=Decimal('10000.00'),
            interest_rate=Decimal('0.05'),
            number_of_payments=12,
            loan_start_date=datetime.now().date(),
            periodicity='1m'
        )
        generate_payment_schedule(self.loan)
        self.payments = Payment.objects.filter(loan=self.loan).order_by('payment_date')

    def test_recalculate_payments(self):
        payment = self.payments[4]
        payment.principal_payment = Decimal('1000.00')
        payment.save()
        recalculate_payments(payment)
        updated_payments = Payment.objects.filter(loan=self.loan).order_by('payment_date')
        payed_principal = Payment.objects.filter(
            loan=self.loan,
            payment_date__lt=payment.payment_date
        ).aggregate(payed_principal=Coalesce(Sum('principal_payment'), Decimal(0)))['payed_principal']
        principal = self.loan.amount - payed_principal
        _, _, period_length = parse_period(self.loan.periodicity)
        interest = self.loan.interest_rate * Decimal(period_length)

        expected_interest_payment = principal * interest
        self.assertAlmostEqual(payment.interest_payment, expected_interest_payment, places=2)

        principal -= payment.principal_payment

        remaining_payments = len(self.payments) - 5
        emi = (interest * principal) / (1 - (1 + interest) ** -remaining_payments)

        for next_payment in updated_payments[5:]:
            interest_amount = principal * interest
            principal_amount = emi - interest_amount

            self.assertAlmostEqual(next_payment.interest_payment, interest_amount, places=2)
            self.assertAlmostEqual(next_payment.principal_payment, principal_amount, places=2)

            principal -= principal_amount
