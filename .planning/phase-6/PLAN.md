# Phase 6 Plan: Rule-Sync & Admin Settings

## Objective
Implement the AI-assisted rule-sync pipeline to process uploaded gazette notifications, extract potential rule changes (as `MLSuggestion`s), and provide the administrative endpoints for human review and publication of new versioned JSON rulepacks.

## Context
- **Rule-Sync:** The Legal Metrology rules are occasionally amended via official gazette notifications (from `emaap.gov.in`). To keep the deterministic rule engine up-to-date, admins upload these PDFs.
- **ML Boundary:** Extracting JSON diffs from a PDF requires an LLM. This must be confined to `/ml/rule_sync.py`. The output must be explicitly framed as suggestions.
- **Admin Review:** A new rulepack version (e.g., `v2.json`) cannot become active until an `ADMIN` role explicitly reviews the AI's suggested diffs, confirms them, sets an `effective_from` date, and hits publish.

## Tasks

### 1. ML Rule Extraction
- **Task 1.1:** Implement `backend/ml/rule_sync.py`.
  - Simulate an LLM extraction pipeline that takes a PDF document (or raw text) and outputs a list of proposed rule changes.
  - Changes must be wrapped in the standard `MLSuggestion` format (e.g., indicating which rule ID is changing, the proposed new JSON structure, and a confidence score).

### 2. Admin Rulepack API
- **Task 2.1:** Implement `backend/api/v1/admin.py`.
  - `POST /api/v1/admin/rule-sync/upload`: Accepts a PDF/text file, calls `/ml/rule_sync.py`, and returns the unconfirmed `MLSuggestion`s.
  - `POST /api/v1/admin/rule-sync/publish`: Accepts the admin's finalized JSON diffs and a new version string (e.g., `v2`). It merges the changes into the current active rulepack, persists the new `v2.json` to the filesystem (or mock DB), and logs the action to the audit trail.

### 3. API Routing
- **Task 3.1:** Mount the `admin.py` router in `backend/main.py`.

### 4. Verification Tests
- **Task 4.1:** Write `backend/tests/test_api_admin.py` to test the upload and extraction logic.
- **Task 4.2:** Test the `publish` endpoint, ensuring that only users with the `ADMIN` role can trigger it (INSPECTOR/SUPERVISOR must receive 403 Forbidden). Ensure the new rulepack becomes accessible via the `RuleEngine`.

## Verification
- Run `pytest backend/tests/test_api_admin.py`.
- Validate the strict RBAC constraints and the successful generation of a new versioned rulepack.
