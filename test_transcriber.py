import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))
import numpy as np
import soundfile as sf
from transcriber import transcribe_file, load_model

# ── Test 1: Transcribe silence (sanity check) ─────────────────────────────────
print("=" * 50)
print("Test 1: Loading Whisper model")
model = load_model()
print("✓ Model loaded\n")

# ── Test 2: Transcribe a pre-made audio file ──────────────────────────────────
print("=" * 50)
print("Test 2: Transcribing sample audio file")

# Create a test WAV with a simple tone (simulates audio)
sample_rate = 16000
duration    = 3
t           = np.linspace(0, duration, int(sample_rate * duration))
audio       = (0.3 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)

test_path = "test_sample.wav"
sf.write(test_path, audio, sample_rate)

result = transcribe_file(test_path, language="English")
print(f"✓ Transcription result: '{result['transcript']}'")
print(f"  Duration : {result['duration']}s")
print(f"  Language : {result['language']}")
print(f"  Timestamp: {result['timestamp']}")

os.remove(test_path)
print()

# ── Test 3: Transcribe a real voice sample ────────────────────────────────────
print("=" * 50)
print("Test 3: Transcribe a real doctor-patient sample")
print("Creating sample audio from text using gTTS...")

try:
    from gtts import gTTS
    import subprocess

    # Install gTTS if not present
    sample_text = (
        "Patient is a 35 year old male presenting with fever for 3 days, "
        "headache, and mild cough. No known allergies. "
        "Currently taking paracetamol 500 milligrams twice daily."
    )

    tts = gTTS(text=sample_text, lang="en", slow=False)
    tts.save("sample_consultation.mp3")

    # Convert mp3 to wav using ffmpeg
    os.system("ffmpeg -i sample_consultation.mp3 sample_consultation.wav -y -loglevel quiet")

    if os.path.exists("sample_consultation.wav"):
        result = transcribe_file("sample_consultation.wav", language="English")
        print(f"\nOriginal text :\n  {sample_text}")
        print(f"\nTranscribed   :\n  {result['transcript']}")
        print(f"\nDuration: {result['duration']}s")

        os.remove("sample_consultation.mp3")
        os.remove("sample_consultation.wav")
    else:
        print("⚠ ffmpeg not found — skipping mp3 test")

except ImportError:
    print("gTTS not installed — installing now...")
    os.system("pip install gTTS")
    print("Re-run this test after install")

print()
print("=" * 50)
print("All transcriber tests complete!")
print("Ready for Phase 3 — Clinical NLP")
