from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from django.shortcuts import get_object_or_404
from datetime import date
from math import pow
from .models import Customer, Loan
from .serializers import (
    CustomerRegisterSerializer,
    CheckEligibilitySerializer,
    CreateLoanSerializer,
)

def round_to_nearest_lakh(amount):
    return int(round(amount / 100000.0) * 100000)

def calculate_emi(p, annual_rate, months):
    r = (annual_rate / 12) / 100
    if r == 0:
        return round(p / months, 2)
    return round(p * r * (1 + r) ** months / ((1 + r) ** months - 1), 2)

def calculate_credit_score(customer):
    qs = Loan.objects.filter(customer=customer)
    n = qs.count()
    if n == 0:
        return 80
    on_time = qs.filter(emis_paid_on_time__gte=1).count()
    score = int((on_time / n) * 100)
    active_sum = sum(l.loan_amount for l in qs.filter(is_active=True))
    if active_sum > customer.approved_limit:
        return 0
    return score

@api_view(['POST'])
def register_customer(request):
    data = CustomerRegisterSerializer(data=request.data)
    if not data.is_valid():
        return Response(data.errors, status=status.HTTP_400_BAD_REQUEST)
    info = data.validated_data
    limit = round_to_nearest_lakh(36 * info['monthly_income'])
    c = Customer.objects.create(
        first_name=info['first_name'],
        last_name=info['last_name'],
        age=info['age'],
        phone_number=info['phone_number'],
        monthly_salary=info['monthly_income'],
        approved_limit=limit,
        current_debt=0,
    )
    return Response({
        "customer_id": c.customer_id,
        "name": f"{c.first_name} {c.last_name}",
        "age": c.age,
        "monthly_income": c.monthly_salary,
        "approved_limit": c.approved_limit,
        "phone_number": c.phone_number
    }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
def check_eligibility(request):
    s = CheckEligibilitySerializer(data=request.data)
    if not s.is_valid():
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)
    d = s.validated_data
    c = get_object_or_404(Customer, customer_id=d['customer_id'])
    score = calculate_credit_score(c)
    current_emis = sum(l.monthly_payment for l in Loan.objects.filter(customer=c, is_active=True))
    corrected_rate = d['interest_rate']
    approved = True
    if score > 50:
        pass
    elif 30 < score <= 50:
        corrected_rate = max(corrected_rate, 12.0)
    elif 10 < score <= 30:
        corrected_rate = max(corrected_rate, 16.0)
    else:
        approved = False
    if current_emis > 0.5 * c.monthly_salary:
        approved = False
    emi = calculate_emi(d['loan_amount'], corrected_rate, d['tenure'])
    return Response({
        "customer_id": c.customer_id,
        "approval": approved,
        "interest_rate": d['interest_rate'],
        "corrected_interest_rate": corrected_rate,
        "tenure": d['tenure'],
        "monthly_installment": emi,
        "credit_score": score
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
def create_loan(request):
    s = CreateLoanSerializer(data=request.data)
    if not s.is_valid():
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)
    d = s.validated_data
    c = get_object_or_404(Customer, customer_id=d['customer_id'])
    score = calculate_credit_score(c)
    corrected_rate = d['interest_rate']
    approved = True
    if score > 50:
        pass
    elif 30 < score <= 50:
        corrected_rate = max(corrected_rate, 12.0)
    elif 10 < score <= 30:
        corrected_rate = max(corrected_rate, 16.0)
    else:
        approved = False
    if not approved:
        return Response({
            "loan_id": None,
            "customer_id": c.customer_id,
            "loan_approved": False,
            "message": "Loan not approved due to low credit score."
        }, status=status.HTTP_200_OK)
    emi = calculate_emi(d['loan_amount'], corrected_rate, d['tenure'])
    loan = Loan.objects.create(
        customer=c,
        loan_amount=d['loan_amount'],
        tenure=d['tenure'],
        interest_rate=corrected_rate,
        monthly_payment=emi,
        emis_paid_on_time=0,
        start_date=date.today(),
        end_date=None,
        is_active=True
    )
    c.current_debt += d['loan_amount']
    c.save()
    return Response({
        "loan_id": loan.loan_id,
        "customer_id": c.customer_id,
        "loan_approved": True,
        "message": "Loan created successfully.",
        "monthly_installment": emi
    }, status=status.HTTP_201_CREATED)

@api_view(['GET'])
def view_loan(request, loan_id):
    loan = get_object_or_404(Loan, loan_id=loan_id)
    c = loan.customer
    return Response({
        "loan_id": loan.loan_id,
        "customer": {
            "id": c.customer_id,
            "first_name": c.first_name,
            "last_name": c.last_name,
            "phone_number": c.phone_number,
            "age": c.age
        },
        "loan_amount": loan.loan_amount,
        "interest_rate": loan.interest_rate,
        "monthly_installment": loan.monthly_payment,
        "tenure": loan.tenure
    })

@api_view(['GET'])
def view_loans_by_customer(request, customer_id):
    c = get_object_or_404(Customer, customer_id=customer_id)
    loans = Loan.objects.filter(customer=c, is_active=True)
    data = []
    for l in loans:
        data.append({
            "loan_id": l.loan_id,
            "loan_amount": l.loan_amount,
            "interest_rate": l.interest_rate,
            "monthly_installment": l.monthly_payment,
            "repayments_left": l.tenure - l.emis_paid_on_time
        })
    return Response(data, status=status.HTTP_200_OK)
