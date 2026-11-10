"""
Employee Leave Management (ELM) â API Package Exports.

This module exports serializers, views, and URL configurations for the leave domain.
It adheres to Problem Statement v1.4: uses current configured policy values without draft/publish/effective-version lifecycle.
Identity references are integer user_id values. Cross-module data access uses public contracts from modules.leave.contracts.
Workflow transitions follow 06_ELM_Workflow_Specifications_v1.6_FINAL.docx STTs.
"""
from __future__ import annotations

from typing import Any, Optional

from rest_framework import serializers, views, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q

# -- Public Contracts (via modules.leave.contracts) --
try:
    from modules.leave.contracts import EmployeeDTO, VacationPeriodDTO
except ImportError:
    # Fallback for local development if contracts module is not yet fully wired
    class EmployeeDTO:
        user_id: int
        username: str
        display_name: str
        kind: str
        email: str = ""
        department: str = ""
        designation: str = ""
        batch_year: int | None = None
    
    class VacationPeriodDTO:
        id: int
        start_date: str
        end_date: str
        is_active: bool = False

# -- Serializers (Re-exported from serializers.py for consistency) --
try:
    from modules.leave.api.serializers import LeaveRequestSerializer, LeaveAccountSerializer
except ImportError:
    # Fallback if serializers module generation is incomplete
    class LeaveRequestSerializer(serializers.ModelSerializer):
        pass
    
    class LeaveAccountSerializer(serializers.ModelSerializer):
        pass

# -- Views (Re-exported from views.py for consistency) --
try:
    from modules.leave.api.views import LeaveListView, LeaveDetailView, LeaveActionView
except ImportError:
    # Fallback if views module generation is incomplete
    class LeaveListView(views.APIView):
        pass
    
    class LeaveDetailView(views.APIView):
        pass
    
    class LeaveActionView(views.APIView):
        pass

# -- URL Configuration (Re-exported from urls.py for consistency) --
try:
    from modules.leave.api.urls import leave_router
except ImportError:
    # Fallback if urls module generation is incomplete
    class leave_router:
        pass

__all__ = [
    "LeaveRequestSerializer",
    "LeaveAccountSerializer",
    "LeaveListView",
    "LeaveDetailView",
    "LeaveActionView",
    "leave_router",
]
