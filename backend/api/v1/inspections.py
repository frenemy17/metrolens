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
    
    return record.data

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
