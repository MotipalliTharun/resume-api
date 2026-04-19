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

class BatchJobInput(BaseModel):
    job_title: str
    company: str
    jd_text: str
    job_url: Optional[str] = None

class BatchTailorResult(BaseModel):
    job_title: str
    company: str
    run_id: int
    filename: str
    total_score: float
    missing_keywords: List[str]
    status: str  # "success" | "error"
    error: Optional[str] = None

# Auth Schemas
class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str
    full_name: Optional[str] = None

class UserLogin(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    subscription_tier: str
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
