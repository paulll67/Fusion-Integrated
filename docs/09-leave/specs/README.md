# ELM Assignment 6 — source specification bundle

This folder contains the six supplied ELM source documents unchanged, plus searchable Markdown text extractions generated from them for local-model code generation. The original DOCX/XLSX files are authoritative; the Markdown files are convenience extracts.

## Confirmed assignment values

- Module name: Employee Leave Management (ELM)
- Module code / slug: `leave`
- Specification folder path: `docs/09-leave/specs/` (confirmed by the student as the instructor/mentor-approved path)
- Blueprint: `docs/09-leave/leave-blueprint.md` (mentor approval reported by the student)
- Runtime: `module-only` prompt shape for the current Fusion-Integrated repository; the local user environment still needs to have the IAM service and fixture configured per the guide.

## Source authority decisions

- Use Problem Statement v1.4 for leave policy/configuration semantics: current configured policy/hierarchy values, without an effective-version lifecycle for leave-policy parameters.
- Use Workflow Specifications v1.6 as authoritative for workflow names, IDs, and State-Transition Tables.
- The uploaded Traceability Matrix is v1.5 and contains older workflow references. Do not override Workflow v1.6 using conflicting older workflow mappings. CFR/AFR mappings from the RTM may be referenced where consistent.

## Professor's Assignment 6 boundary

Generate code using the selected open-source, locally deployed model. Subsequent corrections are limited to file placement, imports, module/route registration, dependency/configuration changes, expected interface names, supplied-database/config wiring, and Fusion-specific structural mismatches. Do not conduct additional bug finding, code review, systematic BR verification, workflow-logic repair, security hardening, maintainability work, optimization, or a thorough functional test campaign.
