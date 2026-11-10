"""
Employee Leave Management (ELM) — API Views Layer.

Wires endpoint actions to services/selectors with permissions and scopes declared by the approved blueprint.
No business logic resides here; all validation, routing, and state transitions are handled in services or domain layers.
Identity references are integer user_id values. Cross-module data access uses public contracts from modules.leave.contracts.
"""
from __future__ import annotations

from typing import Any, Optional

from django.conf import settings
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api import csrf
from core.api.exceptions import BadRequestError, ConflictError, NotFoundError
from fusion_auth.client import IamUnavailable
from fusion_auth.permissions import HasModuleGrant, HasPermission

from modules.directory import contracts as directory
from modules.leave.api import serializers as s
from modules.leave.api.permissions import ScopedCollection
from modules.leave.authentication import (
    COOKIE_NAME as EMPLOYEE_COOKIE,
)
from modules.leave.authentication import (
    COOKIE_PATH as EMPLOYEE_COOKIE_PATH,
)
from modules.leave.authentication import EmployeeAuthentication
from modules.leave.models import (
    LeaveRequest,
    WorkflowTask,
    RequestAction,
    LeaveAccount,
    SubstituteAssignment,
    LeavePolicyConfig,
    HierarchyConfig,
    HolidayRHCalendar,
    ResumptionRecord,
    OfflineSanctionRecord,
)
from modules.leave.selectors import scoping
from modules.leave.services import (
    leave_request as leave_service,
    workflow_task as task_service,
    request_action as action_service,
    leave_account as account_service,
    substitute_assignment as sub_service,
    policy_config as policy_service,
    hierarchy_config as hierarchy_service,
    holiday_rh_calendar as calendar_service,
    resumption_record as resumption_service,
    offline_sanction_record as offline_service,
)
from modules.leave.contracts import EmployeeDTO

MODULE = HasModuleGrant("leave_cell")

P_VIEW_REQUESTS = "leave_cell.leave_request.view"
P_MANAGE_REQUESTS = "leave_cell.leave_request.manage"
P_VIEW_SELF_REQUESTS = "leave_cell.leave_request.view_self"
P_MANAGE_SUBSTITUTES = "leave_cell.substitute.manage"
P_MANAGE_POLICY = "leave_cell.policy.manage"
P_MANAGE_HIERARCHY = "leave_cell.hierarchy.manage"
P_MANAGE_CALENDAR = "leave_cell.calendar.manage"
P_VIEW_BALANCES = "leave_cell.balance.view"
P_MANAGE_RESUMPTION = "leave_cell.resumption.manage"
P_MANAGE_OFFLINE = "leave_cell.offline.manage"
P_MANAGE_SLA = "leave_cell.sla.manage"

def _actor(request):
    return getattr(request, "principal", None)

def _int_param(params, name):
    """A non-integer filter is a 400, not a ValueError deep in the ORM."""
    raw = params.get(name)
    if raw in (None, ""):
        return None
    try:
        return int(raw)
    except (TypeError, ValueError) as exc:
        raise BadRequestError(f"{name} must be a number.", code="invalid_filter") from exc

def _client_ip(request):
    """The hop our proxy added, not the first one the client claimed."""
    from rest_framework.settings import api_settings

    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    hops = api_settings.NUM_PROXIES or 0
    if forwarded and hops:
        addrs = forwarded.split(",")
        return addrs[-1].strip()
    return ""

class LeaveRequestView(generics.ListCreateAPIView):
    """List and create leave requests.

Validates transport layer constraints (dates, non-empty fields).
Business rules (balance checks, overlap detection) are enforced in services."""

    permission_classes = [HasPermission(P_MANAGE_REQUESTS)]
    serializer_class = s.LeaveRequestSerializer
    queryset = LeaveRequest.objects.none()

    @extend_schema(
        summary="List or create leave requests",
        description="Retrieve all leave requests or create a new one. Requires manage permission.",
        responses={201: s.LeaveRequestSerializer},
    )
    def get_queryset(self):
        """Filter queryset based on user scope."""
        return scoping.get_leave_requests(_actor(self.request))

    def perform_create(self, serializer):
        """Create a new leave request via service layer."""
        instance = self.serializer.save()
        # Service handles validation, state transition to 'Draft' or 'Awaiting Substitute Response'
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class LeaveRequestDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update (pre-approval), and delete leave requests.

