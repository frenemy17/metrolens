# Roadmap

## Phase 1: DB Models & Deterministic CV Foundation
- Define PostgreSQL database models and Alembic migrations.
- Implement `/core/cv/` module with strict deterministic mathematical logic.
- Create synthetic PIL image test for `cv2` logic.
- **Verification:** Synthetic PIL test must pass before moving forward.

## Phase 2: Rule Engine & Role-Based Auth
- Implement `/core/rules/` rule engine.
- Load `rulepacks/v1.json` with the mandated rules and testing for the rule engine.
- Implement Authentication and RBAC (JWT & roles).

## Phase 3: Inspection Flow & Capture Endpoints
- Build Inspections CRUD and search endpoints.
- Implement image upload with synchronous blur/glare validation.
- Build the `/calibrate` and `/measurements` endpoints.
- Integrate Tesseract in `/ml/` to return `MLSuggestion`.

## Phase 4: Verdict, Audit & Reporting
- Implement `/evaluate` and verdict generation.
- Implement the override flow and append-only `audit_log`.
- Generate PDF and DOCX reports.

## Phase 5: E-commerce Audit & Enforcement Workflows
- Implement E-commerce API cross-checking.
- Implement Legal Action State Machine (Enforcement Workflow).
- Create Dashboard summary and stats endpoints.

## Phase 6: Rule-Sync & Deployment
- Implement `/ml/rule_sync/` for AI-assisted amendment scraping.
- Finalize `docker-compose.yml` (API, Postgres, Minio).
- Generate `/docs/architecture.md`.

## Phase 7: Web Application (Next.js)
- Build out web app screens (Login, Inspections, Details, Dashboard, Admin views).

## Phase 8: Mobile Application (Flutter + Kotlin)
- Build out mobile app with offline-first capabilities.
- Implement the Native Kotlin + OpenCV NDK capture module.
