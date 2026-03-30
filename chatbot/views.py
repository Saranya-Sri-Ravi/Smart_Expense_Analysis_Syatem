from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

import os
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
            return Response({"reply": "❌ Authentication missing. Please login again."})

        mcp = MCPClient(
            base_url="http://localhost:8000/mcp",
            token=auth
        )

        msg = message.lower()

        # =========================
        # MAIN MENU
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
        # SHOW MONTHS
        # =========================
        if "details" in msg:
            months_data = mcp.get_months()
            months = months_data.get("months", [])

            if not months:
                return Response({"reply": "No data available"})

            buttons = ""
            for m in months:
                buttons += f"<button onclick=\"sendQuickMessage('{m}')\">{m}</button>"

            return Response({
                "reply": f"<p>Select a month:</p><div class='menu'>{buttons}</div>"
            })

        # =========================
        # MONTH SUMMARY
        # =========================
        if "-" in msg:
            res = mcp.get_month_summary(msg)

            return Response({
                "reply": f"""
<div class="card">
<p><b>Month:</b> {res.get('month')}</p>
<p><b>Income:</b> ₹{res.get('income')}</p>
<p><b>Expense:</b> ₹{res.get('expense')}</p>
<p><b>Balance:</b> ₹{res.get('balance')}</p>
</div>
"""
            })

        # =========================
        # TOTAL SPENDING
        # =========================
        if "total spending" in msg:
            data = mcp.get_all_data()
            total = sum(float(e["amount"]) for e in data.get("expenses", []))

            return Response({
                "reply": f"<div class='card'>💰 Total Spending: ₹{total}</div>"
            })

        # =========================
        # FINANCIAL ADVICE (FORMATTED)
        # =========================
        if "advice" in msg:
            load_dotenv()
            api_key = os.getenv("GROQ_API_KEY")

            client = Groq(api_key=api_key)

            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {
                        "role": "system",
                        "content": "Give 5 short financial tips as simple bullet points without numbering."
                    },
                    {
                        "role": "user",
                        "content": "Give financial advice"
                    }
                ]
            )

            advice_text = response.choices[0].message.content

            # Convert to HTML bullet list
            tips = advice_text.split("\n")

            formatted_tips = ""
            for tip in tips:
                tip = tip.strip().replace("*", "").replace("-", "")
                if tip:
                    formatted_tips += f"<li>{tip}</li>"

            return Response({
                "reply": f"""
<div class="card">
<h4>💡 Financial Tips</h4>
<ul>
{formatted_tips}
</ul>
</div>
"""
            })

        return Response({"reply": "Type 'hi' to start"})

    except Exception as e:
        print("ERROR:", str(e))
        return Response({"reply": "❌ Server error occurred"})