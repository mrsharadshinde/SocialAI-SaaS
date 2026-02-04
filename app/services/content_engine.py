import google.generativeai as genai
from groq import Groq
import json
import random
import time

class ContentEngine:
    def __init__(self, gemini_key=None, groq_key=None, provider="Groq"):
        self.gemini_key = gemini_key
        self.groq_key = groq_key
        self.provider = provider

    def generate_idea(self, persona, tone, language="English"):
        print(f"🧠 Brain: Generating concept using {self.provider}...")
        
        # 1. GENERATE DYNAMIC TOPIC
        # We use a simple randomized list for speed/reliability, or you can ask AI to generate it.
        topics = [
            "The dark side of success", "Why nice guys finish last", "The hypocrisy of society", 
            "Money vs Happiness", "Modern dating struggles", "The lie of hard work", 
            "Loneliness in big cities", "Social media fakeness", "Childhood nostalgia", 
            "Betrayal by friends", "The rat race", "Finding God in nature", 
            "Why we fear death", "The beauty of pain", "Lost dreams"
        ]
        selected_topic = random.choice(topics)
        
        selected_lang = random.choice(["English", "Hindi", "Marathi"])
        print(f"🌍 Language: {selected_lang} | Topic: {selected_topic}")

        # 2. THE PROMPT
        prompt = f""" 
        You are an AI agent with this persona: "{persona}".
        Your tone is: "{tone}"
        
        TASK:
        Generate 1 Instagram Reel idea about: "{selected_topic}".
        The 'Quote' MUST be written in {selected_lang}.

        GUIDELINES:
        - If {selected_lang} is Hindi/Marathi, use Devanagari script.
        - Keep the quote short (max 10-15 words).
        - The Caption should be in English but can use Hinglish words.

        STRICTLY OUTPUT JSON format like this:
        {{
            "quote": "The text to display on video",
            "visual_search_term": "Pexels search query (ALWAYS ENGLISH)",
            "caption": "Instagram caption",
            "hashtags": "List of 10 hashtags"
        }}
        """

        # 3. ROUTING LOGIC
        if self.provider == "Groq":
            return self._generate_with_groq(prompt, selected_lang)
        else:
            return self._generate_with_gemini(prompt, selected_lang)

    # --- ENGINE 1: GROQ (Fastest / Recommended) ---
    def _generate_with_groq(self, prompt, lang):
        if not self.groq_key:
            return None, "Missing Groq API Key. Update your profile."
        
        try:
            client = Groq(api_key=self.groq_key)
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a JSON-only generator."},
                    {"role": "user", "content": prompt}
                ],
                temperature=1,
                max_tokens=1024,
                response_format={"type": "json_object"}
            )
            response_text = completion.choices[0].message.content
            data = json.loads(response_text)
            data['language'] = lang
            return data, None
        except Exception as e:
            return None, f"Groq Error: {str(e)}"

    # --- ENGINE 2: GEMINI (Fallback) ---
    def _generate_with_gemini(self, prompt, lang):
        if not self.gemini_key:
            return None, "Missing Gemini API Key. Update your profile."
            
        genai.configure(api_key=self.gemini_key)
        
        # Updated Model List (Using stable version names to avoid 404s)
        models_queue = [
            "gemini-2.0-flash",
            "gemini-1.5-flash-latest", # Tries the latest alias
            "gemini-1.5-flash",        # Standard
            "gemini-pro"
        ]

        last_error = ""

        for model_name in models_queue:
            try:
                print(f"🔄 Gemini: Attempting {model_name}...")
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(
                    prompt, 
                    generation_config={"response_mime_type": "application/json"}
                )
                
                clean_text = response.text.replace('```json', '').replace('```', '').strip()
                data = json.loads(clean_text)
                data['language'] = lang
                print(f"✅ Success with {model_name}!")
                return data, None

            except Exception as e:
                print(f"⚠️ {model_name} Failed: {e}")
                last_error = str(e)
                time.sleep(1)
                continue
        
        return None, f"All Gemini models failed. Try switching to Groq in dashboard. Error: {last_error}"