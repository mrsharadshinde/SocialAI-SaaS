import streamlit as st
import sys
import os
import uuid
import time
from dotenv import load_dotenv

load_dotenv()

# --- PATH SETUP ---
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from app import database, models, crud

# Initialize DB
models.Base.metadata.create_all(bind=database.engine)

st.set_page_config(page_title="ReelFactory AI", page_icon="🎬", layout="wide")

# --- AUTH HELPER FUNCTIONS ---
def update_session_token(user_id, token):
    db = database.SessionLocal()
    user = db.query(models.UserProfile).filter(models.UserProfile.id == user_id).first()
    if user:
        user.session_token = token
        db.commit()
    db.close()

def check_auto_login():
    params = st.query_params
    token = params.get("auth", None)
    
    if token and 'user_id' not in st.session_state:
        db = database.SessionLocal()
        user = db.query(models.UserProfile).filter(models.UserProfile.session_token == token).first()
        db.close()
        
        if user:
            st.session_state['user_id'] = user.id
            st.session_state['username'] = user.username
            st.success("🔄 Auto-logged in!")
            time.sleep(0.5)
            st.rerun()

# --- PAGES ---
def login_page():
    st.title("🔐 Login to ReelFactory")
    col1, col2 = st.columns([1, 2])
    with col1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            db = database.SessionLocal()
            user = crud.get_user_by_username(db, username)
            db.close()
            
            if user and user.password_hash == password:
                st.session_state['user_id'] = user.id
                st.session_state['username'] = user.username
                new_token = str(uuid.uuid4())
                update_session_token(user.id, new_token)
                st.query_params["auth"] = new_token
                st.success(f"Welcome back, {username}!")
                st.rerun()
            else:
                st.error("Invalid username or password")

def register_page():
    st.title("🆕 Create Account")
    with st.form("register_form"):
        username = st.text_input("Choose Username")
        password = st.text_input("Choose Password", type="password")
        st.markdown("---")
        tone = st.text_input("Content Tone", value="Sarcastic, Logical, Maverick")
        visual = st.text_input("Visual Style", value="Dark, Rain, Nature, Aesthetic")
        persona = st.text_area("Persona Prompt", value="You are a 23yo digital creator...")
        st.markdown("### 🔑 API Keys")
        groq_key = st.text_input("Groq API Key (Recommended)", type="password")
        gemini_key = st.text_input("Gemini API Key", type="password")
        pexels_key = st.text_input("Pexels API Key", type="password")
        
        if st.form_submit_button("Create Account"):
            if not username or not password:
                st.error("Username and Password are required!")
                return
            db = database.SessionLocal()
            if crud.get_user_by_username(db, username):
                st.error("Username taken!")
            else:
                crud.create_user(db, username, password, persona, tone, visual, gemini_key, groq_key, pexels_key, provider="Groq")
                st.success("Account Created! Please Login.")
            db.close()

