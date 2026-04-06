from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

import os
import re
from dotenv import load_dotenv
from groq import Groq

from .mcp_client import MCPClient

@login_required
@ensure_csrf_cookie
def chat_ui(request):
    return render(request, "chat.html")


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chatbot_api(request):

    try:
        message = request.data.get("message", "").strip()

        if not message:
            return Response({"reply": "Please enter a message"})

        auth = request.headers.get("Authorization")

        if not auth:
            return Response({"reply": "❌ Authentication missing"})

        # =========================
        # SESSION MEMORY (LIGHT)
        # =========================
        last_month = request.session.get("last_month")

        mcp = MCPClient(
            base_url="http://localhost:8000/mcp",
            token=auth
        )

        msg = message.lower()

        # =========================
        # 🟢 MENU (ALWAYS SAFE UI)
        # =========================
        if msg in ["hi", "hello", "start", "menu"]:
            return Response({
                "reply": """
<p>Select an option:</p>
<div class="menu">
<button onclick="sendQuickMessage('details')">📊 Monthly Details</button>
<button onclick="sendQuickMessage('total spending')">💰 Total Spending</button>
<button onclick="sendQuickMessage('advice')">🤖 Financial Advice</button>
</div>
"""
            })

        # =========================
        # 🟢 SHOW MONTH BUTTONS
        # =========================
        if any(word in msg for word in ["detail", "expense", "summary", "report"]):

            months = mcp.get_months().get("months", [])

            buttons = "".join([
                f"<button onclick=\"sendQuickMessage('{m}')\">{m}</button>"
                for m in months
            ])

            return Response({
                "reply": f"<p>Select a month:</p><div class='menu'>{buttons}</div>"
            })

        # =========================
        # 🟢 MONTH SELECTED
        # =========================
        month_match = re.search(r"\d{4}-\d{2}", msg)

        if month_match:
            month = month_match.group()

            request.session["last_month"] = month  # ✅ store context

            res = mcp.get_month_summary(month)

            return Response({
                "reply": f"""
<div class="card">
<p><b>Month:</b> {res.get('month')}</p>
<p><b>Income:</b> ₹{res.get('income')}</p>
<p><b>Expense:</b> ₹{res.get('expense')}</p>
<p><b>Balance:</b> ₹{res.get('balance')}</p>
</div>

<div class="menu">
<button onclick="sendQuickMessage('details')">🔄 Change Month</button>
<button onclick="sendQuickMessage('total spending')">💰 Total</button>
<button onclick="sendQuickMessage('advice')">🤖 Advice</button>
</div>
"""
            })

        # =========================
        # 🟢 TOTAL SPENDING
        # =========================
        if "total" in msg:

            data = mcp.get_all_data()
            expenses = data.get("expenses", [])

            total = sum(float(e["amount"]) for e in expenses)

            return Response({
                "reply": f"""
<div class="card">
💰 <b>Total Spending:</b> ₹{total}
</div>

<div class="menu">
<button onclick="sendQuickMessage('details')">📊 Monthly</button>
</div>
"""
            })

        # =========================
        # 🟢 CATEGORY ANALYSIS (REAL DATA ONLY)
        # =========================
        if "category" in msg or "highest" in msg:

            data = mcp.get_all_data()
            expenses = data.get("expenses", [])

            if last_month:
                expenses = [e for e in expenses if e["date"].startswith(last_month)]

            category_totals = {}

            for e in expenses:
                cat = e.get("category_name", "Other")
                category_totals[cat] = category_totals.get(cat, 0) + float(e["amount"])

            if not category_totals:
                return Response({"reply": "No data available"})

            max_cat = max(category_totals, key=category_totals.get)
            max_amt = category_totals[max_cat]

            return Response({
                "reply": f"""
<div class="card">
<b>Top Category:</b> {max_cat}<br>
<b>Amount:</b> ₹{max_amt}<br>
<b>Month:</b> {last_month if last_month else "All Time"}
</div>
"""
            })

        # =========================
        # 🤖 AI (STRICT MODE - NO FAKE DATA)
        # =========================
        if "advice" in msg:

            data = mcp.get_all_data()

            expenses = data.get("expenses", [])[:20]
            incomes = data.get("incomes", [])

            load_dotenv()
            api_key = os.getenv("GROQ_API_KEY")

            client = Groq(api_key=api_key)

            prompt = f"""
You are a financial assistant.

STRICT RULES:
- Use ONLY given data
- Do NOT create new numbers
- Give 3 short insights

Expenses:
{expenses}

Incomes:
{incomes}
"""

            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}]
            )

            text = response.choices[0].message.content

            tips = ""
            for line in text.split("\n"):
                if line.strip():
                    tips += f"<li>{line}</li>"

            return Response({
                "reply": f"""
<div class="card">
<h4>💡 Advice</h4>
<ul>{tips}</ul>
</div>
"""
            })

        # =========================
        # DEFAULT
        # =========================
        return Response({
            "reply": """
<p>I didn't understand.</p>
<div class="menu">
<button onclick="sendQuickMessage('details')">📊 Monthly Details</button>
</div>
"""
        })

    except Exception as e:
        print("ERROR:", str(e))
        return Response({"reply": "❌ Server error"})