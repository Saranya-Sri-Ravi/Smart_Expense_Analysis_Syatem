from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.db.models.functions import ExtractMonth
from expenses.models import Expense, Income
from datetime import date

# ✅ ENV SETUP
from dotenv import load_dotenv
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # points to expense_tracker folder

load_dotenv(os.path.join(BASE_DIR, ".env"))


@login_required
def dashboard(request):

    print("DASHBOARD VIEW CALLED")

    user = request.user

    # =========================
    # FILTER
    # =========================
    month = int(request.GET.get("month", date.today().month))
    year = int(request.GET.get("year", date.today().year))

    expenses = Expense.objects.filter(user=user, date__month=month, date__year=year)
    incomes = Income.objects.filter(user=user, date__month=month, date__year=year)

    # =========================
    # TOTALS
    # =========================
    total_expense = expenses.aggregate(Sum("amount"))["amount__sum"] or 0
    total_income = incomes.aggregate(Sum("amount"))["amount__sum"] or 0
    balance = total_income - total_expense

    # =========================
    # CATEGORY CHART
    # =========================
    category_data = expenses.values("category__name").annotate(total=Sum("amount"))
    categories = [item["category__name"] for item in category_data]
    amounts = [float(item["total"]) for item in category_data]

    # =========================
    # MONTHLY TREND (ALL DATA)
    # =========================
    monthly_data = (
        Expense.objects.filter(user=user)
        .annotate(month=ExtractMonth("date"))
        .values("month")
        .annotate(total=Sum("amount"))
        .order_by("month")
    )

    month_map = {
        1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr",
        5: "May", 6: "Jun", 7: "Jul", 8: "Aug",
        9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
    }

    months = [month_map[item["month"]] for item in monthly_data]
    monthly_totals = [float(item["total"]) for item in monthly_data]

    # =========================
    # RECENT EXPENSES
    # =========================
    recent_expenses = expenses.order_by("-date")[:5]

    # =========================
    # 🤖 AI RECOMMENDATION (GROQ)
    # =========================

    api_key = os.getenv("GROQ_API_KEY")

    print("API KEY:", os.getenv("GROQ_API_KEY"))

    if api_key:
        try:
            from groq import Groq

            client = Groq(api_key=api_key)

            prompt = f"""

            All amounts are in Indian Rupees (₹).
            
            Monthly Income: {total_income}
            Monthly Expense: {total_expense}
            Balance: {balance}

            Give 3 short financial suggestions.
            """

            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            raw_text = response.choices[0].message.content

            # Convert to list
            points = raw_text.split("\n")

            # Remove empty lines
            points = [p.strip() for p in points if p.strip()]

            # Convert to HTML list
            formatted = "<ul>"

            for p in points:
                formatted += f"<li>{p}</li>"

            formatted += "</ul>"

            ai_recommendations = formatted
            

        except Exception as e:
            print("AI ERROR:", e)
            ai_recommendations = "⚠ AI service unavailable"
    else:
        ai_recommendations = "⚠ API key not found"

    # =========================
    # CONTEXT
    # =========================
    context = {
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": balance,

        "categories": categories,
        "amounts": amounts,

        "months": months,
        "monthly_totals": monthly_totals,

        "recent_expenses": recent_expenses,

        "selected_month": month,
        "selected_year": year,

        "ai_recommendations": ai_recommendations
    }

    return render(request, "dashboard.html", context)