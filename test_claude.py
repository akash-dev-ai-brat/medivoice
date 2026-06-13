import anthropic

client = anthropic.Anthropic(api_key="YOUR_API_KEY_HERE")

message = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=500,
    messages=[
        {
            "role": "user",
            "content": """You are a clinical assistant. Convert this transcript into a SOAP note:

Transcript: Patient is a 35-year-old male complaining of fever for 3 days, 
headache, and mild cough. No known allergies. Currently taking paracetamol 
500mg twice daily. Temperature is 101°F.

Generate a brief SOAP note with ICD-10 code."""
        }
    ]
)

print("✓ Claude API working")
print("\nSample SOAP note:")
print(message.content[0].text)