from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional
import uuid
import cv2
import numpy as np

from api.deps import get_current_user_payload, RoleChecker
from core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from core.cv.quality import calculate_blur_score, calculate_glare_score
from core.cv.calibration import calibrate_scale
from core.cv.measurement import get_ink_row_height_px, calculate_measured_height_mm
from ml.ocr import run_ocr
from core.audit import create_audit_log
from core.rules.engine import RuleEngine

router = APIRouter()

# Instantiate the rule engine at the module level
rule_engine = RuleEngine()

# DTOs
class InspectionCreate(BaseModel):
    category: Optional[str] = None
    channel: Optional[str] = None

class Point(BaseModel):
    x: float
    y: float

class CalibrateRequest(BaseModel):
    image_id: str
    corners: List[Point] # Must be 4 points
    reference_size_mm: float = 30.0

class MeasurementRequest(BaseModel):
    image_id: str
    roi_top_left: Point
    roi_bottom_right: Point
    declaration_type: str
    printing_method: str

class MeasurementUpdate(BaseModel):
    confirmed_text: str
    
class EvaluateRequest(BaseModel):
    pdp_area_cm2: float
    inspection_context: dict

# In-memory mock storage for files and DB records (to simulate execution)
mock_db = {
    "inspections": {},
    "images": {},
    "measurements": {},
    "audit_logs": {}
}
# A mock "S3" storage for numpy images
mock_s3 = {}

@router.post("")
async def create_inspection(
    inspection: InspectionCreate,
    current_user: dict = Depends(RoleChecker(["INSPECTOR", "SUPERVISOR", "ADMIN"]))
):
    insp_id = str(uuid.uuid4())
    mock_db["inspections"][insp_id] = {
        "id": insp_id,
        "officer_id": current_user["user_id"],
        "status": "DRAFT",
        "category": inspection.category,
        "channel": inspection.channel
    }
    return mock_db["inspections"][insp_id]

@router.get("/search")
async def search_inspections(
    q: Optional[str] = None,
    search: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 12,
    current_user: dict = Depends(RoleChecker(["INSPECTOR", "SUPERVISOR", "ADMIN"])),
    db: AsyncSession = Depends(get_db)
):
    import math
    from core.models import InspectionRecord
    from sqlalchemy.future import select
    
    result = await db.execute(select(InspectionRecord).order_by(InspectionRecord.created_at.desc()))
    records = result.scalars().all()
    items = [r.data for r in records if r.data]
    
    # Filter by status with synonyms
    if status:
        s_upper = status.strip().upper()
        if s_upper in ("NON-COMPLIANT", "FAIL", "POTENTIAL NON-COMPLIANCE"):
            target_statuses = {"NON-COMPLIANT", "FAIL", "POTENTIAL NON-COMPLIANCE", "IMPROVEMENT_NOTICE_ISSUED", "DIRECT_ENFORCEMENT"}
            items = [i for i in items if (
                (i.get("overall_compliance") or i.get("overallStatus") or i.get("status") or "").upper() in target_statuses
                or (i.get("enforcement_status") or "").upper() in target_statuses
            )]
        elif s_upper in ("COMPLIANT", "PASS"):
            target_statuses = {"COMPLIANT", "PASS"}
            items = [i for i in items if (
                (i.get("overall_compliance") or i.get("overallStatus") or i.get("status") or "").upper() in target_statuses
                or (i.get("enforcement_status") or "").upper() in target_statuses
            )]
        else:
            items = [i for i in items if (
                (i.get("overall_compliance") or i.get("overallStatus") or i.get("status") or "").upper() == s_upper
                or (i.get("enforcement_status") or "").upper() == s_upper
            )]
    
    # Text search across product name, brand name, id, and manufacturer
    query_term = (search or q or "").strip().lower()
    if query_term:
        items = [i for i in items if (
            query_term in (i.get("product", {}).get("product_name") or "").lower()
            or query_term in (i.get("product", {}).get("brand_name") or "").lower()
            or query_term in (i.get("extracted_fields", {}).get("product_name") or "").lower()
            or query_term in (i.get("extracted_fields", {}).get("brand_name") or "").lower()
            or query_term in (i.get("id") or "").lower()
        )]
    
    total_items = len(items)
    total_pages = max(1, math.ceil(total_items / max(1, limit)))
    start_idx = (max(1, page) - 1) * limit
    paged_items = items[start_idx : start_idx + limit]
    
    return {
        "data": {
            "scans": paged_items,
            "total_pages": total_pages,
            "total": total_items,
            "page": page,
            "limit": limit
        }
    }

