# Employee Leave Management (ELM) — Assignment 6 Blueprint Draft

**Status:** Phase 2 blueprint approved by mentor (approval reported by the student on 2026-10-12). Local-model code generation has not yet run.

## 0. Decisions confirmed by the student

- **Module name:** Employee Leave Management (ELM).
- **Module code / URL slug:** `leave`.
- **Workflow authority:** `06_ELM_Workflow_Specifications_v1.6_FINAL.docx` is authoritative for workflow IDs, names, complete paths, and State-Transition Tables (STTs). The uploaded v1.5 Traceability Matrix is older for workflow mappings; do not copy its conflicting workflow IDs/names.
- **Policy-configuration interpretation:** Follow `01_ELM_Problem_Statement_v1.4_FINAL.docx` §§5 and 12: use current configured policy/hierarchy values, without a draft/publish/effective-version lifecycle for leave-policy parameters.
- **Assignment 6 coding boundary:** Generate code with the selected open-source locally deployed model. After generation, make only integration/mechanical corrections (file placement, imports, registration, routes, dependency/configuration, interface adaptation, database/config wiring, Fusion-specific structural mismatches). Do not conduct systematic BR review, hunt missing requirements, repair workflow logic, harden security, optimize, or run a thorough functional test campaign.

## 1. Supplied specification inventory and provenance

The six original source files now reside at the confirmed repository-relative path `docs/09-leave/specs/`. Searchable Markdown extractions are present alongside the originals for local-model context.

| Artifact | Supplied version | Intended use |
|---|---|---|
| `01_ELM_Problem_Statement_v1.4_FINAL.docx` | PS v1.4 | Domain boundaries, leave policy, lifecycle and actor context. |
| `02_ELM_Functional_Requirement_Specification_v1.5_FINAL.xlsx` | Requirements v1.5 | CFR/AFR requirements vocabulary and acceptance focus. |
| `03_ELM_Use_Case_Specifications_v1.4_FINAL.docx` | UC v1.4 | 20 active use cases; `EL-UC-006` is retired. |
| `04_ELM_Business_Rule_Specifications_v1.4_FINAL.docx` | BR v1.4 | 36 active business rules; `BR-EL-021` and `BR-EL-026` are retired identifiers. |
| `06_ELM_Traceability_Matrix_v1.5_FINAL.xlsx` | RTM v1.5 | CFR/AFR mappings where consistent; its workflow mapping is not authoritative against WF v1.6. |
| `06_ELM_Workflow_Specifications_v1.6_FINAL.docx` | WF v1.6 | Authoritative workflow registry and STTs: 17 complete basis workflows and 4 composite workflows. |

**Confirmed specification path:** `docs/09-leave/specs/`. The student explicitly confirmed this is the approved path. The original source documents were copied there unchanged; `.md` files are text extractions for model context.

## 2. Intended scope from the ELM specifications

The module covers new leave applications (CL, RH, SCL, EL, COL, VL), embedded Station Leave details, substitute consent and replacement after decline, Unit Head review, optional Establishment routing, final sanctioning, pending withdrawal, pre-start cancellation of approved leave, ongoing EL/COL/VL extension, resumption submission/review, employee balance/history, printable/exportable applications, policy/hierarchy configuration, published holiday/RH calendar administration, recording already-sanctioned offline leave, authorized leave-record maintenance, SLA threshold configuration/processing, and year-end balance processing.

The Academic Calendar is an external source for VL vacation-period data. Year-end and SLA-threshold occurrences are event triggers, not human actors. Retired IDs must not be revived as active implementation targets.

## 3. Phase 2 blueprint

### 3.1 (a) Traceability table — active business rules

The enforcement points below are planned design locations, not claims of implementation or a functional review. Business rules remain in domain/service layers rather than being encoded only in API views.

