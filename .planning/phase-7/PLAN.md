# Phase 7 Plan: Web Application (Next.js)

## Objective
Scaffold and build the MetroLens Web Application using Next.js 15 (App Router), TypeScript, and Tailwind CSS. The web app serves as the primary dashboard for Supervisors and Admins, and the case review portal for Inspectors.

## Context
- **Stack:** Next.js 15, TypeScript, Tailwind CSS, shadcn/ui (for serious, accessible, government-tool styling).
- **Architecture:** The web app will communicate with the FastAPI backend created in Phases 1-6 via a centralized API client layer.
- **Roles:** 
  - `INSPECTOR`: Can view and manage their own inspections, upload images (manual fallback to mobile), confirm OCR text, and evaluate cases.
  - `SUPERVISOR`: Dashboard analytics, view all inspections, trigger enforcement transitions (e.g. `IMPROVEMENT_NOTICE_ISSUED`).
  - `ADMIN`: Everything above, plus the `/admin/rule-sync` dashboard to upload gazette PDFs and review AI diffs for publishing.

## Tasks

### 1. Scaffold Next.js Application
- **Task 1.1:** Use `create-next-app` to scaffold the `webapp/` directory with App Router, TypeScript, and Tailwind.
- **Task 1.2:** Initialize shadcn/ui and configure a clean, high-contrast, "government-tool" theme.
- **Task 1.3:** Setup the centralized Axios/Fetch API client (`webapp/src/lib/api.ts`) with JWT interceptors for auth.

### 2. Core Authentication & Layout
- **Task 2.1:** Build the `/login` page and authentication context to store the JWT and user role.
- **Task 2.2:** Build a role-aware sidebar layout (`webapp/src/components/layout/Sidebar.tsx`) that conditionally renders navigation links (e.g., "Rule Sync" only visible to Admins).

### 3. Inspection Views & Overrides
- **Task 3.1:** Build the `/inspections` list view (Data Table) with status badges and search/filtering.
- **Task 3.2:** Build the `/inspections/[id]` detail view.
  - Display the uploaded images and overlay the bounding boxes/ROIs.
  - Render the **Measurement Confirmation Panel**: an explicit UI where the officer reviews the `MLSuggestion` and types in the confirmed text (triggering the backend `PATCH` route).
  - Include the "Evaluate" button to trigger the deterministic verdict and display the resulting report/audit log.

### 4. Admin Rule-Sync Dashboard
- **Task 4.1:** Build the `/admin/rules` dashboard.
  - Provide a file upload dropzone for Gazette PDFs.
  - Render a side-by-side diff view of the current rulepack vs. the AI's `MLSuggestion` for amendments.
  - Provide a "Publish Update" button.

## Verification
- Run Next.js local development server (`npm run dev`).
- Manually test login with the hardcoded users (`inspector1`, `supervisor1`, `admin1`).
- Verify role-based UI access and integration with the mocked local backend endpoints.
