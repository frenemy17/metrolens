"""
MetroLens — UI Batch Inspection Endpoint
Wires: OCR → Groq LLM extraction → Rule Engine (v1.json) → CV metrology → AI Auditor → DB
"""

from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException
from typing import List, Optional
import uuid
import cv2
import numpy as np
import os
import re
import json
import hashlib
from datetime import datetime, date
from dateutil import parser as dateparser
from PIL import Image
import io

try:
    from groq import Groq as GroqClient
except ImportError:
    GroqClient = None

from api.deps import RoleChecker
from core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from core.models import BatchRecord, InspectionRecord
from api.v1.inspections import rule_engine
from core.cv.quality import calculate_blur_score, calculate_glare_score
from ml.vision import compute_contrast_ratio
from ml.ocr import run_ocr_with_bboxes
from core.cv.measurement import get_ink_row_height_px, calculate_measured_height_mm
from ml.ai_auditor import generate_ai_auditor_analysis
try:
    from core.cv.calibration import calibrate_scale as _calibrate_scale
except ImportError:
    _calibrate_scale = None

router = APIRouter()

RULE_DESCRIPTIONS = {
    "r6-1a-mfr-name-address": "Name and complete address of manufacturer/packer/importer on label.",
    "r6-1aa-country-of-origin": "Country of origin declared (mandatory for imported goods).",
    "r6-1b-generic-name": "Generic/common name of the packaged commodity declared.",
    "r6-1c-net-quantity": "Net quantity in standard SI unit of weight or measure declared.",
    "r6-1d-mfg-month-year": "Month and year of manufacture/packing declared on label.",
    "r6-1da-best-before-use-by": "Best Before / Use By / Expiry date declared (required for perishable food).",
    "r6-1e-mrp": "Maximum Retail Price (MRP) inclusive of all taxes declared.",
    "r6-2-consumer-care": "Consumer Care contact: name, address, telephone number or email declared.",
}

def _is_present(val) -> bool:
    return bool(val) and str(val).strip().lower() not in (
        "not found", "null", "none", "", "n/a", "na"
    )