@router.get("/{id}")
async def get_inspection(
    id: str, 
    current_user: dict = Depends(RoleChecker(["INSPECTOR", "SUPERVISOR", "ADMIN"])),
    db: AsyncSession = Depends(get_db)
):
    from core.models import InspectionRecord
    from sqlalchemy.future import select

    result = await db.execute(select(InspectionRecord).where(InspectionRecord.id == id))
    record = result.scalars().first()
    
    if not record:
        raise HTTPException(status_code=404, detail="Inspection not found")
    
    # Return both direct dict and wrapped in { "data": ... } for complete frontend compatibility
    return {"data": record.data, **(record.data or {})}

class InspectionUpdate(BaseModel):
    extractedFields: Optional[dict] = None
    extracted_fields: Optional[dict] = None
    productName: Optional[str] = None
    brandName: Optional[str] = None

@router.put("/{id}")
async def update_inspection(
    id: str,
    req: InspectionUpdate,
    current_user: dict = Depends(RoleChecker(["INSPECTOR", "SUPERVISOR", "ADMIN"])),
    db: AsyncSession = Depends(get_db)
):
    from core.models import InspectionRecord
    from sqlalchemy.future import select
    from sqlalchemy.orm.attributes import flag_modified
    import re
    from datetime import date
    from dateutil import parser as dateparser

    result = await db.execute(select(InspectionRecord).where(InspectionRecord.id == id))
    record = result.scalars().first()
    if not record:
        raise HTTPException(status_code=404, detail="Inspection not found")

    inspection = dict(record.data or {})
    extracted = dict(inspection.get("extracted_fields") or {})
    
    new_fields = req.extractedFields or req.extracted_fields or {}
    for k, v in new_fields.items():
        extracted[k] = v

    if req.productName:
        extracted["product_name"] = req.productName
    if req.brandName:
        extracted["brand_name"] = req.brandName

    inspection["extracted_fields"] = extracted

    prod = dict(inspection.get("product") or {})
    if extracted.get("product_name"):
        prod["product_name"] = extracted["product_name"]
    if extracted.get("brand_name"):
        prod["brand_name"] = extracted["brand_name"]
    inspection["product"] = prod

    def _is_present(val) -> bool:
        return bool(val) and str(val).strip().lower() not in (
            "not found", "null", "none", "", "n/a", "na"
        )

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
        if _is_present(extracted.get(field)):
            present_decls.append(decl_id)

    v1_rulepack = rule_engine.get_rulepack("v1")
    inspection_context = {
        "is_imported": False,
        "commodity_may_become_unfit_over_time": True,
        "commodity_size_relevant_to_sale": False,
    }
    
    decl_evals = rule_engine.evaluate_mandatory_declarations(
        v1_rulepack, present_decls, inspection_context
    ) if v1_rulepack else []

    rules = []
    defects = 0

    rule_descriptions = {
        "r6-1a-mfr-name-address": "Name and complete address of manufacturer/packer/importer on label.",
        "r6-1aa-country-of-origin": "Country of origin declared (mandatory for imported goods).",
        "r6-1b-generic-name": "Generic/common name of the packaged commodity declared.",
        "r6-1c-net-quantity": "Net quantity in standard SI unit of weight or measure declared.",
        "r6-1d-mfg-month-year": "Month and year of manufacture/packing declared on label.",
        "r6-1da-best-before-use-by": "Best Before / Use By / Expiry date declared (required for perishable food).",
        "r6-1e-mrp": "Maximum Retail Price (MRP) inclusive of all taxes declared.",
        "r6-2-consumer-care": "Consumer Care contact: name, address, telephone number or email declared.",
    }

    for ev in decl_evals:
        st = ev.get("status", "FAIL")
        if st == "FAIL":
            defects += 1
        rules.append({
            "rule_id": ev["rule_id"],
            "rule_title": ev.get("citation", ev["rule_id"]),
            "status": st,
            "detail": rule_descriptions.get(ev["rule_id"], "Declaration present." if st == "PASS" else "Mandatory declaration missing."),
        })

    # MRP Check
    mrp_val = extracted.get("mrp")
    raw_ocr = str(extracted.get("raw_ocr_text", "")).lower()
    if not _is_present(mrp_val):
        defects += 1
        rules.append({
            "rule_id": "r6-1e-mrp",
            "rule_title": "Rule 6(1)(e) — Maximum Retail Price (MRP)",
            "status": "FAIL",
            "detail": "Maximum Retail Price (MRP) declaration not found on label.",
        })
    else:
        has_tax = any(q in raw_ocr for q in ["incl", "inclusive", "taxes", "tax", "all taxes"]) or "incl" in str(mrp_val).lower()
        if has_tax:
            rules.append({
                "rule_id": "r6-1e-mrp",
                "rule_title": "Rule 6(1)(e) — Maximum Retail Price (MRP)",
                "status": "PASS",
                "detail": f"MRP ₹{mrp_val} declared inclusive of all taxes in accordance with Rule 6(1)(e).",
            })
        else:
            defects += 1
            rules.append({
                "rule_id": "r6-1e-mrp",
                "rule_title": "Rule 6(1)(e) — Maximum Retail Price (MRP)",
                "status": "POTENTIAL NON-COMPLIANCE",
                "detail": f"MRP ₹{mrp_val} present, but missing explicit 'inclusive of all taxes' qualifier mandatory under Rule 6(1)(e).",
            })

    # Unit Sale Price (USP)
    usp_val = extracted.get("unit_sale_price")
    nq_val = extracted.get("net_quantity")
    if _is_present(usp_val):
        rules.append({
            "rule_id": "r6-11-unit-sale-price",
            "rule_title": "Rule 6(11) — Unit Sale Price (USP)",
            "status": "PASS",
            "detail": f"Unit Sale Price '{usp_val}' declared as required under Rule 6(11).",
        })
    elif _is_present(nq_val) and _is_present(mrp_val):
        try:
            nq_clean = re.sub(r"[^\d.]", "", str(nq_val))
            mrp_clean = re.sub(r"[^\d.]", "", str(mrp_val))
            if nq_clean and mrp_clean:
                nq_num = float(nq_clean)
                mrp_num = float(mrp_clean)
                unit = extracted.get("net_quantity_unit", "g")
                if nq_num > 1:
                    computed_usp = round(mrp_num / nq_num, 2)
                    rules.append({
                        "rule_id": "r6-11-unit-sale-price",
                        "rule_title": "Rule 6(11) — Unit Sale Price (USP)",
                        "status": "POTENTIAL NON-COMPLIANCE",
                        "detail": f"Unit Sale Price missing. Recommended declaration: ₹{computed_usp}/{unit} (calculated from ₹{mrp_val} for {nq_val}{unit}). Mandatory under Rule 6(11).",
                    })
        except Exception:
            pass

    # FSSAI License
    fssai_val = extracted.get("fssai_license")
    fssai_pass = _is_present(fssai_val)
    if not fssai_pass:
        defects += 1
    rules.append({
        "rule_id": "r-fssai-license",
        "rule_title": "FSSAI License No. (FSS Act, 2006)",
        "status": "PASS" if fssai_pass else "FAIL",
        "detail": f"FSSAI Lic. No. {fssai_val} found on label." if fssai_pass else "FSSAI License Number absent. Mandatory for all food articles.",
    })

    # Ingredients
    ingr_val = extracted.get("ingredients")
    ingr_pass = _is_present(ingr_val)
    if not ingr_pass:
        defects += 1
    rules.append({
        "rule_id": "r-fssai-ingredients",
        "rule_title": "Ingredients List (FSS Regulations, 2011)",
        "status": "PASS" if ingr_pass else "FAIL",
        "detail": "Ingredients list declared on label." if ingr_pass else "Ingredients list absent. Required under FSS Regulations.",
    })

    # Expiry Check
    bb_val = extracted.get("best_before")
    if _is_present(bb_val):
        try:
            exp_date = dateparser.parse(str(bb_val), dayfirst=True, fuzzy=True).date()
            if exp_date < date.today():
                defects += 1
                rules.append({
                    "rule_id": "r-expiry-check",
                    "rule_title": "Expiry / Best Before Date Check",
                    "status": "FAIL",
                    "detail": f"Product EXPIRED. Best before date '{bb_val}' is past today ({date.today().isoformat()}).",
                })
            else:
                days_left = (exp_date - date.today()).days
                rules.append({
                    "rule_id": "r-expiry-check",
                    "rule_title": "Expiry / Best Before Date Check",
                    "status": "PASS",
                    "detail": f"Product within shelf life. Expires {bb_val} ({days_left} days remaining).",
                })
        except Exception:
            rules.append({
                "rule_id": "r-expiry-check",
                "rule_title": "Expiry / Best Before Date Check",
                "status": "MANUAL REVIEW",
                "detail": f"Could not parse best before date '{bb_val}'. Manual verification required.",
            })

    # Retain existing metrology evaluations (numeral height, contrast, etc.)
    old_violations = inspection.get("violations", [])
    for v in old_violations:
        vid = v.get("rule_id", "")
        if vid in ["r7-2-numeral-height", "r9-1b-contrast", "r12-6-misleading-wording"]:
            if v.get("status") == "FAIL":
                defects += 1
            rules.append(v)

    hard_fails = [r for r in rules if r["status"] == "FAIL"]
    soft_fails = [r for r in rules if r["status"] == "POTENTIAL NON-COMPLIANCE"]

    if len(hard_fails) == 0 and len(soft_fails) == 0:
        overall_compliance = "COMPLIANT"
    elif len(hard_fails) > 0:
        overall_compliance = "NON-COMPLIANT"
    else:
        overall_compliance = "POTENTIAL NON-COMPLIANCE"

    compliance_score = max(0, 100 - (len(hard_fails) * 15) - (len(soft_fails) * 7))

    inspection["violations"] = rules
    inspection["total_violations"] = defects
    inspection["high_violations"] = len(hard_fails)
    inspection["overall_compliance"] = overall_compliance
    inspection["overallStatus"] = overall_compliance
    inspection["compliance_score"] = compliance_score

    record.data = inspection
    flag_modified(record, "data")
    await db.commit()
    await db.refresh(record)

    return {
        "status": "success",
        "data": record.data,
        **(record.data or {})
    }

