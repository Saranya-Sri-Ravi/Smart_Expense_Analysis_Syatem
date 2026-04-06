from django.db import models
from django.conf import settings

DEFAULT_CATEGORIES = [
    "Food",
    "Travel",
    "Shopping",
    "Bills",
    "Health",
    "Entertainment",
    "Other"
]

class Category(models.Model):

    name = models.CharField(max_length=100)

    class Meta:
        unique_together = ['name']  
        ordering = ['name']                  

    def __str__(self):
        return self.name


class Income(models.Model):

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    source = models.CharField(max_length=200)
    date = models.DateField()

    def __str__(self):
        return f"{self.user} - {self.amount}"


class Expense(models.Model):

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    date = models.DateField()

    def __str__(self):
        return f"{self.category} - {self.amount}"