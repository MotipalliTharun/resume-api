from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from sqlalchemy.sql import func
from db import Base

class TailorRun(Base):
    __tablename__ = "tailor_runs"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    job_title = Column(String(256), default="")
    company = Column(String(256), default="")
    full_name = Column(String(256), default="YOUR NAME")

    jd_text = Column(Text, nullable=False)
    resume_text = Column(Text, nullable=False)

    score_keyword = Column(Float, default=0.0)
    score_semantic = Column(Float, default=0.0)
    score_ats = Column(Float, default=0.0)
    score_total = Column(Float, default=0.0)

    missing_keywords = Column(Text, default="")
    tailored_text = Column(Text, default="")
    tailored_md = Column(Text, default="")
    tailored_html = Column(Text, default="")

class CoverLetter(Base):
    __tablename__ = "cover_letters"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    job_title = Column(String(256), default="")
    company = Column(String(256), default="")
    full_name = Column(String(256), default="YOUR NAME")

    jd_text = Column(Text, nullable=False)
    resume_text = Column(Text, nullable=False)
    
    # The generated content
    cover_letter_text = Column(Text, default="") # Plain text / MD from LLM
    cover_letter_html = Column(Text, default="") # Rendered HTML