| ID | What it requires | Planned layer | Planned enforcement point | Notes |
|---|---|---|---|---|
| BR-EL-001 | Only supported, applicable leave categories may be requested. | Domain + service | `domain/eligibility.py`; apply/extension service before state creation. | Used with current configured policy. |
| BR-EL-002 | CL entitlement is 8 days/year; unused CL lapses at year end. | Domain + ledger service | `domain/entitlements.py`; year-end processor. | CL account transaction records. |
| BR-EL-003 | RH entitlement is 2 days/year and must match the effective published RH calendar; unused RH lapses. | Domain + calendar selector + ledger service | RH request validation; year-end processor. | Calendar publication remains distinct from policy versioning. |
| BR-EL-004 | SCL is up to 15 days/year; admissibility is decided by the competent authority; unused SCL lapses. | Domain + decision service | Entitlement validation and final sanction decision. | Do not invent an encoded purpose-admissibility rule. |
| BR-EL-005 | Non-faculty employees receive 30 EL/year; unused EL carries forward. | Domain + ledger service | Annual credit and year-end processor. | Employee category comes from employment/identity contract. |
| BR-EL-006 | Faculty receive 60 VL associated with Academic Calendar vacation periods; VL is usable only in applicable vacation periods. | Domain + external contract | `domain/entitlements.py`; Academic Calendar contract adapter. | Do not read academic source tables directly. |
| BR-EL-007 | Unused VL converts to EL at year end at 2 VL : 1 EL, including fractional conversion. | Domain + ledger service | Year-end calculation and EL credit entry. | VL itself does not carry forward. |
| BR-EL-008 | EL produced by VL conversion is credited to the faculty member's EL account and may carry forward. | Domain + ledger service | Year-end ledger posting. | Use traceable account transactions. |
| BR-EL-009 | COL entitlement/treatment follows the specified 20-day/year policy and medical-evidence condition where applicable; unused COL carries forward. | Domain + service | Entitlement/evidence validation and account ledger. | Evidence requirement only where applicable per source. |
| BR-EL-010 | First-half/second-half CL use is supported; an approved half-day consumes 0.5 CL day. | Domain + ledger service | CL request validation and approval posting. | Store half-day value without rounding away fractions. |
| BR-EL-011 | EL, COL, and VL count continuously across the interval, including weekends/closed holidays; this does not apply to CL/SCL/RH. | Domain | `domain/counting.py` shared by request and extension validation. | Category-dependent counting. |
| BR-EL-012 | Applicant overlap is prohibited, except first-half and second-half CL on the same date are not overlapping if they occupy different halves. | Domain + transactional service | Overlap selector plus serialized validation/create transaction. | Applies to pending and approved leave. |
| BR-EL-013 | Station Leave details are captured within the same leave application when applicable. | Domain/model + service | Application payload and aggregate validation. | No separate Station Leave request process. |
| BR-EL-014 | A substitute must be another employee, not the applicant, and have no overlapping pending/approved leave during the responsibility interval. | Domain + selector | `domain/substitutes.py`; batched employment/leave lookup. | No substitute user-role/designation is invented. |
| BR-EL-015 | Required substitute consent must be accepted before approval routing; decline enables replacement or withdrawal. | Domain state machine + service | Substitute-response and replacement services. | Apply exact WF v1.6 transitions. |
| BR-EL-016 | Unit Head is final decision-maker for CL/RH, including associated Station Leave. | Domain + service | Unit Head review command and authority guard. | CL/RH final approve/reject. |
| BR-EL-017 | For higher-sanction leave, Unit Head records Recommended/Not Recommended; Not Recommended is not a final rejection. | Domain + service | Unit Head review action and transition table. | Do not collapse recommendation into sanction. |
| BR-EL-018 | Higher-sanction requests follow the configured hierarchy. | Domain + service | `domain/routing.py`; route service. | Do not hardcode a single authority chain. |
| BR-EL-019 | Resolve the competent authority from applicant/unit/designation/category/current hierarchy; use Establishment only when configured. | Domain + contract/config selector | `domain/routing.py`; current hierarchy config selector. | Optional Establishment step is a conditional transition. |
| BR-EL-020 | Director's own leave uses the Director-specific self-sanction rule. | Domain + service | Applicant/authority resolution before routing. | Use the director path in WF v1.6. |
| BR-EL-022 | Pending request withdrawal is immediate, terminates remaining processing, prevents later approval/rejection and informs concerned roles. | Domain state machine + service + outbox | Withdrawal service, task closure, notification events. | Do not delete historical request/action records. |
| BR-EL-023 | Approved leave can be cancelled only before it begins; cancellation follows the original applicable hierarchy. | Domain + service | Cancellation request validation and cancellation workflow. | Once leave has started, use extension/resumption instead. |
| BR-EL-024 | After approved cancellation, revised leave is a fresh application; the approved request is not edited in place. | Domain + service | Cancellation decision/posting and new-application endpoint. | Preserve old request history. |
| BR-EL-025 | Extension is supported for ongoing EL/COL/VL and posts only incremental period if approved; rejection leaves original leave unchanged. | Domain + service + ledger | Extension validation, workflow transitions, incremental ledger posting. | Does not extend CL/RH/SCL under this baseline. |
| BR-EL-027 | Resumption applies to EL/COL/VL and is reviewed by applicable sanctioning authority. | Domain + service | Resumption submission/review services. | Normal/early/late handled according to BR-028. |
| BR-EL-028 | Normal resumption leaves approved period/balance unchanged; early/late return adjusts actual period and balance after review and synchronizes attendance/leave records. | Domain + service + integration contract | Resumption outcome service and downstream contract/event. | Adjustments only after review. |
| BR-EL-029 | Retrospective already-sanctioned leave is recorded with sanction/reference evidence and consistency validation; it synchronizes records/balance, not a second approval. | Service + ledger | Offline record service and audit/account entry. | Distinct from a new sanction workflow. |
| BR-EL-030 | Use current configured leave policy and hierarchy values, without a draft/publish/effective-version lifecycle. | Config selector + admin service | Current policy/hierarchy settings read by domain/services. | Student explicitly selected PS v1.4 §§5, 12. |
| BR-EL-031 | Date/RH validation uses the currently effective published holiday/RH calendar. | Domain + calendar selector | Current published calendar query. | Calendar itself has create/revise/publish lifecycle. |
| BR-EL-032 | Reminder is emitted/logged only if the SLA-controlled task is still pending at reminder threshold. | Scheduled task + service | `tasks.py`/scheduled processor and idempotent task service. | Event-triggered UC; no standalone workflow. |
| BR-EL-033 | Escalation occurs only when a task remains pending past escalation threshold; notify/escalate and log configured action. | Scheduled task + service | SLA processor and configured routing/responsibility action. | Skip tasks no longer pending. |
| BR-EL-034 | Submitted requests are not modified in place. | Service + API shape | State-changing commands; no general update endpoint for submitted requests. | Changes use withdrawal/fresh application. |
| BR-EL-035 | Assigned actionable workflow tasks notify the assigned user. | Service + outbox | Task assignment event and notification integration. | No generic notification for every intermediate state unless specified. |
| BR-EL-036 | Role-based authorization: ELM actions are limited to authenticated users with the required role permission. | API permission gates + scoped selectors + service-level actor checks where the action changes state. | Shared Fusion/IAM permission context and module selectors. | Do not reproduce IAM tables inside ELM; exact designation grants remain open. |
| BR-EL-037 | Administrative maintenance is not sanctioning: record maintenance must not create a new sanction decision. | Domain + service | Authorized leave-record maintenance/offline record services. | Keep maintenance and sanction commands distinct. |
| BR-EL-038 | Reminder/escalation thresholds are configurable and govern event-triggered SLA processing. | Config model + admin service + task processor | SLA settings and scheduled processor. | Use current configured thresholds. |

