import json
import os
from typing import Dict, Any, List, Optional
from core.cv.measurement import evaluate_guard_band

class RuleEngine:
    def __init__(self, rulepacks_dir: str = "rulepacks"):
        self.rulepacks_dir = rulepacks_dir
        self.rulepacks = {}
        self.load_rulepacks()

    def load_rulepacks(self):
        # In a real scenario, this would load from DB, but for now we load from JSON files in the directory
        if not os.path.exists(self.rulepacks_dir):
            return
        
        for filename in os.listdir(self.rulepacks_dir):
            if filename.endswith(".json"):
                path = os.path.join(self.rulepacks_dir, filename)
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    version = data.get("version")
                    if version:
                        self.rulepacks[version] = data

    def get_rulepack(self, version: str) -> Dict[str, Any]:
        return self.rulepacks.get(version, {})

    def get_active_rulepack(self) -> Dict[str, Any]:
        if "v1" in self.rulepacks:
            return self.rulepacks["v1"]
        if self.rulepacks:
            return next(iter(self.rulepacks.values()))
        return {}

    def evaluate_height(
        self, 
        rulepack: Dict[str, Any], 
        pdp_area_cm2: float, 
        printing_method: str, 
        measured_height_mm: float, 
        confidence_flag: str
    ) -> Dict[str, Any]:
        """
        Evaluate Rule 7(2)-(3) Table-I height requirements.
        """
        height_table = rulepack.get("height_table", {})
        bands = height_table.get("bands", [])
        
        # Find the correct band
        selected_band = None
        for band in bands:
            max_area = band.get("pdp_area_cm2_max")
            if max_area is None or pdp_area_cm2 <= max_area:
                selected_band = band
                break
                
        if not selected_band:
            selected_band = bands[-1] if bands else {}

        # Determine if it's a blown/formed/molded printing method
        is_molded = printing_method.upper() in ["BLOWN", "FORMED", "MOLDED"]
        
        threshold = selected_band.get("blown_formed_molded_mm") if is_molded else selected_band.get("normal_mm")
        
        if threshold is None:
            return {"status": "PASS", "threshold": None} # Or whatever fallback
            
        status = evaluate_guard_band(measured_height_mm, float(threshold), confidence_flag)
        
        return {
            "status": status,
            "measured_value": str(measured_height_mm),
            "threshold": str(threshold),
            "citation": height_table.get("citation")
        }

    def evaluate_misleading_wording(self, rulepack: Dict[str, Any], text: str) -> Dict[str, Any]:
        """
        Evaluate Rule 12(6) misleading quantity wording.
        """
        rule_data = rulepack.get("misleading_quantity_wording", {})
        flag_words = rule_data.get("flag_if_present", [])
        
        text_lower = text.lower()
        found_words = [word for word in flag_words if word.lower() in text_lower]
        
        if found_words:
            return {
                "status": rule_data.get("severity", "SUSPECTED_NON_STANDARD"),
                "measured_value": f"Found: {', '.join(found_words)}",
                "citation": rule_data.get("citation")
            }
            
        return {
            "status": "PASS",
            "citation": rule_data.get("citation")
        }
        
    def evaluate_mandatory_declarations(
        self, 
        rulepack: Dict[str, Any], 
        present_declarations: List[str], 
        inspection_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Evaluate Rule 6(1) presence of mandatory declarations.
        """
        results = []
        mandatory = rulepack.get("mandatory_declarations", [])
        
        for rule in mandatory:
            if rule.get("check") != "presence":
                continue
                
            rule_id = rule.get("id")
            citation = rule.get("citation")
            
            # Check waivers/exemptions
            if "waived_if" in rule and inspection_context.get(rule["waived_if"]):
                continue
            if "condition" in rule and not inspection_context.get(rule["condition"]):
                continue
            if "exempt" in rule:
                exempt_list = rule["exempt"]
                if any(inspection_context.get(ex) for ex in exempt_list):
                    continue
                    
            # Check presence
            is_present = rule_id in present_declarations
            status = "PASS" if is_present else "FAIL"
            
            results.append({
                "rule_id": rule_id,
                "status": status,
                "citation": citation
            })
            
        return results
