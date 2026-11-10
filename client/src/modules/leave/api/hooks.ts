/**
 * Employee Leave Management (ELM) — API Hooks.
 *
 * TanStack Query hooks for leave applications, workflows, accounts, and policies.
 * Uses the shared HTTP client (`client/lib/http`).
 * Identity references are integer `user_id` values; cross-module data uses public contracts.
 */

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationOptions,
} from "@tanstack/react-query";

import { http } from "../../../lib/http";
import type {
  LeaveAccount,
  LeaveRequest,
  WorkflowTask,
  LeavePolicyConfig,
  HierarchyConfig,
  HolidayRHCalendar,
  SLAConfig,
} from "./types";

const KEY = "leave";

// -----------------------------------------------------------------------------
// Query Keys
// -----------------------------------------------------------------------------
export const keys = {
  requests: (f?: unknown) => [KEY, "requests", f] as const,
  request: (id: number) => [KEY, "request", id] as const,
  tasks: (requestId?: number) => [KEY, "tasks", requestId] as const,
  accounts: (userId?: number) => [KEY, "accounts", userId] as const,
  account: (employeeUserId: number, category?: string) =>
    [KEY, "account", employeeUserId, category] as const,
  policies: () => [KEY, "policies"] as const,
  hierarchy: () => [KEY, "hierarchy"] as const,
  calendars: () => [KEY, "calendars"] as const,
  sla: () => [KEY, "sla"] as const,
};

// -----------------------------------------------------------------------------
// Invalidate Helpers
// -----------------------------------------------------------------------------
function invalidateAll(qc: ReturnType<typeof useQueryClient>) {
  qc.invalidateQueries({ queryKey: [KEY] });
}

function invalidateRequest(requestId: number) {
  invalidateAll();
  // Invalidate related tasks and account if known
  invalidateTask(requestId);
  invalidateAccount(requestId);
}

function invalidateTask(taskId: number) {
  invalidateAll();
}

function invalidateAccount(userId: number, category?: string) {
  invalidateAll();
}

// -----------------------------------------------------------------------------
// Leave Request Hooks
// -----------------------------------------------------------------------------
/** Fetches a list of leave requests with optional filtering.
 * @param filters - Optional filters (status, category, employee_id)
 */
export function useLeaveRequests(filters?: {
  status?: string;
  category?: string;
  employee_user_id?: number;
}) {
  return useQuery({
    queryKey: keys.requests(filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append("status", filters.status);
      if (filters?.category) params.append("category", filters.category);
      if (filters?.employee_user_id) params.append("employee_user_id", String(filters.employee_user_id));

      const res = await http.get<Page<{ data: LeaveRequest[] }>>("/leave/requests", { params: params.toString() });
      return res.data;
    },
    staleTime: 30_000,
  });
}

/** Fetches a single leave request by ID.
 * @param id - The unique identifier of the leave request
 */
export function useLeaveRequest(id: number) {
  return useQuery({
    queryKey: keys.request(id),
    queryFn: async () => {
      const res = await http.get<LeaveRequest>(`/leave/requests/${id}`);
      return res.data;
    },
    enabled: id != null,
  });
}

/** Fetches workflow tasks associated with a specific leave request.
 * @param requestId - The ID of the leave request
 */
export function useLeaveTasks(requestId: number) {
  return useQuery({
    queryKey: keys.tasks(requestId),
    queryFn: async () => {
      const res = await http.get<Page<{ data: WorkflowTask[] }>>(`/leave/tasks/${requestId}`);
      return res.data;
    },
    enabled: requestId != null,
  });
}

// -----------------------------------------------------------------------------
// Leave Account Hooks
// -----------------------------------------------------------------------------
/** Fetches the leave account balance for a specific employee and category.
 * @param employeeUserId - The user ID of the employee
 * @param category - Optional category filter (e.g., 'CL', 'RH')
 */
export function useLeaveAccount(employeeUserId: number, category?: string) {
  return useQuery({
    queryKey: keys.account(employeeUserId, category),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (category) params.append("category", category);

      const res = await http.get<LeaveAccount>(`/leave/accounts/${employeeUserId}`, { params: params.toString() });
      return res.data;
    },
  });
}

/** Fetches a history of ledger entries for an employee.
 * @param employeeUserId - The user ID of the employee
 */
export function useLeaveHistory(employeeUserId: number) {
  return useQuery({
    queryKey: keys.account(employeeUserId),
    queryFn: async () => {
      const res = await http.get<Page<{ data: { type: string; amount: number; description: string }[] }>>(`/leave/accounts/${employeeUserId}/history`);
      return res.data;
    },
  });
}

// -----------------------------------------------------------------------------
// Workflow & Task Hooks
// -----------------------------------------------------------------------------
/** Fetches all active workflow tasks across the system.
 */
export function useWorkflowTasks() {
  return useQuery({
    queryKey: keys.tasks(),
    queryFn: async () => {
      const res = await http.get<Page<{ data: WorkflowTask[] }>>("/leave/tasks");
      return res.data;
    },
  });
}

// -----------------------------------------------------------------------------
// Policy & Configuration Hooks
// -----------------------------------------------------------------------------
/** Fetches the current leave policy configuration.
 * Note: No draft/publish/effective-version lifecycle is used per Problem Statement v1.4.
 */
