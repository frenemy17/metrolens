# Phase 3 Plan: Inspection Flow & Capture Endpoints

## Objective
Implement the main FastAPI routing layer for Inspections and image handling, integrate the `/ml/` OCR boundary, and connect the deterministic CV models created in Phase 1 to the HTTP API.

## Context
- **API Surface:** FastAPI application serving JSON over REST.
- **Image Upload:** Images are uploaded as `multipart/form-data`. They immediately undergo synchronous blur/glare validation using the CV quality checks from Phase 1 before being saved.
- **ML Boundary:** Tesseract OCR will be implemented in `/ml/ocr.py`. It MUST wrap results in an `MLSuggestion` dict/Pydantic model containing `value` and `confidence`. `/ml/README.md` must be created to document this strict boundary.

## Tasks

### 1. ML Boundary & OCR Integration
- **Task 1.1:** Create `backend/ml/README.md` explicitly stating that all models run here, outputs must be wrapped in `MLSuggestion`, and `/core/` never consumes these directly without human or rule-sync confirmation.
- **Task 1.2:** Implement `backend/ml/ocr.py` using `pytesseract`.
  - Process cropped ROI images.
  - Return `{"value": extracted_text, "confidence": conf_score}`.

### 2. Base API Configuration & Auth Routes
- **Task 2.1:** Implement `backend/api/v1/auth_routes.py` to handle `POST /auth/login` (verifying credentials or firebase IDs and returning JWT) and `GET /auth/me`.
- **Task 2.2:** Setup main FastAPI app in `backend/main.py` routing to `/api/v1/...` and configuring CORS.

### 3. Inspection & Image Routes
- **Task 3.1:** Implement `backend/api/v1/inspections.py`.
  - `POST /inspections` (Create).
  - `GET /inspections/search` (Search via trigram/query).
  - `GET /inspections/{id}` and `PATCH /inspections/{id}`.
- **Task 3.2:** Implement image upload route `POST /inspections/{id}/images`.
  - Accept `multipart/form-data` and tags (`PRIMARY_PANEL`, etc.).
  - Synchronously call `calculate_blur_score` and `calculate_glare_score`.
  - Return `pass/fail` boolean and scores.

### 4. Calibration & Measurement Routes
- **Task 4.1:** Implement `POST /inspections/{id}/calibrate`.
  - Accept image ID and 4 tapped corners.
  - Call `calibrate_scale()` from Phase 1.
  - Save result to database and return rectified context.
- **Task 4.2:** Implement `POST /inspections/{id}/measurements`.
  - Accept ROI coordinates, `declaration_type`, and `printing_method`.
  - Extract ROI from stored image.
  - Call `/ml/ocr.py` for OCR text (`MLSuggestion`).
  - Call `get_ink_row_height_px` and `calculate_measured_height_mm` from Phase 1.
  - Save Measurement to DB and return the payload.
- **Task 4.3:** Implement `PATCH /measurements/{id}` for officer confirmation/editing of the OCR text.

### 5. Verification Tests
- **Task 5.1:** Write `backend/tests/test_api_inspections.py` to mock `TestClient` API endpoints for Inspection CRUD and Image upload validation.
- **Task 5.2:** Write `backend/tests/test_api_measurements.py` to verify the Calibration and Measurement endpoints connect the CV and ML layers correctly.

## Verification
- Run `pytest backend/tests/test_api_inspections.py backend/tests/test_api_measurements.py`.
- Endpoints must respond with 200/201 and correct payload formats.
