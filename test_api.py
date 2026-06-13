import requests
import json

BASE = "http://localhost:8000"

print("=" * 55)
print("     MediVoice — FastAPI Backend Test")
print("=" * 55)

# Test 1 — Health check
print("\nTest 1: Health check...")
r = requests.get(f"{BASE}/health")
print(f"  Status : {r.status_code}")
print(f"  Response: {r.json()}")

# Test 2 — Process transcript
print("\nTest 2: Process transcript...")
payload = {
    "transcript": """
        Patient is a 35 year old male with fever for 3 days,
        headache and mild cough. No known allergies.
        Temperature 101°F, BP 120/80 mmhg, pulse 88 bpm.
        Taking paracetamol 500mg twice daily.
    """,
    "language"     : "English",
    "patient_name" : "Test Patient"
}
r = requests.post(f"{BASE}/process-transcript", json=payload)
print(f"  Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"  Session ID  : {data['session_id']}")
    print(f"  Primary Dx  : {data['soap_note']['assessment']['primary_diagnosis']}")
    print(f"  ICD-10 codes: {[c['code'] for c in data['soap_note']['assessment']['icd10_codes']]}")
    session_id = data["session_id"]
else:
    print(f"  Error: {r.text}")
    session_id = 1

# Test 3 — Get all sessions
print("\nTest 3: List all sessions...")
r = requests.get(f"{BASE}/sessions")
data = r.json()
print(f"  Total sessions: {data['count']}")
for s in data["sessions"][:3]:
    print(f"    ID {s['id']} — {s['patient_name']} — {s['created_at']}")

# Test 4 — Get single session
print(f"\nTest 4: Get session {session_id}...")
r = requests.get(f"{BASE}/sessions/{session_id}")
if r.status_code == 200:
    data = r.json()
    print(f"  Patient   : {data['patient_name']}")
    print(f"  Language  : {data['language']}")
    print(f"  Diagnosis : {data['soap_note']['assessment']['primary_diagnosis']}")
else:
    print(f"  Error: {r.text}")

# Test 5 — Export PDF
print(f"\nTest 5: Export PDF for session {session_id}...")
r = requests.get(f"{BASE}/sessions/{session_id}/export-pdf")
if r.status_code == 200:
    with open(f"data/test_export_{session_id}.pdf", "wb") as f:
        f.write(r.content)
    print(f"  ✓ PDF saved to data/test_export_{session_id}.pdf")
else:
    print(f"  Error: {r.text}")

print("\n" + "=" * 55)
print("✓ All API tests complete! Ready for Phase 6 — Streamlit UI")
print("=" * 55)