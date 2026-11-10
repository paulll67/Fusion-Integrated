"""HTTP endpoints for the Employee Leave Management module."""

from django.http import Http404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from fusion_auth.permissions import HasModuleGrant, HasPermission
from modules.leave.api import serializers as s
from modules.leave.models import (
    HierarchyConfig,
    HolidayRHCalendar,
    LeaveAccount,
    LeavePolicyConfig,
    LeaveRequest,
    OfflineSanctionRecord,
    RequestAction,
    ResumptionRecord,
    SLAConfig,
    WorkflowTask,
)
from modules.leave.selectors import scoping

MODULE = HasModuleGrant("leave")
P_VIEW = "leave.request.view"
P_VIEW_SELF = "leave.request.view_self"
P_CREATE = "leave.request.create"
P_REVOKE = "leave.request.revoke"
P_REVIEW = "leave.request.review"
P_APPROVE = "leave.request.approve"
P_EXPORT = "leave.request.export"
P_TASK_VIEW = "leave.workflow_task.view"
P_TASK_UPDATE = "leave.workflow_task.update"
P_TASK_ASSIGN = "leave.workflow_task.assign"
P_BALANCE = "leave.balance.view"
P_HISTORY = "leave.history.view"
P_RESUMPTION = "leave.resumption.create"
P_POLICY = "leave.policy.manage"
P_HIERARCHY = "leave.hierarchy.manage"
P_CALENDAR = "leave.calendar.manage"
P_RECORD = "leave.record.manage"
P_SLA = "leave.sla.manage"


def _actor(request):
    return getattr(request, "principal", None)


class LeaveRequestView(generics.ListCreateAPIView):
    serializer_class = s.LeaveRequestSerializer
    permission_classes = [MODULE, HasPermission(P_VIEW, P_VIEW_SELF, P_CREATE)]

    def get_queryset(self):
        return scoping.leave_requests_for(_actor(self.request))

    def perform_create(self, serializer):
        actor = _actor(self.request)
        serializer.save(
            user_id=actor.user_id,
            has_substitute=bool(serializer.validated_data.get("substitute_user_id")),
        )


class LeaveRequestDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = s.LeaveRequestSerializer
    permission_classes = [MODULE, HasPermission(P_VIEW_SELF, P_REVOKE)]

    def get_queryset(self):
        return scoping.leave_requests_for(_actor(self.request))

    def perform_destroy(self, instance):
        instance.status = "CANCELLED"
        instance.is_cancelled = True
        instance.save(update_fields=["status", "is_cancelled", "updated_at"])


@extend_schema(
    request=s.LeaveRequestSerializer,
    responses=s.LeaveRequestSerializer,
)
class LeaveRequestDecisionView(APIView):
    permission_classes = [MODULE, HasPermission(P_REVIEW, P_APPROVE)]

    def post(self, request, pk):
        instance = scoping.leave_request_by_id(pk, _actor(request))
        if instance is None:
            raise Http404
        action = str(request.data.get("action", "")).lower()
        if action not in {"approve", "reject"}:
            return Response(
                {"detail": "action must be approve or reject"}, status=status.HTTP_400_BAD_REQUEST
            )
        if action == "approve" and not _actor(request).has_permission(P_APPROVE):
            return Response(
                {"detail": "Approval permission required"}, status=status.HTTP_403_FORBIDDEN
            )
        if action == "reject" and not _actor(request).has_permission(P_REVIEW):
            return Response(
                {"detail": "Review permission required"}, status=status.HTTP_403_FORBIDDEN
            )
        instance.status = "APPROVED" if action == "approve" else "REJECTED"
        instance.save(update_fields=["status", "updated_at"])
        RequestAction.objects.create(
            request_id=instance,
            actor_user_id=_actor(request).user_id,
            action_type=action.upper(),
            outcome=instance.status,
            reason=str(request.data.get("reason", "")),
        )
        return Response(s.LeaveRequestSerializer(instance).data)


