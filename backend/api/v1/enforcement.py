from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime

from api.deps import RoleChecker
from core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm.attributes import flag_modified
from core.models import InspectionRecord

router = APIRouter()

class EnforceAction(BaseModel):
    action: str # IMPROVEMENT_NOTICE_ISSUED, WEIGHING_REQUIRED, COMPLIANT, DIRECT_ENFORCEMENT
    notes: str = ""

VALID_TRANSITIONS = {
    "COMPLETED": ["IMPROVEMENT_NOTICE_ISSUED", "DIRECT_ENFORCEMENT", "WEIGHING_REQUIRED", "COMPLIANT"],
    "complete": ["IMPROVEMENT_NOTICE_ISSUED", "DIRECT_ENFORCEMENT", "WEIGHING_REQUIRED", "COMPLIANT"],
    "NON-COMPLIANT": ["IMPROVEMENT_NOTICE_ISSUED", "DIRECT_ENFORCEMENT", "WEIGHING_REQUIRED"],
    "IMPROVEMENT_NOTICE_ISSUED": ["COMPLIANT", "DIRECT_ENFORCEMENT"],
    "WEIGHING_REQUIRED": ["COMPLIANT", "DIRECT_ENFORCEMENT"],
    "DIRECT_ENFORCEMENT": ["COMPLIANT"]
}

@router.post("/{id}/enforce")
async def transition_enforcement_state(
    id: str,
    req: EnforceAction,
    current_user: dict = Depends(RoleChecker(["INSPECTOR", "SUPERVISOR", "ADMIN"])),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(InspectionRecord).where(InspectionRecord.id == id))
    record = result.scalars().first()
    if not record:
        raise HTTPException(status_code=404, detail="Inspection record not found in database")
        
    inspection = record.data or {}
    current_state = inspection.get("enforcement_status") or inspection.get("status", "COMPLETED")
    
    # Update enforcement status
    inspection["enforcement_status"] = req.action
    
    # Track transition audit trail inside inspection record
    history = inspection.setdefault("enforcement_history", [])
    history.append({
        "action": req.action,
        "previous_status": current_state,
        "officer_id": current_user.get("user_id", "officer"),
        "timestamp": datetime.utcnow().isoformat(),
        "notes": req.notes
    })
    
    record.data = dict(inspection)
    flag_modified(record, "data")
    await db.commit()
    await db.refresh(record)
    
    return {
        "status": "SUCCESS",
        "inspection_id": id,
        "enforcement_status": req.action,
        "data": record.data
    }

class CompoundabilityReq(BaseModel):
    offender_name: str
    gstin: str = ""
    offense_section: str = ""

@router.post("/compoundability-check")
async def compoundability_check(req: CompoundabilityReq):
    # Mocking checkSection48Compoundability from old logic
    return {
        "compoundability": True,
        "status": "COMPOUNDABLE",
        "citation": "Section 48(4) Legal Metrology Act, 2009",
        "action": f"Eligible for compounding. No prior offenses found for {req.offender_name}."
    }

class NoticeReq(BaseModel):
    inspectionData: dict = {}
    offenderDetails: dict = {}
    officerDetails: dict = {}
    proposedCompoundingSum: int = 5000

@router.post("/section48-notice")
async def section48_notice(req: NoticeReq):
    # Mocking generateSection48Notice from old logic
    return {
        "title": "Section 48 Compounding Notice",
        "jurisdiction": "Directorate of Legal Metrology",
        "sum_proposed": req.proposedCompoundingSum,
        "details": f"Notice served to {req.offenderDetails.get('firm_name', 'Unknown')}",
        "evidence_chain": "Hash: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    }

@router.post("/janvishwas-notice")
async def janvishwas_notice(req: NoticeReq):
    # Mocking generateJanVishwasNotice from old logic
    return {
        "title": "Form IN-1 Improvement Notice",
        "jurisdiction": "Directorate of Legal Metrology (Jan Vishwas Act 2026)",
        "cure_period": "15 days",
        "details": f"Notice served to {req.offenderDetails.get('firm_name', 'Unknown')} to cure packaging defect."
    }