@router.post("/{id}/images")
async def upload_image(
    id: str,
    file: UploadFile = File(...),
    image_type: str = Form(...), # PRIMARY_PANEL, SIDE, BACK
    gps_lat: Optional[float] = Form(None),
    gps_lng: Optional[float] = Form(None),
    device_session_id: Optional[str] = Form(None),
    current_user: dict = Depends(RoleChecker(["INSPECTOR", "SUPERVISOR", "ADMIN"]))
):
    # Read image
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img_cv is None:
        raise HTTPException(status_code=400, detail="Invalid image file")

    # Synchronous quality checks
    blur = calculate_blur_score(img_cv)
    glare = calculate_glare_score(img_cv)
    
    # Example arbitrary thresholds for pass/fail
    is_valid = blur > 5.0 and glare < 0.35
    
    img_id = str(uuid.uuid4())
    mock_s3[img_id] = img_cv
    
    mock_db["images"][img_id] = {
        "id": img_id,
        "inspection_id": id,
        "image_type": image_type,
        "blur_score": blur,
        "glare_score": glare,
        "valid": is_valid,
        "gps_lat": gps_lat,
        "gps_lng": gps_lng,
        "device_session_id": device_session_id
    }
    
    return mock_db["images"][img_id]

@router.post("/{id}/calibrate")
async def calibrate_image(
    id: str,
    req: CalibrateRequest,
    current_user: dict = Depends(RoleChecker(["INSPECTOR", "SUPERVISOR", "ADMIN"]))
):
    img = mock_s3.get(req.image_id)
    if img is None:
        raise HTTPException(status_code=404, detail="Image not found")
        
    if len(req.corners) != 4:
        raise HTTPException(status_code=400, detail="Must provide exactly 4 corners")
        
    corners = [(pt.x, pt.y) for pt in req.corners]
    
    result = calibrate_scale(img, corners, req.reference_size_mm)
    
    # Store scale inside the image metadata (or a calibration table)
    mock_db["images"][req.image_id]["calibration"] = result
    
    return result

