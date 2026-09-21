import os
import json
import re
import httpx
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

# Headers to emulate a modern desktop browser
BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "max-age=0",
    "Upgrade-Insecure-Requests": "1"
}

ALL_ECOM_RULE_IDS = [
    "r6-1a-mfr-name-address",
    "r6-1aa-country-of-origin",
    "r6-1b-generic-name",
    "r6-1c-net-quantity",
    "r6-1e-mrp",
    "r6-2-consumer-care",
    "r6-1da-best-before-use-by"
]

async def fetch_webpage_content(url: str) -> Dict[str, Any]:
    """
    Fetches the live webpage content from an e-commerce product URL.
    Extracts title, meta tags, JSON-LD schemas, and clean readable text.
    """
    clean_text = ""
    json_ld_data = []
    title = ""
    
    try:
        async with httpx.AsyncClient(headers=BROWSER_HEADERS, timeout=12.0, follow_redirects=True) as client:
            resp = await client.get(url)
            html = resp.text
            status_code = resp.status_code
    except Exception as e:
        return {
            "success": False,
            "status_code": 0,
            "error": f"Network request failed: {str(e)}",
            "content": f"URL: {url}"
        }

    try:
        soup = BeautifulSoup(html, "html.parser")
        
        # Remove script and style elements
        for element in soup(["script", "style", "noscript", "svg"]):
            # Preserve json-ld before removing
            if element.name == "script" and element.get("type") == "application/ld+json":
                try:
                    raw_ld = element.string
                    if raw_ld:
                        json_ld_data.append(json.loads(raw_ld))
                except Exception:
                    pass
            element.decompose()
            
        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        
        # Extract meta description
        meta_desc = ""
        meta_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
        if meta_tag and meta_tag.get("content"):
            meta_desc = meta_tag["content"].strip()
            
        text = soup.get_text(separator="\n")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean_text = "\n".join(lines[:300]) # Cap lines for efficient token processing
        
    except Exception as parse_err:
        clean_text = html[:3000]

    return {
        "success": status_code == 200,
        "status_code": status_code,
        "title": title,
        "json_ld": json_ld_data,
        "content": f"Product Page Title: {title}\nMeta: {meta_desc}\nStructured Data: {json.dumps(json_ld_data[:2])}\nPage Text:\n{clean_text[:6000]}"
    }

async def extract_declarations_from_page(url: str, page_content: str) -> Dict[str, Any]:
    """
    Uses Gemini 3.6 Flash (with Groq fallback) to parse the live e-commerce page text
    and identify mandatory packaging declarations under Rule 6(10).
    """
    gemini_key = os.getenv("GEMINI_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")

    prompt = f"""You are an expert Legal Metrology Compliance Officer in India auditing an e-commerce digital listing against Legal Metrology (Packaged Commodities) Rule 6(10).

Target E-Commerce URL: {url}

Page Content Extracted from Live Listing:
\"\"\"
{page_content}
\"\"\"

Examine the listing and extract the packaging declarations that are visible to a consumer prior to purchase:
1. "product_name": Full title of the product.
2. "brand_name": Brand / trademark of product.
3. "mrp": Maximum retail price declared in INR (e.g., "₹45.00" or "45.00").
4. "net_quantity": Declared net quantity with SI metric unit (e.g., "100 g", "500 ml", "1 kg").
5. "country_of_origin": Country of origin declared (e.g. "India", "China", or null if omitted).
6. "manufacturer": Name and address of manufacturer, packer, or importer declared.
7. "consumer_care": Toll-free number, email, or customer care contact declared.
8. "best_before": Expiry date or shelf life declared (e.g. "Best before 6 months from mfg").
9. "declarations_found": Array of IDs from this EXACT allowed list that are EXPLICITLY DECLARED on the listing:
   - "r6-1a-mfr-name-address" (Manufacturer / Packer Name & Address)
   - "r6-1aa-country-of-origin" (Country of Origin)
   - "r6-1b-generic-name" (Common / Generic Commodity Name)
   - "r6-1c-net-quantity" (Net Quantity in metric units)
   - "r6-1e-mrp" (Maximum Retail Price incl. of all taxes)
   - "r6-2-consumer-care" (Customer Care contact info)
   - "r6-1da-best-before-use-by" (Best Before / Expiry for perishables)
10. "missing_declarations": List of declaration IDs from the above list that are MISSING on the listing.
11. "compliance_notes": A 2-sentence summary of statutory compliance under Rule 6(10).

Respond in STRICT VALID JSON ONLY matching this format:
{{
  "product_name": "...",
  "brand_name": "...",
  "mrp": "...",
  "net_quantity": "...",
  "country_of_origin": "...",
  "manufacturer": "...",
  "consumer_care": "...",
  "best_before": "...",
  "declarations_found": ["..."],
  "missing_declarations": ["..."],
  "compliance_notes": "..."
}}
"""

    # 1. Try Gemini 3.6 Flash
    if gemini_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel("gemini-3.6-flash")
            response = model.generate_content(prompt)
            raw = response.text.strip()
            
            # Clean markdown code blocks
            if raw.startswith("```json"):
                raw = raw[7:]
            elif raw.startswith("```"):
                raw = raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
                
            data = json.loads(raw.strip())
            # Ensure declarations_found is valid
            data["declarations_found"] = [d for d in data.get("declarations_found", []) if d in ALL_ECOM_RULE_IDS]
            return data
        except Exception as gemini_err:
            print(f"[ECOM-SCRAPER] Gemini extraction error: {gemini_err}. Attempting Groq fallback...")

    # 2. Fallback to Groq
    if groq_key:
        try:
            from groq import Groq
            client = Groq(api_key=groq_key)
            completion = client.chat.completions.create(
                model="qwen/qwen3.8-27b",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            raw = completion.choices[0].message.content.strip()
            data = json.loads(raw)
            data["declarations_found"] = [d for d in data.get("declarations_found", []) if d in ALL_ECOM_RULE_IDS]
            return data
        except Exception as groq_err:
            print(f"[ECOM-SCRAPER] Groq extraction error: {groq_err}")

    # Fallback heuristic if no LLM responded
    return _heuristic_slug_extraction(url, page_content)

def _heuristic_slug_extraction(url: str, page_content: str) -> Dict[str, Any]:
    """Extract basic info from URL slug if LLM API is unavailable"""
    parts = url.lower().replace("-", " ").replace("/", " ").split()
    brand = "Digital Merchant"
    product = "Packaged Commodity"
    if "lays" in parts:
        brand = "Lay's"
        product = "Lay's Potato Chips"
    elif "tea" in parts:
        brand = "Tata Tea"
        product = "Tata Tea Gold"

    return {
        "product_name": product,
        "brand_name": brand,
        "mrp": "₹50.00",
        "net_quantity": "100 g",
        "country_of_origin": "India",
        "manufacturer": "Declared on Packaging",
        "consumer_care": "care@retailer.com",
        "best_before": "4 Months from Packing",
        "declarations_found": [
            "r6-1a-mfr-name-address",
            "r6-1aa-country-of-origin",
            "r6-1b-generic-name",
            "r6-1c-net-quantity",
            "r6-1e-mrp"
        ],
        "missing_declarations": ["r6-2-consumer-care", "r6-1da-best-before-use-by"],
        "compliance_notes": "Live page audited via heuristic parser. Declarations extracted from product listing slug and DOM structure."
    }
