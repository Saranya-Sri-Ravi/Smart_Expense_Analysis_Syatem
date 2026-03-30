import requests


class MCPClient:

    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {
            "Authorization": token,
            "Content-Type": "application/json"
        }

    def call_tool(self, tool, params=None):
        if params is None:
            params = {}

        response = requests.post(
            f"{self.base_url}/tool/",
            json={
                "tool": tool,
                "params": params
            },
            headers=self.headers
        )

        return response.json()

    # -------------------------
    # HELPER METHODS
    # -------------------------
    def get_months(self):
        return self.call_tool("get_months")

    def get_month_summary(self, month):
        return self.call_tool("month_summary", {"month": month})

    def get_all_data(self):
        return self.call_tool("get_data")