@router.post("/{id}/measurements")
async def create_measurement(
    id: str,
    req: MeasurementRequest,
    current_user: dict = Depends(RoleChecker(["INSPECTOR", "SUPERVISOR", "ADMIN"]))
):
    img = mock_s3.get(req.image_id)
    if img is None:
        raise HTTPException(status_code=404, detail="Image not found")
        
    calib = mock_db["images"][req.image_id].get("calibration")
    if not calib:
        raise HTTPException(status_code=400, detail="Image not calibrated")
        
    # Crop ROI
    x1, y1 = int(req.roi_top_left.x), int(req.roi_top_left.y)
    x2, y2 = int(req.roi_bottom_right.x), int(req.roi_bottom_right.y)
    
    roi_crop = img[y1:y2, x1:x2]
    
    if roi_crop.size == 0:
        raise HTTPException(status_code=400, detail="Invalid ROI dimensions")
        
    # 1. Deterministic Math
    height_px = get_ink_row_height_px(roi_crop)
    height_mm = calculate_measured_height_mm(height_px, calib["mm_px_scale"])
    
    # 2. ML Suggestion (OCR)
    ocr_suggestion = run_ocr(roi_crop)
    
    meas_id = str(uuid.uuid4())
    record = {
        "id": meas_id,
        "inspection_id": id,
        "image_id": req.image_id,
        "declaration_type": req.declaration_type,
        "printing_method": req.printing_method,
        "height_mm": height_mm,
        "ocr_suggestion": ocr_suggestion,
        "confirmed_text": None  # Requires human confirmation
    }
    
    mock_db["measurements"][meas_id] = record
    return record