### 3.1 (a) Traceability table — active use cases

| ID | Use case / actor | Planned entry point and enforcement | Related rules / workflows from the supplied UC specification |
|---|---|---|---|
| EL-UC-001 | Apply for Leave — Employee | `POST /requests`; application service validates category, balance, counting, calendar, overlap, station leave, and substitute gates. | BR-EL-001–015, 020, 030–031, 036; CW-EL-01. |
| EL-UC-002 | Respond to Substitute Request — Substitute / Responsibility Holder | `POST /tasks/{id}/substitute-response`; service records accept/decline then applies WF transition. | BR-EL-014–015, 035–036; CW-EL-01, CW-EL-03. |
| EL-UC-003 | Review Leave-Related Request at Unit Head — Unit Head | `POST /requests/{id}/unit-head-review`; decision type depends on category/context. | BR-EL-016–020, 023, 025, 030, 036; CW-EL-01–03. |
| EL-UC-004 | Verify and Route Higher-Sanction Request — Establishment processing role | `POST /requests/{id}/route`; resolves next authority from current hierarchy. | BR-EL-018–019, 023, 025, 030, 036; CW-EL-01–03. |
| EL-UC-005 | Make Final Sanctioning Decision — configured Sanctioning Authority | `POST /requests/{id}/decision`; records final approval/rejection and context-specific effects. | BR-EL-004, 017–020, 023–025, 030, 036; CW-EL-01–03. |
| EL-UC-007 | Withdraw Pending Request — Employee | `POST /requests/{id}/withdraw`; transitions pending request to terminal withdrawn state and closes tasks. | BR-EL-022, 034, 036; CW-EL-01 and CW-EL-03 when applicable. |
| EL-UC-008 | Request Cancellation of Approved Leave — Employee | `POST /requests/{id}/cancellation`; creates cancellation request only before start. | BR-EL-023–024, 030, 036; CW-EL-02. |
| EL-UC-009 | Request Extension of Ongoing Leave — Employee | `POST /requests/{id}/extensions`; validate supported category and incremental interval. | BR-EL-001, 005–015, 017–019, 025, 030–031, 036; CW-EL-03. |
| EL-UC-010 | Submit Resumption of Duty — Employee | `POST /resumptions`; creates review-pending resumption record for EL/COL/VL. | BR-EL-027, 036; CW-EL-04. |
| EL-UC-011 | Review Resumption — Applicable Sanctioning Authority | `POST /resumptions/{id}/review`; normal/early/late outcome after authority review. | BR-EL-027–028, 036; CW-EL-04. |
| EL-UC-012 | View Leave Balances and History — Employee | `GET /me/balances`, `GET /me/history`; selectors restrict to the employee's own records. | BR-EL-036; workflow N/A. |
| EL-UC-013 | Obtain Printable/Exportable Leave Application — Employee | `GET /requests/{id}/export`; own-request selector and export permission. | BR-EL-036; workflow N/A. |
| EL-UC-014 | Maintain Policy and Hierarchy Configuration — Authorized administrative role | `GET/PUT /admin/policy`, `GET/PUT /admin/hierarchy`; current config only. | BR-EL-030, 036; workflow N/A. |
| EL-UC-015 | Maintain and Publish Holiday/RH Calendar — Authorized administrative role | `POST /admin/calendars`, `POST /admin/calendars/{id}/publish`; publishes a replacement calendar. | BR-EL-003, 031, 036; workflow N/A. |
| EL-UC-016 | Record Already-Sanctioned Offline Leave — Leave Administrator | `POST /admin/offline-leaves`; requires sanction/reference evidence and uses account synchronization, not approval. | BR-EL-029, 036–037; workflow N/A. |
| EL-UC-017 | Maintain Authorized Leave Records — Authorized administrative role | `POST/PUT /admin/leave-records`; maintenance action separated from approval/sanction. | BR-EL-036–037; workflow N/A. |
| EL-UC-018 | Configure Workflow SLA Thresholds — Authorized administrative role | `GET/PUT /admin/sla`; stores reminder/escalation threshold configuration. | BR-EL-038, 036; workflow N/A. |
| EL-UC-019 | Nominate Replacement Substitute After Decline — Employee | `POST /requests/{id}/replacement-substitute`; validates replacement and awaits consent again. | BR-EL-014–015, 022, 036; CW-EL-01, CW-EL-03. |
| EL-UC-020 | Execute Year-End Leave Processing — event-triggered | Management command/task; applies category lapse/carry-forward/conversion and writes account transactions. | BR-EL-002–009 and BR-EL-028 as applicable to the year-end outcome; event-triggered, not a human actor/workflow. |
| EL-UC-021 | Process SLA Threshold Event — event-triggered | Management command/task checks only still-pending tasks and applies configured reminder/escalation behavior. | BR-EL-032–033, 038; cross-cutting transition only where WF v1.6 specifies a routing-changing escalation. |

