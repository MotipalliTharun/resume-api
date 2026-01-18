import re
from rapidfuzz import fuzz

STOP = {
    "and","or","the","a","an","to","for","with","in","on","of","at","by","from",
    "is","are","be","as","this","that","will","you","we","our","your"
}

def extract_keywords(jd_text: str, max_keywords: int = 40) -> list[str]:
    # Simple ATS-ish keyword extractor:
    # - pull capitalized tech words, acronyms, tools, common skill tokens
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9\+\.\-#]{1,}", jd_text)
    norm = []
    for t in tokens:
        low = t.lower()
        if low in STOP:
            continue
        if len(low) < 2:
            continue
        norm.append(low)

    # frequency
    freq = {}
    for t in norm:
        freq[t] = freq.get(t, 0) + 1

    # prioritize tech-ish tokens
    def tech_weight(tok: str) -> float:
        w = freq[tok]
        if any(x in tok for x in ["java","spring","kafka","aws","azure","gcp","docker","kubernetes","sql","postgres","redis","mongodb","react","node","oauth","jwt","grpc","rest","graphql","linux","terraform","ci/cd","jenkins"]):
            w += 3
        if tok.isupper():
            w += 1
        if any(ch in tok for ch in ["+",".","#","-"]):
            w += 1
        return w

    ranked = sorted(freq.keys(), key=lambda x: tech_weight(x), reverse=True)
    # de-dup common variants
    out = []
    for r in ranked:
        if r in out:
            continue
        if len(out) >= max_keywords:
            break
        out.append(r)
    return out

def keyword_coverage_score(resume_text: str, keywords: list[str]) -> tuple[float, list[str]]:
    rt = resume_text.lower()
    matched = []
    missing = []
    present = 0
    for kw in keywords:
        if kw in rt:
            present += 1
            matched.append(kw)
        else:
            missing.append(kw)
    score = present / max(1, len(keywords))
    return score, missing, matched

def ats_format_score(text: str) -> float:
    # Basic ATS-safe checks: headings + no weird characters + bullet sanity
    score = 1.0
    # penalize tables-ish patterns
    if "|" in text and "----" in text:
        score -= 0.15
    # penalize too many unicode bullets
    if "•" in text:
        score -= 0.05
    # require headings
    must = ["summary", "skills", "experience", "education"]
    low = text.lower()
    for h in must:
        if h not in low:
            score -= 0.15
    # overlong lines
    long_lines = [ln for ln in text.splitlines() if len(ln) > 140]
    if len(long_lines) > 5:
        score -= 0.1
    return max(0.0, min(1.0, score))

def text_similarity_Fuzzy(jd_text: str, resume_text: str) -> float:
    # fallback similarity (not embeddings)
    return fuzz.token_set_ratio(jd_text, resume_text) / 100.0

def top_requirements(jd_text: str, n: int = 8) -> list[str]:
    # quick extraction of requirement-like lines
    lines = [l.strip() for l in jd_text.splitlines() if l.strip()]
    req = []
    for l in lines:
        low = l.lower()
        if any(x in low for x in ["must", "required", "requirements", "responsibilities", "you will", "we are seeking", "experience with"]):
            req.append(l)
    # fallback: first N meaningful lines
    if len(req) < 3:
        req = lines[:n]
    return req[:n]
