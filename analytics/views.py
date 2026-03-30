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

BASE_DIR = Path(__file__).resolve().parent.parent

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

    # 🔥 FIX: Convert Decimal → float
    total_income = float(total_income)
    total_expense = float(total_expense)
    balance = float(balance)

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
    # 🤖 SMART AI RECOMMENDATION
    # =========================

    api_key = os.getenv("GROQ_API_KEY")
    print("API KEY:", api_key)

    if api_key:
        try:
            from groq import Groq

            client = Groq(api_key=api_key)

            # 🧠 DATA PREPARATION

            # Top category
            if amounts:
                max_index = amounts.index(max(amounts))
                top_category = categories[max_index]
                top_amount = amounts[max_index]
            else:
                top_category = "N/A"
                top_amount = 0

            # Trend detection
            if len(monthly_totals) >= 2:
                if monthly_totals[-1] > monthly_totals[-2]:
                    trend = "increasing"
                else:
                    trend = "decreasing"
            else:
                trend = "stable"

            # Rule-based insights
            insights = []

            if total_expense > total_income:
                insights.append("Spending exceeds income")

            if balance < 0:
                insights.append("Negative balance")

            if total_income > 0 and total_expense > 0.8 * total_income:
                insights.append("Spending is close to income limit")

            # Recent expenses data
            recent_data = list(
                recent_expenses.values("category__name", "amount", "date")
            )

            # 💡 PROMPT
            prompt = f"""
You are an intelligent financial advisor.

All amounts are in Indian Rupees (₹).

Financial Summary:
- Monthly Income: {total_income}
- Monthly Expense: {total_expense}
- Balance: {balance}

Top Spending Category:
- {top_category}: ₹{top_amount}

Spending Trend:
- {trend}

Category Breakdown:
{list(zip(categories, amounts))}

Recent Expenses:
{recent_data}

System Insights:
{insights}

Task:
Give exactly 3 personalized financial recommendations.

Rules:
- Must be based on the given data
- Mention category names where relevant
- Include a short reason
- Keep each point concise (1–2 lines)
- Avoid generic advice
"""

            print("Calling Groq API...")

            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            raw_text = response.choices[0].message.content
            print("RAW AI RESPONSE:", raw_text)

            # 🧹 CLEAN OUTPUT
            points = []
            for p in raw_text.split("\n"):
                p = p.replace("-", "").replace("*", "").strip()
                if p:
                    points.append(p)

            formatted = "<ul>"
            for p in points[:3]:
                formatted += f"<li>{p}</li>"
            formatted += "</ul>"

            ai_recommendations = formatted

        except Exception as e:
            import traceback
            traceback.print_exc()
            ai_recommendations = f"⚠ AI ERROR: {str(e)}"

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