Retired IDs intentionally excluded as live targets: `EL-UC-006`, `BR-EL-021`, and `BR-EL-026`.

### 3.2 (b) Proposed domain model

These are approved proposed aggregates/components to map the supplied specification into the platform; exact field conventions follow the existing platform patterns.

| Model / component | Key data (logical) | Responsibilities / constraints |
|---|---|---|
| `LeaveRequest` | `id`, `employee_user_id`, category, start/end, CL half, purpose, station-leave fields, status, submitted timestamp, linked original request where applicable | One request lifecycle; no in-place modification after submission; actor identity stored as an IAM user ID, not a cross-module FK. |
| `WorkflowTask` | request/resumption reference, task kind, assigned user/role context, state, assigned/due/reminder/escalation timestamps | Tracks actionable assignments and current task state; notification on assignment; stale or completed tasks must not be reprocessed as pending. |
| `RequestAction` / history | request reference, actor user ID, action/outcome, timestamp, reason/evidence reference | Append-oriented action history for user-visible status/history and operations. |
| `LeaveAccount` + `LeaveLedgerEntry` | employee user ID, category/account, transaction type, amount, request/year-end source, timestamp | Balances derived/maintained via explicit entries for approval, incremental extension, cancellation adjustment, resumption adjustment, offline record and year end. Concurrency-sensitive balance changes use transactions/locking. |
| `SubstituteAssignment` | request reference, applicant user ID, substitute user ID, response, responsibility interval | Applicant differs from substitute; substitute must be an eligible employee and cannot overlap pending/approved leave; accepted consent gates onward routing. |
| `LeavePolicyConfig` | current leave entitlements/counting parameters and configuration values | Current configured values only; no effective-dated policy-version lifecycle. |
| `HierarchyConfig` | org-unit/designation/category routing facts and optional Establishment step | Stores current routing configuration; resolution belongs in domain/service layer. |
| `HolidayRHCalendar` + dates | calendar metadata, date, RH marker, publication state/time | Only currently effective published calendar is used for date/RH validation; calendar publication itself is supported. |
| `ResumptionRecord` | request/approved leave reference, actual resumption date, required details, review status, reviewed outcome | Supported only for EL/COL/VL; balance/period synchronization after required review for early/late return. |
| `OfflineSanctionRecord` | employee, category/interval, sanction/reference evidence, consistency outcome, source leave/account transaction | Synchronizes an already-authorized paper/offline leave; does not issue a second sanction. |
| `SLAConfig` | reminder threshold, escalation threshold, configured escalation action/routing behavior | Configuration used by event-triggered SLA processing; current values apply. |

