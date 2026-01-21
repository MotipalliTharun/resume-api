import json
import re
import httpx
from typing import Dict, List, Set, Any
from collections import Counter

class HybridKeywordExtractor:
    
    # Regex patterns for "Exact Keyword Harvesting" (Step 2)
    PATTERNS = [
        r'\b[A-Z][a-zA-Z0-9+.]+\b',      # PascalCase or CAPSWords (e.g. ReactJS, AWS)
        r'\b[A-Z]{2,}\b',                 # Acronyms (e.g. API, SQL)
        r'\b[A-Za-z]+\.js\b',             # .js extensions (e.g. node.js)
        r'\b[A-Za-z]+\s(?:Boot|Framework|API|Services)\b', # Targeted phrase patterns
        r'\b(?:C\+\+|C\#|\.NET)\b',       # Special chars (C++, C#, .NET)
    ]
    
    # Common stop words to filter out from Regex harvest (Basic filtering)
    STOP_WORDS = {
        "THE", "AND", "FOR", "WITH", "YOU", "ARE", "WILL", "THAT", "THIS", "FROM",
        "EXPERIENCE", "RESPONSIBILITIES", "REQUIREMENTS", "QUALIFICATIONS", "SUMMARY",
        "DESCRIPTION", "TEAM", "WORK", "SKILLS", "STRONG", "GOOD", "PREFERRED",
        "YEARS", "DEGREE", "BACHELOR", "MASTER", "UNIVERSITY", "LOCATION", "JOB",
        "TITLE", "COMPANY", "FULL", "TIME", "PART", "CONTACT", "PLEASE", "APPLY", "ROLE"
    }

    @staticmethod
    def regex_harvest(text: str) -> List[str]:
        """
        Step 2: Exact keyword harvesting using Regex.
        Captures Capitalized words, Acronyms, Versioned terms.
        """
        candidates = []
        for pat in HybridKeywordExtractor.PATTERNS:
            matches = re.findall(pat, text)
            candidates.extend(matches)
        
        # Filter junk
        cleaned = []
        for c in candidates:
            # Min length 2
            if len(c) < 2: continue
            # Remove purely numeric (unless valid like 3D?) -> usually junk
            if c.isdigit(): continue
            # Stop words
            if c.upper() in HybridKeywordExtractor.STOP_WORDS: continue
            
            cleaned.append(c)
        
        return list(set(cleaned))

    @staticmethod
    async def ai_extract_and_categorize(openai_api_key: str, openai_model: str, jd_text: str) -> Dict[str, Any]:
        """
        Step 5 & 7: Semantic Expansion & Categorization via LLM.
        """
        prompt = f"""You are a Gold-Standard CV Keyword Extractor. 
Analyze the Job Description below and extract technical skills into these 6 buckets.

**RULES:**
1. **EXTRACT ALL** explicit technical keywords.
2. **NO HALLUCINATION**: precise terms only.
3. **EXACT SPELLING**: Keep JD's casing/punctuation (e.g. "ReactJS").
4. **INFER HIDDEN SKILLS**: (e.g. "Event-Driven" -> includes "Kafka" only if strongly implied, else just "Event-Driven").

**CATEGORIES:**
1. **Core Tech**: Languages & Core Platforms (Java, Python, Node.js)
2. **Frameworks**: Libs & Tools (Spring Boot, React, Pandas)
3. **Architecture**: Concepts (Microservices, REST, CI/CD)
4. **Cloud/Infra**: (AWS, Docker, K8s, Terraform)
5. **Domain**: Industry terms (Payments, HL7, KYC, SaaS)
6. **Soft/Behavioral**: (Agile, Leadership - ONLY if critical)

**Return valid JSON:**
{{
  "core_tech": ["..."],
  "frameworks": ["..."],
  "architecture": ["..."],
  "cloud": ["..."],
  "domain": ["..."],
  "soft_skills": ["..."],
  "responsibilities": ["Top 5 critical technical duties..."]
}}

**Job Description:**
{jd_text[:4000]}
"""
        headers = {
            "Authorization": f"Bearer {openai_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": openai_model,
            "messages": [{"role": "system", "content": "Extract keywords JSON."}, {"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 1000
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
                resp.raise_for_status()
                content = resp.json()["choices"][0]["message"]["content"]
                
                # Parse JSON
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                    
                return json.loads(content)
        except Exception as e:
            print(f"AI Extraction Failed: {e}")
            return {}

    @staticmethod
    def calculate_relevance(keyword: str, jd_text: str, is_ai_found: bool) -> float:
        """
        Step 4: Relevance Scoring.
        """
        score = 1.0
        kf = keyword.lower()
        jf = jd_text.lower()
        
        # Frequency
        count = jf.count(kf)
        if count >= 3: score += 1.5
        elif count >= 2: score += 1.0
        
        # Source Confidence
        if is_ai_found: score += 1.0 # AI understands context
        
        # Length/Specifics (heuristics)
        # e.g. "Java" vs "Java 17"
        if len(keyword.split()) > 1: score += 0.5 
        
        return round(score, 2)

async def extract_keywords_with_ai(openai_api_key: str, openai_model: str, jd_text: str) -> Dict[str, Any]:
    """
    Orchestrates the Hybrid Pipeline: Rules + AI -> Scored & Categorized.
    Returns standard dict for compatibility + metadata.
    """
    # 1. Regex Harvest (Fast, Deterministic)
    regex_keywords = HybridKeywordExtractor.regex_harvest(jd_text)
    
    # 2. AI Extraction (Semantic, Categorized)
    ai_data = await HybridKeywordExtractor.ai_extract_and_categorize(openai_api_key, openai_model, jd_text)
    
    # 3. Merge & Deduplicate
    # We prefer AI's categorization but ensure we didn't miss Regex finds.
    # We will build a "master list" for relevance scoring.
    
    final_keywords = set()
    categories = {
        "core_tech": set(ai_data.get("core_tech") or []),
        "frameworks": set(ai_data.get("frameworks") or []),
        "architecture": set(ai_data.get("architecture") or []),
        "cloud": set(ai_data.get("cloud") or []),
        "domain": set(ai_data.get("domain") or []),
        "soft_skills": set(ai_data.get("soft_skills") or []),
    }
    
    # Add regex words to 'core_tech' if not present (simple fallback bucket)
    # or just treat them as unclassified "High Value"
    for rk in regex_keywords:
        # Check if already in any category
        found = False
        for cat_set in categories.values():
            if rk in cat_set: # Exact match
                found = True
                break
            # Case insensitive check?
            if any(c.lower() == rk.lower() for c in cat_set):
                found = True
                break
        
        if not found:
            # Add to 'uncategorized' or generic list. 
            # For simplicity, let's put them in 'core_tech' or a new list.
            # But the user wants structured. Let's add them to a 'detected' pool
            final_keywords.add(rk)

    # Flatten categories to final_keywords
    for cat_set in categories.values():
        for k in cat_set:
            final_keywords.add(k)
            
    # 4. Scoring (Optional step to filter low value, currently just passing all)
    # scored = []
    # for k in final_keywords:
    #     s = HybridKeywordExtractor.calculate_relevance(k, jd_text, True)
    #     scored.append((k, s))
    # scored.sort(key=lambda x: x[1], reverse=True)
    # top_k = [x[0] for x in scored[:60]] 
    
    # For now, return the comprehensive list
    
    # 5. Format Output
    # We need to return the structure expected by main.py but we can enrich it
    # main.py expects: {"keywords": [...], "responsibilities": [...]}
    
    # We will prioritize Categorized ones + Regex ones
    all_kws = list(final_keywords)
    
    # Preserve categorization for prompt injection if possible?
    # We can pack it into the 'keywords' list as strings "Category: Keyword"? 
    # Or just return a flat list for main.py to score, BUT modify main.py to use categories.
    # For compatibility, we return flat list, but we structure 'missing_keywords' in main logic?
    # Actually, let's return the structured dict nested in 'meta' or just flatten for now.
    
    return {
        "keywords": all_kws,
        "responsibilities": ai_data.get("responsibilities", []),
        "categories": {k: list(v) for k, v in categories.items()} # Extra data for consumer
    }

async def extract_contact_info_with_ai(openai_api_key: str, openai_model: str, resume_text: str) -> dict:
     # ... keep existing contact info extraction ...
    import httpx
    prompt = f"""Extract personal contact info from resume. Return JSON: {{ "full_name": "", "email": "", "phone": "", "linkedin": "", "location": "", "portfolio": "" }}"""
    headers = { "Authorization": f"Bearer {openai_api_key}", "Content-Type": "application/json" }
    prompt = f"""Analyze the above resume text and extract the candidate's personal contact information.
    
    Return ONLY valid JSON in this exact format:
    {{
      "full_name": "First Last",
      "email": "email@example.com",
      "phone": "(123) 456-7890",
      "linkedin": "linkedin.com/in/...",
      "location": "City, State",
      "portfolio": "github.com/..."
    }}
    
    If a field is missing, return an empty string "". 
    Do NOT invent information.
    
    **Resume Text:**
    {resume_text}
    """
    
    payload = {
        "model": openai_model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            
            # Robust JSON extraction
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            ai_data = {}
            if json_match:
                ai_data = json.loads(json_match.group(0))
            else:
                ai_data = json.loads(content) # Fallback to raw try
            
            # --- HYBRID BACKUP: REGEX ENRICHMENT ---
            # If AI missed email/phone, try regex on the raw text
            if not ai_data.get("email"):
                email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', resume_text)
                if email_match:
                    ai_data["email"] = email_match.group(0)
            
            if not ai_data.get("phone"):
                # Matches various phone formats: (123) 456-7890, 123-456-7890, +1 123 456 7890
                phone_match = re.search(r'(\+\d{1,2}\s?)?(\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}', resume_text)
                if phone_match:
                    ai_data["phone"] = phone_match.group(0)
            
            if not ai_data.get("linkedin"):
                 li_match = re.search(r'linkedin\.com/in/[a-zA-Z0-9_-]+', resume_text, re.IGNORECASE)
                 if li_match:
                     ai_data["linkedin"] = li_match.group(0)

            return ai_data

    except Exception as e:
        print(f"AI Contact Extraction Failed: {e}")
        # Even if AI fails, run regex
        fallback = {}
        try:
            import re
            email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', resume_text)
            if email_match: fallback["email"] = email_match.group(0)
            
            phone_match = re.search(r'(\+\d{1,2}\s?)?(\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}', resume_text)
            if phone_match: fallback["phone"] = phone_match.group(0)
            
            li_match = re.search(r'linkedin\.com/in/[a-zA-Z0-9_-]+', resume_text, re.IGNORECASE)
            if li_match: fallback["linkedin"] = li_match.group(0)
        except: pass
            
        return fallback
