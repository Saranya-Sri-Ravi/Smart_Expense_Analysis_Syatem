from django.urls import path
from .views import mcp_tool

urlpatterns = [
    path("tool/", mcp_tool),
]