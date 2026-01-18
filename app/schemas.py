from pydantic import BaseModel
from typing import List, Optional

class ScoreBreakdown(BaseModel):
    keyword_score: float
    semantic_score: float
    ats_score: float
    total_score: float
    missing_keywords: List[str]
    matched_keywords: List[str] = []

class TailorResponse(BaseModel):
    run_id: int
    scores: ScoreBreakdown
    tailored_text: str
    tailored_md: str

class AnalyzeResponse(BaseModel):
    scores: ScoreBreakdown
    extracted_keywords: List[str]
    jd_top_requirements: List[str]

class RunUpdateRequest(BaseModel):
    tailored_text: str
