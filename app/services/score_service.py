import re
from typing import Dict, List, Any

# Section Weighting Multipliers
SECTION_WEIGHTS = {
    "SKILLS": 1.5,
    "EXPERIENCE": 1.2, 
    "PROJECTS": 1.1,
    "SUMMARY": 1.0,
    "UNKNOWN": 1.0
}

# Match Type Weights
MATCH_WEIGHTS = {
    "EXACT": 1.0,    # Exact spelling and casing
    "ALIAS": 0.85,   # Case-insensitive or known alias
    "SEMANTIC": 0.65 # Partial or related
}

# Category Weights for Final Score
CATEGORY_WEIGHTS = {
    "core_tech": 0.35,
    "frameworks": 0.25,
    "architecture": 0.20,
    "domain": 0.15,
    "soft_skills": 0.05
}

class ATSScoreEngine:

    @staticmethod
    def identify_section(text_index: int, section_ranges: List[tuple]) -> str:
        """
        Determines which resume section a keyword match belongs to based on character index.
        """
        for sec_name, (start, end) in section_ranges:
            if start <= text_index < end:
                return sec_name
        return "UNKNOWN"

    @staticmethod
    def _map_sections(resume_text: str) -> List[tuple]:
        """
        Basic regex heuristic to map start/end indices of resume sections.
        """
        # Common headers
        headers = {
            "SKILLS": r"\b(SKILLS|TECHNICAL SKILLS|TECHNOLOGIES)\b",
            "EXPERIENCE": r"\b(EXPERIENCE|WORK HISTORY|EMPLOYMENT)\b",
            "PROJECTS": r"\b(PROJECTS|KEY PROJECTS)\b",
            "SUMMARY": r"\b(SUMMARY|PROFILE|OBJECTIVE)\b",
            "EDUCATION": r"\b(EDUCATION|ACADEMIC)\b"
        }
        
        found = []
        for name, pattern in headers.items():
            for match in re.finditer(pattern, resume_text, re.IGNORECASE):
                found.append((match.start(), name))
        
        found.sort() # Sort by start index
        
        # Create ranges
        ranges = []
        for i in range(len(found)):
            start, name = found[i]
            # End is start of next section, or end of text
            end = found[i+1][0] if i+1 < len(found) else len(resume_text)
            ranges.append((name, (start, end)))
            
        return ranges

    @staticmethod
    def calculate_weighted_score(
        resume_text: str,
        categorized_keywords: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """
        Calculates the Weighted ATS Score based on the user's formula.
        Input: 
           resume_text: str
           categorized_keywords: dict { "core_tech": ["Java", "React"], ... }
        """
        
        section_ranges = ATSScoreEngine._map_sections(resume_text)
        scores_by_category = {}
        missing_critical = []
        matched_details = []

        total_weighted_points = 0.0
        
        # 1. Iterate through each category
        for category, keywords in categorized_keywords.items():
            if not keywords: 
                scores_by_category[category] = 100.0 # No requirements = Full score? Or logic N/A
                continue
                
            cat_score_accum = 0.0
            cat_max_weight = len(keywords) # Max possible is 1.0 * count
            
            # For each keyword in this category
            for kw in keywords:
                # Find all matches
                # We use regex to find indices for section mapping
                # Match Exact vs Alias
                
                # Check EXACT match first (Case sensitive)
                exact_pattern = re.compile(rf"\b{re.escape(kw)}\b")
                exact_matches = [m for m in exact_pattern.finditer(resume_text)]
                
                # Check ALIAS/Case-Insensitive match
                alias_pattern = re.compile(rf"\b{re.escape(kw)}\b", re.IGNORECASE)
                alias_matches = [m for m in alias_pattern.finditer(resume_text)]
                
                # Determine best match type found
                match_type = None
                matches_found = []
                
                if exact_matches:
                    match_type = "EXACT"
                    matches_found = exact_matches
                elif alias_matches:
                    match_type = "ALIAS"
                    matches_found = alias_matches
                else:
                    # Missing
                    match_type = "MISSING"
                    if category == "core_tech": # Critical
                        missing_critical.append(kw)
                        
                if match_type != "MISSING":
                    # Calculate score for this keyword occurrence(s)
                    # Use frequency cap of 3
                    
                    # We take the BEST individual occurrence score? Or sum up to cap?
                    # User formula: "Where it appears matters."
                    # Let's sum the weighted values of the first 3 matches.
                    
                    kw_points = 0.0
                    trunc_matches = matches_found[:3] # Max 3 occurrences count
                    
                    for m in trunc_matches:
                        # Determine section
                        sec_name = ATSScoreEngine.identify_section(m.start(), section_ranges)
                        pos_weight = SECTION_WEIGHTS.get(sec_name, 1.0)
                        type_weight = MATCH_WEIGHTS[match_type]
                        
                        kw_points += (type_weight * pos_weight)
                    
                    # Normalize single keyword contribution to max 1.0 (or let it boost?)
                    # User formula: "Category Coverage = Sum(scores) / Sum(weights)"
                    # This implies scores can exceed 1.0 per keyword if position boosts it.
                    # e.g., Exact match (1.0) in Skills (1.5) = 1.5 points.
                    # This helps compensate for imperfect recall elsewhere.
                    
                    cat_score_accum += kw_points
                    
                    matched_details.append({
                        "keyword": kw,
                        "category": category,
                        "match_type": match_type,
                        "count": len(matches_found),
                        "points": round(kw_points, 2)
                    })
                
            # Calculate raw category percentage (0.0 to 1.0, clamped)
            # Denominator is simply count of keywords (each worth "1.0" base).
            # If position weighting boosts numerator, coverage can > 100%. Clamp it.
            
            raw_coverage = cat_score_accum / max(1, len(keywords))
            final_cat_coverage = min(raw_coverage, 1.0)
            
            scores_by_category[category] = round(final_cat_coverage * 100, 1)

        # 2. Calculate Final Weighted ATS Score
        final_ats_score = 0.0
        
        # Ensure we have defaults for standard cats if missing from extraction
        for cat in CATEGORY_WEIGHTS:
            coverage = scores_by_category.get(cat, 0.0) # 0 to 100
            weight = CATEGORY_WEIGHTS[cat]
            final_ats_score += (coverage * weight)

        # 3. Apply Penalties
        # Penalty: Missing Critical Skills (Core Tech) -> Cap at 65%
        if missing_critical:
            # Check ratio. If > 50% criticals missing? Or just ANY?
            # User said: "Must have: React, Java. Missing one -> cap <= 65%"
            # Heuristic: If missing > 1 critical item or specific ones?
            # Let's just apply a flat cap if Core Tech coverage < 50%
            
            core_cov = scores_by_category.get("core_tech", 0.0)
            if core_cov < 50.0:
                 final_ats_score = min(final_ats_score, 65.0)

        return {
            "total_score": round(final_ats_score, 1),
            "category_scores": scores_by_category, 
            "missing_critical": missing_critical,
            "matched_details": matched_details
        }

# --- Legacy Compatibility Wrappers for Main.py ---

def keyword_coverage_score(resume_text: str, keywords: list[str]) -> tuple:
    """
    Legacy wrapper. Converts flat keyword list into 'core_tech' bucket for scoring.
    """
    # Create fake categorized input
    cats = {"core_tech": keywords} # Treat all as core
    engine = ATSScoreEngine()
    result = engine.calculate_weighted_score(resume_text, cats)
    
    # Map back to expected legacy return signature: (score_0_1, missing_list, matched_list)
    score = result["total_score"] / 100.0
    
    # Differentiate missing/matched
    all_kws = set(keywords)
    matched = set([m["keyword"] for m in result["matched_details"]])
    missing = list(all_kws - matched)
    
    return score, missing, list(matched)

def ats_format_score(text: str) -> float:
    # Keep the simple formatting check from before
    score = 100.0 # scale up to 100? or keep 0-1
    # ... actually let's just stick to the old logic approx 0-1 for compatibility
    # Copying old logic lightly
    if "|" in text and "----" in text: score -= 15
    if "•" in text: score -= 5
    must = ["summary", "skills", "experience", "education"]
    low = text.lower()
    for h in must:
        if h not in low: score -= 15
        
    return max(0, min(100, score)) / 100.0

def extract_keywords(jd_text: str) -> list[str]:
    # Basic regex extractor (Step 2 fallback)
    # We can utilize our Hybrid logic if we imported it, or just keep simple here.
    # For now, keep simple to avoid circular deps if any.
    return re.findall(r"\b[A-Z][a-zA-Z0-9+]+\b", jd_text) # Simple

def top_requirements(jd_text: str, n: int = 8) -> list[str]:
    # Legacy wrapper for top requirements extraction
    lines = [l.strip() for l in jd_text.splitlines() if l.strip()]
    req = []
    for l in lines:
        low = l.lower()
        if any(x in low for x in ["must", "required", "requirements", "responsibilities", "you will", "we are seeking", "experience with"]):
            req.append(l)
    if len(req) < 3:
        req = lines[:n]
    return req[:n]
