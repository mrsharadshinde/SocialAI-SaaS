from sqlalchemy.orm import Session
from . import models

def get_user_by_username(db: Session, username: str):
    return db.query(models.UserProfile).filter(models.UserProfile.username == username).first()

# Updated to receive Groq Key and Provider
def create_user(db: Session, username, persona, tone, visual, g_key, groq_key, p_key, provider="Groq"):
    db_user = models.UserProfile(
        username=username,
        persona_prompt=persona,
        content_tone=tone,
        visual_style=visual,
        gemini_api_key=g_key,
        groq_api_key=groq_key,  # <--- NEW
        pexels_api_key=p_key,
        ai_provider=provider    # <--- NEW
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id, persona, tone, visual, g_key, groq_key, p_key, provider):
    db_user = db.query(models.UserProfile).filter(models.UserProfile.id == user_id).first()
    if db_user:
        db_user.persona_prompt = persona
        db_user.content_tone = tone
        db_user.visual_style = visual
        db_user.gemini_api_key = g_key
        db_user.groq_api_key = groq_key  # <--- NEW
        db_user.pexels_api_key = p_key
        db_user.ai_provider = provider   # <--- NEW
        db.commit()
        db.refresh(db_user)
    return db_user