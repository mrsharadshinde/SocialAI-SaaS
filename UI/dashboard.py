import streamlit as st
import sys
import os
import random
from dotenv import load_dotenv

# Load env variables for defaults
load_dotenv()

# --- PATH SETUP ---
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from app import database, models, crud

# Initialize DB
models.Base.metadata.create_all(bind=database.engine)

st.set_page_config(page_title="SocialAI SaaS", page_icon="🤖", layout="wide")

st.title("🤖 SocialAI Factory")
st.subheader("Manage Your AI Influencers")

# Sidebar
option = st.sidebar.selectbox("Menu", ["Create Profile", "Manage Profiles", "Generation Studio"])

# --- OPTION 1: CREATE PROFILE ---
if option == "Create Profile":
    st.header("Create New AI Agent")

    with st.form("profile_form"):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 👤 Identity")
            username = st.text_input("Bot Name", value="ThinkingStrom")
            tone = st.text_input("Content Tone", value="Sarcastic, Logical, Maverick")
            visual = st.text_input("Visual Style", value="Dark, Rain, Nature, Aesthetic, India")
        
        with col2:
            st.markdown("### 🧠 The Brain")
            # Default provider preference
            provider = st.radio("Default Provider", ["Groq", "Gemini"], horizontal=True)
            
            # API KEYS
            default_gemini = os.getenv("GEMINI_API_KEY", "")
            default_pexels = os.getenv("PEXELS_API_KEY", "")
            default_groq = os.getenv("GROQ_API_KEY", "")
            
            groq_key = st.text_input("Groq API Key", value=default_groq, type="password")
            gemini_key = st.text_input("Gemini API Key", value=default_gemini, type="password")
            pexels_key = st.text_input("Pexels API Key", value=default_pexels, type="password")

        st.markdown("### 📝 Persona")
        persona = st.text_area("Persona Prompt", height=100, value="You are ThinkingStrom, a 23 yo Indian Maverick. You are an Atheist who believes Nature is god. You criticize societal double standards and religious politics logically. You speak to the Indian youth.")
        
        submitted = st.form_submit_button("Save Profile")
        
        if submitted:
            db = database.SessionLocal()
            existing = crud.get_user_by_username(db, username)
            if existing:
                st.error("User already exists!")
            else:
                crud.create_user(db, username, persona, tone, visual, gemini_key, groq_key, pexels_key, provider)
                st.success(f"Agent '{username}' created with {provider}!")
            db.close()

# --- OPTION 2: MANAGE PROFILES (EDIT) ---
elif option == "Manage Profiles":
    st.header("Edit Active Agents")
    db = database.SessionLocal()
    users = db.query(models.UserProfile).all()
    
    if not users:
        st.info("No agents found.")
    else:
        user_map = {u.username: u for u in users}
        selected_user = st.selectbox("Select Agent to Edit", list(user_map.keys()))
        
        if selected_user:
            user = user_map[selected_user]
            
            with st.form("edit_form"):
                st.markdown(f"**Editing: {user.username}**")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    new_provider = st.radio("Default Provider", ["Groq", "Gemini"], index=0 if user.ai_provider == "Groq" else 1, horizontal=True)
                    new_tone = st.text_input("Content Tone", value=user.content_tone)
                    new_visual = st.text_input("Visual Style", value=user.visual_style)
                
                with col_b:
                    new_groq = st.text_input("Groq Key", value=user.groq_api_key, type="password")
                    new_gemini = st.text_input("Gemini Key", value=user.gemini_api_key, type="password")
                    new_pexels = st.text_input("Pexels Key", value=user.pexels_api_key, type="password")

                new_persona = st.text_area("Persona Prompt", value=user.persona_prompt)

                update_submitted = st.form_submit_button("Update Profile")
                
                if update_submitted:
                    crud.update_user(
                        db, 
                        user.id, 
                        new_persona, 
                        new_tone, 
                        new_visual, 
                        new_gemini, 
                        new_groq, 
                        new_pexels,
                        new_provider
                    )
                    st.success("Profile Updated! Refreshing...")
    db.close()

