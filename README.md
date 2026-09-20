# MetroLens (राष्ट्रीय विधिक मापविज्ञान पोर्टल)

**AI-Assisted Legal Metrology Compliance & Inspection System**  
Built for the Ministry of Consumer Affairs, Food & Public Distribution, Government of India.

---

## Overview

MetroLens is a digital metrology enforcement and verification platform engineered to automate package label inspections under the **Legal Metrology (Packaged Commodities) Rules, 2011**, **Food Safety and Standards Act, 2006**, and the **Jan Vishwas (Amendment of Provisions) Act, 2023**.

The system combines classical Computer Vision, Optical Character Recognition (OCR), and deterministic legal rulepacks with an AI Auditor to provide court-admissible inspection records adhering to **Section 65B of the Indian Evidence Act**.

---

## Architecture & Principles

MetroLens strictly separates probabilistic AI from deterministic rule evaluation:

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│ Multi-Panel     │ ----> │ Tesseract OCR   │ ----> │ Groq / Regex    │
│ Image Capture   │       │ (eng + hin)     │       │ Structured Field│
└─────────────────┘       └─────────────────┘       │ Extraction      │
                                                           │
                                                           ▼
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│ Legal Notice    │ <---- │ Deterministic   │ <---- │ Computer Vision │
│ Generation      │       │ Rule Engine v1  │       │ Metrology       │
│ (Form IN-1)     │       │ (15 PCR Rules)  │       │ (Cap-Height/Cal)│
└─────────────────┘       └─────────────────┘       └─────────────────┘
```

1. **OCR & Multi-Panel Stitching**: Extracts text and coordinate bounding boxes across all panels of packaged goods.
2. **Structured Field Extraction**: Groq LLM (`qwen/qwen3.8-27b`) or deterministic regex fallback extracts 14 mandatory declarations (MRP, Net Qty, FSSAI, Best Before, Packer Details, etc.).
3. **Computer Vision Metrology**:
   - Laplacian variance blur detection
   - Luminance histogram glare analysis
   - Ink-row vertical projection profiling for numeral cap-height measurement
   - ArUco marker fiducial scale calibration
   - Relative luminance contrast ratio calculation (ISO/IEC & WCAG standard)
4. **Deterministic Rule Engine (`v1.json`)**:
   - 100% deterministic evaluation of Rule 6(1)(a)-(g), Rule 7(2) Table-I numeral height, and Rule 9(1)(b) contrast.
5. **Enforcement & Jan Vishwas Routing**:
   - Automated routing between `COMPLIANT`, `IMPROVEMENT_NOTICE` (15-day statutory cure period for first offences), and `DIRECT` compounding proceedings under Section 48.
6. **Digital Chain of Custody**: SHA-256 digital hashing of image evidence buffers.

---

## Repository Structure

```
metrolens/
├── backend/                  # FastAPI Python backend
│   ├── alembic/              # Database migrations
│   ├── api/v1/               # REST API endpoints (inspections, enforcement, dashboard, rules)
│   ├── core/                 # Rule engine, database models, security, metrology
│   ├── ml/                   # OCR, AI auditor, Computer Vision, gazette rule sync
│   ├── rulepacks/            # Versioned Legal Metrology rule definitions (v1.json)
│   ├── tests/                # Automated pytest suite
│   ├── .env.example          # Environment configuration template
│   └── requirements.txt      # Python dependencies
│
├── frontend/                 # Next.js 15 Web Application
│   ├── app/                  # App Router pages (upload, results, history, dashboard, rules)
│   ├── components/           # Institutional Indian Government UI components
│   ├── lib/                  # Client-side API integration & utilities
│   ├── public/               # Static assets & emblems
│   └── .env.example          # Environment configuration template
│
└── .planning/                # Project roadmap, specs, and execution logs
```

---

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- Tesseract OCR (`brew install tesseract` on macOS / `apt install tesseract-ocr` on Linux)

---

### Backend Setup

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Create and activate virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Add your GROQ_API_KEY and GEMINI_API_KEY in .env
   ```

5. **Start the FastAPI server**:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
   API Documentation: `http://localhost:8000/docs`

---

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Configure environment variables**:
   ```bash
   cp .env.example .env.local
   ```

4. **Run the Next.js development server**:
   ```bash
   npm run dev
   ```
   Access the portal at `http://localhost:3000`

---

## License

Government of India &copy; 2026. Developed for statutory compliance under the Legal Metrology Act, 2009.
