# ML Boundary

**WARNING: STRICT ARCHITECTURAL BOUNDARY**

This directory (`/ml/`) is the **ONLY** place in the MetroLens backend where Machine Learning models (such as OCR, Category Classifiers, or LLM wrappers for Rule Sync) are permitted to run.

## Rules of Engagement

1. **No ML in Core:** ML dependencies and weights must not leak into `/core/cv/` or `/core/rules/`.
2. **MLSuggestion Wrapper:** Every output generated in this directory must be wrapped in an `MLSuggestion` structure, typically containing `value` and `confidence` fields.
3. **No Direct Consumption:** Nothing in `/core/` may consume an `MLSuggestion` directly. It MUST be routed through an officer's explicit confirm/edit action (for field captures) or an admin's explicit publish action (for rule-syncs) before it becomes usable evidence or changes a verdict.

This deterministic boundary is critical for the legal credibility of the system.
