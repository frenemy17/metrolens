# Phase 8 Plan: Mobile Application (Flutter + Kotlin)

## Objective
Develop the field application for Legal Metrology officers. This mobile app focuses on offline-first operation for rural physical inspections and features a Native Kotlin module bridging OpenCV C++ (via NDK) to perform real-time, deterministic capture validations (blur/glare) directly on the device.

## Context
- **Stack:** Flutter (UI, API client, local state) + Android Native Kotlin (OpenCV CameraX).
- **Core Requirement:** "Real code, not stubs." However, since a full Android build environment (SDK/NDK) exceeds the immediate web-centric sandbox, we will scaffold the Flutter project structure and author the critical Native Kotlin OpenCV bridge files to demonstrate the exact logic for edge-side deterministic math validation.
- **Offline-First:** Inspections must be capable of being stored in a local SQLite DB (e.g., `sqflite`) and synced via a bulk `/api/v1/inspections/sync` endpoint when network connectivity is restored.

## Tasks

### 1. Scaffold Mobile Project
- **Task 1.1:** Scaffold a directory structure under `mobile/` to represent the Flutter application.
- **Task 1.2:** Define the core `pubspec.yaml` with dependencies for HTTP, SQLite, and platform channels.

### 2. Native CameraX & OpenCV Module (Android)
- **Task 2.1:** Write the Kotlin Native Module (`mobile/android/app/src/main/kotlin/.../OpenCVCameraPlugin.kt`).
  - Implements the Flutter `MethodChannel` (`com.metrolens.cv/camera`).
  - Utilizes CameraX to intercept image frames.
  - Applies deterministic OpenCV math (Laplacian variance for blur, pixel thresholding for glare) locally, matching the backend's Python logic. This ensures bad photos are rejected *before* ever hitting the backend.

### 3. Offline Data Sync
- **Task 3.1:** Implement `mobile/lib/services/sync_service.dart`.
  - Defines the SQLite schema for caching pending inspections and captured image paths.
  - Implements a retry-loop that pushes `multipart/form-data` to the backend when the network state changes.

### 4. Field Inspection UI
- **Task 4.1:** Scaffold `mobile/lib/screens/capture_screen.dart`.
  - A Flutter UI wrapping the Native Camera View.
  - Displays real-time UI guides (e.g., "Too Blurry", "Glare Detected") driven directly by the Kotlin module's frame callbacks.
- **Task 4.2:** Scaffold `mobile/lib/screens/dashboard_screen.dart` showing pending sync queues and assigned physical inspections.

## Verification
- We will rely on static code analysis and structural validity for the Dart and Kotlin files, proving the architecture of the mobile edge-verification and offline-sync system.
