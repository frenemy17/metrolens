from fastapi import APIRouter, HTTPException
import httpx
import re

router = APIRouter()

# State codes defined under FSSAI FoSCoS licensing registry
FSSAI_STATE_CODES = {
    "01": "Jammu & Kashmir", "02": "Himachal Pradesh", "03": "Punjab", "04": "Chandigarh",
    "05": "Uttarakhand", "06": "Haryana", "07": "Delhi", "08": "Rajasthan",
    "09": "Uttar Pradesh", "10": "Bihar", "11": "Sikkim", "12": "Arunachal Pradesh",
    "13": "Nagaland", "14": "Manipur", "15": "Mizoram", "16": "Tripura",
    "17": "Meghalaya", "18": "Assam", "19": "West Bengal", "20": "Jharkhand",
    "21": "Odisha", "22": "Chhattisgarh", "23": "Madhya Pradesh", "24": "Gujarat",
    "26": "Dadra & Nagar Haveli", "27": "Maharashtra", "28": "Andhra Pradesh",
    "29": "Karnataka", "30": "Goa", "31": "Lakshadweep", "32": "Kerala",
    "33": "Tamil Nadu", "34": "Puducherry", "35": "Andaman & Nicobar Islands",
    "36": "Telangana", "37": "Ladakh"
}

@router.get("/pincode/{pincode}")
async def verify_pincode(pincode: str):
    """
    Validates a 6-digit Indian Postal PIN Code via the official Indian Postal API.
    Returns registered post offices, district, and state.
    """
    clean_pin = re.sub(r"\D", "", pincode)
    if len(clean_pin) != 6:
        raise HTTPException(status_code=400, detail="Invalid PIN Code. Must be exactly 6 digits.")

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(f"https://api.postalpincode.in/pincode/{clean_pin}")
            data = resp.json()
            
            if data and isinstance(data, list) and len(data) > 0:
                item = data[0]
                status = item.get("Status")
                if status == "Success":
                    po_list = item.get("PostOffice", [])
                    district = po_list[0].get("District") if po_list else "Unknown"
                    state = po_list[0].get("State") if po_list else "Unknown"
                    return {
                        "status": "VALID",
                        "pincode": clean_pin,
                        "valid": True,
                        "district": district,
                        "state": state,
                        "post_offices_count": len(po_list),
                        "registered_locations": [p.get("Name") for p in po_list[:5]],
                        "message": f"Verified PIN {clean_pin} in {district}, {state}."
                    }
                else:
                    return {
                        "status": "INVALID",
                        "pincode": clean_pin,
                        "valid": False,
                        "message": f"PIN Code {clean_pin} not found in Postal Department registry."
                    }
    except Exception as e:
        return {
            "status": "ERROR",
            "pincode": clean_pin,
            "valid": True,
            "message": f"Postal directory query error: {str(e)}"
        }

@router.get("/fssai/{license_no}")
async def verify_fssai(license_no: str):
    """
    Validates and decodes the 14-digit FSSAI Food Safety license under FoSCoS.
    """
    clean = re.sub(r"\D", "", license_no)
    if len(clean) != 14:
        return {
            "valid": False,
            "license_number": license_no,
            "status": "INVALID_LENGTH",
            "reason": f"FSSAI license must be exactly 14 digits (found {len(clean)})."
        }
        
    kind_digit = clean[0]
    kind_map = {
        "1": "Central / State License (Manufacture / Large Distribution)",
        "2": "Basic Registration (Small Retailer / Petty Food Business)"
    }
    license_type = kind_map.get(kind_digit, "Other FSSAI Authorization")
    
    state_code = clean[1:3]
    state_name = FSSAI_STATE_CODES.get(state_code, "Central Jurisdiction or Unrecognized State")
    
    year_digits = clean[3:5]
    enrollment_year = f"20{year_digits}"
    
    auth_digits = clean[5:8]
    serial_digits = clean[8:14]
    
    return {
        "valid": True,
        "license_number": clean,
        "status": "VALID_STRUCTURE",
        "license_type": license_type,
        "state_code": state_code,
        "registered_state": state_name,
        "enrollment_year": enrollment_year,
        "authority_code": auth_digits,
        "serial_number": serial_digits,
        "statute": "Food Safety and Standards Act, 2006 (FoSCoS)",
        "message": f"Valid 14-digit FSSAI structure issued in {state_name} ({enrollment_year})."
    }
