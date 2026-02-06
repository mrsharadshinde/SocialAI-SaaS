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

# --- PAGE CONFIG & CUSTOM STYLING ---
st.set_page_config(page_title="ReelFactory AI", page_icon="🎬", layout="wide")

# Custom CSS for Professional Look
st.markdown("""
<style>
    .stApp { background-color: #0E1117; }
    h1, h2, h3 { font-family: 'Inter', sans-serif; font-weight: 600; }
    .stButton>button { border-radius: 8px; font-weight: bold; transition: all 0.3s; }
    .stButton>button:hover { transform: scale(1.02); }
    .stTextInput>div>div>input { border-radius: 8px; }
    div[data-testid="stMetricValue"] { font-size: 1.5rem; }
</style>
""", unsafe_allow_html=True)

# --- LOAD SYSTEM KEYS (Your "Free Tier" Keys) ---
# ⚠️ MAKE SURE THESE ARE IN YOUR .env FILE
SYSTEM_GROQ = os.getenv("GROQ_API_KEY")
SYSTEM_GEMINI = os.getenv("GEMINI_API_KEY")
SYSTEM_PEXELS = os.getenv("PEXELS_API_KEY")

# --- SESSION STATE SETUP ---
if 'guest_usage' not in st.session_state:
    st.session_state['guest_usage'] = 0
if 'page_view' not in st.session_state:
    st.session_state['page_view'] = 'studio'

# --- AUTH HELPERS ---
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
            st.toast(f"Welcome back, {user.username}!", icon="👋")
            time.sleep(0.5)
            st.rerun()

def logout():
    st.query_params.clear() 
    if 'user_id' in st.session_state:
        update_session_token(st.session_state['user_id'], None)
        del st.session_state['user_id']
        del st.session_state['username']
    st.session_state['page_view'] = 'studio'
    st.rerun()

# --- VIEWS ---

def login_view():
    col_c = st.columns([1,1,1])[1]
    with col_c:
        st.subheader("🔐 Access Your Studio")
        with st.container(border=True):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.button("Login", use_container_width=True, type="primary"):
                db = database.SessionLocal()
                user = crud.get_user_by_username(db, username)
                db.close()
                if user and user.password_hash == password:
                    st.session_state['user_id'] = user.id
                    st.session_state['username'] = user.username
                    new_token = str(uuid.uuid4())
                    update_session_token(user.id, new_token)
                    st.query_params["auth"] = new_token
                    st.session_state['page_view'] = 'studio'
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        if st.button("⬅️ Go Back", use_container_width=True):
            st.session_state['page_view'] = 'studio'
            st.rerun()

def register_view():
    col_c = st.columns([1,2,1])[1]
    with col_c:
        st.subheader("🚀 Join ReelFactory")
        with st.container(border=True):
            username = st.text_input("Choose Username")
            password = st.text_input("Choose Password", type="password")
            st.markdown("---")
            c1, c2 = st.columns(2)
            with c1: tone = st.text_input("Default Tone", value="Sarcastic")
            with c2: visual = st.text_input("Default Visual", value="Dark Cinematic")
            persona = st.text_area("Default Persona", value="You are a digital creator...", height=100)
            
            if st.button("Create Account", use_container_width=True, type="primary"):
                if not username or not password:
                    st.error("Fields required!")
                else:
                    db = database.SessionLocal()
                    if crud.get_user_by_username(db, username):
                        st.error("Username taken!")
                    else:
                        crud.create_user(db, username, password, persona, tone, visual, "", "", "", provider="Groq")
                        st.toast("Account Created! Please Login.", icon="✅")
                        st.session_state['page_view'] = 'login'
                        time.sleep(1)
                        st.rerun()
                    db.close()
        if st.button("⬅️ Go Back", use_container_width=True):
            st.session_state['page_view'] = 'studio'
            st.rerun()

