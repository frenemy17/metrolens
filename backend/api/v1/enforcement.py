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
async def compoundability_check(
    req: CompoundabilityReq,
    db: AsyncSession = Depends(get_db)
):
    """
    Real Section 48(4) Legal Metrology Act repeat offender audit:
    Under Section 48(4), an offense is compoundable ONLY if the offender has NOT
    committed a similar offense within the previous 3 years.
    Second and subsequent offenses within 3 years are strictly NON-COMPOUNDABLE
    and mandate direct prosecution.
    """
    from datetime import timedelta
    three_years_ago = datetime.utcnow() - timedelta(days=3 * 365)
    
    result = await db.execute(select(InspectionRecord))
    all_records = result.scalars().all()
    
    prior_offenses = []
    name_clean = req.offender_name.strip().lower()
    gstin_clean = req.gstin.strip().upper()
    
    for rec in all_records:
        data = rec.data or {}
        compliance = str(data.get("overall_compliance") or data.get("verdict") or "").upper()
        if compliance == "COMPLIANT":
            continue
            
        prod = data.get("product") or {}
        extracted = data.get("extracted_fields") or {}
        
        cand_name = str(extracted.get("manufacturer_name") or prod.get("brand_name") or "").lower()
        cand_gstin = str(extracted.get("gstin") or "").upper()
        
        name_match = bool(name_clean and (name_clean in cand_name or cand_name in name_clean))
        gstin_match = bool(gstin_clean and gstin_clean == cand_gstin)
        
        if name_match or gstin_match:
            created_str = data.get("created_at") or data.get("timestamp")
            rec_date = None
            if created_str:
                try:
                    rec_date = datetime.fromisoformat(created_str.replace("Z", "+00:00")).replace(tzinfo=None)
                except Exception:
                    rec_date = rec.created_at
            else:
                rec_date = rec.created_at
                
            if rec_date and rec_date >= three_years_ago:
                prior_offenses.append({
                    "inspection_id": rec.id,
                    "date": rec_date.strftime("%Y-%m-%d"),
                    "product": prod.get("product_name", "Packaged Commodity"),
                    "verdict": compliance
                })
    
    if len(prior_offenses) > 0:
        return {
            "compoundability": False,
            "status": "NON_COMPOUNDABLE",
            "eligible": False,
            "citation": "Section 48(4) Legal Metrology Act, 2009",
            "action": f"REPEAT OFFENDER: Found {len(prior_offenses)} prior violation(s) within the 3-year statutory window for '{req.offender_name}'. Second offenses are strictly non-compoundable under Section 48(4) and mandate court prosecution.",
            "prior_offenses_count": len(prior_offenses),
            "prior_offenses": prior_offenses[:3],
            "penalty_amount": None,
            "prosecution_required": True
        }
    
    return {
        "compoundability": True,
        "status": "COMPOUNDABLE",
        "eligible": True,
        "citation": "Section 48(4) Legal Metrology Act, 2009",
        "action": f"Eligible for compounding. First recorded offense within 3-year window for '{req.offender_name}'. Form IN-1 Improvement Notice recommended under Jan Vishwas Act.",
        "prior_offenses_count": 0,
        "prior_offenses": [],
        "penalty_amount": 5000,
        "prosecution_required": False
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
