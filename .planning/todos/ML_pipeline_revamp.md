# ML Pipeline Revamp
- Add explicit section for raw OCR extractions.
- Guarantee no hallucination (Temperature 0.0, Structured JSON Output).
- Directly pipe OCR text into deterministic Rule Engine.
- [FIXED] Upgrade API from `gemini-1.5-flash` to `gemini-2.5-flash` to fix the 404 Error that was blocking OCR extractions.
- [FIXED] Remove all hardcoded fallbacks from Next.js (e.g. `250 g`, `India`, `₹0.18/g`) which masked the Gemini crash by displaying fake data.