def main_app():
    with st.sidebar:
        st.write(f"👤 **{st.session_state['username']}**")
        if st.button("Logout"):
            st.query_params.clear() 
            update_session_token(st.session_state['user_id'], None)
            del st.session_state['user_id']
            del st.session_state['username']
            st.rerun()
    
    st.title("🎬 ReelFactory Studio")
    db = database.SessionLocal()
    current_user = db.query(models.UserProfile).filter(models.UserProfile.id == st.session_state['user_id']).first()
    
    tab_gen, tab_settings = st.tabs(["⚡ Generation Studio", "⚙️ Settings & Keys"])

    # --- TAB 1: GENERATION STUDIO ---
    with tab_gen:
        if not current_user:
            st.error("User not found.")
            return

        # 1. INPUT AREA (SPLIT INTO TABS)
        mode_ai, mode_manual = st.tabs(["🤖 AI Brainstorm", "✍️ Write Your Own"])

        # --- A. AI MODE ---
        with mode_ai:
            col_sw, col_btn = st.columns([1, 3])
            with col_sw:
                is_groq = (current_user.ai_provider == "Groq")
                active_provider = st.radio("Active Brain", ["Groq", "Gemini"], index=0 if is_groq else 1, horizontal=True)

            with col_btn:
                st.write("") 
                st.write("") 
                if st.button("🧠 Generate Idea", use_container_width=True):
                     prog_bar = st.progress(0, text="🧠 Brainstorming...")
                     from app.services.content_engine import ContentEngine
                     engine = ContentEngine(gemini_key=current_user.gemini_api_key, groq_key=current_user.groq_api_key, provider=active_provider)
                     
                     prog_bar.progress(50, text="✨ Thinking...")
                     idea, error = engine.generate_idea(current_user.persona_prompt, current_user.content_tone)
                     
                     prog_bar.progress(100, text="✅ Done!")
                     time.sleep(0.5)
                     prog_bar.empty()

                     if idea:
                        st.session_state['current_idea'] = idea
                        # Reset render state
                        for key in ['bg_video_path', 'current_style', 'final_video']:
                            if key in st.session_state: del st.session_state[key]
                        st.rerun()
                     else:
                        st.error(f"Error: {error}")

        # --- B. MANUAL MODE (NEW FEATURE) ---
        with mode_manual:
            with st.form("manual_idea_form"):
                st.caption("Have an idea? Write it yourself and let the engine render it.")
                
                # Manual Inputs
                custom_quote = st.text_area("Your Quote / Text", height=100, placeholder="e.g., Money returns, time doesn't.")
                custom_visual = st.text_input("Background Visual Search", placeholder="e.g., Time lapse clock, busy city, sunset")
                
                if st.form_submit_button("🚀 Set Custom Idea"):
                    if not custom_quote or not custom_visual:
                        st.error("Please enter both the Quote and a Visual Search term.")
                    else:
                        # We manually construct the 'idea' object just like the AI would
                        manual_idea = {
                            "quote": custom_quote,
                            "visual_search_term": custom_visual,
                            "language": "Manual",
                            "caption": "Custom Post",
                            "hashtags": ""
                        }
                        
                        st.session_state['current_idea'] = manual_idea
                        
                        # Reset render state so we don't show old videos
                        for key in ['bg_video_path', 'current_style', 'final_video']:
                            if key in st.session_state: del st.session_state[key]
                            
                        st.success("Idea Set! Scroll down to render.")
                        time.sleep(1)
                        st.rerun()

        # 2. RENDER STUDIO (Works for BOTH AI and Manual)
        if 'current_idea' in st.session_state:
            idea = st.session_state['current_idea']
            st.markdown("---")
            c1, c2 = st.columns([2,1])
            with c1: st.info(f"**Quote:** {idea['quote']}")
            with c2: st.info(f"**Visual:** {idea['visual_search_term']}")

            st.subheader("🎬 Controls")
            col_r, col_s, col_sty = st.columns(3)
            
            render = col_r.button("▶️ Render", use_container_width=True)
            swap = col_s.button("🔄 Swap BG", use_container_width=True)
            style = col_sty.button("🎨 Style", use_container_width=True)

            if render or swap or style:
                if not current_user.pexels_api_key:
                    st.error("⚠️ Missing Pexels API Key!")
                else:
                    prog_bar = st.progress(0, text="🚀 Starting Engine...")
                    from app.services.video_engine import VideoEngine
                    video_eng = VideoEngine(current_user.pexels_api_key)
                    
                    # 1. Background
                    if swap or 'bg_video_path' not in st.session_state:
                        bg = video_eng.get_stock_video(idea['visual_search_term'], progress_bar=prog_bar)
                        if bg: st.session_state['bg_video_path'] = bg
                        else: st.error("No video found.")
                    else:
                        prog_bar.progress(40, text="✅ Using Cached Background")

                    # 2. Style
                    styles = video_eng.get_style_names()
                    if style and 'current_style' in st.session_state:
                        idx = styles.index(st.session_state['current_style'])
                        st.session_state['current_style'] = styles[(idx + 1) % len(styles)]
                    elif 'current_style' not in st.session_state:
                        st.session_state['current_style'] = styles[0]
                    
                    # 3. Render
                    if 'bg_video_path' in st.session_state:
                        s_name = st.session_state['current_style']
                        path = video_eng.create_video(
                            st.session_state['bg_video_path'], 
                            idea['quote'], 
                            style_name=s_name,
                            progress_bar=prog_bar
                        )
                        st.session_state['final_video'] = path
                        prog_bar.progress(100, text="✅ Done!")
                        time.sleep(1)
                        prog_bar.empty()

            if 'final_video' in st.session_state:
                st.success(f"✅ Rendered Style: {st.session_state.get('current_style', 'Default')}")
                st.markdown("---")
                col_left, col_center, col_right = st.columns([3, 4, 3])
                with col_center:
                    st.caption("Preview:")
                    st.video(st.session_state['final_video'])

    # --- TAB 2: SETTINGS ---
    with tab_settings:
        st.subheader("🔐 API Keys & Persona")
        with st.form("settings_form"):
            col_a, col_b = st.columns(2)
            with col_a:
                g_status = "✅ Saved" if current_user.groq_api_key else "❌ Missing"
                st.caption(f"Groq Key ({g_status})")
                new_groq = st.text_input("Update Groq Key", type="password", placeholder="Leave empty to keep")
                gem_status = "✅ Saved" if current_user.gemini_api_key else "❌ Missing"
                st.caption(f"Gemini Key ({gem_status})")
                new_gemini = st.text_input("Update Gemini Key", type="password", placeholder="Leave empty to keep")
            with col_b:
                pex_status = "✅ Saved" if current_user.pexels_api_key else "❌ Missing"
                st.caption(f"Pexels Key ({pex_status})")
                new_pexels = st.text_input("Update Pexels Key", type="password", placeholder="Leave empty to keep")
            st.markdown("---")
            new_persona = st.text_area("Persona", value=current_user.persona_prompt)
            new_tone = st.text_input("Tone", value=current_user.content_tone)
            new_visual = st.text_input("Visual Style", value=current_user.visual_style)
            if st.form_submit_button("💾 Save Settings"):
                crud.update_user(db, current_user.id, new_persona, new_tone, new_visual, new_gemini, new_groq, new_pexels, current_user.ai_provider)
                st.success("Settings Updated!")
                st.rerun()
    db.close()

# --- APP START ---
check_auto_login()

if 'user_id' not in st.session_state:
    tab1, tab2 = st.tabs(["Login", "Register"])
    with tab1: login_page()
    with tab2: register_page()
else:
    main_app()