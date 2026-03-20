from django import forms
from .models import Expense, Income, Category



class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ["category", "amount", "description", "date"]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            self.fields['category'].queryset = Category.objects.filter(user=user)

class IncomeForm(forms.ModelForm):

    class Meta:
        model = Income
        fields = ["amount", "date"]