@extend_schema(responses=s.LeaveRequestSerializer(many=True))
class LeaveRequestExportView(APIView):
    permission_classes = [MODULE, HasPermission(P_EXPORT)]

    def get(self, request):
        rows = LeaveRequest.objects.filter(user_id=_actor(request).user_id)
        return Response(s.LeaveRequestSerializer(rows, many=True).data)


class SubstituteAssignmentView(generics.ListCreateAPIView):
    serializer_class = s.SubstituteAssignmentSerializer
    permission_classes = [MODULE, HasPermission(P_TASK_UPDATE)]

    def get_queryset(self):
        return scoping.substitute_assignments_for(_actor(self.request))

    def perform_create(self, serializer):
        serializer.save(applicant_user_id=_actor(self.request).user_id)


class LeavePolicyConfigView(generics.RetrieveUpdateAPIView):
    serializer_class = s.LeavePolicyConfigSerializer
    permission_classes = [MODULE, HasPermission(P_POLICY)]

    def get_object(self):
        obj = LeavePolicyConfig.objects.order_by("-created_at").first()
        if obj is None:
            raise Http404
        return obj


class HierarchyConfigView(generics.RetrieveUpdateAPIView):
    serializer_class = s.HierarchyConfigSerializer
    permission_classes = [MODULE, HasPermission(P_HIERARCHY)]

    def get_object(self):
        obj = HierarchyConfig.objects.order_by("-created_at").first()
        if obj is None:
            raise Http404
        return obj


class HolidayRHCalendarView(generics.RetrieveUpdateAPIView):
    serializer_class = s.HolidayRHCalendarSerializer
    permission_classes = [MODULE, HasPermission(P_CALENDAR, "leave.calendar.publish")]

    def get_object(self):
        obj = (
            HolidayRHCalendar.objects.filter(is_published=True).order_by("-effective_from").first()
        )
        if obj is None:
            raise Http404
        return obj


class LeaveBalanceView(generics.ListAPIView):
    serializer_class = s.LeaveAccountSerializer
    permission_classes = [MODULE, HasPermission(P_BALANCE)]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return LeaveAccount.objects.none()
        return LeaveAccount.objects.filter(user_id=_actor(self.request).user_id)


class ResumptionRecordView(generics.ListCreateAPIView):
    serializer_class = s.ResumptionRecordSerializer
    permission_classes = [MODULE, HasPermission(P_RESUMPTION)]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return ResumptionRecord.objects.none()
        return ResumptionRecord.objects.filter(request_id__user_id=_actor(self.request).user_id)

    def perform_create(self, serializer):
        request_id = self.request.data.get("request_id")
        serializer.save(request_id_id=request_id)


class OfflineSanctionRecordView(generics.RetrieveUpdateAPIView):
    serializer_class = s.OfflineSanctionRecordSerializer
    permission_classes = [MODULE, HasPermission(P_RECORD)]

    def get_queryset(self):
        return OfflineSanctionRecord.objects.filter(employee_user_id=_actor(self.request).user_id)


class SLAConfigView(generics.RetrieveUpdateAPIView):
    serializer_class = s.SLAConfigSerializer
    permission_classes = [MODULE, HasPermission(P_SLA)]

    def get_object(self):
        obj = SLAConfig.objects.order_by("-created_at").first()
        if obj is None:
            raise Http404
        return obj


class WorkflowTaskView(generics.ListAPIView):
    serializer_class = s.WorkflowTaskSerializer
    permission_classes = [MODULE, HasPermission(P_TASK_VIEW)]

    def get_queryset(self):
        return scoping.workflow_tasks_for(_actor(self.request))


class WorkflowTaskDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = s.WorkflowTaskSerializer
    permission_classes = [MODULE, HasPermission(P_TASK_UPDATE, P_TASK_ASSIGN)]

    def get_queryset(self):
        return WorkflowTask.objects.all()


class RequestActionView(generics.ListAPIView):
    serializer_class = s.RequestActionSerializer
    permission_classes = [MODULE, HasPermission(P_HISTORY, P_VIEW_SELF)]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return RequestAction.objects.none()
        return RequestAction.objects.filter(request_id__user_id=_actor(self.request).user_id)
