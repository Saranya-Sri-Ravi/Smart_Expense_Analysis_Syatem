from django.urls import path
from .views import (
    add_income, add_expense, expense_list,
    get_expenses, create_expense,
    get_income, create_income
)

urlpatterns = [

    # HTML
    path('add-income/', add_income),
    path('add-expense/', add_expense),
    path('expenses/', expense_list),

    # API
    path('api/expenses/', get_expenses),
    path('api/expenses/add/', create_expense),

    path('api/income/', get_income),
    path('api/income/add/', create_income),
]