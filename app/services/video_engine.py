import os
import random
import requests
import PIL.Image
import textwrap
from moviepy.config import change_settings
from dotenv import load_dotenv
from proglog import ProgressBarLogger 

load_dotenv()

if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

magick_path = os.getenv("IMAGEMAGICK_BINARY")
if not magick_path and os.name == 'nt':
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

# --- CUSTOM LOGGER ---
class StreamlitLogger(ProgressBarLogger):
    def __init__(self, st_progress_bar, start_percent, end_percent):
        super().__init__()
        self.st_bar = st_progress_bar
        self.start_pct = start_percent
        self.end_pct = end_percent
        self.scale = end_percent - start_percent

    def callback(self, **changes):
        pass

    def bars_callback(self, bar, attr, value, old_value=None):
        if bar == 't':
            total = self.bars[bar]['total']
            if total > 0:
                percentage = value / total
                current_ui_val = self.start_pct + (percentage * self.scale)
                self.st_bar.progress(int(current_ui_val), text=f"🎬 Rendering: {int(percentage*100)}%")

class VideoEngine:
    def __init__(self, pexels_key):
        self.api_key = pexels_key
        self.assets_dir = "assets"
        self.temp_dir = "assets/temp"
        os.makedirs(self.temp_dir, exist_ok=True)
        
        self.font_serif = "assets/fonts/bold_font.ttf"
        self.font_sans = "assets/fonts/Poppins-Bold.ttf"

        # Styles adjusted for 720p resolution
        self.styles = [
            {"name": "Classic Serif", "font": self.font_serif, "color": 'white', "stroke_color": 'black', "stroke_width": 2, "fontsize": 50, "v_pos": 600},
            {"name": "Modern Yellow", "font": self.font_sans, "color": '#FFD700', "stroke_color": 'black', "stroke_width": 2, "fontsize": 48, "v_pos": 650},
            {"name": "Clean Cream", "font": self.font_sans, "color": '#FFFDD0', "stroke_color": '#333333', "stroke_width": 1, "fontsize": 52, "v_pos": 600},
            {"name": "Neon Blue", "font": self.font_sans, "color": '#00FFFF', "stroke_color": '#000000', "stroke_width": 2, "fontsize": 50, "v_pos": 600}
        ]

    def get_style_names(self):
        return [s['name'] for s in self.styles]

    def get_stock_video(self, search_term, progress_bar=None):
        print(f"👀 Searching: {search_term}")
        headers = {"Authorization": self.api_key}
        params = {"query": search_term, "orientation": "portrait", "size": "medium", "per_page": 10, "page": random.randint(1, 3)}
        
        try:
            if progress_bar: progress_bar.progress(5, text="🔍 Searching Pexels API...")
            
            response = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params)
            data = response.json()
            
            if not data.get('videos'):
                 params["query"] = "nature abstract"
                 params["page"] = 1
                 response = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params)
                 data = response.json()
            
            if not data.get('videos'): return None
            
            video_data = random.choice(data['videos'])
            best_video = next((v for v in video_data['video_files'] if v['height'] >= 720), video_data['video_files'][0])
            video_url = best_video['link']
            
            print(f"⬇️ Downloading...")
            video_path = os.path.join(self.temp_dir, "background.mp4")
            
            with requests.get(video_url, stream=True) as r:
                r.raise_for_status()
                total_length = int(r.headers.get('content-length', 0))
                dl = 0
                with open(video_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        dl += len(chunk)
                        f.write(chunk)
                        if progress_bar and total_length > 0:
                            percent = int(10 + (dl / total_length) * 30)
                            progress_bar.progress(percent, text=f"⬇️ Downloading: {int((dl/total_length)*100)}%")
                            
            return video_path
        except Exception as e:
            print(f"❌ Error downloading video: {e}")
            return None

    def create_video(self, video_path, quote_text, style_name=None, progress_bar=None):
        try:
            # 720p Config
            TARGET_W = 720
            TARGET_H = 1280
            
            # 👇 UPDATED DURATION HERE 👇
            target_duration = random.randint(7, 10) 
            
            if style_name:
                style = next((s for s in self.styles if s['name'] == style_name), random.choice(self.styles))
            else:
                style = random.choice(self.styles)
            
            clip = VideoFileClip(video_path)
            
            # 1. Resize early to save RAM
            if clip.h > 1280:
                clip = clip.resize(height=1280) 

            # 2. Safe Loop
            if clip.duration < target_duration:
                n_loops = int(target_duration / clip.duration) + 2
                clip = clip.loop(n=n_loops)
                clip = clip.set_duration(target_duration)
            else:
                clip = clip.subclip(0, target_duration)
            
            # 3. Crop to 720x1280
            if clip.w / clip.h > 9/16:
                 clip = clip.resize(height=TARGET_H)
                 clip = clip.crop(x1=clip.w/2 - (TARGET_W/2), y1=0, width=TARGET_W, height=TARGET_H)
            else:
                 clip = clip.resize(width=TARGET_W)
                 clip = clip.crop(y1=clip.h/2 - (TARGET_H/2), x1=0, width=TARGET_W, height=TARGET_H)

            # 4. Text
            wrapped_text = "\n".join(textwrap.wrap(quote_text, width=22))
            
            txt_clip = TextClip(
                wrapped_text, 
                fontsize=style["fontsize"], 
                color=style["color"], 
                font=style["font"], 
                stroke_color=style["stroke_color"], 
                stroke_width=style["stroke_width"], 
                size=(TARGET_W - 100, None), 
                method='caption'
            )
            
            txt_clip = txt_clip.set_pos(('center', style["v_pos"])).set_duration(target_duration)

            final_clip = CompositeVideoClip([clip, txt_clip])
            output_path = os.path.join(self.assets_dir, "final_reel.mp4")
            
            my_logger = None
            if progress_bar:
                my_logger = StreamlitLogger(progress_bar, 50, 100)
            
            final_clip.write_videofile(
                output_path, 
                fps=24, 
                codec='libx264', 
                audio_codec=None, 
                preset="medium", 
                logger=my_logger,
                threads=2 
            )
            
            clip.close()
            txt_clip.close()
            final_clip.close()
            
            return output_path
            
        except Exception as e:
            print(f"❌ Error Editing: {e}")
            return None