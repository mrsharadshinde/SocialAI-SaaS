from sqlalchemy import Column, Integer, String, Boolean, Text
from .database import Base

class UserProfile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)

    # Core Brain
    persona_prompt = Column(Text)
    content_tone = Column(String)
    language = Column(String, default="English")

    # Visuals
    visual_style = Column(String)

    # Secrets
    gemini_api_key = Column(String)
    groq_api_key = Column(String)      # <--- NEW: Store Groq Key
    pexels_api_key = Column(String)
    insta_username = Column(String)
    insta_password = Column(String)

    # Preferences
    ai_provider = Column(String, default="Groq") # <--- NEW: "Gemini" or "Groq"

    is_active = Column(Boolean, default=True)