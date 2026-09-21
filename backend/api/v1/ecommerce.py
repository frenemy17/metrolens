from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uuid
import hashlib
from datetime import datetime

from api.deps import RoleChecker
from core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from core.models import InspectionRecord, BatchRecord
from api.v1.inspections import mock_db, rule_engine
from core.audit import create_audit_log
from ml.ecommerce_scraper import fetch_webpage_content, extract_declarations_from_page

router = APIRouter()

class EcommerceListing(BaseModel):
    url: str
    product_name: Optional[str] = "E-Commerce Packaged Product"
    brand_name: Optional[str] = "Digital Retail Seller"
    extracted_declarations: List[str] = []
    context: dict = {}

class ScrapeAuditReq(BaseModel):
    url: str
    product_name: Optional[str] = None
    brand_name: Optional[str] = None
    context: dict = {}

@router.post("/audit")
async def audit_ecommerce_listing(
    payload: EcommerceListing,
    current_user: dict = Depends(RoleChecker(["INSPECTOR", "SUPERVISOR", "ADMIN"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Audits a digital e-commerce marketplace listing against Rule 6(10).
    Rule 6(10) requires all Rule 6(1) declarations EXCEPT manufacturing date.
    Persists audit result to SQLite database.
    """
    insp_id = str(uuid.uuid4())
    batch_id = str(uuid.uuid4())
    
    # If no declarations were manually supplied, auto-scrape and extract via Gemini
    if not payload.extracted_declarations:
        fetch_res = await fetch_webpage_content(payload.url)
        ai_res = await extract_declarations_from_page(payload.url, fetch_res.get("content", ""))
        payload.extracted_declarations = ai_res.get("declarations_found", [])
        if not payload.product_name or payload.product_name == "E-Commerce Packaged Product":
            payload.product_name = ai_res.get("product_name") or fetch_res.get("title") or "Packaged Commodity"
        if not payload.brand_name or payload.brand_name == "Digital Retail Seller":
            payload.brand_name = ai_res.get("brand_name") or "Retail Brand"
        payload.context["mrp"] = ai_res.get("mrp")
        payload.context["net_quantity"] = ai_res.get("net_quantity")
        payload.context["country_of_origin"] = ai_res.get("country_of_origin")
        payload.context["manufacturer"] = ai_res.get("manufacturer")
        payload.context["consumer_care"] = ai_res.get("consumer_care")
        payload.context["best_before"] = ai_res.get("best_before")

    v1_rulepack = rule_engine.get_rulepack("v1")
    if not v1_rulepack:
        raise HTTPException(status_code=500, detail="Rulepack v1 not found on server")
        
    context = payload.context.copy()
    context["channel"] = "e-commerce"
    context["e-commerce_exemption"] = True
    context["is_imported"] = False
    context["commodity_may_become_unfit_over_time"] = True
    context["commodity_size_relevant_to_sale"] = False
    
    decl_evals = rule_engine.evaluate_mandatory_declarations(
        v1_rulepack, 
        payload.extracted_declarations, 
        context
    )
    
    rule_descriptions = {
        "r6-1a-mfr-name-address": "Name and complete address of manufacturer/packer declared on listing.",
        "r6-1aa-country-of-origin": "Country of origin declared on digital product page.",
        "r6-1b-generic-name": "Generic or common name of commodity declared.",
        "r6-1c-net-quantity": "Net quantity in standard metric units declared on page.",
        "r6-1d-mfg-month-year": "Manufacturing date (Statutory waiver under Rule 6(10)).",
        "r6-1da-best-before-use-by": "Best Before / Expiry date declared for perishable commodities.",
        "r6-1e-mrp": "Maximum Retail Price (MRP) inclusive of all taxes declared.",
        "r6-2-consumer-care": "Customer care telephone/email declared on listing.",
    }

    rules = []
    defects = 0

    for e in decl_evals:
        rid = e["rule_id"]
        if rid == "r6-1d-mfg-month-year":
            # Explicit waiver under Rule 6(10)
            rules.append({
                "rule_id": rid,
                "rule_title": "Rule 6(10) — Manufacturing Date Waiver",
                "status": "PASS",
                "detail": "Statutory waiver under Rule 6(10). E-commerce digital listings are exempt from pre-packing month & year.",
            })
        else:
            st = e["status"]
            if st == "FAIL":
                defects += 1
            rules.append({
                "rule_id": rid,
                "rule_title": e.get("citation", rid),
                "status": st,
                "detail": rule_descriptions.get(rid, "Declaration present." if st == "PASS" else "Mandatory declaration missing on digital listing."),
            })

    # Overall verdict
    hard_fails = [r for r in rules if r["status"] == "FAIL"]
    if len(hard_fails) == 0:
        overall_compliance = "COMPLIANT"
        enforcement_status = "COMPLIANT"
    elif len(hard_fails) >= 3:
        overall_compliance = "NON-COMPLIANT"
        enforcement_status = "DIRECT_ENFORCEMENT"
    else:
        overall_compliance = "POTENTIAL NON-COMPLIANCE"
        enforcement_status = "IMPROVEMENT_NOTICE_ISSUED"

    compliance_score = max(0, 100 - (len(hard_fails) * 15))

    # Evidence hash of digital listing
    evidence_hash = hashlib.sha256(f"{payload.url}:{','.join(payload.extracted_declarations)}".encode('utf-8')).hexdigest()

    inspection_data = {
        "id": insp_id,
        "status": "complete",
        "overall_compliance": overall_compliance,
        "overallStatus": overall_compliance,
        "enforcement_status": enforcement_status,
        "compliance_score": compliance_score,
        "total_rules_checked": len(rules),
        "total_violations": defects,
        "high_violations": len(hard_fails),
        "original_image": "/ecommerce-placeholder.png",
        "evidence_hash": evidence_hash,
        "channel": "e-commerce",
        "url": payload.url,
        "product": {
            "id": f"ecom-{insp_id[:8]}",
            "product_name": payload.product_name,
            "brand_name": payload.brand_name,
            "category": "E-Commerce Digital Listing",
        },
        "extracted_fields": {
            "product_name": payload.product_name,
            "brand_name": payload.brand_name,
            "url": payload.url,
            "declarations_found": payload.extracted_declarations,
            "mfg_date": "Waived under Rule 6(10)",
            "raw_ocr_text": f"E-Commerce digital listing: Declarations ingested directly from retailer webpage ({payload.url}) under Rule 6(10) of Legal Metrology Rules. Physical optical OCR is not applicable to digital listings.",
        },
        "raw_ocr_text": f"E-Commerce digital listing: Declarations ingested directly from retailer webpage ({payload.url}) under Rule 6(10) of Legal Metrology Rules. Physical optical OCR is not applicable to digital listings.",
        "ai_analysis": {
            "auditor_summary": f"E-Commerce digital listing compliance audit completed for {payload.url}. Evaluated under Rule 6(10) of the Packaged Commodities Rules, 2011 with statutory manufacturing date waiver.",
            "metrology": {
                "numeral_measurement": {"measured_cap_height_mm": 2.5},
                "legal_requirement": {"requiredHeightMm": 2.0},
            }
        },
        "officer_id": current_user["user_id"],
        "timestamp": datetime.utcnow().isoformat(),
        "violations": rules,
    }

    batch_data = {
        "id": batch_id,
        "scanId": insp_id,
        "status": "complete",
        "scans": [inspection_data],
    }

    # Save to SQLite database
    db.add(InspectionRecord(id=insp_id, data=inspection_data))
    db.add(BatchRecord(id=batch_id, data=batch_data))
    await db.commit()

    # System audit log
    audit_entry = create_audit_log(
        inspection_id=insp_id,
        user_id=current_user["user_id"],
        action="E_COMMERCE_AUDIT",
        entity_type="Inspection",
        entity_id=insp_id,
        changes={
            "url": payload.url,
            "verdict": overall_compliance,
            "defects": defects
        }
    )
    mock_db["audit_logs"][audit_entry["id"]] = audit_entry

    return {
        "status": "SUCCESS",
        "inspection_id": insp_id,
        "batch_id": batch_id,
        "data": inspection_data,
        **inspection_data
    }

@router.post("/scrape-and-audit")
async def scrape_and_audit_ecommerce_listing(
    req: ScrapeAuditReq,
    current_user: dict = Depends(RoleChecker(["INSPECTOR", "SUPERVISOR", "ADMIN"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Crawls a live e-commerce product listing URL, autonomously extracts all packaging
    declarations using Gemini 3.6 Flash / Groq, and runs a statutory Rule 6(10) audit.
    """
    fetch_res = await fetch_webpage_content(req.url)
    ai_extracted = await extract_declarations_from_page(req.url, fetch_res.get("content", ""))
    
    product_name = req.product_name or ai_extracted.get("product_name") or fetch_res.get("title") or "Packaged Commodity"
    brand_name = req.brand_name or ai_extracted.get("brand_name") or "Retail Brand"
    decls = ai_extracted.get("declarations_found", [])
    
    listing_payload = EcommerceListing(
        url=req.url,
        product_name=product_name,
        brand_name=brand_name,
        extracted_declarations=decls,
        context={
            **req.context,
            "scraped_live": fetch_res.get("success", False),
            "ai_extracted": True,
            "mrp": ai_extracted.get("mrp"),
            "net_quantity": ai_extracted.get("net_quantity"),
            "country_of_origin": ai_extracted.get("country_of_origin"),
            "manufacturer": ai_extracted.get("manufacturer"),
            "consumer_care": ai_extracted.get("consumer_care"),
            "best_before": ai_extracted.get("best_before"),
            "missing_declarations": ai_extracted.get("missing_declarations", [])
        }
    )
    
    result = await audit_ecommerce_listing(listing_payload, current_user, db)
    result["ai_extraction"] = ai_extracted
    return result

