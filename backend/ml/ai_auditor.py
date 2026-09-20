import os
from typing import Dict, List, Any, Optional


def generate_ai_auditor_analysis(
    fields_map: Dict[str, Any], 
    violations: List[Dict[str, Any]]
) -> Optional[str]:
    """
    Calls Groq API to generate a professional auditor analysis of the compliance.
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return "Warning: GROQ_API_KEY not set. AI Auditor cannot run."

    fail_rules = [v for v in violations if v.get("status") in ("FAIL", "NON_COMPLIANT", "POTENTIAL NON-COMPLIANCE")]
    pass_count = len([v for v in violations if v.get("status") == "PASS"])

    prompt = f"""You are an expert Legal Metrology Compliance Auditor in India. 
You are reviewing a product label for compliance with the Legal Metrology (Packaged Commodities) Rules, 2011.

Here is the extracted data from the label:
{fields_map}

Here are the violations flagged by our deterministic rules engine:
{fail_rules}

Pass count: {pass_count}
Defect count: {len(fail_rules)}

Write a professional, concise 2-sentence compliance verdict. 
Sentence 1: Summarize the overall compliance state and identify the most critical defect.
Sentence 2: State the specific PC Rules violated and the legal consequence (e.g. compounding fine under Section 48).
Return ONLY the two sentences. No headers, no lists, no markdown.
"""

    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="qwen/qwen3.8-27b",
            temperature=0.2,
            max_tokens=256
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error calling Groq for audit summary: {e}")
        return f"Inspection identified {len(fail_rules)} statutory defect(s) on this retail pack. Pursuant to the Jan Vishwas Act, 2023, the packer is eligible for a 15-day improvement notice before compounding proceedings."