Database-level constraint candidates: `start_date <= end_date`; unique calendar date within a calendar; non-negative configured threshold values; non-negative entitlement quantities. The overlap exception for first/second-half CL and concurrent balance allocation require domain-aware transactional enforcement rather than a simplistic uniqueness constraint. No identity/role tables or cross-module foreign keys are to be added.

### 3.3 (c) Declarative lifecycle/state model

Implement transitions as a declarative table or equivalent domain transition registry derived from `06_ELM_Workflow_Specifications_v1.6_FINAL.docx` STTs. Services submit explicit events; state transitions are not ad hoc view-level `if` chains. This summary is an overview; WF v1.6's STTs remain the source of exact guards and outcomes.

| Context | From state | Event / actor | Guard or outcome | Result |
|---|---|---|---|---|
| New leave, no substitute | Draft / Not Submitted | EL-UC-001 / Employee | Valid submission; no substitute required; applicant is not Director | Awaiting Unit Head Review |
| New leave, substitute required | Draft / Not Submitted | EL-UC-001 / Employee | Valid submission; required substitute | Awaiting Substitute Response |
| Substitute response | Awaiting Substitute Response | EL-UC-002 / Substitute | Accept and applicant is not Director | Awaiting Unit Head Review (or relevant Director self-sanction path) |
| Substitute response | Awaiting Substitute Response | EL-UC-002 / Substitute | Decline | Applicant Action Required |
| Replacement | Applicant Action Required | EL-UC-019 / Employee | Eligible replacement nominated | Awaiting Substitute Response |
| CL/RH review | Awaiting Unit Head Review | EL-UC-003 / Unit Head | CL/RH final outcome is Approve | Approved |
| CL/RH review | Awaiting Unit Head Review | EL-UC-003 / Unit Head | CL/RH final outcome is Reject | Rejected |
| Higher-sanction new leave | Unit Head review / recommendation completed | EL-UC-003 then optional EL-UC-004 then EL-UC-005 | Follow current hierarchy; Not Recommended is not final rejection | Final Approved or Rejected outcome |
| Pending withdrawal | Any still-pending supported request state | EL-UC-007 / Employee | Before final approval | Withdrawn; remaining tasks/actions terminated |
| Approved leave cancellation | Approved, before approved start | EL-UC-008 then applicable UC-003/004/005 | Applicable hierarchy decision | Cancelled with balance restoration/adjustment if approved; original approval unchanged if rejected |
| Extension | Ongoing EL/COL/VL | EL-UC-009 plus substitute/review/routing as required | Valid incremental period; required gates pass | Extension approved/rejected; original leave is preserved as the base |
| Resumption | Resumption Review Pending | EL-UC-011 / applicable authority | Normal/early/late actual return outcome | Normal leaves original balance/period unchanged; early/late sync actual period/balance after review |
| Year end | Event boundary | EL-UC-020 / system event | Current policy/year-end rules | Lapse CL/RH/SCL, carry EL/COL, convert unused faculty VL to EL; ledger records outcomes |
| SLA threshold | Task still pending at threshold | EL-UC-021 / time event | Reminder/escalation threshold reached and task remains pending | Notify/log; only apply routing change if explicitly configured and specified |

