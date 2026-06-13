import sys

checks = []

try:
    import whisper
    checks.append(("Whisper", True, ""))
except Exception as e:
    checks.append(("Whisper", False, str(e)))

try:
    import fastapi
    checks.append(("FastAPI", True, ""))
except Exception as e:
    checks.append(("FastAPI", False, str(e)))

try:
    import anthropic
    checks.append(("Anthropic SDK", True, ""))
except Exception as e:
    checks.append(("Anthropic SDK", False, str(e)))

try:
    import streamlit
    checks.append(("Streamlit", True, ""))
except Exception as e:
    checks.append(("Streamlit", False, str(e)))

try:
    import medspacy
    checks.append(("medspaCy", True, ""))
except Exception as e:
    checks.append(("medspaCy", False, str(e)))

try:
    import fpdf
    checks.append(("fpdf2", True, ""))
except Exception as e:
    checks.append(("fpdf2", False, str(e)))

try:
    import twilio
    checks.append(("Twilio", True, ""))
except Exception as e:
    checks.append(("Twilio", False, str(e)))

try:
    import pyaudio
    checks.append(("PyAudio", True, ""))
except Exception as e:
    checks.append(("PyAudio", False, str(e)))

try:
    import soundfile
    checks.append(("SoundFile", True, ""))
except Exception as e:
    checks.append(("SoundFile", False, str(e)))

try:
    import dotenv
    checks.append(("python-dotenv", True, ""))
except Exception as e:
    checks.append(("python-dotenv", False, str(e)))

import os
icd_exists = os.path.exists("data/icd10_codes.json")
checks.append(("ICD-10 JSON", icd_exists, "" if icd_exists else "Create data/icd10_codes.json"))

print("\n====== MediVoice Setup Check ======")
all_good = True
for name, status, err in checks:
    icon = "✓" if status else "✗"
    msg = f"  {icon} {name}"
    if not status:
        msg += f"  ← {err[:60]}" if err else "  ← MISSING"
        all_good = False
    print(msg)

print()
if all_good:
    print("All systems go! Ready for Phase 2.")
else:
    print("Fix the ✗ items above then re-run this script.")