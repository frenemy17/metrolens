from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Dict, Any
import json
import os
from copy import deepcopy

from api.deps import RoleChecker, get_current_user_payload
from ml.rule_sync import extract_rule_suggestions
from core.audit import create_audit_log
from api.v1.inspections import rule_engine, mock_db

router = APIRouter()

class RulePublishRequest(BaseModel):
    new_version_name: str
    effective_from: str
    source_citation: str
    approved_changes: List[Dict[str, Any]] # The extracted 'value' payloads from MLSuggestion

@router.post("/rule-sync/upload")
async def upload_gazette_pdf(
    file: UploadFile = File(...),
    current_user: dict = Depends(RoleChecker(["ADMIN"]))
):
    """
    Accepts a gazette PDF, triggers the ML boundary for LLM extraction,
    and returns unconfirmed MLSuggestions.
    """
    contents = await file.read()
    
    # Run the ML boundary function
    suggestions = extract_rule_suggestions(contents)
    
    return {
        "filename": file.filename,
        "suggestions": suggestions
    }

@router.post("/rule-sync/publish")
async def publish_rulepack(
    req: RulePublishRequest,
    current_user: dict = Depends(RoleChecker(["ADMIN"]))
):
    """
    Takes human-reviewed and confirmed JSON diffs, merges them into the 
    current rulepack, and publishes a new version (e.g. v2.json).
    """
    # 1. Fetch current active rulepack (assume v1 for this mock)
    base_pack = rule_engine.get_rulepack("v1")
    if not base_pack:
        raise HTTPException(status_code=500, detail="Base rulepack v1 not found")
        
    # 2. Deepcopy and apply changes
    new_pack = deepcopy(base_pack)
    new_pack["version"] = req.new_version_name
    new_pack["effective_from"] = req.effective_from
    new_pack["source_citation"] = req.source_citation
    
    # Apply human-confirmed changes
    for change in req.approved_changes:
        action = change.get("action")
        details = change.get("details")
        
        if action == "ADD_MANDATORY_DECLARATION":
            new_pack["mandatory_declarations"].append(details)
        # Handle other types of actions (UPDATE_HEIGHT_TABLE, etc.)
            
    # 3. Save the new rulepack
    rulepacks_dir = rule_engine.rulepacks_dir
    if not os.path.exists(rulepacks_dir):
        os.makedirs(rulepacks_dir)
        
    filepath = os.path.join(rulepacks_dir, f"{req.new_version_name}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(new_pack, f, indent=2)
        
    # 4. Reload engine cache
    rule_engine.load_rulepacks()
    
    # 5. Audit Log the publication
    audit_entry = create_audit_log(
        inspection_id="SYSTEM",
        user_id=current_user["user_id"],
        action="PUBLISH_RULEPACK",
        entity_type="Rulepack",
        entity_id=req.new_version_name,
        changes={
            "base_version": "v1",
            "new_version": req.new_version_name,
            "applied_changes": req.approved_changes
        }
    )
    mock_db["audit_logs"][audit_entry["id"]] = audit_entry
    
    return {
        "status": "SUCCESS",
        "new_version": req.new_version_name,
        "rulepack": new_pack
    }

@router.get("/rules")
async def get_active_rules(current_user: dict = Depends(RoleChecker(["INSPECTOR", "SUPERVISOR", "ADMIN"]))):
    pack = rule_engine.get_active_rulepack()
    rules_list = []
    
    rule_names = {
        "r6-1a-mfr-name-address": "Manufacturer Name & Address",
        "r6-1aa-country-of-origin": "Country of Origin",
        "r6-1b-generic-name": "Common / Generic Name",
        "r6-1c-net-quantity": "Net Quantity Declaration",
        "r6-1d-mfg-month-year": "Month & Year of Manufacture",
        "r6-1da-best-before-use-by": "Best Before / Expiry Date",
        "r6-1e-mrp": "Maximum Retail Price (MRP)",
        "r6-1f-dimensions": "Dimensions of Commodity",
        "r6-2-consumer-care": "Consumer Care Details",
        "r6-3-no-alter-sticker": "No Sticker / Tamper-Free MRP",
        "r6-10-ecommerce-declarations": "E-Commerce Digital Listing",
    }
    
    for rule in pack.get("mandatory_declarations", []):
        rid = rule.get("id", "")
        citation = rule.get("citation", "")
        name = rule_names.get(rid, citation or rid)
        desc = rule.get("format_rule") or rule.get("condition") or f"Mandatory requirement under {citation}"
        rules_list.append({
            "id": rid,
            "rule_id": rid,
            "category": "Mandatory",
            "name": name,
            "description": str(desc),
            "status": "active",
            "severity": "high",
            "active": True,
            "citation": citation
        })
        
    height_table = pack.get("height_table", {})
    if height_table:
        rules_list.append({
            "id": "r7-2-numeral-height",
            "rule_id": "r7-2-numeral-height",
            "category": "Table",
            "name": "Rule 7(2) — Numeral Cap Height",
            "description": f"Minimum numeral height based on Principal Display Panel area ({height_table.get('citation', '')})",
            "status": "active",
            "severity": "high",
            "active": True,
            "citation": height_table.get("citation", "Rule 7(2)")
        })

    for check in pack.get("manner", {}).get("checks", []):
        cid = check.get("id", "")
        rules_list.append({
            "id": cid,
            "rule_id": cid,
            "category": "Manner",
            "name": cid.replace("r9-", "Rule 9 - ").replace("-", " ").title(),
            "description": check.get("rule", "Legibility, prominence, and language requirements"),
            "status": "active",
            "severity": "medium",
            "active": True,
            "citation": pack.get("manner", {}).get("citation", "Rule 9")
        })

    return {"data": rules_list}

