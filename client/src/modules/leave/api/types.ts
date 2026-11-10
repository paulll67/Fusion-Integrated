/**
 * Employee Leave Management (ELM) — API Types.
 *
 * TypeScript interfaces mirroring generated ELM serializer fields and domain aggregates.
 * Identity references are integer user_id values.
 * Money and CPI arrive as STRINGS, as Django serialises Decimal. Parsing them into JS numbers
 * puts float arithmetic on a salary figure.
 */

export interface Page<T> {
  results: T[];
  next: string | null;
  previous: string | null;
}

/**
 * Leave Category Enum.
 * CL: Casual Leave (8 days/year)
 * RH: Restricted Holiday (2 days/year)
 * SCL: Special Casual Leave (up to 15 days/year)
 * EL: Earned Leave (30 days/year for non-faculty, carries forward)
 * VL: Vacation Leave (60 days/year for faculty, converts to EL at year-end)
 * COL: Compensatory/Overtime Leave (20 days/year, medical/balance-controlled)
 */
export type LeaveCategory = "CL" | "RH" | "SCL" | "EL" | "VL" | "COL";

/**
 * Leave Request Status.
 * Derived from Workflow v1.6 STTs and Use Cases.
 */
export type LeaveRequestStatus =
  | "draft"
  | "submitted"
  | "awaiting_substitute_response"
  | "awaiting_unit_head_review"
  | "approved"
  | "rejected"
  | "cancelled"
  | "withdrawn"
  | "extension_pending"
  | "resumption_pending";

/**
 * Leave Request Aggregate.
 * Represents a single leave application lifecycle.
 */
export interface LeaveRequest {
  id: number;
  employee_user_id: number;
  category: LeaveCategory;
  start_date: string; // ISO Date string
  end_date: string;   // ISO Date string
  purpose: string | null;
  station_leave_details: Record<string, unknown> | null;
  status: LeaveRequestStatus;
  submitted_at: string; // ISO Date string
  
  /**
   * Linked original request where applicable (e.g., extension or resumption).
   * Null for new requests.
   */
  linked_original_request_id: number | null;
  
  /**
   * Current balance deduction tracking.
   * For CL/RH/SCL/EL/COL/VL, this tracks the specific days consumed.
   */
  balance_deduction: number;
}

/**
 * Workflow Task Aggregate.
 * Tracks actionable assignments and current task state.
 */
export interface WorkflowTask {
  id: number;
  request_id: number;
  task_kind: "unit_head_review" | "substitute_response" | "establishment_routing" | "final_sanction" | "resumption_review";
  assigned_user_id: number | null;
  role_context: string; // e.g., "Unit Head", "Director"
  state: "pending" | "assigned" | "completed" | "escalated";
  assigned_at: string | null;
  due_at: string | null;
  reminder_sent_at: string | null;
  escalation_triggered_at: string | null;
}

/**
 * Request Action / History Entry.
 * Append-oriented record for user-visible status/history and operations.
 */
export interface RequestAction {
  id: number;
  request_id: number;
  actor_user_id: number;
  action_type: "submit" | "withdraw" | "cancel" | "approve" | "reject" | "extend" | "resumption_submit" | "sanction_record";
  outcome: string; // e.g., "Approved", "Rejected", "Withdrawn"
  timestamp: string;
  reason: string | null;
  evidence_reference: string | null;
}

/**
 * Leave Account Aggregate.
 * Represents the leave balance for an employee.
 */
export interface LeaveAccount {
  id: number;
  employee_user_id: number;
  category: LeaveCategory;
  total_entitlement: number; // Annual entitlement (e.g., 8, 30, 60)
  available_balance: number;
  used_this_year: number;
  carry_forward_eligible: boolean;
  last_updated_at: string;
}

/**
 * Leave Ledger Entry.
 * Explicit transaction record for balance changes.
 */
export interface LeaveLedgerEntry {
  id: number;
  account_id: number;
  transaction_type: "allocation" | "deduction" | "carry_forward" | "year_end_conversion" | "adjustment";
  amount: number;
  request_id: number | null; // Linked to the specific leave request if applicable
  year: number;
  description: string;
  timestamp: string;
}

/**
 * Substitute Assignment Aggregate.
 * Tracks substitute consent and responsibility coverage.
 */
export interface SubstituteAssignment {
  id: number;
  request_id: number;
  applicant_user_id: number;
  substitute_user_id: number;
  response: "accepted" | "declined";
  responsibility_interval_start: string;
  responsibility_interval_end: string;
  created_at: string;
}

/**
 * Leave Policy Configuration.
 * Current configured values only; no draft/publish/effective-version lifecycle.
 */
export interface LeavePolicyConfig {
  id: number;
  category: LeaveCategory;
  annual_entitlement: number;
  counting_rule: "continuous" | "standard"; // continuous for EL/COL/VL, standard for CL/RH/SCL
  carry_forward_eligible: boolean;
  year_end_conversion_rate: number | null; // e.g., 2 VL : 1 EL
}

/**
 * Hierarchy Configuration.
 * Stores current routing configuration.
 */
export interface HierarchyConfig {
  id: number;
  employee_user_id: number;
  unit_head_role: string;
  higher_sanction_roles: string[]; // e.g., ["Deputy Registrar", "Director"]
  establishment_routing_enabled: boolean;
  director_self_sanction_allowed: boolean;
}

/**
 * Holiday/RH Calendar Aggregate.
 * Only currently effective published calendar is used for date/RH validation.
 */
export interface HolidayRHCalendar {
  id: number;
  year: number;
  is_published: boolean;
  publication_date: string | null;
  holidays: { date: string; kind: "CL" | "RH" | "SCL" }[];
}

/**
 * Resumption Record.
 * Supported only for EL/COL/VL; balance/period synchronization after required review.
 */
export interface ResumptionRecord {
  id: number;
  request_id: number;
  actual_resumption_date: string;
  required_details: Record<string, unknown> | null;
  review_status: "pending" | "reviewed";
  reviewed_outcome: "normal" | "early_return" | "late_return";
  balance_adjustment_applied: boolean;
}

/**
 * Offline Sanction Record.
 * Synchronizes an already-authorized paper/offline leave.
 */
export interface OfflineSanctionRecord {
  id: number;
  employee_user_id: number;
  category: LeaveCategory;
  interval_start: string;
  interval_end: string;
  sanction_reference: string;
  consistency_outcome: "synchronized" | "conflict_detected";
  source_leave_account_transaction_id: number | null;
}

/**
 * SLA Configuration.
 * Used by event-triggered SLA processing.
 */
export interface SLAConfig {
  id: number;
  task_kind: string;
  reminder_threshold_hours: number;
  escalation_threshold_hours: number;
  escalation_action: "notify" | "reroute" | "auto_approve";
}

/**
 * Page wrapper for list responses.
 */
export interface LeavePage<T> extends Page<T> {
  total_count: number;
}

/**
 * Employee DTO (mirroring Django serializer fields).
 */
export interface EmployeeDTO {
  user_id: number;
  username: string;
  display_name: string;
  kind: "faculty" | "staff";
  email: string;
  department: string;
  designation: string;
  batch_year: number | null;
}

/**
 * Vacation Period DTO (mirroring Django serializer fields).
 */
export interface VacationPeriodDTO {
  id: number;
  start_date: string;
  end_date: string;
  is_active: boolean;
}

/**
 * Error response for API validation failures.
 */
export interface ValidationError {
  field: string;
  reason: string;
  required: unknown;
  actual: unknown;
  message: string;
}

/**
 * Response envelope for API endpoints.
 */
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  errors?: ValidationError[];
  message?: string;
}
