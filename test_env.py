from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=".env")

api_key = os.getenv("GROQ_API_KEY")

print("API KEY:", api_key)
