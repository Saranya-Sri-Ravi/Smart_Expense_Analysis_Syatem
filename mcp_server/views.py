from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import requests

BASE_URL = "http://localhost:8000/expense"


def get_headers(request):
    return {"Authorization": request.headers.get("Authorization")}


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mcp_tool(request):
    tool = request.data.get("tool")
    params = request.data.get("params", {})

    headers = get_headers(request)

    # =========================
    # TOOL: GET MONTHS
    # =========================
    if tool == "get_months":

        exp = requests.get(f"{BASE_URL}/api/expenses/", headers=headers).json()
        inc = requests.get(f"{BASE_URL}/api/income/", headers=headers).json()

        dates = [i["date"] for i in inc] + [e["date"] for e in exp]
        months = sorted(set([d[:7] for d in dates]))

        return Response({"months": months})

    # =========================
    # TOOL: MONTH SUMMARY
    # =========================
    elif tool == "month_summary":

        month = params.get("month")

        exp = requests.get(f"{BASE_URL}/api/expenses/", headers=headers).json()
        inc = requests.get(f"{BASE_URL}/api/income/", headers=headers).json()

        income_sum = sum(float(i["amount"]) for i in inc if i["date"].startswith(month))
        expense_sum = sum(float(e["amount"]) for e in exp if e["date"].startswith(month))

        return Response({
            "month": month,
            "income": income_sum,
            "expense": expense_sum,
            "balance": income_sum - expense_sum
        })

    # =========================
    # TOOL: GET ALL DATA
    # =========================
    elif tool == "get_data":

        exp = requests.get(f"{BASE_URL}/api/expenses/", headers=headers)
        inc = requests.get(f"{BASE_URL}/api/income/", headers=headers)

        return Response({
            "expenses": exp.json(),
            "incomes": inc.json()
        })

    return Response({"error": "Invalid tool"}, status=400)