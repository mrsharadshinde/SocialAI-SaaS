from sqlalchemy import Column, Integer, String, Boolean, Text
from .database import Base

class UserProfile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)

    session_token = Column(String, nullable=True)
    
    # Core Brain (Defaults)
    persona_prompt = Column(Text, default="You are a helpful creative assistant.")
    content_tone = Column(String, default="Professional, Engaging")
    language = Column(String, default="English")

    # Visuals (Defaults)
    visual_style = Column(String, default="Cinematic, Minimalist")

    # Secrets
    gemini_api_key = Column(String, nullable=True)
    groq_api_key = Column(String, nullable=True)
    pexels_api_key = Column(String, nullable=True)
    
    # Preferences
    ai_provider = Column(String, default="Groq")

    is_active = Column(Boolean, default=True)