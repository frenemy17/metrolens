# Phase 5 Plan: E-commerce Audit & Enforcement Workflow

## Objective
Implement the backend modules to handle Rule 6(10) E-commerce declaration checks and to manage the post-inspection state transitions (Enforcement Workflow) for issuing and tracking legal notices.

## Context
- **E-Commerce Audit:** Under Rule 6(10), e-commerce platforms must display specific mandatory declarations (everything from Rule 6(1) except the manufacturing date) on the digital listing. We need an endpoint to simulate scraping/fetching an e-commerce listing and evaluating it against the rule engine.
- **Enforcement Workflow:** When a physical or digital inspection results in `FAIL` or `SUSPECTED_NON_STANDARD`, the system must facilitate state transitions. The workflow moves an inspection from `COMPLETED` -> `IMPROVEMENT_NOTICE_ISSUED` -> `COMPLIANT` (if remediated) or `DIRECT_ENFORCEMENT` (if escalated). `WEIGHING_REQUIRED` is a special escalation for physical inspections.

## Tasks

### 1. E-Commerce Audit Endpoint
- **Task 1.1:** Implement `backend/api/v1/ecommerce.py`.
  - `POST /api/v1/ecommerce/audit`
  - Accepts a URL or JSON payload representing the digital listing's extracted text/metadata.
  - Utilizes the Phase 2 rule engine (`evaluate_mandatory_declarations`) with the `channel: "e-commerce"` context to verify compliance with Rule 6(10).
  - Creates a digital inspection record and returns the verdict.

### 2. Enforcement State Machine
- **Task 2.1:** Implement `backend/api/v1/enforcement.py`.
  - `POST /api/v1/inspections/{id}/enforce`
  - Allows `SUPERVISOR` or `ADMIN` roles to transition the state of a failed inspection.
  - Supported transitions: 
    - `COMPLETED (FAIL)` -> `IMPROVEMENT_NOTICE_ISSUED`
    - `COMPLETED (SUSPECTED_NON_STANDARD)` -> `WEIGHING_REQUIRED`
    - `IMPROVEMENT_NOTICE_ISSUED` -> `COMPLIANT` or `DIRECT_ENFORCEMENT`
  - Ensures state transitions are logged to the `audit.py` ledger.

### 3. API Routing
- **Task 3.1:** Register `ecommerce.py` and `enforcement.py` routers in `backend/main.py`.

### 4. Verification Tests
- **Task 4.1:** Write `backend/tests/test_api_ecommerce.py` to test that e-commerce specific rules (like ignoring mfg date but requiring MRP/origin) apply correctly.
- **Task 4.2:** Write `backend/tests/test_api_enforcement.py` to ensure RBAC protections on escalations and valid state machine transitions.

## Verification
- Run `pytest backend/tests/test_api_ecommerce.py backend/tests/test_api_enforcement.py`.
- Ensure e-commerce audits enforce Rule 6(10) properly and that the state transitions correctly map out the legal workflow.
