# Phase 4 Plan: Verdict, Audit & Reporting

## Objective
Implement the final evaluation flow triggering the rule engine, construct the immutable Audit Log system to track officer interactions (especially OCR confirmation), and develop the formal Evidence Report generation module.

## Context
- **Evaluation:** Once an officer has confirmed all measurements for an inspection, the `POST /inspections/{id}/evaluate` endpoint is called. This aggregates the confirmed data, passes it through the deterministic rule engine (built in Phase 2), and persists the verdict (`PASS`, `FAIL`, `SUSPECTED_NON_STANDARD`).
- **Audit Logs:** To satisfy legal requirements, every human decision (such as confirming or overriding an `MLSuggestion`) must be audited. This will be implemented at the API or DB boundary.
- **Reporting:** After evaluation, a formal summary (JSON or PDF representation) must be generated that details the exact mathematical offsets, calibration metrics, and the rulepack version applied.

## Tasks

### 1. Audit Logging
- **Task 1.1:** Implement audit logging utilities in `backend/core/audit.py`.
- **Task 1.2:** Integrate the audit logging into `backend/api/v1/inspections.py`. Specifically, when `PATCH /measurements/{id}` is called to confirm an OCR text, an entry must be appended to the inspection's audit trail detailing the user ID, original ML suggestion, and the human's final confirmed text.

### 2. Verdict Evaluation Endpoint
- **Task 2.1:** Implement `POST /api/v1/inspections/{id}/evaluate` in `backend/api/v1/inspections.py`.
  - Fetch all confirmed measurements tied to the inspection.
  - Execute `evaluate_mandatory_declarations`, `evaluate_height`, and `evaluate_misleading_wording` from `core.rules.engine`.
  - Aggregate the results into a final `PASS`, `FAIL`, or `SUSPECTED_NON_STANDARD` verdict.
  - Update the Inspection status to `COMPLETED` and persist the verdict details.

### 3. Evidence Reporting
- **Task 3.1:** Implement `backend/api/v1/reports.py`.
  - Define `GET /api/v1/inspections/{id}/report`.
  - Compile the inspection metadata, calibration proof (corners + scale), the individual measurements (including the deterministic mm height and the rule engine threshold), and the final verdict into a structured JSON payload (which can later be converted to PDF on the client or via a separate service).
- **Task 3.2:** Wire `reports.py` into `main.py` routing.

### 4. Verification Tests
- **Task 4.1:** Write `backend/tests/test_api_evaluate.py` to simulate a complete inspection flow: create -> upload -> calibrate -> measure -> confirm -> evaluate, and assert the final verdict correctly reflects the underlying rules.
- **Task 4.2:** Ensure audit trails are correctly registered in the mock DB during the confirmation step in the tests.

## Verification
- Run `pytest backend/tests/test_api_evaluate.py`.
- Ensure the verdict corresponds exactly to the strict Phase 2 deterministic engine logic.
