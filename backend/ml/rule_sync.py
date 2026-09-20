import os
import json
import google.generativeai as genai
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

def extract_rule_suggestions(pdf_text_or_bytes: Any) -> List[Dict[str, Any]]:
    """
    Uses Google Gemini API to parse a gazette PDF (or text) and propose rule changes
    in JSON format. If API key is missing or fails, falls back to a mock response.
    """
    
    if not api_key:
        return _mock_suggestion()
        
    try:
        # For this prototype, we'll assume pdf_text_or_bytes is either string or we convert it to string
        text_content = str(pdf_text_or_bytes)[:15000] # Cap length for prompt
        
        prompt = f"""
        You are a Legal Metrology expert AI. Read the following gazette text and identify any amendments 
        to packaging and labeling rules. 
        Output your findings STRICTLY as a JSON array of amendment objects.
        Each object must match this schema:
        {{
            "action": "ADD_MANDATORY_DECLARATION" | "UPDATE_HEIGHT_TABLE",
            "details": {{
                "id": "unique-rule-id",
                "citation": "E.g., Rule 6(1)(g)",
                "check": "presence",
                "condition": "condition if any"
            }},
            "explanation": "Human readable explanation of what this amendment changes."
        }}
        
        Gazette Text:
        {text_content}
        """
        
        model = genai.GenerativeModel('gemini-3.6-flash')
        response = model.generate_content(prompt)
        
        # Parse the JSON from the response
        response_text = response.text.strip()
        if response_text.startswith("```json"):
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif response_text.startswith("```"):
            response_text = response_text.split("```")[1].split("```")[0].strip()
            
        parsed_data = json.loads(response_text)
        
        results = []
        for item in parsed_data:
            results.append({
                "value": {
                    "action": item.get("action"),
                    "details": item.get("details")
                },
                "confidence": 0.95,
                "explanation": item.get("explanation", "Extracted by Gemini AI.")
            })
        return results

    except Exception as e:
        print(f"Gemini API Error: {str(e)}")
        # Fallback to mock on error
        return _mock_suggestion()


def _mock_suggestion() -> List[Dict[str, Any]]:
    mocked_llm_diff = {
        "action": "ADD_MANDATORY_DECLARATION",
        "details": {
            "id": "r6-1g-qr-code",
            "citation": "Rule 6(1)(g)",
            "check": "presence",
            "condition": "commodity_is_electronic"
        }
    }
    
    return [
        {
            "value": mocked_llm_diff,
            "confidence": 0.85,
            "explanation": "The gazette text indicates all electronic commodities must now bear a scannable QR Code on the principal display panel."
        }
    ]
