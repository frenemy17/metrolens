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
    fail_rules = [v for v in violations if v.get("status") in ("FAIL", "NON_COMPLIANT", "POTENTIAL NON-COMPLIANCE")]
    pass_count = len([v for v in violations if v.get("status") == "PASS"])

    if not api_key:
        if fail_rules:
            return f"Inspection identified {len(fail_rules)} statutory defect(s) across tested packaging declarations. Pursuant to the Jan Vishwas Act, 2023, the packer is eligible for a 15-day statutory improvement notice before compounding proceedings."
        return f"All {pass_count} tested mandatory declarations conform to statutory requirements under the Legal Metrology (Packaged Commodities) Rules, 2011."

    prompt = f"""You are an authorized Legal Metrology Compliance Auditor for the Department of Consumer Affairs, Government of India. 
You are reviewing a product label for compliance with the Legal Metrology (Packaged Commodities) Rules, 2011.

Here is the extracted data from the label:
{fields_map}

Here are the findings recorded by the statutory verification engine:
{fail_rules}

Pass count: {pass_count}
Defect count: {len(fail_rules)}

Write an authoritative, concise 2-sentence statutory compliance verdict. 
Sentence 1: Summarize the overall compliance state and identify the primary defect, if any.
Sentence 2: State the specific statutory provisions violated and the administrative enforcement action (e.g. Form IN-1 Improvement Notice with 15-day cure window, or Section 48 compounding).
Return ONLY the two sentences. No headers, no greetings, no conversational filler, no markdown.
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
        print(f"Error calling language service for audit summary: {e}")
        if fail_rules:
            return f"Inspection identified {len(fail_rules)} statutory defect(s) on this retail pack. Pursuant to the Jan Vishwas Act, 2023, the packer is eligible for a 15-day improvement notice before compounding proceedings."
        return f"Package conforms to mandatory declarations under the Legal Metrology (Packaged Commodities) Rules, 2011."
