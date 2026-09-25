import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("Error: GEMINI_API_KEY is not set. Please set it in your .env file.")
    exit(1)

client = genai.Client(api_key=api_key)
model_name = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

print(f"Testing Gemini connection with model: {model_name}...")
try:
    response = client.models.generate_content(
        model=model_name,
        contents="Say hello in one simple sentence."
    )
    print("\nResponse from Gemini:")
    print(response.text)
except Exception as e:
    print(f"\nError calling Gemini API: {e}")