def profile_settings_view(current_user):
    st.subheader(f"⚙️ Settings: {current_user.username}")
    with st.container(border=True):
        st.info("💡 Add your own API keys here to remove limits and speed up generation.")
        with st.form("settings_form"):
            c1, c2 = st.columns(2)
            with c1:
                new_groq = st.text_input("Groq API Key", type="password", placeholder="Paste key here...")
            with c2:
                new_pexels = st.text_input("Pexels API Key", type="password", placeholder="Paste key here...")
            
            st.markdown("---")
            new_persona = st.text_area("My Persona", value=current_user.persona_prompt)
            
            if st.form_submit_button("💾 Save Profile", type="primary"):
                db = database.SessionLocal()
                crud.update_user(db, current_user.id, new_persona, current_user.content_tone, current_user.visual_style, 
                               current_user.gemini_api_key, new_groq, new_pexels, current_user.ai_provider)
                db.close()
                st.toast("Settings Saved!", icon="💾")
                time.sleep(1)
                st.session_state['page_view'] = 'studio'
                st.rerun()
    if st.button("⬅️ Back to Studio"):
        st.session_state['page_view'] = 'studio'
        st.rerun()

def studio_view():
    # --- NAVBAR ---
    c1, c2 = st.columns([6, 2])
    with c1:
        st.title("🎬 ReelFactory Studio")
    with c2:
        if 'user_id' in st.session_state:
            st.write(f"👤 **{st.session_state['username']}**")
            cols = st.columns(2)
            if cols[0].button("⚙️"): st.session_state['page_view'] = 'profile'; st.rerun()
            if cols[1].button("Log Out"): logout()
        else:
            cols = st.columns(2)
            if cols[0].button("Login"): st.session_state['page_view'] = 'login'; st.rerun()
            if cols[1].button("Sign Up", type="primary"): st.session_state['page_view'] = 'register'; st.rerun()

    # --- USER DATA & GUEST LOGIC ---
    db = database.SessionLocal()
    current_user = None
    if 'user_id' in st.session_state:
        current_user = db.query(models.UserProfile).filter(models.UserProfile.id == st.session_state['user_id']).first()
    db.close()

    # DEFAULTS
    d_tone, d_vis, d_per = "Sarcastic", "Dark Nature", "You are a creative assistant."
    if current_user:
        d_tone = current_user.content_tone or d_tone
        d_vis = current_user.visual_style or d_vis
        d_per = current_user.persona_prompt or d_per

    # GUEST BANNER
    if not current_user:
        rem = 3 - st.session_state['guest_usage']
        if rem > 0:
            st.markdown(f"""
            <div style="background-color: #1e3a8a; padding: 15px; border-radius: 10px; margin-bottom: 20px; display: flex; align-items: center; justify-content: space-between;">
                <span style="color: white; font-weight: bold;">👋 Guest Mode Active</span>
                <span style="background-color: #3b82f6; padding: 5px 10px; border-radius: 5px; color: white;">{rem} Free Credits Left</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.error("🚫 Guest credits exhausted. Please Sign Up (it's free!) to continue.")

    # --- MAIN STUDIO UI ---
    tab_ai, tab_manual = st.tabs(["✨ AI Generator", "✍️ Manual Mode"])

    with tab_ai:
        with st.container(border=True):
            c_in1, c_in2 = st.columns([1, 2])
            with c_in1:
                st.markdown("#### 🎨 Style")
                i_tone = st.text_input("Content Tone", value=d_tone)
                i_vis = st.text_input("Visual Style", value=d_vis)
                provider = st.selectbox("AI Model", ["Groq", "Gemini"])
            with c_in2:
                st.markdown("#### 🧠 Persona")
                i_per = st.text_area("Instructions", value=d_per, height=145)

            if st.button("✨ Generate Idea", use_container_width=True, type="primary"):
                # LIMIT CHECK
                if not current_user and st.session_state['guest_usage'] >= 3:
                    st.error("Please Login to continue.")
                else:
                    # KEY SELECTION LOGIC
                    active_groq = current_user.groq_api_key if current_user and current_user.groq_api_key else SYSTEM_GROQ
                    active_gemini = current_user.gemini_api_key if current_user and current_user.gemini_api_key else SYSTEM_GEMINI
                    
                    # Validate Keys
                    valid_key = False
                    if provider == "Groq" and active_groq: valid_key = True
                    if provider == "Gemini" and active_gemini: valid_key = True

                    if not valid_key:
                        st.error(f"⚠️ System Error: No API Key available for {provider}. Please check .env file.")
                    else:
                        if not current_user: st.session_state['guest_usage'] += 1
                        
                        prog = st.progress(0, text="🚀 Waking up AI...")
                        from app.services.content_engine import ContentEngine
                        eng = ContentEngine(gemini_key=active_gemini, groq_key=active_groq, provider=provider)
                        
                        prog.progress(40, text="🧠 Brainstorming...")
                        idea, err = eng.generate_idea(i_per, i_tone)
                        
                        if idea:
                            st.session_state['current_idea'] = idea
                            # Clean slate for new render
                            if 'final_video' in st.session_state: del st.session_state['final_video']
                            prog.progress(100, text="Done!")
                            time.sleep(0.5)
                            prog.empty()
                            st.rerun()
                        else:
                            st.error(f"Generation Failed: {err}")

    with tab_manual:
        with st.container(border=True):
            m_quote = st.text_area("Your Quote")
            m_vis = st.text_input("Background Search Term")
            if st.button("🚀 Set Idea", use_container_width=True):
                st.session_state['current_idea'] = {
                     "quote": m_quote,
                     "visual_search_term": m_vis,
                     "language": "Manual", "caption": "", "hashtags": ""
                 }
                st.rerun()

    # --- PREVIEW & RENDER SECTION ---
    if 'current_idea' in st.session_state:
        st.markdown("### 🎬 Production")
        idea = st.session_state['current_idea']
        
        with st.container(border=True):
            c_info1, c_info2 = st.columns([3, 1])
            with c_info1: st.info(f"**Quote:** \"{idea['quote']}\"")
            with c_info2: st.caption(f"**Visual:** {idea['visual_search_term']}")

            cols = st.columns(3)
            do_render = cols[0].button("▶️ Render Video", use_container_width=True, type="primary")
            do_swap = cols[1].button("🔄 Swap Background", use_container_width=True)
            do_style = cols[2].button("🎨 Change Font", use_container_width=True)

            if do_render or do_swap or do_style:
                # PEXELS KEY LOGIC
                active_pexels = current_user.pexels_api_key if current_user and current_user.pexels_api_key else SYSTEM_PEXELS
                
                if not active_pexels:
                    st.error("⚠️ System Error: Pexels API Key missing.")
                else:
                    bar = st.progress(0, text="Initializing...")
                    from app.services.video_engine import VideoEngine
                    v_eng = VideoEngine(active_pexels)
                    
                    # 1. Background
                    if do_swap or 'bg_video_path' not in st.session_state:
                        bg = v_eng.get_stock_video(idea['visual_search_term'], progress_bar=bar)
                        if bg: st.session_state['bg_video_path'] = bg
                        else: st.error("No video found.")
                    else:
                        bar.progress(30, text="Using Cached Background")

                    # 2. Style
                    styles = v_eng.get_style_names()
                    curr = st.session_state.get('current_style', styles[0])
                    if do_style:
                        idx = styles.index(curr)
                        curr = styles[(idx + 1) % len(styles)]
                    st.session_state['current_style'] = curr

                    # 3. Render
                    if 'bg_video_path' in st.session_state:
                        path = v_eng.create_video(
                            st.session_state['bg_video_path'], 
                            idea['quote'], 
                            style_name=curr,
                            progress_bar=bar
                        )
                        if path:
                            st.session_state['final_video'] = path
                            bar.empty()
                            st.toast("Render Complete!", icon="✅")
                        else:
                            st.error("Render Failed (Memory/Error)")

        # FINAL VIDEO DISPLAY
        if st.session_state.get('final_video'):
            st.markdown("---")
            col_v = st.columns([1,1,1])[1]
            with col_v:
                st.caption("Final Result:")
                try:
                    with open(st.session_state['final_video'], 'rb') as f:
                        vb = f.read()
                        st.video(vb)
                        st.download_button("⬇️ Download Reel", vb, "reel.mp4", "video/mp4", use_container_width=True)
                except:
                    st.warning("Video file expired. Please render again.")

# --- ROUTER ---
check_auto_login()

if st.session_state['page_view'] == 'login': login_view()
elif st.session_state['page_view'] == 'register': register_view()
elif st.session_state['page_view'] == 'profile':
    db = database.SessionLocal()
    u = db.query(models.UserProfile).filter(models.UserProfile.id == st.session_state['user_id']).first()
    db.close()
    if u: profile_settings_view(u)
    else: studio_view()
else:
    studio_view()