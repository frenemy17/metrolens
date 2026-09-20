from fastapi import APIRouter, Depends
from api.deps import RoleChecker
from core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from core.models import InspectionRecord
from datetime import datetime
import json

router = APIRouter()

@router.get("/stats")
async def get_dashboard_stats(
    current_user: dict = Depends(RoleChecker(["INSPECTOR", "SUPERVISOR", "ADMIN"])),
    db: AsyncSession = Depends(get_db)
):
    # Fetch all inspections
    result = await db.execute(select(InspectionRecord))
    records = result.scalars().all()
    
    inspections = [r.data for r in records]
    total_scans = len(inspections)
    compliant = 0
    improvement_notices = 0
    section48_actions = 0
    
    # Calculate stats — check enforcement_status first, fall back to overall_compliance
    for i in inspections:
        es = i.get("enforcement_status", "")
        oc = (i.get("overall_compliance") or i.get("overallStatus") or "").upper()
        if es == "COMPLIANT" or oc == "COMPLIANT":
            compliant += 1
        elif es == "IMPROVEMENT_NOTICE_ISSUED" or oc in ("NON-COMPLIANT", "POTENTIAL NON-COMPLIANCE"):
            improvement_notices += 1
        elif es == "DIRECT_ENFORCEMENT":
            section48_actions += 1
    
    recent_scans = []
    # Sort by created_at (descending)
    sorted_records = sorted(records, key=lambda x: x.created_at, reverse=True)

    for r in sorted_records[:5]:
        insp = r.data
        recent_scans.append({
            "id": insp.get("id", r.id),
            "product_name": insp.get("product", {}).get("product_name", f"Scan {r.id[:8]}"),
            "status": insp.get("status", "COMPLETE").lower(),
            "timestamp": r.created_at.isoformat()
        })

    # Calculate top violated rules
    violation_counts = {}
    for insp in inspections:
        for violation in insp.get("violations", []):
            if violation.get("status", "").lower() in ["fail", "manual review"]:
                rid = violation.get("rule_id", "Unknown")
                violation_counts[rid] = violation_counts.get(rid, 0) + 1
    
    top_violated = [{"rule_id": rid, "count": count} for rid, count in sorted(violation_counts.items(), key=lambda x: x[1], reverse=True)[:3]]

    return {
        "data": {
            "total_scans": total_scans,
            "compliant": compliant,
            "improvement_notices": improvement_notices,
            "section48_actions": section48_actions,
            "top_violated_rules": top_violated,
            "recent_scans": recent_scans
        }
    }