Workflow registry authority: `BW-EL-01` through `BW-EL-17` and `CW-EL-01` through `CW-EL-04` from Workflow v1.6. The 17 complete basis-workflow names are: New CL/RH — No Substitute Gate; New CL/RH — Substitute Accepted (No Loop); New CL/RH — Substitute Declined, Replacement Accepted (One Loop Traversal); New Higher-Sanction Leave — No Substitute Gate; New Higher-Sanction Leave — Substitute Accepted (No Loop); New Higher-Sanction Leave — Substitute Declined, Replacement Accepted (One Loop Traversal); Director Self-Sanction — No Substitute Gate; Director Self-Sanction — Substitute Accepted (No Loop); Director Self-Sanction — Substitute Declined, Replacement Accepted (One Loop); CL/RH Approved-Leave Cancellation; Higher-Sanction Approved-Leave Cancellation; Ongoing Leave Extension — No Substitute Gate; Ongoing Leave Extension — Substitute Accepted (No Loop); Ongoing Leave Extension — Substitute Declined, Replacement Accepted (One Loop Traversal); Normal Resumption Review; Early Resumption Review; Late Resumption Review. Composite workflows: New Leave Processing and Pending Withdrawal; Approved Leave Cancellation; Ongoing Leave Extension; Resumption Review.

### 3.4 (d) Permission manifest plan

Permission syntax must follow `docs/02-iam/rbac-model.md`: `<module_code>.<singular_resource>.<closed_list_verb>`. Candidate permission names for blueprint discussion:

- `leave.request.view`, `leave.request.create`, `leave.request.review`, `leave.request.approve`, `leave.request.assign`, `leave.request.revoke`
- `leave.workflow_task.view`, `leave.workflow_task.update`, `leave.workflow_task.assign`
- `leave.balance.view`, `leave.application.export`, `leave.resumption.create`, `leave.resumption.review`
- `leave.policy.manage`, `leave.hierarchy.manage`, `leave.calendar.manage`, `leave.calendar.publish`
- `leave.record.manage`, `leave.sla.manage`, `leave.account.update`

These are candidates, not a finalized manifest. Resource/verb choices and which are dangerous must be reconciled with the exact actions in the approved blueprint. Do not use a verb outside the repository's closed list (`view`, `create`, `update`, `delete`, `approve`, `publish`, `review`, `assign`, `revoke`, `export`, `import`, `restore`, `manage`).

