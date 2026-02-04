import os
import random
import requests
import PIL.Image
import textwrap
from moviepy.config import change_settings
from dotenv import load_dotenv

load_dotenv()

# --- COMPATIBILITY FIX ---
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

# --- SMART CONFIGURATION FOR IMAGEMAGICK ---
magick_path = os.getenv("IMAGEMAGICK_BINARY")
if not magick_path and os.name == 'nt':
    # Fallback paths for Windows
    common_paths = [
        r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe",
        r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
    ]
    for p in common_paths:
        if os.path.exists(p):
            magick_path = p
            break

if magick_path and os.path.exists(magick_path):
    change_settings({"IMAGEMAGICK_BINARY": magick_path})

from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip

class VideoEngine:
    def __init__(self, pexels_key):
        self.api_key = pexels_key
        self.assets_dir = "assets"
        self.temp_dir = "assets/temp"
        os.makedirs(self.temp_dir, exist_ok=True)
        
        self.font_serif = "assets/fonts/bold_font.ttf"
        self.font_sans = "assets/fonts/Poppins-Bold.ttf"

        # --- STYLES ---
        self.styles = [
            {
                "name": "Classic Serif",
                "font": self.font_serif,
                "color": 'white',
                "stroke_color": 'black',
                "stroke_width": 3,
                "fontsize": 70,
                "v_pos": 850 
            },
            {
                "name": "Modern Yellow",
                "font": self.font_sans,
                "color": '#FFD700', 
                "stroke_color": 'black',
                "stroke_width": 2,
                "fontsize": 68,
                "v_pos": 900 
            },
            {
                "name": "Clean Cream",
                "font": self.font_sans,
                "color": '#FFFDD0',
                "stroke_color": '#333333',
                "stroke_width": 1,
                "fontsize": 72,
                "v_pos": 850 
            },
            {
                "name": "Neon Blue",
                "font": self.font_sans,
                "color": '#00FFFF',
                "stroke_color": '#000000',
                "stroke_width": 2,
                "fontsize": 70,
                "v_pos": 850
            }
        ]

    # Helper to get list of style names for the dashboard
    def get_style_names(self):
        return [s['name'] for s in self.styles]

    def get_stock_video(self, search_term):
        print(f"👀 Eyes: Searching Pexels for '{search_term}'...")
        headers = {"Authorization": self.api_key}
        
        # FEATURE: Randomize page to get fresh results each time
        params = {
            "query": search_term, 
            "orientation": "portrait", 
            "size": "medium", 
            "per_page": 10,  # Fetch more options
            "page": random.randint(1, 3) # Randomize results page
        }
        
        try:
            response = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params)
            data = response.json()
            
            # Fallback
            if 'videos' not in data or not data['videos']:
                 params["query"] = "nature abstract"
                 params["page"] = 1
                 response = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params)
                 data = response.json()
            
            if not data.get('videos'): return None
            
            # Pick one random video from the 10 results
            video_data = random.choice(data['videos'])
            
            # Get best quality available
            best_video = next((v for v in video_data['video_files'] if v['height'] >= 720), video_data['video_files'][0])
            video_url = best_video['link']
            
            print(f"⬇️ Downloading video ID: {video_data['id']}...")
            video_path = os.path.join(self.temp_dir, "background.mp4")
            with requests.get(video_url, stream=True) as r:
                r.raise_for_status()
                with open(video_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192): f.write(chunk)
            return video_path
        except Exception as e:
            print(f"❌ Error downloading video: {e}")
            return None

    # UPDATED: Added style_name argument AND Safe Loop Logic
    def create_video(self, video_path, quote_text, style_name=None):
        print(f"🎬 Hands: Editing video (Style: {style_name})...")
        try:
            target_duration = random.randint(6, 9) # Short & sweet
            
            # Select Style: If specific name passed, use it. Else random.
            if style_name:
                style = next((s for s in self.styles if s['name'] == style_name), random.choice(self.styles))
            else:
                style = random.choice(self.styles)
            
            # --- SAFE LOOP LOGIC START ---
            clip = VideoFileClip(video_path)
            
            # If the downloaded video is shorter than our target (e.g. 3s vs 9s)
            if clip.duration < target_duration:
                # Calculate how many times we need to repeat it to be safe
                # e.g. 9s / 3s = 3 loops. Add +2 just to be extremely safe.
                n_loops = int(target_duration / clip.duration) + 2
                clip = clip.loop(n=n_loops)
                # Now forcibly set the duration (cuts off the excess)
                clip = clip.set_duration(target_duration)
            else:
                # If video is long enough, just trim it
                clip = clip.subclip(0, target_duration)
            # --- SAFE LOOP LOGIC END ---
            
            # Resize and Crop to Reel format (9:16)
            if clip.w / clip.h > 9/16:
                 clip = clip.resize(height=1920)
                 clip = clip.crop(x1=clip.w/2 - 540, y1=0, width=1080, height=1920)
            else:
                 clip = clip.resize(width=1080)
                 clip = clip.crop(y1=clip.h/2 - 960, x1=0, width=1080, height=1920)

            wrapped_text = "\n".join(textwrap.wrap(quote_text, width=22))
            
            txt_clip = TextClip(
                wrapped_text, 
                fontsize=style["fontsize"], 
                color=style["color"], 
                font=style["font"], 
                stroke_color=style["stroke_color"], 
                stroke_width=style["stroke_width"], 
                size=(800, None), 
                method='caption'
            )
            
            txt_clip = txt_clip.set_pos(('center', style["v_pos"])).set_duration(target_duration)

            final_clip = CompositeVideoClip([clip, txt_clip])
            output_path = os.path.join(self.assets_dir, "final_reel.mp4")
            
            final_clip.write_videofile(output_path, fps=24, codec='libx264', audio_codec=None, preset="medium")
            
            return output_path
            
        except Exception as e:
            print(f"❌ Error Editing: {e}")
            return None