Updates are restricted to pre-approval states; post-approval requires cancellation workflow."""

    permission_classes = [HasPermission(P_VIEW_SELF_REQUESTS)]
    serializer_class = s.LeaveRequestSerializer

    def get_queryset(self):
        """Filter to user's own requests."""
        return scoping.get_own_leave_requests(_actor(self.request))

    @extend_schema(
        summary="Retrieve, update (pre-approval), or delete a leave request",
        description="Get details of a specific request. Update is allowed only before final approval. Delete triggers cancellation workflow.",
        responses={200: s.LeaveRequestSerializer},
    )
    def get_object(self):
        """Retrieve the specific leave request."""
        return scoping.get_own_leave_request(_actor(self.request), self.kwargs["pk"])

    def update(self, request, *args, **kwargs):
        """Update request details only if not yet approved."""
        instance = self.get_object()
        # Service checks state and applies updates
        serializer = self.serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Delete (cancel) the leave request."""
        instance = self.get_object()
        # Service handles cancellation workflow and state transition
        task_service.cancel_leave_request(instance.id)
        return Response(status=status.HTTP_204_NO_CONTENT)

class SubstituteAssignmentView(generics.ListCreateAPIView):
    """Manage substitute assignments for pending leave requests."""

    permission_classes = [HasPermission(P_MANAGE_SUBSTITUTES)]
    serializer_class = s.SubstituteAssignmentSerializer

    @extend_schema(
        summary="List or create substitute assignments",
        description="Retrieve assigned substitutes or nominate a new one for a pending request.",
        responses={201: s.SubstituteAssignmentSerializer},
    )
    def get_queryset(self):
        """Filter to active substitute requests."""
        return scoping.get_active_substitute_requests(_actor(self.request))

    def perform_create(self, serializer):
        """Nominate a substitute via service layer."""
        instance = self.serializer.save()
        # Service handles eligibility check and state transition to 'Awaiting Substitute Response'
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class LeavePolicyConfigView(generics.RetrieveUpdateAPIView):
    """Retrieve and update current leave policy configuration.

No draft/publish/effective-version lifecycle; uses current configured values."""

    permission_classes = [HasPermission(P_MANAGE_POLICY)]
    serializer_class = s.LeavePolicyConfigSerializer

    @extend_schema(
        summary="Retrieve or update leave policy configuration",
        description="Get current leave entitlements and parameters. Update applies immediately.",
        responses={200: s.LeavePolicyConfigSerializer},
    )
    def get_object(self):
        """Retrieve the active policy config."""
        return scoping.get_active_leave_policy_config()

    def update(self, request, *args, **kwargs):
        """Update current policy configuration."""
        instance = self.get_object()
        serializer = self.serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        return super().update(request, *args, **kwargs)

class HierarchyConfigView(generics.RetrieveUpdateAPIView):
    """Retrieve and update organizational hierarchy configuration."""

    permission_classes = [HasPermission(P_MANAGE_HIERARCHY)]
    serializer_class = s.HierarchyConfigSerializer

    @extend_schema(
        summary="Retrieve or update hierarchy configuration",
        description="Get current routing facts and optional Establishment step. Update applies immediately.",
        responses={200: s.HierarchyConfigSerializer},
    )
    def get_object(self):
        """Retrieve the active hierarchy config."""
        return scoping.get_active_hierarchy_config()

    def update(self, request, *args, **kwargs):
        """Update current hierarchy configuration."""
        instance = self.get_object()
        serializer = self.serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        return super().update(request, *args, **kwargs)

class HolidayRHCalendarView(generics.RetrieveUpdateAPIView):
    """Retrieve and publish holiday/RH calendar.

