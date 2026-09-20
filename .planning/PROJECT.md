# MetroLens

## Overview
MetroLens is a Legal Metrology compliance-inspection system for SIH 2026 (PS 26034 — Ministry of Consumer Affairs, Dept. of Consumer Affairs). The system provides a unified REST API contract serving a Python backend, a web application, and a mobile application.

## Core Principles
- **Deterministic Pipeline:** AI/ML only assists, it never decides. The pipeline is strictly deterministic.
- **Accuracy:** The system is demoed and judged on correctness, relying heavily on deterministic computer vision math.
- **Architecture Enforcement:** Strict folder boundaries (`/core/cv/`, `/core/rules/`, `/ml/`) must be maintained.
- **Real Code:** No stubs; actual working code is required.

## Tech Stack
- **Backend:** Python 3.11, FastAPI + Pydantic v2, PostgreSQL via SQLAlchemy 2.0 (async) + Alembic.
- **Computer Vision:** OpenCV (headless) for pure, deterministic math operations.
- **OCR:** Tesseract (pytesseract, eng+hin) as primary, with optional EasyOCR/PP-OCR for confidence cross-check only.
- **Storage:** S3-shaped object storage (local disk in dev, Minio in Docker Compose).
- **Auth:** Backend issues custom JWTs; mobile uses Firebase Auth for identity which is exchanged for a backend token.
- **Web App:** Next.js 15 (App Router) + TypeScript + Tailwind.
- **Mobile App:** Flutter (Android-first, iOS-compatible) with native Android Kotlin + OpenCV NDK capture module.
