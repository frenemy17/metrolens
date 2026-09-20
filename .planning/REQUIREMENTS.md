# Requirements

## Backend

### 1. Architecture Boundaries
- `/core/cv/`: Pure OpenCV+numpy math. Deterministic (homography, rectification, mm/px scale, ink-row height, blur, glare).
- `/core/rules/`: Pure Python rule engine over versioned JSON rulepacks. No ML/LLM calls.
- `/ml/`: ML operations isolated here (OCR text, category classifier, rule-sync extraction). Output always wrapped in `MLSuggestion{value, confidence}`. Never consumed directly by `/core/`.

### 2. Deterministic CV Math
- **Calibration:** 4-corner tap of a 30x30mm card -> refine with `cv2.cornerSubPix` -> `cv2.getPerspectiveTransform` -> scale.
- **Confidence:** >8% mismatch in opposite sides flags as `UNRELIABLE`.
- **Ink-row height:** Otsu-threshold ROI, measure dark pixel span * scale.
- **Guard-band:** Uncertainty U=0.15mm (doubled if UNRELIABLE). `|measured - threshold| < U` -> `CANNOT_DETERMINE`.
- **Testing:** Synthetic PIL image test must pass *first* before other features are built.

### 3. Rule Engine
- **JSON Rulepacks:** Versioned (e.g., `v1.json`, `v2.json` diffs). Driven by inspection date and `effective_from`.
- **Rules Covered:** Applicability (R3), Exemptions (R26), Mandatory Declarations (R6), Height (R7), Placement (R8), Manner (R9), Misleading (R12), Units (R13).
- **Rule Sync:** AI-assisted extraction from gazette (`emaap.gov.in`) -> admin review -> publish.

### 4. Data Model
- PostgreSQL: `officers`, `inspections`, `evidence_images`, `calibrations`, `measurements`, `rule_evaluations`, `audit_log`, `rulepacks`.
- Audit Log is append-only, never UPDATE.

### 5. API Surface
- **Auth:** JWT with roles (INSPECTOR, SUPERVISOR, ADMIN).
- **Inspections:** CRUD, search, image upload with synchronous blur/glare check.
- **Measurement:** Calibration & Measurement endpoints.
- **Verdict:** Rule evaluation & Verdict endpoints.
- **Audit:** Overrides & Audit log retrieval.
- **Reports:** PDF & DOCX generation (WeasyPrint/python-docx).
- **E-commerce Audit:** Cross-check declared details against public platform APIs.
- **Enforcement Workflow:** Manage state transitions (COMPLIANT, IMPROVEMENT_NOTICE_ISSUED, DIRECT_ENFORCEMENT, WEIGHING_REQUIRED).

## Web App
- **Stack:** Next.js 15, TypeScript, Tailwind. Government-tool serious UI.
- **Role-Aware Views:** Inspector (own tasks) vs. Supervisor/Admin (global).
- **Key Screens:** Login, Search, Detail (Viewer + Verdict + Override), New Form, Dashboard (Recharts), Admin Settings (Rulepacks, Sync, Users).

## Mobile App
- **Stack:** Flutter (shell) + Native Kotlin (capture).
- **Capabilities:** Offline-first design (sqflite queuing).
- **Authentication:** Firebase Auth -> Backend Token.
- **Capture Module (Kotlin + NDK):** Guided prompts, on-device blur, corner tap, pinch-zoom, ROI drag.
- **On-Device Pre-Check:** Fast ML Kit or PP-OCR-mobile text validation (UX aid only).
- **Evidence Stamp:** GPS (lat/lng), timestamp, officer ID, device session ID embedded in images/measurements.

## Non-Goals
- Never estimate weight from an image.
- No LLM in `/core/`.
- No AI-touched field is usable evidence without human confirmation.
