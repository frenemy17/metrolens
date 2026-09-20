import pytest
import os
import json
from core.rules.engine import RuleEngine

@pytest.fixture
def rule_engine():
    # Make sure we point to the correct rulepacks dir
    current_dir = os.path.dirname(os.path.abspath(__file__))
    rulepacks_dir = os.path.join(os.path.dirname(current_dir), "rulepacks")
    return RuleEngine(rulepacks_dir=rulepacks_dir)

def test_load_rulepack(rule_engine):
    v1_rulepack = rule_engine.get_rulepack("v1")
    assert v1_rulepack is not None
    assert v1_rulepack.get("version") == "v1"
    assert "height_table" in v1_rulepack

def test_evaluate_height(rule_engine):
    v1_rulepack = rule_engine.get_rulepack("v1")
    
    # Normal printed, area 100 -> normal_mm is 1.5. measured is 1.5 -> PASS
    result1 = rule_engine.evaluate_height(
        rulepack=v1_rulepack,
        pdp_area_cm2=100.0,
        printing_method="PRINTED",
        measured_height_mm=1.5,
        confidence_flag="RELIABLE"
    )
    assert result1["status"] == "PASS"
    assert result1["threshold"] == "1.5"
    
    # Molded, area 100 -> molded_mm is 3.0. measured is 2.9, diff is 0.1 < 0.15 -> CANNOT_DETERMINE
    result2 = rule_engine.evaluate_height(
        rulepack=v1_rulepack,
        pdp_area_cm2=100.0,
        printing_method="MOLDED",
        measured_height_mm=2.9,
        confidence_flag="RELIABLE"
    )
    assert result2["status"] == "CANNOT_DETERMINE"
    
    # Measured 2.7 -> diff is 0.3 > 0.15 -> FAIL
    result3 = rule_engine.evaluate_height(
        rulepack=v1_rulepack,
        pdp_area_cm2=100.0,
        printing_method="MOLDED",
        measured_height_mm=2.7,
        confidence_flag="RELIABLE"
    )
    assert result3["status"] == "FAIL"

def test_evaluate_misleading_wording(rule_engine):
    v1_rulepack = rule_engine.get_rulepack("v1")
    
    result = rule_engine.evaluate_misleading_wording(v1_rulepack, "Net Weight minimum 500g")
    assert result["status"] == "SUSPECTED_NON_STANDARD"
    
    result_clean = rule_engine.evaluate_misleading_wording(v1_rulepack, "Net Weight 500g")
    assert result_clean["status"] == "PASS"

def test_evaluate_mandatory_declarations(rule_engine):
    v1_rulepack = rule_engine.get_rulepack("v1")
    
    # Normal item
    present_decls = ["r6-1a-mfr-name-address", "r6-1b-generic-name", "r6-1c-net-quantity"]
    context = {}
    
    results = rule_engine.evaluate_mandatory_declarations(v1_rulepack, present_decls, context)
    
    # r6-1b and r6-1c are present -> PASS
    # r6-1d (mfg month) is missing -> FAIL
    for r in results:
        if r["rule_id"] in ["r6-1a-mfr-name-address", "r6-1b-generic-name", "r6-1c-net-quantity"]:
            assert r["status"] == "PASS"
        elif r["rule_id"] == "r6-1d-mfg-month-year":
            assert r["status"] == "FAIL"
            
    # Test exemption
    context_exempt = {"lpg_cylinder_14_2kg_or_5kg_PSU": True}
    results_exempt = rule_engine.evaluate_mandatory_declarations(v1_rulepack, present_decls, context_exempt)
    
    # r6-1d should be skipped entirely
    rule_ids_checked = [r["rule_id"] for r in results_exempt]
    assert "r6-1d-mfg-month-year" not in rule_ids_checked