Candidate system-only permission coverage for event processing should be kept narrowly scoped and expressed using approved resource/action names, not granted to a human designation. Exact `SYSTEM_PERMISSIONS`, `MODULE`, and `ROLE_GRANTS` cannot be finalized until the mentor confirms the designation names available in the fixture/IAM. Logical actor labels in the ELM documents are not automatically literal ERP designation names. `faculty` and `staff` may be built-in identity kinds; confirm how the seed helper represents them before grants are made.

### 3.5 (e) Planned endpoint list

All paths below are relative to `/api/v1/leave/`. Each endpoint needs the authentication/permission gate and selector scope described below; the listed routes are a proposed interface, not a claim that they exist now.

| Method + path | Action / response | Gate / scope |
|---|---|---|
| `POST requests` | Submit a new application; return request + current state | `leave.request.create`; applicant is current user |
| `GET requests` | List requests visible to current actor/task scope | `leave.request.view`; selectors scope by applicant or assigned action |
| `GET requests/{id}` | Request summary/history for authorized view | `leave.request.view`; request/task scope |
| `POST requests/{id}/substitute-response` | Accept/decline assigned substitute task | task update/review permission; assigned substitute only |
| `POST requests/{id}/unit-head-review` | Record permitted Unit Head decision/recommendation | review permission; resolved Unit Head assignment |
| `POST requests/{id}/route` | Complete configured Establishment routing step | assign permission; only when step configured |
| `POST requests/{id}/decision` | Final approve/reject | approve permission; resolved final authority |
| `POST requests/{id}/withdraw` | Withdraw pending request | revoke permission; applicant ownership and pending-state guard |
| `POST requests/{id}/cancellation` | Start pre-start cancellation request | create permission; approved original leave not started |
| `POST requests/{id}/extensions` | Start extension request | create permission; ongoing EL/COL/VL only |
| `POST resumptions` | Submit actual resumption | create permission; current user's supported leave |
| `POST resumptions/{id}/review` | Review resumption and apply defined outcome | review/approve permission; assigned authority |
| `GET me/balances` | Current employee leave balances | balance view; current employee only |
| `GET me/history` | Leave request/account history | request/balance view; current employee only |
| `GET requests/{id}/export` | Printable/exportable leave application | export permission; request view scope |
| `GET/PUT admin/policy` | View/update current policy configuration | manage permission; authorized administrator |
| `GET/PUT admin/hierarchy` | View/update current routing hierarchy configuration | manage permission; authorized administrator |
| `POST admin/calendars` | Create/revise holiday/RH calendar | manage permission; authorized administrator |
| `POST admin/calendars/{id}/publish` | Publish calendar and make it effective | publish permission; authorized administrator |
| `POST admin/offline-leaves` | Record already-sanctioned offline leave with evidence | manage permission; Leave Administrator only |
| `POST/PUT admin/leave-records` | Maintain authorized records without sanction | manage permission; authorized maintenance role |
| `GET/PUT admin/sla` | View/change reminder/escalation thresholds | manage permission; authorized administrator |

Sidebar item proposal for IAM-generated navigation: `id/code: leave`, `label: Leave`, `icon: calendar-check`, `base_path: /leave`, with individual nav links for employee requests/balances, assigned tasks, and authorized administration. The exact role-filtered nav items must match frontend routes and permissions; do not grant the module broadly just to make it visible during a demo.

### 3.6 (f) Contracts and integration dependencies

- Use `modules/directory/contracts.py` for batched user identity lookups (`get_users(user_ids)`) and employee projections; never join to another module's tables or the ERP `auth_user` table directly.
- The architecture context map states that Leave needs HR-owned `get_employments(user_ids)`; the provided source ZIP has no HR domain app. Treat the HR contract as a dependency to confirm/add through the contract interface rather than querying `fusionlab` or inventing HR tables.
- Vacation-period applicability for VL depends on the external Academic Calendar service/module. Obtain or request a plural/batched contract such as `get_vacation_periods(...)` from its owner; no direct cross-database access.
- If resumption must synchronize attendance records, expose/request an explicit contract or event with the attendance-owning module; do not write to its database.
- ELM's own request/balance/config data remains in `fusion_integrated`; IAM/RBAC remains in `fusion_system_db`; employee/ERP ownership stays with the authoritative upstream systems.

