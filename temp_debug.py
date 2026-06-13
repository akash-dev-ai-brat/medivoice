# temp_debug.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

import os
from groq import Groq
from dotenv import load_dotenv
load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

response = client.chat.completions.create(
    model="llama3-70b-8192",
    messages=[{"role": "user", "content": "Say hello in one word"}],
    max_tokens=10
)

print("Response type:", type(response))
print("Full response:", response)
print("Content:", response.choices[0].message.content)