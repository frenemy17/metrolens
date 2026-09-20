# TODO: Customize UI to Backend & Map Backend Features

**Status:** COMPLETED
**Created:** 2026-09-20T17:38:00+05:30

## Objective
Customize the Next.js UI to match the exact features supported by our Python FastAPI backend, and map any missing UI expectations to the backend.

## Details
- If the frontend relies on a feature that the backend doesn't have, implement the necessary endpoint/logic in the backend.
- Ensure all API calls (e.g., dashboard stats, rules list, scans/inspections) are correctly wired up with matching JSON payload structures.
- Remove or stub UI elements for features that are not part of the backend scope.

## Next Steps
- Audit the Next.js frontend code (e.g., `app/dashboard`, `app/results`, `app/rules`, `app/upload`) to identify all required API endpoints.
- Map each frontend request to the corresponding `/api/v1/inspections` or `/api/v1/auth` endpoint.
- Adjust the backend FastAPI models to output the JSON structure expected by the frontend (or vice-versa).
- Implement backend logic for any missing features (e.g., dashboard statistics).