# --- OPTION 3: GENERATION STUDIO (REDESIGNED) ---
elif option == "Generation Studio":
    st.header("⚙️ Generation Studio")
    
    db = database.SessionLocal()
    users = db.query(models.UserProfile).all()
    user_names = [u.username for u in users]
    
    if not user_names:
        st.warning("No agents found. Go create one!")
    else:
        # 1. Select User
        selected_username = st.selectbox("Select Agent", user_names)
        user = crud.get_user_by_username(db, selected_username)
        
        st.markdown("---")

        # 2. INSTANT BRAIN SWITCH
        col_switch, col_btn = st.columns([1, 2])
        
        with col_switch:
            current_idx = 0 if user.ai_provider == "Groq" else 1
            active_provider = st.radio(
                "🧠 Active Brain", 
                ["Groq", "Gemini"], 
                index=current_idx, 
                horizontal=True
            )

        with col_btn:
            st.write("") # Spacer
            st.write("") # Spacer
            # 3. GENERATE BUTTON
            generate_clicked = st.button("🧠 1. Generate Idea", use_container_width=True)

        if generate_clicked:
             with st.spinner(f"Thinking with {active_provider}..."):
                from app.services.content_engine import ContentEngine
                
                engine = ContentEngine(
                    gemini_key=user.gemini_api_key, 
                    groq_key=user.groq_api_key, 
                    provider=active_provider
                )
                
                idea, error = engine.generate_idea(user.persona_prompt, user.content_tone)
                
                if idea:
                    st.session_state['current_idea'] = idea
                    # ⚠️ RESET VIDEO STATE WHEN NEW IDEA ARRIVES
                    # This ensures we don't use an old video for a new quote
                    if 'bg_video_path' in st.session_state: del st.session_state['bg_video_path']
                    if 'current_style' in st.session_state: del st.session_state['current_style']
                    if 'final_video' in st.session_state: del st.session_state['final_video']
                    
                    st.success(f"Idea Generated using {active_provider}!")
                else:
                    st.error(f"Error: {error}")

        # 4. VIDEO STUDIO
        if 'current_idea' in st.session_state:
            idea = st.session_state['current_idea']
            
            st.markdown("---")
            col_a, col_b = st.columns([2, 1])
            with col_a:
                st.info(f"**Quote:** {idea['quote']}")
                st.caption(f"Language: {idea.get('language')}")
            with col_b:
                 st.info(f"**Visual:** {idea['visual_search_term']}")

            # --- NEW CONTROL PANEL ---
            st.subheader("🎬 Video Controls")
            
            col_render, col_swap, col_style = st.columns(3)
            
            # The Three Buttons
            render_btn = col_render.button("▶️ Render Video", use_container_width=True)
            swap_btn = col_swap.button("🔄 Swap Background", use_container_width=True)
            style_btn = col_style.button("🎨 Change Style", use_container_width=True)

            # Logic Handler
            if render_btn or swap_btn or style_btn:
                if not user.pexels_api_key:
                    st.error("Missing Pexels API Key!")
                else:
                    from app.services.video_engine import VideoEngine
                    video_eng = VideoEngine(user.pexels_api_key)
                    
                    # A. BACKGROUND LOGIC
                    # If 'Swap' clicked OR we don't have a background yet -> Download
                    if swap_btn or 'bg_video_path' not in st.session_state:
                        with st.spinner("🔍 Finding new background..."):
                            bg_path = video_eng.get_stock_video(idea['visual_search_term'])
                            if bg_path:
                                st.session_state['bg_video_path'] = bg_path
                            else:
                                st.error("No video found.")

                    # B. STYLE LOGIC
                    # Get list of styles from engine
                    available_styles = video_eng.get_style_names()
                    
                    # If 'Change Style' clicked -> Cycle to next style
                    if style_btn and 'current_style' in st.session_state:
                        curr_idx = available_styles.index(st.session_state['current_style'])
                        # Move to next index, loop back to 0 if at end
                        next_idx = (curr_idx + 1) % len(available_styles)
                        st.session_state['current_style'] = available_styles[next_idx]
                    
                    # If no style set -> Pick random
                    elif 'current_style' not in st.session_state:
                        st.session_state['current_style'] = random.choice(available_styles)

                    # C. RENDER LOGIC
                    # Use the stored video path and stored style
                    if 'bg_video_path' in st.session_state:
                        style_to_use = st.session_state['current_style']
                        
                        with st.spinner(f"Rendering ({style_to_use})..."):
                            final_path = video_eng.create_video(
                                st.session_state['bg_video_path'], 
                                idea['quote'], 
                                style_name=style_to_use
                            )
                            st.session_state['final_video'] = final_path

            # SHOW FINAL RESULT
            if 'final_video' in st.session_state:
                st.success(f"✅ Rendered Style: {st.session_state.get('current_style', 'Default')}")
                st.video(st.session_state['final_video'])

    db.close()