Only currently effective published calendar is used for date/RH validation."""

    permission_classes = [HasPermission(P_MANAGE_CALENDAR)]
    serializer_class = s.HolidayRHCalendarSerializer

    @extend_schema(
        summary="Retrieve or publish holiday/RH calendar",
        description="Get current effective calendar. Publish updates the active calendar.",
        responses={200: s.HolidayRHCalendarSerializer},
    )
    def get_object(self):
        """Retrieve the currently effective published calendar."""
        return scoping.get_effective_holiday_rh_calendar()

    def update(self, request, *args, **kwargs):
        """Publish new holiday/RH calendar."""
        instance = self.get_object()
        serializer = self.serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        return super().update(request, *args, **kwargs)

class LeaveBalanceView(generics.RetrieveAPIView):
    """Retrieve employee leave balances and history."""

    permission_classes = [HasPermission(P_VIEW_BALANCES)]
    serializer_class = s.LeaveBalanceSerializer

    @extend_schema(
        summary="Retrieve leave balances and history",
        description="Get current balance and transaction history for the authenticated user.",
        responses={200: s.LeaveBalanceSerializer},
    )
    def get_object(self):
        """Retrieve balances for the authenticated user."""
        return scoping.get_user_leave_balances(_actor(self.request))

class ResumptionRecordView(generics.ListCreateAPIView):
    """Manage resumption records for ongoing leave (EL/CL/VL)."""

    permission_classes = [HasPermission(P_MANAGE_RESUMPTION)]
    serializer_class = s.ResumptionRecordSerializer

    @extend_schema(
        summary="List or create resumption records",
        description="Submit actual return date for ongoing leave. Requires review by applicable authority.",
        responses={201: s.ResumptionRecordSerializer},
    )
    def get_queryset(self):
        """Filter to user's active resumption requests."""
        return scoping.get_active_resumption_requests(_actor(self.request))

    def perform_create(self, serializer):
        """Submit resumption via service layer."""
        instance = self.serializer.save()
        # Service handles state transition to 'Resumption Review Pending'
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class OfflineSanctionRecordView(generics.RetrieveUpdateAPIView):
    """Synchronize already-sanctioned offline leave."""

    permission_classes = [HasPermission(P_MANAGE_OFFLINE)]
    serializer_class = s.OfflineSanctionRecordSerializer

    @extend_schema(
        summary="Retrieve or synchronize offline-sanctioned leave",
        description="Record an already-authorized paper/offline leave to sync with the system.",
        responses={200: s.OfflineSanctionRecordSerializer},
    )
    def get_object(self):
        """Retrieve the offline sanction record."""
        return scoping.get_offline_sanction_record(_actor(self.request), self.kwargs["pk"])

    def update(self, request, *args, **kwargs):
        """Synchronize offline leave record."""
        instance = self.get_object()
        serializer = self.serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        return super().update(request, *args, **kwargs)

class SLAConfigView(generics.RetrieveUpdateAPIView):
    """Configure workflow SLA thresholds."""

    permission_classes = [HasPermission(P_MANAGE_SLA)]
    serializer_class = s.SLAConfigSerializer

    @extend_schema(
        summary="Retrieve or configure SLA thresholds",
        description="Set reminder and escalation thresholds for pending tasks.",
        responses={200: s.SLAConfigSerializer},
    )
    def get_object(self):
        """Retrieve the active SLA config."""
        return scoping.get_active_sla_config()

    def update(self, request, *args, **kwargs):
        """Update SLA configuration."""
        instance = self.get_object()
        serializer = self.serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        return super().update(request, *args, **kwargs)

class WorkflowTaskView(generics.ListAPIView):
    """List actionable workflow tasks for the authenticated user."""

    permission_classes = [HasPermission(P_VIEW_SELF_REQUESTS)]
    serializer_class = s.WorkflowTaskSerializer

    @extend_schema(
        summary="List actionable workflow tasks",
        description="Retrieve pending or assigned tasks relevant to the authenticated user.",
        responses={200: s.WorkflowTaskSerializer},
    )
    def get_queryset(self):
        """Filter to user's active tasks."""
        return scoping.get_user_workflow_tasks(_actor(self.request))

class RequestActionView(generics.ListAPIView):
    """List action history for a leave request."""

    permission_classes = [HasPermission(P_VIEW_SELF_REQUESTS)]
    serializer_class = s.RequestActionSerializer

    @extend_schema(
        summary="List action history for a leave request",
        description="Retrieve append-oriented action history for user-visible status.",
        responses={200: s.RequestActionSerializer},
    )
    def get_queryset(self):
        """Filter to actions for the specific request."""
        return scoping.get_request_action_history(_actor(self.request), self.kwargs["pk"])
