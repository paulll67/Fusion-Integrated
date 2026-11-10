"""Employee Leave Management (ELM) — Declarative State Machine.

A declarative table of legal moves, so an illegal transition is impossible to express rather than merely rejected, and "who may do this?" has exactly one answer per edge. Pure Python, so the rules test in milliseconds with no DB.

Authoritative source: Workflow Specifications v1.6 (STTs).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import FrozenSet, Tuple

# -- State Constants --
DRAFT = "draft"
SUBMITTED = "submitted"
AWAITING_SUBSTITUTE_RESPONSE = "awaiting_substitute_response"
APPLICANT_ACTION_REQUIRED = "applicant_action_required"
AWAITING_UNIT_HEAD_REVIEW = "awaiting_unit_head_review"
AWAITING_ESTABLISHMENT_ROUTING = "awaiting_establishment_routing"
AWAITING_FINAL_SANCTION_DECISION = "awaiting_final_sanction_decision"
AWAITING_RESUMPTION_REVIEW = "awaiting_resumption_review"
AWAITING_SLA_ESCALATION = "awaiting_sla_escalation"

# Terminal States
TERMINAL = frozenset({
    "approved",
    "rejected",
    "withdrawn",
    "cancelled",
    "extended",
    "resumed",
})

# In-flight states (not terminal)
IN_FLIGHT = frozenset({
    DRAFT,
    SUBMITTED,
    AWAITING_SUBSTITUTE_RESPONSE,
    APPLICANT_ACTION_REQUIRED,
    AWAITING_UNIT_HEAD_REVIEW,
    AWAITING_ESTABLISHMENT_ROUTING,
    AWAITING_FINAL_SANCTION_DECISION,
    AWAITING_RESUMPTION_REVIEW,
    AWAITING_SLA_ESCALATION,
})

# -- Actor Constants --
EMPLOYEE = "employee"
SUBSTITUTE = "substitute"
UNIT_HEAD = "unit_head"
ESTABLISHMENT = "establishment"
SANCTIONING_AUTHORITY = "sanctioning_authority"
SYSTEM = "system"  # For SLA events

# -- Exception Classes --
class InvalidTransition(Exception):
    def __init__(self, frm: str, to: str):
        super().__init__(f"Cannot move a request from {frm!r} to {to!r}.")
        self.frm, self.to = frm, to

class ActorNotAllowed(Exception):
    def __init__(self, actor_kind: str, frm: str, to: str):
        super().__init__(
            f"A {actor_kind} may not move a request from {frm!r} to {to!r}.")
        self.actor_kind, self.frm, self.to = actor_kind, frm, to

class GuardFailed(Exception):
    def __init__(self, guard: str, message: str = ""):
        super().__init__(message or f"Guard {guard!r} failed.")
        self.guard = guard

# -- Transition Dataclass --
@dataclass(frozen=True)
class Transition:
    frm: str
    to: str
    permission: str
    actors: FrozenSet[str]
    guards: Tuple[str, ...] = field(default_factory=tuple)

def _transition(
    frm: str,
    to: str,
    permission: str,
    actors: FrozenSet[str],
    guards: Tuple[str, ...] = (),
) -> Transition:
    """Helper to construct a Transition object."""
    return Transition(frm, to, permission, actors, guards)

# -- State Machine Registry --
TRANSITIONS: Tuple[Transition, ...] = (
    # ==================== NEW LEAVE WORKFLOWS ====================
    
    # --- BW-EL-01 / 02 / 03: New CL/RH (No Substitute / With Substitute) ---
    # Employee submits valid request
    _transition(DRAFT, SUBMITTED, "leave_cell.application.create",
                frozenset({EMPLOYEE}),
                ("window_open", "profile_complete", "is_eligible", "may_apply", "no_substitute_required")),
    
    # Employee submits valid request with substitute required
    _transition(DRAFT, SUBMITTED, "leave_cell.application.create",
                frozenset({EMPLOYEE}),
                ("window_open", "profile_complete", "is_eligible", "may_apply", "substitute_required")),
    
    # Substitute accepts (BW-EL-02)
    _transition(SUBMITTED, AWAITING_UNIT_HEAD_REVIEW, "leave_cell.substitute_response.accept",
                frozenset({SUBSTITUTE}),
                ("eligible_substitute", "applicant_not_director")),
    
    # Substitute declines -> Applicant Action Required (BW-EL-03)
    _transition(SUBMITTED, APPLICANT_ACTION_REQUIRED, "leave_cell.substitute_response.decline",
                frozenset({SUBSTITUTE}),
                ("eligible_substitute", "applicant_not_director")),
    
    # Employee nominates replacement (BW-EL-03)
    _transition(APPLICANT_ACTION_REQUIRED, AWAITING_SUBSTITUTE_RESPONSE, "leave_cell.replacement_nomination",
                frozenset({EMPLOYEE}),
                ("eligible_replacement_nominated")),
    
    # Unit Head reviews and approves/rejects (BW-EL-01/02/03)
    _transition(AWAITING_UNIT_HEAD_REVIEW, "approved", "leave_cell.unit_head_decision.approve",
                frozenset({UNIT_HEAD}),
                ("cl_rh_category", "valid_period")),
    
    _transition(AWAITING_UNIT_HEAD_REVIEW, "rejected", "leave_cell.unit_head_decision.reject",
                frozenset({UNIT_HEAD}),
                ("cl_rh_category", "valid_period")),
    
    # --- BW-EL-04 / 05 / 06: New Higher-Sanction Leave ---
    # Employee submits valid higher-sanction request
    _transition(DRAFT, SUBMITTED, "leave_cell.application.create",
                frozenset({EMPLOYEE}),
                ("window_open", "profile_complete", "is_eligible", "may_apply", "higher_sanction_category", "no_substitute_required")),
    
    # Employee submits valid higher-sanction request with substitute
    _transition(DRAFT, SUBMITTED, "leave_cell.application.create",
                frozenset({EMPLOYEE}),
                ("window_open", "profile_complete", "is_eligible", "may_apply", "higher_sanction_category", "substitute_required")),
    
    # Substitute accepts higher-sanction
    _transition(SUBMITTED, AWAITING_UNIT_HEAD_REVIEW, "leave_cell.substitute_response.accept",
                frozenset({SUBSTITUTE}),
                ("eligible_substitute", "applicant_not_director")),
    
    # Employee nominates replacement for higher-sanction
    _transition(APPLICANT_ACTION_REQUIRED, AWAITING_SUBSTITUTE_RESPONSE, "leave_cell.replacement_nomination",
                frozenset({EMPLOYEE}),
                ("eligible_replacement_nominated")),
    
    # Unit Head reviews and recommends/recommends-not
    _transition(AWAITING_UNIT_HEAD_REVIEW, AWAITING_ESTABLISHMENT_ROUTING, "leave_cell.unit_head_decision.recommend",
                frozenset({UNIT_HEAD}),
                ("higher_sanction", "establishment_configured")),
    
    _transition(AWAITING_UNIT_HEAD_REVIEW, AWAITING_FINAL_SANCTION_DECISION, "leave_cell.unit_head_decision.not_recommend",
                frozenset({UNIT_HEAD}),
                ("higher_sanction", "no_establishment_step")),
    
    # Establishment verifies and routes (BW-EL-04/05/06)
    _transition(AWAITING_ESTABLISHMENT_ROUTING, AWAITING_FINAL_SANCTION_DECISION, "leave_cell.estab_routing.verify",
                frozenset({ESTABLISHMENT}),
                ("routing_context_valid")),
    
    # Sanctioning Authority makes final decision
    _transition(AWAITING_FINAL_SANCTION_DECISION, "approved", "leave_cell.sanction_decision.approve",
                frozenset({SANCTIONING_AUTHORITY}),
                ("higher_sanction", "valid_period")),
    
    _transition(AWAITING_FINAL_SANCTION_DECISION, "rejected", "leave_cell.sanction_decision.reject",
                frozenset({SANCTIONING_AUTHORITY}),
                ("higher_sanction", "valid_period")),
    
    # --- BW-EL-07: Director Self-Sanction ---
    # Employee submits valid request (Director)
    _transition(DRAFT, SUBMITTED, "leave_cell.application.create",
                frozenset({EMPLOYEE}),
                ("window_open", "profile_complete", "is_eligible", "may_apply", "director_applicant", "no_substitute_required")),
    
    # Director self-sanctions
    _transition(SUBMITTED, "approved", "leave_cell.director_self_sanction.approve",
                frozenset({EMPLOYEE}),
                ("director_applicant", "valid_period")),
    
    _transition(SUBMITTED, "rejected", "leave_cell.director_self_sanction.reject",
                frozenset({EMPLOYEE}),
                ("director_applicant", "valid_period")),

    # ==================== CANCELLATION WORKFLOWS ====================
    
    # --- BW-EL-10 / 11: Approved Leave Cancellation ---
    # Employee requests cancellation of approved leave
    _transition("approved", AWAITING_UNIT_HEAD_REVIEW, "leave_cell.cancellation_request",
                frozenset({EMPLOYEE}),
                ("cl_rh_category", "before_start_date")),
    
    # Unit Head reviews cancellation
    _transition(AWAITING_UNIT_HEAD_REVIEW, "cancelled", "leave_cell.unit_head_decision.approve_cancel",
                frozenset({UNIT_HEAD}),
                ("cl_rh_category", "valid_period")),
    
    _transition(AWAITING_UNIT_HEAD_REVIEW, "rejected", "leave_cell.unit_head_decision.reject_cancel",
                frozenset({UNIT_HEAD}),
                ("cl_rh_category", "valid_period")),
    
    # Higher-sanction cancellation path
    _transition("approved", AWAITING_UNIT_HEAD_REVIEW, "leave_cell.cancellation_request",
                frozenset({EMPLOYEE}),
                ("higher_sanction_category", "before_start_date")),
    
    _transition(AWAITING_UNIT_HEAD_REVIEW, AWAITING_ESTABLISHMENT_ROUTING, "leave_cell.unit_head_decision.recommend_cancel",
                frozenset({UNIT_HEAD}),
                ("higher_sanction", "establishment_configured")),
    
    _transition(AWAITING_UNIT_HEAD_REVIEW, AWAITING_FINAL_SANCTION_DECISION, "leave_cell.unit_head_decision.not_recommend_cancel",
                frozenset({UNIT_HEAD}),
                ("higher_sanction", "no_establishment_step")),
    
    _transition(AWAITING_ESTABLISHMENT_ROUTING, AWAITING_FINAL_SANCTION_DECISION, "leave_cell.estab_routing.verify_cancel",
                frozenset({ESTABLISHMENT}),
                ("routing_context_valid")),
    
    _transition(AWAITING_FINAL_SANCTION_DECISION, "cancelled", "leave_cell.sanction_decision.approve_cancel",
                frozenset({SANCTIONING_AUTHORITY}),
                ("higher_sanction", "valid_period")),
    
    _transition(AWAITING_FINAL_SANCTION_DECISION, "rejected", "leave_cell.sanction_decision.reject_cancel",
                frozenset({SANCTIONING_AUTHORITY}),
                ("higher_sanction", "valid_period")),

    # ==================== EXTENSION WORKFLOWS ====================
    
    # --- BW-EL-12 / 13 / 14: Ongoing Leave Extension ---
    # Employee requests extension of ongoing leave
    _transition("ongoing", AWAITING_UNIT_HEAD_REVIEW, "leave_cell.extension_request",
                frozenset({EMPLOYEE}),
                ("valid_incremental_period", "substitute_not_required")),
    
    _transition("ongoing", AWAITING_UNIT_HEAD_REVIEW, "leave_cell.extension_request",
                frozenset({EMPLOYEE}),
                ("valid_incremental_period", "substitute_required")),
    
    # Substitute accepts extension
    _transition(AWAITING_SUBSTITUTE_RESPONSE, AWAITING_UNIT_HEAD_REVIEW, "leave_cell.substitute_response.accept",
                frozenset({SUBSTITUTE}),
                ("eligible_substitute", "applicant_not_director")),
    
    # Employee nominates replacement for extension
    _transition(APPLICANT_ACTION_REQUIRED, AWAITING_SUBSTITUTE_RESPONSE, "leave_cell.replacement_nomination",
                frozenset({EMPLOYEE}),
                ("eligible_replacement_nominated")),
    
    # Unit Head reviews and approves/rejects extension
    _transition(AWAITING_UNIT_HEAD_REVIEW, "extended", "leave_cell.unit_head_decision.approve_extend",
                frozenset({UNIT_HEAD}),
                ("valid_incremental_period", "cl_rh_category")),
    
    _transition(AWAITING_UNIT_HEAD_REVIEW, "rejected", "leave_cell.unit_head_decision.reject_extend",
                frozenset({UNIT_HEAD}),
                ("valid_incremental_period", "cl_rh_category")),
    
    # Higher-sanction extension path
    _transition("ongoing", AWAITING_UNIT_HEAD_REVIEW, "leave_cell.extension_request",
                frozenset({EMPLOYEE}),
                ("valid_incremental_period", "higher_sanction_category", "substitute_not_required")),
    
    _transition("ongoing", AWAITING_UNIT_HEAD_REVIEW, "leave_cell.extension_request",
                frozenset({EMPLOYEE}),
                ("valid_incremental_period", "higher_sanction_category", "substitute_required")),
    
    # Substitute accepts higher-sanction extension
    _transition(AWAITING_SUBSTITUTE_RESPONSE, AWAITING_UNIT_HEAD_REVIEW, "leave_cell.substitute_response.accept",
                frozenset({SUBSTITUTE}),
                ("eligible_substitute", "applicant_not_director")),
    
    # Employee nominates replacement for higher-sanction extension
    _transition(APPLICANT_ACTION_REQUIRED, AWAITING_SUBSTITUTE_RESPONSE, "leave_cell.replacement_nomination",
                frozenset({EMPLOYEE}),
                ("eligible_replacement_nominated")),
    
    # Unit Head reviews and recommends/recommends-not for extension
    _transition(AWAITING_UNIT_HEAD_REVIEW, AWAITING_ESTABLISHMENT_ROUTING, "leave_cell.unit_head_decision.recommend_extend",
                frozenset({UNIT_HEAD}),
                ("higher_sanction", "establishment_configured")),
    
    _transition(AWAITING_UNIT_HEAD_REVIEW, AWAITING_FINAL_SANCTION_DECISION, "leave_cell.unit_head_decision.not_recommend_extend",
                frozenset({UNIT_HEAD}),
                ("higher_sanction", "no_establishment_step")),
    
    # Establishment verifies and routes extension
    _transition(AWAITING_ESTABLISHMENT_ROUTING, AWAITING_FINAL_SANCTION_DECISION, "leave_cell.estab_routing.verify_extend",
                frozenset({ESTABLISHMENT}),
                ("routing_context_valid")),
    
    # Sanctioning Authority makes final decision on extension
    _transition(AWAITING_FINAL_SANCTION_DECISION, "extended", "leave_cell.sanction_decision.approve_extend",
                frozenset({SANCTIONING_AUTHORITY}),
                ("higher_sanction", "valid_incremental_period")),
    
    _transition(AWAITING_FINAL_SANCTION_DECISION, "rejected", "leave_cell.sanction_decision.reject_extend",
                frozenset({SANCTIONING_AUTHORITY}),
                ("higher_sanction", "valid_incremental_period")),

    # ==================== RESUMPTION WORKFLOWS ====================
    
    # --- BW-EL-15 / 16 / 17: Resumption Review ---
    # Employee submits resumption of duty
    _transition("resumed_pending", AWAITING_RESUMPTION_REVIEW, "leave_cell.resumption_submission",
                frozenset({EMPLOYEE}),
                ("valid_resumption_date", "cl_rh_category")),
    
    # Sanctioning Authority reviews resumption
    _transition(AWAITING_RESUMPTION_REVIEW, "resumed", "leave_cell.sanction_decision.approve_resumption",
                frozenset({SANCTIONING_AUTHORITY}),
                ("normal_return", "valid_period")),
    
    # Sanctioning Authority reviews early/late return
    _transition(AWAITING_RESUMPTION_REVIEW, "resumed", "leave_cell.sanction_decision.approve_resumption",
                frozenset({SANCTIONING_AUTHORITY}),
                ("early_or_late_return", "valid_period")),

    # ==================== SYSTEM / EVENT WORKFLOWS ====================
    
    # --- EL-UC-020: Year-End Processing ---
    # System executes year-end processing (lapse CL/RH/SCL, carry EL/COL, convert VL)
    _transition("approved", "lapsed", "leave_cell.year_end.process",
                frozenset({SYSTEM}),
                ("cl_rh_category", "year_end_boundary")),
    
    _transition("approved", "carried", "leave_cell.year_end.process",
                frozenset({SYSTEM}),
                ("el_col_category", "year_end_boundary")),
    
    _transition("approved", "converted", "leave_cell.year_end.process",
                frozenset({SYSTEM}),
                ("vl_category", "unused_faculty", "year_end_boundary")),

    # --- EL-UC-021: SLA Threshold Event ---
    # System triggers SLA escalation if task pending
    _transition("awaiting_unit_head_review", AWAITING_SLA_ESCALATION, "leave_cell.sla.trigger",
                frozenset({SYSTEM}),
                ("task_pending", "sla_threshold_reached")),
    
    # SLA escalation leads to notification or routing change
    _transition(AWAITING_SLA_ESCALATION, AWAITING_UNIT_HEAD_REVIEW, "leave_cell.sla.escalate",
                frozenset({SYSTEM}),
                ("notification_sent", "routing_changed")),
)
