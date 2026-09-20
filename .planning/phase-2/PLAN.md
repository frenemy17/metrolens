# Phase 2 Plan: Rule Engine & Role-Based Auth

## Objective
Implement the pure Python deterministic rule engine, load the base Legal Metrology `v1` rulepack, and set up JWT-based Authentication and Role-Based Access Control (RBAC) for the API layer.

## Context
- **Rule Engine:** Must live strictly in `/core/rules/`. Evaluates measurements and inspection data against a versioned JSON rulepack without any ML dependency.
- **Rulepacks:** The `v1.json` rulepack must exactly mirror the structure provided in the initial spec (effective from 2018-01-01, mapping rules 3, 26, 6, 7, 8, 9, 12, 13).
- **Auth/RBAC:** Custom JWT issuance from the backend. Endpoints will use a `require_role()` dependency to distinguish between `INSPECTOR`, `SUPERVISOR`, and `ADMIN`.

## Tasks

### 1. Versioned JSON Rulepack
- **Task 1.1:** Create `backend/rulepacks/v1.json` containing the exact `v1` JSON structure specified in the requirements (applicability, exemptions, mandatory_declarations, height_table, placement, manner, misleading_quantity, unit_rules).

### 2. Core Rule Engine
- **Task 2.1:** Implement `backend/core/rules/engine.py`:
  - Load the appropriate rulepack based on the inspection's date and the rulepack's `effective_from` date.
  - Implement deterministic evaluation for `presence`, `format`, `pattern`, and `placement` checks.
  - Implement height table lookup (handling standard vs `blown_formed_molded_mm`).
  - Calculate verdicts: `PASS`, `FAIL`, `CANNOT_DETERMINE` (utilizing the G8 guard-band from Phase 1), or `SUSPECTED_NON_STANDARD`.

### 3. Authentication & RBAC
- **Task 3.1:** Implement `backend/core/security.py`:
  - JWT creation and decoding utilizing `python-jose` and `passlib`.
  - Password hashing utilities.
- **Task 3.2:** Implement `backend/api/deps.py`:
  - `get_current_user` dependency to extract and validate the JWT.
  - `RoleChecker` dependency class to enforce `INSPECTOR`, `SUPERVISOR`, and `ADMIN` access.

### 4. Verification Tests
- **Task 4.1:** Write `backend/tests/test_rule_engine.py`:
  - Unit test `v1` rulepack loading.
  - Test deterministic height evaluation against the `height_table` (e.g., standard vs molded material thresholds).
  - Test mandatory declaration presence logic and exemptions (e.g., `fast_food_packed_by_hotel_restaurant`).
- **Task 4.2:** Write `backend/tests/test_auth.py` to ensure role dependencies correctly allow/reject mock requests.

## Verification
- Run `pytest backend/tests/test_rule_engine.py` and `pytest backend/tests/test_auth.py`.
- Both must pass, proving the rule engine is completely deterministic and decoupled from ML.
