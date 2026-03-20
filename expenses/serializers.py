from rest_framework import serializers
from .models import Expense, Income, Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


class ExpenseSerializer(serializers.ModelSerializer):

    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Expense
        fields = [
            'id',
            'amount',
            'description',
            'date',
            'category',
            'category_name'
        ]


class IncomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Income
        fields = [
            'id',
            'amount',
            'source',
            'date'
        ]