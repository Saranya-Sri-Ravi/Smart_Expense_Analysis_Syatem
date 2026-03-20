from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import ExpenseForm, IncomeForm
from django.db.models import Sum
from .models import Income, Expense

# 🔥 DRF IMPORTS
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .serializers import ExpenseSerializer, IncomeSerializer


# =========================
# EXISTING VIEWS (NO CHANGE)
# =========================

@login_required
def add_income(request):
    if request.method == "POST":
        form = IncomeForm(request.POST)
        if form.is_valid():
            income = form.save(commit=False)
            income.user = request.user
            income.save()
            return redirect("dashboard")
    else:
        form = IncomeForm()

    return render(request, "add_income.html", {"form": form})


@login_required
def add_expense(request):
    if request.method == "POST":
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()
            return redirect("dashboard")
    else:
        form = ExpenseForm()

    return render(request, "add_expense.html", {"form": form})


@login_required
def expense_list(request):
    expenses = Expense.objects.filter(user=request.user).order_by("-date")
    return render(request, "expense_list.html", {"expenses": expenses})


# =========================
# 🔥 API VIEWS
# =========================

@api_view(['GET'])
def get_expenses(request):
    expenses = Expense.objects.filter(user=request.user)
    serializer = ExpenseSerializer(expenses, many=True)
    return Response(serializer.data)


@api_view(['POST'])
def create_expense(request):
    serializer = ExpenseSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_income(request):
    income = Income.objects.filter(user=request.user)
    serializer = IncomeSerializer(income, many=True)
    return Response(serializer.data)


@api_view(['POST'])
def create_income(request):
    serializer = IncomeSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data)

    return Response(serializer.errors)