export function useLeavePolicyConfig() {
  return useQuery({
    queryKey: keys.policies,
    queryFn: async () => {
      const res = await http.get<LeavePolicyConfig>("/leave/policy/configure");
      return res.data;
    },
  });
}

/** Fetches the current hierarchy configuration.
 */
export function useHierarchyConfig() {
  return useQuery({
    queryKey: keys.hierarchy,
    queryFn: async () => {
      const res = await http.get<HierarchyConfig>("/leave/hierarchy/configure");
      return res.data;
    },
  });
}

/** Fetches the currently effective published holiday/RH calendar.
 */
export function useHolidayRHCalendar() {
  return useQuery({
    queryKey: keys.calendars,
    queryFn: async () => {
      const res = await http.get<HolidayRHCalendar>("/leave/calendars/published");
      return res.data;
    },
  });
}

/** Fetches SLA configuration thresholds.
 */
export function useSLAConfig() {
  return useQuery({
    queryKey: keys.sla,
    queryFn: async () => {
      const res = await http.get<SLAConfig>("/leave/sla/configure");
      return res.data;
    },
  });
}

// -----------------------------------------------------------------------------
// Mutation Hooks
// -----------------------------------------------------------------------------
/** Submits a new leave request.
 * @param data - Leave request data including employee_user_id, category, dates, etc.
 */
export function useSubmitLeaveRequest() {
  return useMutation({
    mutationFn: async (data: { employee_user_id: number; category: string; start_date: string; end_date: string; purpose?: string }) => {
      const res = await http.post<LeaveRequest>("/leave/requests", data);
      return res.data;
    },
    onMutate: (data) => {
      invalidateAll();
    },
  });
}

/** Cancels an approved leave request before the start date.
 * @param id - The ID of the leave request
 */
export function useCancelLeaveRequest() {
  return useMutation({
    mutationFn: async (id: number) => {
      const res = await http.post(`/leave/requests/${id}/cancel`);
      return res.data;
    },
    onMutate: (id) => {
      invalidateRequest(id);
    },
  });
}

/** Withdraws a pending leave request.
 * @param id - The ID of the leave request
 */
export function useWithdrawLeaveRequest() {
  return useMutation({
    mutationFn: async (id: number) => {
      const res = await http.post(`/leave/requests/${id}/withdraw`);
      return res.data;
    },
    onMutate: (id) => {
      invalidateRequest(id);
    },
  });
}

/** Extends an ongoing leave request (EL/COL/VL).
 * @param id - The ID of the leave request
 * @param extensionData - Extension details
 */
export function useExtendLeaveRequest() {
  return useMutation({
    mutationFn: async (id: number, data: { start_date: string; end_date: string }) => {
      const res = await http.post(`/leave/requests/${id}/extend`, data);
      return res.data;
    },
    onMutate: (id) => {
      invalidateRequest(id);
    },
  });
}

/** Assigns a substitute for a leave request requiring responsibility coverage.
 * @param id - The ID of the leave request
 * @param data - Substitute assignment details
 */
export function useAssignSubstitute() {
  return useMutation({
    mutationFn: async (id: number, data: { employee_user_id: number; responsible_until?: string }) => {
      const res = await http.post(`/leave/requests/${id}/substitute`, data);
      return res.data;
    },
    onMutate: (id) => {
      invalidateRequest(id);
    },
  });
}

/** Records an offline-sanctioned leave.
 * @param id - The ID of the leave request
 * @param data - Offline sanction details
 */
export function useRecordOfflineSanction() {
  return useMutation({
    mutationFn: async (id: number, data: { evidence_url?: string; notes?: string }) => {
      const res = await http.post(`/leave/requests/${id}/offline-sanction`, data);
      return res.data;
    },
    onMutate: (id) => {
      invalidateRequest(id);
    },
  });
}

/** Submits a resumption record for early/late return.
 * @param id - The ID of the approved leave request
 * @param data - Resumption details
 */
export function useSubmitResumption() {
  return useMutation({
    mutationFn: async (id: number, data: { actual_start_date: string; actual_end_date: string }) => {
      const res = await http.post(`/leave/requests/${id}/resumption`, data);
      return res.data;
    },
    onMutate: (id) => {
      invalidateRequest(id);
    },
  });
}

/** Handles SLA escalation or reminder actions.
 * @param taskId - The ID of the pending task
 */
export function useHandleSLATask(taskId: number, action: "escalate" | "notify") {
  return useMutation({
    mutationFn: async (taskId: number, action: "escalate" | "notify") => {
      const res = await http.post(`/leave/tasks/${taskId}/sla`, { action });
      return res.data;
    },
    onMutate: (taskId) => {
      invalidateTask(taskId);
    },
  });
}

// -----------------------------------------------------------------------------
// Type Guards & Helpers
// -----------------------------------------------------------------------------
function isLeaveRequest(data: unknown): data is LeaveRequest {
  return typeof data === "object" && data !== null && "id" in data;
}

function isWorkflowTask(data: unknown): data is WorkflowTask {
  return typeof data === "object" && data !== null && "task_kind" in data;
}

// -----------------------------------------------------------------------------
// Exports for external modules (if needed)
// -----------------------------------------------------------------------------
export { keys };
export { invalidateAll, invalidateRequest, invalidateAccount };
