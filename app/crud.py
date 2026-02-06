from sqlalchemy.orm import Session
from . import models

def get_user_by_username(db: Session, username: str):
    return db.query(models.UserProfile).filter(models.UserProfile.username == username).first()

def create_user(db: Session, username, password, persona, tone, visual, g_key, groq_key, p_key, provider="Groq"):
    db_user = models.UserProfile(
        username=username,
        password_hash=password,
        persona_prompt=persona,
        content_tone=tone,
        visual_style=visual,
        gemini_api_key=g_key,
        groq_api_key=groq_key,
        pexels_api_key=p_key,
        ai_provider=provider
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
        db_user.ai_provider = provider
        
        # Only update keys if the user actually typed something new (non-empty)
        if g_key: db_user.gemini_api_key = g_key
        if groq_key: db_user.groq_api_key = groq_key
        if p_key: db_user.pexels_api_key = p_key
        
        db.commit()
        db.refresh(db_user)
    return db_user