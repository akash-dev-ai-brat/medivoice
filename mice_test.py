# mic_test.py
import sys
sys.path.append("backend")
from transcriber import record_and_transcribe

print("Mic test — speak for 10 seconds after prompt")
result = record_and_transcribe(duration=10, language="English")
print(f"\nYou said: {result['transcript']}")