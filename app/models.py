from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
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

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    email = Column(String(256), unique=True, index=True, nullable=False)
    hashed_password = Column(String(256), nullable=False)
    full_name = Column(String(256), default="")
    
    is_active = Column(Integer, default=1) # 1=Active, 0=Inactive
    subscription_tier = Column(String(50), default="free") # free, pro, enterprise
    subscription_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Auth Extensions
    reset_token = Column(String(256), nullable=True)
    reset_token_expires = Column(DateTime(timezone=True), nullable=True)
    google_id = Column(String(256), nullable=True)
    
    # Stripe
    stripe_customer_id = Column(String(256), nullable=True, index=True)
    subscriptions = relationship("Subscription", back_populates="user")

class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    stripe_subscription_id = Column(String(256), unique=True, index=True)
    status = Column(String(50)) # trialing, active, past_due, canceled, unpaid
    price_id = Column(String(256))
    current_period_end = Column(DateTime(timezone=True))
    cancel_at_period_end = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", back_populates="subscriptions")

