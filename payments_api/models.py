from django.db import models

# Create your models here.


class Loan(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    loan_start_date = models.DateField()
    number_of_payments = models.IntegerField()
    periodicity = models.CharField(max_length=10)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=4)


class Payment(models.Model):
    payment_date = models.DateField()
    principal_payment = models.DecimalField(max_digits=10, decimal_places=2)
    interest_payment = models.DecimalField(max_digits=10, decimal_places=2)

    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='payments')

