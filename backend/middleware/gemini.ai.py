import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found. Please set it in your environment or a .env file.")

genai.configure(api_key=api_key)

model_pro = genai.GenerativeModel('gemini-2.5-pro')
model_flash = genai.GenerativeModel('gemini-2.5-flash')