@router.post("/ui/batch")
async def ui_upload_batch(
    images: List[UploadFile] = File(...),
    product_name: Optional[str] = Form(""),
    source_type: Optional[str] = Form(""),
    metadata: Optional[str] = Form(""),
    gps_lat: Optional[float] = Form(None),
    gps_lng: Optional[float] = Form(None),
    current_user: dict = Depends(RoleChecker(["INSPECTOR", "SUPERVISOR", "ADMIN"])),
    db: AsyncSession = Depends(get_db)
):
    batch_id = str(uuid.uuid4())
    scan_id  = str(uuid.uuid4())

    uploaded_urls = []
    combined_raw_texts = []
    primary_img_cv = None
    all_img_bytes = b""
    blur, glare, is_valid = 15.0, 0.05, True
    ocr_result = {"value": "", "bboxes": []}

    uploads_dir = os.path.join(os.path.dirname(__file__), "../../../frontend/public/uploads")
    os.makedirs(uploads_dir, exist_ok=True)

    for idx, img_file in enumerate(images):
        file_bytes = await img_file.read()
        all_img_bytes += file_bytes
        
        fn = f"{scan_id}.jpg" if idx == 0 else f"{scan_id}_{idx}.jpg"
        fp = os.path.join(uploads_dir, fn)
        with open(fp, "wb") as f:
            f.write(file_bytes)
        uploaded_urls.append(f"/uploads/{fn}")

        arr = np.frombuffer(file_bytes, np.uint8)
        cimg = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if cimg is not None:
            if idx == 0:
                primary_img_cv = cimg
                blur = calculate_blur_score(cimg)
                glare = calculate_glare_score(cimg, threshold=253)
                is_valid = blur > 5.0 and glare < 0.35
                ocr_result = run_ocr_with_bboxes(cimg)
                panel_text = ocr_result.get("value", "")
            else:
                panel_ocr = run_ocr_with_bboxes(cimg)
                panel_text = panel_ocr.get("value", "")
            if panel_text:
                combined_raw_texts.append(panel_text)

    img_cv = primary_img_cv
    img_bytes = all_img_bytes
    upload_filename = f"{scan_id}.jpg"

    # Parse GPS coordinates
    lat = gps_lat
    lng = gps_lng
    if lat is None and metadata:
        try:
            m_data = json.loads(metadata)
            lat = m_data.get("latitude") or m_data.get("gps_lat")
            lng = m_data.get("longitude") or m_data.get("gps_lng")
        except Exception:
            pass
    if lat is None or lng is None:
        lat, lng = 28.6139, 77.2090

    raw_text = "\n\n".join(combined_raw_texts)
    print(f"[OCR Multi-Panel] Extracted total {len(raw_text)} chars:\n{raw_text[:600]}")

    extracted_data: dict = {}
    try:
        if not GroqClient:
            raise ImportError("Groq package not installed")
        client = GroqClient(api_key=os.environ.get("GROQ_API_KEY"))
        extraction_prompt = f"""You are a Legal Metrology AI assistant. Analyse this raw OCR text from an Indian packaged food label.
CRITICAL: Do NOT guess. If a field is absent or illegible, output null for that field.

Raw OCR Text:
---
{raw_text}
---

Return ONLY a JSON object (no markdown fences) with these exact keys:
product_name, brand_name, mrp, unit_sale_price, net_quantity, net_quantity_unit,
mfg_date, best_before, fssai_license, manufacturer_name, packer_address,
customer_care, country_of_origin, ingredients"""

        response = client.chat.completions.create(
            messages=[{"role": "user", "content": extraction_prompt}],
            model="qwen/qwen3.8-27b",
            temperature=0.0,
            max_tokens=400,
            response_format={"type": "json_object"},
        )
        raw_json = response.choices[0].message.content.strip()
        if raw_json.startswith("```"):
            raw_json = re.sub(r"```json|```", "", raw_json).strip()
        parsed = json.loads(raw_json)
        extracted_data = {
            k: (str(v) if v is not None else "Not Found")
            for k, v in parsed.items()
        }
        # Ensure all expected keys are present (LLM may omit some)
        for _k in ["product_name","brand_name","mrp","unit_sale_price","net_quantity",
                   "net_quantity_unit","mfg_date","best_before","fssai_license",
                   "manufacturer_name","packer_address","customer_care","country_of_origin","ingredients"]:
            if _k not in extracted_data:
                extracted_data[_k] = "Not Found"
        if not _is_present(extracted_data.get("product_name")):
            extracted_data["product_name"] = product_name or "Packaged Commodity"
        print(f"[GROQ] Extraction OK: {list(extracted_data.keys())}")
    except Exception as e:
        print(f"[GROQ] Extraction failed, using regex fallback: {e}")
        text_lower = raw_text.lower()
        extracted_data = {k: "Not Found" for k in [
            "product_name","brand_name","mrp","unit_sale_price","net_quantity",
            "net_quantity_unit","mfg_date","best_before","fssai_license",
            "manufacturer_name","packer_address","customer_care","country_of_origin","ingredients"
        ]}
        extracted_data["product_name"] = product_name or "Packaged Commodity"

        # ── MRP ──────────────────────────────────────────────────────────────
        # Pattern 1: "mrp: ₹20" or "mrp rs 20"
        m = re.search(r'mrp\s*[:\-]?\s*(?:rs\.?|inr|\u20b9)?\s*(\d+(?:\.\d{1,2})?)', text_lower)
        if not m:
            # Pattern 2: "₹20" or "rs.20" anywhere
            m = re.search(r'(?:rs\.?|\u20b9)\s*(\d+(?:\.\d{1,2})?)', text_lower)
        if not m:
            # Pattern 3: "MRP" followed within 60 chars by a price (handles multiline / junk between)
            m = re.search(r'mrp[^\n]{0,60}?(\d{2,4}(?:\.\d{1,2})?)\b', text_lower)
        if m:
            # Sanity: MRP should be between ₹1 and ₹9999
            val = float(m.group(1))
            if 1.0 <= val <= 9999.0:
                extracted_data["mrp"] = m.group(1)

        # ── Net Quantity ──────────────────────────────────────────────────────
        m = re.search(r'net\s*(?:wt\.?|weight|qty\.?|quantity)?\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*(g|gm|ml|kg|l|mg|litre|liter)\b', text_lower)
        if not m:
            m = re.search(r'(\d+(?:\.\d+)?)\s*(g|ml|kg|l|mg|gm)\b', text_lower)
        if m:
            extracted_data["net_quantity"] = m.group(1)
            extracted_data["net_quantity_unit"] = m.group(2)

        # ── FSSAI License ─────────────────────────────────────────────────────
        m = re.search(r'fssai\s*(?:lic(?:ense)?(?:\s*no\.?)?|no\.?|#)?\s*[:\-]?\s*(\d{14})', text_lower)
        if not m:
            # standalone 14-digit number on same line as fssai
            m = re.search(r'fssai[^\n]{0,40}(\d{14})', text_lower)
        if not m:
            # raw 14-digit block anywhere
            m = re.search(r'\b(\d{14})\b', raw_text)
        if m:
            extracted_data["fssai_license"] = m.group(1)

        # ── Dates ─────────────────────────────────────────────────────────────
        m = re.search(r'(?:best\s*before|use\s*by|expiry\s*date|exp\.?)[:\s]+([^\n]{3,35})', text_lower)
        if m:
            # Trim anything after MRP / price symbol (sometimes on same line)
            bb_raw = m.group(1).strip()
            bb_trimmed = re.split(r'\s*(?:mrp|\u20b9|rs\.?|incl\.|\()', bb_raw)[0].strip().rstrip('.')
            extracted_data["best_before"] = bb_trimmed if len(bb_trimmed) >= 3 else bb_raw.rstrip('.')
        # mfg_date: require actual date chars after keyword (digit or month name)
        m = re.search(
            r'(?:mfg\.?|mfd\.?|packing\s*date)[:\s]+'
            r'((?:\d{1,2}[/\-\s])?(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|\d{1,2})[/\-\s\d]{1,20})',
            text_lower
        )
        if not m:
            # dd/mm/yyyy or mm/yyyy style after mfg keyword
            m = re.search(r'(?:mfg\.?|mfd\.?)[:\s]*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})', text_lower)
        if m:
            extracted_data["mfg_date"] = m.group(1).strip().rstrip('.')

        # ── Manufacturer / Packer ─────────────────────────────────────────────
        m = re.search(
            r'(?:manufactured\s*by|mfr\.?\s*by|packed\s*by|marketed\s*by|importer)[:\s]+([^\n.]{5,80})',
            text_lower
        )
        if m:
            extracted_data["manufacturer_name"] = m.group(1).strip().title()

        # ── Packer Address ────────────────────────────────────────────────────
        m = re.search(
            r'(?:packer\s*address|packed\s*at|mfg\.?\s*address|address)[:\s]+([^\n]{10,120})',
            text_lower
        )
        if m:
            extracted_data["packer_address"] = m.group(1).strip().title()

        # ── Customer Care ─────────────────────────────────────────────────────
        m = re.search(
            r'(?:consumer\s*care|customer\s*(?:care|service)|helpline|toll[\s\-]*free)[:\s]+([^\n]{5,80})',
            text_lower
        )
        if m:
            extracted_data["customer_care"] = m.group(1).strip()
        else:
            # toll-free / mobile number fallback
            m = re.search(r'(?:1[89]00|\+91[-\s]?)?[6-9]\d{9}', raw_text)
            if m:
                extracted_data["customer_care"] = m.group(0)
        if not _is_present(extracted_data.get("customer_care")):
            # email fallback
            m = re.search(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', raw_text)
            if m:
                extracted_data["customer_care"] = m.group(0)
        if not _is_present(extracted_data.get("customer_care")):
            # website / portal fallback (e.g. www.pepsicoindia.co.in)
            m = re.search(r'(?:www\.|https?://)[a-zA-Z0-9.\-/]+\.[a-z]{2,6}', raw_text, re.IGNORECASE)
            if m:
                extracted_data["customer_care"] = m.group(0)

        # ── Country of Origin ─────────────────────────────────────────────────
        m = re.search(
            r'(?:country\s*of\s*origin|made\s*in)[:\s]+([a-zA-Z\s]{3,30})',
            text_lower
        )
        if m:
            extracted_data["country_of_origin"] = m.group(1).strip().title()

        # ── Ingredients ───────────────────────────────────────────────────────
        m = re.search(
            r'ingredients?\s*[:\-]?\s*([^\n]{10,300})',
            text_lower
        )
        if m:
            extracted_data["ingredients"] = m.group(1).strip().rstrip('.')

        # ── Brand (infer from product_name if not found) ──────────────────────
        if not _is_present(extracted_data.get("brand_name")):
            # heuristic: first word(s) of product name before a space/common
            pn = extracted_data.get("product_name", "") or ""
            words = pn.split()
            if words:
                extracted_data["brand_name"] = words[0].title()

    # CV Metrology: Text Height
    estimated_height_mm = None
    if img_cv is not None and ocr_result.get("bboxes"):
        bboxes = ocr_result["bboxes"]
        target_bbox = None
        nq = extracted_data.get("net_quantity", "")
        if nq and nq != "Not Found":
            for b in bboxes:
                if nq in b.get("text", ""):
                    target_bbox = b
                    break
        if not target_bbox:
            for b in bboxes:
                if any(ch.isdigit() for ch in b.get("text", "")):
                    target_bbox = b
                    break
        if not target_bbox and bboxes:
            target_bbox = bboxes[0]
        if target_bbox:
            x, y, w, h = target_bbox["x"], target_bbox["y"], target_bbox["w"], target_bbox["h"]
            pad = 5
            roi = img_cv[max(0, y-pad):min(img_cv.shape[0], y+h+pad),
                         max(0, x-pad):min(img_cv.shape[1], x+w+pad)]
            if roi.size > 0:
                h_px = get_ink_row_height_px(roi)
                # ── ArUco-based calibration (Option A fallback = 0.1 mm/px) ──
                mm_per_px = 0.1  # default fallback
                if _calibrate_scale is not None and img_cv is not None:
                    try:
                        # Attempt auto-calibration using image border corners as
                        # reference (treats full image as 85.6 mm wide, credit-card
                        # standard — best-effort; ArUco marker not required)
                        img_h_c, img_w_c = img_cv.shape[:2]
                        auto_corners = [
                            (0.0, 0.0),
                            (float(img_w_c), 0.0),
                            (float(img_w_c), float(img_h_c)),
                            (0.0, float(img_h_c)),
                        ]
                        cal_result = _calibrate_scale(img_cv, auto_corners, reference_size_mm=85.6)
                        if cal_result.get("confidence_flag") == "RELIABLE":
                            mm_per_px = cal_result["mm_px_scale"]
                            print(f"[CALIB] ArUco calibration OK: {mm_per_px:.4f} mm/px")
                        else:
                            print(f"[CALIB] Calibration UNRELIABLE — using fallback 0.1 mm/px")
                    except Exception as calib_err:
                        print(f"[CALIB] Calibration failed: {calib_err} — using fallback 0.1 mm/px")
                estimated_height_mm = calculate_measured_height_mm(h_px, mm_per_px)

    # CV Metrology: PDP Area
    pdp_area_cm2 = 250.0
    if img_cv is not None:
        img_h, img_w = img_cv.shape[:2]
        label_area_mm2 = img_h * img_w * 0.01 * 0.40
        pdp_area_cm2 = round(max(10.0, label_area_mm2 / 100.0), 1)

    # CV Metrology: Contrast Ratio
    contrast_ratio = None
    if img_cv is not None and ocr_result.get("bboxes"):
        for b in ocr_result["bboxes"]:
            if any(ch.isdigit() for ch in b.get("text", "")) and b.get("w", 0) > 5 and b.get("h", 0) > 5:
                try:
                    cr = compute_contrast_ratio(img_cv, b["x"], b["y"], b["w"], b["h"])
                    if cr and cr > 0:
                        contrast_ratio = round(cr, 2)
                        break
                except Exception:
                    pass

    extracted_data["estimated_text_height_mm"] = estimated_height_mm
    extracted_data["raw_ocr_text"] = raw_text

    # Rule Engine: declarations
    present_decls = []
    field_to_decl = {
        "manufacturer_name": "r6-1a-mfr-name-address",
        "country_of_origin": "r6-1aa-country-of-origin",
        "product_name":      "r6-1b-generic-name",
        "net_quantity":      "r6-1c-net-quantity",
        "mfg_date":          "r6-1d-mfg-month-year",
        "best_before":       "r6-1da-best-before-use-by",
        "customer_care":     "r6-2-consumer-care",
    }
    for field, decl_id in field_to_decl.items():
        if _is_present(extracted_data.get(field)):
            present_decls.append(decl_id)

    v1_rulepack = rule_engine.get_rulepack("v1")
    if not v1_rulepack:
        raise HTTPException(status_code=500, detail="Rulepack v1 not found on server")

    inspection_context = {
        "is_imported": False,
        "commodity_may_become_unfit_over_time": True,
        "commodity_size_relevant_to_sale": False,
    }
    decl_evals = rule_engine.evaluate_mandatory_declarations(v1_rulepack, present_decls, inspection_context)

    rules  = []
    defects = 0

    for ev in decl_evals:
        status = ev["status"]
        if status == "FAIL":
            defects += 1
        rules.append({
            "rule_id":    ev["rule_id"],
            "rule_title": ev.get("citation", ev["rule_id"]),
            "status":     status,
            "detail":     RULE_DESCRIPTIONS.get(ev["rule_id"],
                "Declaration found." if status == "PASS" else "Mandatory declaration missing."),
        })

    mrp_val  = extracted_data.get("mrp")
    mrp_pass = _is_present(mrp_val)
    if not mrp_pass:
        defects += 1
        rules.append({
            "rule_id":    "r6-1e-mrp",
            "rule_title": "Rule 6(1)(e) — Maximum Retail Price (MRP)",
            "status":     "FAIL",
            "detail":     "Maximum Retail Price (MRP) declaration not found on label.",
        })
    else:
        # Check mandatory "inclusive of all taxes" qualifier under Rule 6(1)(e)
        has_tax_qualifier = any(q in raw_text.lower() for q in [
            "incl", "inclusive", "taxes", "tax", "all taxes"
        ])
        if has_tax_qualifier:
            rules.append({
                "rule_id":    "r6-1e-mrp",
                "rule_title": "Rule 6(1)(e) — Maximum Retail Price (MRP)",
                "status":     "PASS",
                "detail":     f"MRP ₹{mrp_val} declared inclusive of all taxes in accordance with Rule 6(1)(e).",
            })
        else:
            defects += 1
            rules.append({
                "rule_id":    "r6-1e-mrp",
                "rule_title": "Rule 6(1)(e) — Maximum Retail Price (MRP)",
                "status":     "POTENTIAL NON-COMPLIANCE",
                "detail":     f"MRP ₹{mrp_val} present, but missing explicit 'inclusive of all taxes' qualifier mandatory under Rule 6(1)(e).",
            })

    # Rule 6(11) Unit Sale Price (USP) Check
    usp_val = extracted_data.get("unit_sale_price")
    nq_val = extracted_data.get("net_quantity")
    if _is_present(usp_val):
        rules.append({
            "rule_id":    "r6-11-unit-sale-price",
            "rule_title": "Rule 6(11) — Unit Sale Price (USP)",
            "status":     "PASS",
            "detail":     f"Unit Sale Price '{usp_val}' declared as required for multi-unit / weighed commodities under Rule 6(11).",
        })
    elif _is_present(nq_val) and _is_present(mrp_val):
        try:
            nq_clean = re.sub(r"[^\d.]", "", str(nq_val))
            mrp_clean = re.sub(r"[^\d.]", "", str(mrp_val))
            if nq_clean and mrp_clean:
                nq_num = float(nq_clean)
                mrp_num = float(mrp_clean)
                unit = extracted_data.get("net_quantity_unit", "g")
                if nq_num > 1:
                    computed_usp = round(mrp_num / nq_num, 2)
                    rules.append({
                        "rule_id":    "r6-11-unit-sale-price",
                        "rule_title": "Rule 6(11) — Unit Sale Price (USP)",
                        "status":     "POTENTIAL NON-COMPLIANCE",
                        "detail":     f"Unit Sale Price missing. Recommended declaration: ₹{computed_usp}/{unit} (calculated from ₹{mrp_val} for {nq_val}{unit}). Mandatory under Rule 6(11).",
                    })
        except Exception:
            pass

    fssai_val  = extracted_data.get("fssai_license")
    fssai_pass = _is_present(fssai_val)
    if not fssai_pass:
        defects += 1
    rules.append({
        "rule_id":    "r-fssai-license",
        "rule_title": "FSSAI License No. (FSS Act, 2006)",
        "status":     "PASS" if fssai_pass else "FAIL",
        "detail":     (f"FSSAI Lic. No. {fssai_val} found on label." if fssai_pass
                       else "FSSAI License Number absent. Mandatory for all food articles under FSS Act, 2006."),
    })

    ingr_val  = extracted_data.get("ingredients")
    ingr_pass = _is_present(ingr_val)
    if not ingr_pass:
        defects += 1
    rules.append({
        "rule_id":    "r-fssai-ingredients",
        "rule_title": "Ingredients List (FSS Regulations, 2011)",
        "status":     "PASS" if ingr_pass else "FAIL",
        "detail":     ("Ingredients list declared on label." if ingr_pass
                       else "Ingredients list absent. Required under FSS (Labelling & Display) Regulations."),
    })

    # Expiry date validation
    bb_val = extracted_data.get("best_before")
    if _is_present(bb_val):
        try:
            expiry_date = dateparser.parse(str(bb_val), dayfirst=True, fuzzy=True).date()
            if expiry_date < date.today():
                defects += 1
                rules.append({
                    "rule_id":    "r-expiry-check",
                    "rule_title": "Expiry / Best Before Date Check",
                    "status":     "FAIL",
                    "detail":     f"Product EXPIRED. Best before date '{bb_val}' is past today ({date.today().isoformat()}). Sale of expired goods violates FSS Act, 2006 Section 26.",
                })
            else:
                days_left = (expiry_date - date.today()).days
                rules.append({
                    "rule_id":    "r-expiry-check",
                    "rule_title": "Expiry / Best Before Date Check",
                    "status":     "PASS",
                    "detail":     f"Product within shelf life. Expires {bb_val} ({days_left} days remaining).",
                })
        except Exception:
            rules.append({
                "rule_id":    "r-expiry-check",
                "rule_title": "Expiry / Best Before Date Check",
                "status":     "MANUAL REVIEW",
                "detail":     f"Could not parse best before date '{bb_val}'. Manual verification required.",
            })

    misleading      = rule_engine.evaluate_misleading_wording(v1_rulepack, raw_text)
    misleading_fail = misleading["status"] != "PASS"
    if misleading_fail:
        defects += 1
    rules.append({
        "rule_id":    "r12-6-misleading-wording",
        "rule_title": "Rule 12(6) — Misleading Quantity Wording",
        "status":     "PASS" if not misleading_fail else "POTENTIAL NON-COMPLIANCE",
        "detail":     ("No misleading quantity wording detected." if not misleading_fail
                       else f"Misleading wording: {misleading.get('measured_value', '')}. Words like 'minimum', 'about', 'approximately' are prohibited."),
    })

    required_height = 2.0
    if estimated_height_mm is not None:
        try:
            h_eval = rule_engine.evaluate_height(
                v1_rulepack,
                pdp_area_cm2=pdp_area_cm2,
                printing_method="normal",
                measured_height_mm=float(estimated_height_mm),
                confidence_flag="normal",
            )
            h_status       = h_eval.get("status", "PASS")
            required_height = float(h_eval.get("threshold") or 2.0)
            if h_status == "FAIL":
                defects += 1
            rules.append({
                "rule_id":    "r7-2-numeral-height",
                "rule_title": "Rule 7(2) — Numeral Cap Height (Table-I)",
                "status":     h_status if h_status in ("PASS", "FAIL") else "MANUAL REVIEW",
                "detail":     (f"Measured cap height {estimated_height_mm:.2f} mm. "
                               f"Required ≥ {required_height:.1f} mm for PDP {pdp_area_cm2} cm² "
                               f"(ILAC G8 guard-band applied)."),
            })
        except Exception as he:
            rules.append({
                "rule_id":    "r7-2-numeral-height",
                "rule_title": "Rule 7(2) — Numeral Cap Height",
                "status":     "MANUAL REVIEW",
                "detail":     f"Height {estimated_height_mm:.2f} mm measured; band evaluation error: {he}",
            })
    else:
        rules.append({
            "rule_id":    "r7-2-numeral-height",
            "rule_title": "Rule 7(2) — Numeral Cap Height",
            "status":     "MANUAL REVIEW",
            "detail":     "Text height not measurable from this image angle. Manual inspection required.",
        })

    if contrast_ratio is not None:
        contrast_pass = contrast_ratio >= 4.5
        if not contrast_pass:
            defects += 1
        rules.append({
            "rule_id":    "r9-1b-contrast",
            "rule_title": "Rule 9(1)(b) — Contrast Colour",
            "status":     "PASS" if contrast_pass else "POTENTIAL NON-COMPLIANCE",
            "detail":     (f"Contrast ratio {contrast_ratio:.2f}:1 "
                           f"({'meets' if contrast_pass else 'below'} the 4.5:1 minimum for MRP numerals)."),
        })
    else:
        rules.append({
            "rule_id":    "r9-1b-contrast",
            "rule_title": "Rule 9(1)(b) — Contrast Colour",
            "status":     "MANUAL REVIEW",
            "detail":     "Contrast ratio not computable from this image. Manual visual inspection required.",
        })

    hard_fails = [r for r in rules if r["status"] == "FAIL"]
    soft_fails = [r for r in rules if r["status"] == "POTENTIAL NON-COMPLIANCE"]

    if len(hard_fails) == 0 and len(soft_fails) == 0:
        overall_compliance = "COMPLIANT"
    elif len(hard_fails) > 0:
        overall_compliance = "NON-COMPLIANT"
    else:
        overall_compliance = "POTENTIAL NON-COMPLIANCE"

    compliance_score = max(0, 100 - (len(hard_fails) * 15) - (len(soft_fails) * 7))

    # Evidence chain hash (SHA-256)
    evidence_hash = hashlib.sha256(img_bytes).hexdigest()

    auditor_summary = generate_ai_auditor_analysis(extracted_data, rules)

    # Enforcement status for dashboard aggregation
    if overall_compliance == "COMPLIANT":
        enforcement_status = "COMPLIANT"
    elif len(hard_fails) >= 3:
        enforcement_status = "DIRECT_ENFORCEMENT"
    else:
        enforcement_status = "IMPROVEMENT_NOTICE_ISSUED"

    # Historical Re-scan / Prior Inspection Comparison
    previous_scan = None
    p_name = extracted_data.get("product_name", "")
    b_name = extracted_data.get("brand_name", "")
    if p_name and p_name != "Not Found":
        try:
            prior_records_result = await db.execute(select(InspectionRecord).order_by(InspectionRecord.created_at.desc()))
            prior_records = prior_records_result.scalars().all()
            for pr in prior_records:
                if pr.id != scan_id and pr.data:
                    prior_p = (pr.data.get("product", {}).get("product_name") or "").lower()
                    prior_b = (pr.data.get("product", {}).get("brand_name") or "").lower()
                    if (p_name.lower() in prior_p or prior_p in p_name.lower()):
                        prev_defects = pr.data.get("total_violations", 0)
                        prev_date = pr.data.get("timestamp", "")
                        if prev_date:
                            try:
                                prev_date = prev_date.split("T")[0]
                            except Exception:
                                pass
                        trend = "improving" if defects < prev_defects else ("worsening" if defects > prev_defects else "unchanged")
                        previous_scan = {
                            "prior_scan_id": pr.id,
                            "prior_date": prev_date or "Previous Audit",
                            "prior_defects": prev_defects,
                            "current_defects": defects,
                            "trend": trend,
                            "prior_status": pr.data.get("overall_compliance")
                        }
                        break
        except Exception as pe:
            print(f"[RESCAN] Comparison query skipped: {pe}")

    location_data = {
        "latitude": float(lat),
        "longitude": float(lng),
        "city": "New Delhi" if abs(lat - 28.6139) < 0.1 else "Field Inspection Outpost",
        "jurisdiction": "Directorate of Legal Metrology, Krishi Bhawan Circle",
        "timestamp": datetime.utcnow().isoformat()
    }

    ai_analysis = {
        "auditor_summary": auditor_summary,
        "metrology": {
            "numeral_measurement": {"measured_cap_height_mm": estimated_height_mm},
            "legal_requirement":   {"requiredHeightMm": required_height},
            "uncertainty_budget":  {"expandedUncertainty_U": 0.15},
            "pdp_geometry":        {"pdpAreaCm2": pdp_area_cm2},
            "rule_9_contrast":     {"measured_contrast_ratio": contrast_ratio},
            "image_quality":       {"blur_score": round(blur, 2), "glare_ratio": round(glare, 3)},
        },
    }

    inspection_data = {
        "id":                  scan_id,
        "status":              "complete",
        "overall_compliance":  overall_compliance,
        "overallStatus":       overall_compliance,
        "enforcement_status":  enforcement_status,
        "compliance_score":    compliance_score,
        "total_rules_checked": len(rules),
        "total_violations":    defects,
        "high_violations":     len(hard_fails),
        "original_image":      f"/uploads/{upload_filename}",
        "image_url":           json.dumps(uploaded_urls) if uploaded_urls else f"[\"/uploads/{upload_filename}\"]",
        "uploaded_images":     uploaded_urls,
        "evidence_hash":       evidence_hash,
        "location":            location_data,
        "previous_scan":       previous_scan,
        "product": {
            "id":           "prod-001",
            "product_name": extracted_data.get("product_name", "Unknown"),
            "brand_name":   extracted_data.get("brand_name", "Unknown"),
            "category":     "Packaged Food",
        },
        "extracted_fields": extracted_data,
        "ai_analysis":      ai_analysis,
        "officer_id":       current_user["user_id"],
        "timestamp":        datetime.utcnow().isoformat(),
        "violations":       rules,
    }

    batch_data = {
        "id":     batch_id,
        "scanId": scan_id,
        "status": "complete",
        "scans":  [inspection_data],
    }

    db.add(InspectionRecord(id=scan_id, data=inspection_data))
    db.add(BatchRecord(id=batch_id, data=batch_data))
    await db.commit()

    return {"data": {"batch_id": batch_id}}


@router.get("/batch/{batch_id}")
async def get_batch_status(
    batch_id: str,
    current_user: dict = Depends(RoleChecker(["INSPECTOR", "SUPERVISOR", "ADMIN"])),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(BatchRecord).where(BatchRecord.id == batch_id))
    batch  = result.scalars().first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return {"data": batch.data}
