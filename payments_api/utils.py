import math
from datetime import timedelta
from decimal import Decimal

from django.db.models import Sum
from django.db.models.functions import Coalesce

from payments_api.models import Payment


def parse_period(period):
    period_map = {
        'm': 1 / 12,
        'w': 7 / 365,
        'd': 1 / 365
    }
    period_type = period[-1]
    period_number = int(period[:-1])
    period_length = period_map.get(period_type) * period_number
    return period_type, period_number, period_length


def generate_payment_schedule(loan):

    amount = loan.amount
    interest = loan.interest_rate
    payments_count = loan.number_of_payments
    start_date = loan.loan_start_date
    period_type, period_number, period_length = parse_period(loan.periodicity)

    period_delta_map = {
        'd': lambda start, num: start + timedelta(days=num),
        'w': lambda start, num: start + timedelta(weeks=num),
        'm': lambda start, num: (start.replace(day=1) + timedelta(days=32)).replace(day=start.day)
    }

    payments = []
    rate = interest * Decimal(period_length)
    repayment = rate * amount / Decimal(1 - math.pow(1 + rate, -payments_count))
    for _ in range(payments_count):
        interest_payment = amount * rate
        principal_payment = repayment - interest_payment
        payment_date = period_delta_map[period_type](start_date, period_number)
        payments.append(Payment(
            loan=loan,
            payment_date=payment_date,
            principal_payment=principal_payment,
            interest_payment=interest_payment,
        ))
        start_date = payment_date
        amount -= principal_payment

    Payment.objects.bulk_create(payments)


def recalculate_payments(payment):
    loan = payment.loan
    payments = loan.payments.filter(payment_date__gt=payment.payment_date).order_by('payment_date')
    payed_principal = loan.payments.filter(
        payment_date__lt=payment.payment_date).aggregate(
        payed_principal=Coalesce(Sum('principal_payment'), Decimal(0)))['payed_principal']
    principal = loan.amount - payed_principal

    _, _, period_length = parse_period(loan.periodicity)
    interest = loan.interest_rate * Decimal(period_length)
    if payment.principal_payment != 0:
        interest_amount = principal * interest
        payment.interest_payment = interest_amount
        payment.save(update_fields=['interest_payment'])
        principal -= payment.principal_payment
    remaining_payments = payments.count()
    emi = (interest * principal) / (1 - (1 + interest) ** -remaining_payments)
    updates = []
    for next_payment in payments:
        interest_amount = principal * interest
        principal_amount = emi - interest_amount
        next_payment.interest_payment = interest_amount
        next_payment.principal_payment = principal_amount
        updates.append(next_payment)
        principal -= principal_amount
    Payment.objects.bulk_update(updates, ['interest_payment', 'principal_payment'])