@router.patch("/measurements/{meas_id}")
async def confirm_measurement(
    meas_id: str,
    update: MeasurementUpdate,
    current_user: dict = Depends(RoleChecker(["INSPECTOR", "SUPERVISOR", "ADMIN"]))
):
    if meas_id not in mock_db["measurements"]:
        raise HTTPException(status_code=404, detail="Measurement not found")
        
    meas = mock_db["measurements"][meas_id]
    old_text = meas.get("confirmed_text")
    meas["confirmed_text"] = update.confirmed_text
    
    # Generate Audit Log for the human-over-ML confirmation
    audit_entry = create_audit_log(
        inspection_id=meas["inspection_id"],
        user_id=current_user["user_id"],
        action="CONFIRM_OCR",
        entity_type="Measurement",
        entity_id=meas_id,
        changes={
            "ml_suggestion": meas["ocr_suggestion"]["value"],
            "old_confirmed_text": old_text,
            "new_confirmed_text": update.confirmed_text
        }
    )
    mock_db["audit_logs"][audit_entry["id"]] = audit_entry
    
    return meas

@router.post("/{id}/evaluate")
async def evaluate_inspection(
    id: str,
    req: EvaluateRequest,
    current_user: dict = Depends(RoleChecker(["INSPECTOR", "SUPERVISOR", "ADMIN"]))
):
    if id not in mock_db["inspections"]:
        raise HTTPException(status_code=404, detail="Inspection not found")
        
    v1_rulepack = rule_engine.get_rulepack("v1")
    if not v1_rulepack:
        raise HTTPException(status_code=500, detail="Rulepack v1 not found on server")
        
    # Get all measurements for this inspection
    inspection_measurements = [m for m in mock_db["measurements"].values() if m["inspection_id"] == id]
    
    # Assert all measurements are confirmed
    unconfirmed = [m for m in inspection_measurements if m["confirmed_text"] is None]
    if unconfirmed:
        raise HTTPException(status_code=400, detail=f"Cannot evaluate: {len(unconfirmed)} measurements not confirmed by officer")
        
    present_decls = []
    final_status = "PASS"
    evaluations = []
    
    for meas in inspection_measurements:
        decl_type = meas["declaration_type"]
        present_decls.append(decl_type)
        
        # 1. Height check
        height_eval = rule_engine.evaluate_height(
            v1_rulepack,
            pdp_area_cm2=req.pdp_area_cm2,
            printing_method=meas["printing_method"],
            measured_height_mm=meas["height_mm"],
            confidence_flag="RELIABLE" # In a real system, passed from calibration
        )
        evaluations.append({
            "measurement_id": meas["id"],
            "type": "height",
            "result": height_eval
        })
        if height_eval["status"] != "PASS":
            if final_status != "FAIL": # FAIL trumps CANNOT_DETERMINE
                final_status = height_eval["status"]
                
        # 2. Misleading text check
        wording_eval = rule_engine.evaluate_misleading_wording(v1_rulepack, meas["confirmed_text"])
        evaluations.append({
            "measurement_id": meas["id"],
            "type": "wording",
            "result": wording_eval
        })
        if wording_eval["status"] == "SUSPECTED_NON_STANDARD":
            final_status = "SUSPECTED_NON_STANDARD"
            
    # 3. Mandatory declarations check
    decl_evals = rule_engine.evaluate_mandatory_declarations(v1_rulepack, present_decls, req.inspection_context)
    for e in decl_evals:
        evaluations.append({
            "measurement_id": None,
            "type": "mandatory_declaration",
            "result": e
        })
        if e["status"] == "FAIL":
            final_status = "FAIL"
            
    # Update inspection
    mock_db["inspections"][id]["status"] = "COMPLETED"
    mock_db["inspections"][id]["verdict"] = final_status
    mock_db["inspections"][id]["evaluations"] = evaluations
    
    # Generate AI Auditor Analysis
    from ml.ai_auditor import generate_ai_auditor_analysis
    fields_map = req.inspection_context
    violations = [e for e in evaluations if e.get("result", {}).get("status") == "FAIL"]
    ai_analysis = generate_ai_auditor_analysis(fields_map, violations)
    mock_db["inspections"][id]["ai_analysis"] = ai_analysis
    
    # Audit log the completion
    audit_entry = create_audit_log(
        inspection_id=id,
        user_id=current_user["user_id"],
        action="EVALUATE_INSPECTION",
        entity_type="Inspection",
        entity_id=id,
        changes={
            "old_status": "DRAFT",
            "new_status": "COMPLETED",
            "verdict": final_status
        }
    )
    mock_db["audit_logs"][audit_entry["id"]] = audit_entry
    
    return {
        "inspection_id": id,
        "verdict": final_status,
        "evaluations": evaluations,
        "ai_analysis": ai_analysis
    }