### 3.7 (g) Scheduled work plan

| Job | Trigger/cadence | Planned operation | Failure concern |
|---|---|---|---|
| `year_end_leave_processing` | Configured year-end boundary/event | Apply lapse/carry-forward/VL-to-EL conversion, write ledger entries, report exceptions. | Missed/double posting could leave accounts unsynchronized; use idempotent per-period transactions. |
| `sla_threshold_processing` | Configured periodic schedule or threshold event | Check pending actionable tasks, send reminder/escalation only at configured thresholds, log outcome. | Reprocessing completed tasks can create stale notifications/escalations; use pending-state checks and idempotency. |

Use repository scheduling/outbox patterns. A job registry/cadence must be reconciled with the platform's actual Celery beat conventions before implementation. No standalone workflow is created for year-end or notification-only SLA processing, per Workflow v1.6.

### 3.8 (h) Open questions / stop conditions

1. **Resolved — specification path.** `SPEC_FOLDER_PATH=docs/09-leave/specs/` was confirmed by the student as the approved path; the originals have been copied there unchanged.
2. **Exact IAM designation strings are unavailable in this ZIP.** Need fixture/IAM role names for Unit Head, Establishment processing, sanctioning authorities, and Leave Administrator before `ROLE_GRANTS` can be finalized. Do not invent aliases.
3. **The RTM is v1.5 while workflows are v1.6.** Student approved WF v1.6 as authoritative. The bundle has no synchronized v1.6 RTM, so traceability rows using only CFR/AFR may use the v1.5 RTM where consistent; any conflicting workflow mapping is omitted/marked stale rather than silently harmonized.
4. **HR employment contract and Academic Calendar/attendance contracts are not included in this repository ZIP.** Their owners/interfaces need confirmation. Do not substitute direct database joins.
5. **Resolved — blueprint approval.** The student explicitly confirmed mentor approval on 2026-10-12. Role strings are derived from named ELM actors/roles in the provided specifications; where deployment IAM designation spellings differ, the manifest must use the actual canonical strings before it is seeded.
6. **Local model is not yet used.** Proposed candidate: `qwen2.5-coder:7b` via Ollama, if compatible with the instructor's model choice and hardware. Once approved, record the exact installed model tag, version, size, quantization and runtime from the local installation. Do not state it generated code until that has actually happened.

## 4. Professor's Assignment 6 scope restriction

After locally deployed model generation, permitted corrections only: file placement, imports, Django/frontend module registration, URL/route registration, dependency/configuration adjustment, expected interface-name adaptation, supplied-database/config wiring, and Fusion-specific structural mismatches. Out of scope: checking whether BRs are correctly implemented, searching for missing requirements, systematic functional correctness testing, workflow-logic repair, security hardening, maintainability improvement, and optimization. Record mechanical commands/results accurately; do not imply a thorough test campaign was run.

## 5. Status checklist

- [x] Module name confirmed: ELM.
- [x] Module code confirmed: `leave`.
- [x] Workflow v1.6 confirmed as authoritative for workflows/STTs.
- [x] Policy behavior resolved to follow ELM Problem Statement v1.4 current-config interpretation.
- [x] `SPEC_FOLDER_PATH=docs/09-leave/specs/` confirmed by the student.
- [x] Mentor approval of the blueprint confirmed by the student.
- [ ] Confirm exact deployed IAM designation strings before seeding the permission manifest.
- [ ] Selected local model is actually installed/run; model metadata recorded.
- [ ] Code is generated by that local model only after approval; integration/mechanical corrections only.
- [ ] Mentor separately authorizes push/PR.
- [ ] Google Form is submitted with real PR URL, roll numbers, and actual model/runtime details.

**Current state:** Phase 2 blueprint approval and source path are confirmed. The six original specs are staged in `docs/09-leave/specs/`. No application code or local-model inference has run yet because Ollama/model artifacts cannot be downloaded in this isolated container; code generation must run through the user's local Ollama installation. No branch push, pull request, or Google Form submission has been completed.
