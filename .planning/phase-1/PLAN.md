# Phase 1 Plan: DB Models & Deterministic CV Foundation

## Objective
Establish the foundational data models for the Legal Metrology system and implement the deterministic computer vision math pipeline. This phase deliberately avoids ML/LLM dependencies to ensure a 100% deterministic foundation.

## Context
- **Data Model:** PostgreSQL via SQLAlchemy 2.0 (async). We need tables for `officers`, `inspections`, `evidence_images`, `calibrations`, `measurements`, `rule_evaluations`, `audit_log`, and `rulepacks`.
- **CV Pipeline:** `/core/cv/` must implement homography, rectification, mm/px scale, ink-row height, blur (Laplacian variance), and glare (saturated-pixel ratio).
- **Verification:** Synthetic PIL images will be used to test the CV math accuracy. This must pass before progressing.

## Tasks

### 1. Database Configuration & Models
- **Task 1.1:** Setup database connection logic in `backend/core/database.py` using `asyncpg` and SQLAlchemy.
- **Task 1.2:** Create SQLAlchemy models in `backend/core/models.py`:
  - `Officer` (id, name, role, auth)
  - `Inspection` (id, officer_id, status, etc.)
  - `EvidenceImage` (id, inspection_id, type, gps_lat, gps_lng, device_session_id)
  - `Calibration` (id, inspection_id, mm_px_scale, confidence_flag)
  - `Measurement` (id, inspection_id, image_id, text, height_mm, gps_lat, gps_lng, device_session_id)
  - `RuleEvaluation` (id, inspection_id, rule_id, status)
  - `AuditLog` (append-only)
  - `Rulepack` (versioned JSON)
- **Task 1.3:** Configure Alembic (`alembic.ini`, `env.py`) to support async SQLAlchemy and generate the initial migration script.

### 2. Core CV Pipeline
- **Task 2.1:** Implement image quality checks in `backend/core/cv/quality.py`:
  - Blur detection (Laplacian variance).
  - Glare detection (saturated pixel ratio).
- **Task 2.2:** Implement deterministic calibration in `backend/core/cv/calibration.py`:
  - `cv2.cornerSubPix` refinement of 4 tapped corners.
  - `cv2.getPerspectiveTransform` and `cv2.warpPerspective`.
  - Calculate `mm_per_px` (30x30mm reference card).
  - Calculate confidence (>8% mismatch on opposite sides flags as `UNRELIABLE`).
- **Task 2.3:** Implement measurement in `backend/core/cv/measurement.py`:
  - Otsu thresholding of the ROI crop.
  - Ink-row height calculation (measure dark pixel span * scale).

### 3. Synthetic Verification Tests
- **Task 3.1:** Write synthetic testing framework in `backend/tests/test_cv.py`:
  - Generate a synthetic PIL image with a known square size (representing the 30x30mm card) and known text height.
  - Apply the calibration and measurement pipeline to this image.
  - Assert the computed `mm_per_px` and text height matches the true values within a tight tolerance.

## Verification
- Run `pytest backend/tests/test_cv.py`.
- The tests MUST pass synthetically before executing Phase 2.
