import whisper
import sounddevice as sd
import soundfile as sf
import numpy as np
import tempfile
import os
import queue
import threading
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
SAMPLE_RATE    = 16000   # Whisper expects 16kHz
CHANNELS       = 1       # Mono
CHUNK_DURATION = 30      # seconds per chunk
MODEL_SIZE     = "base"  # base = fast, medium = accurate

# Language codes for Whisper
LANGUAGE_MAP = {
    "English" : "en",
    "Hindi"   : "hi",
    "Bengali" : "bn"
}


# ── Model loader ──────────────────────────────────────────────────────────────
_model = None

def load_model():
    """Load Whisper model once and cache it"""
    global _model
    if _model is None:
        print(f"Loading Whisper {MODEL_SIZE} model...")
        _model = whisper.load_model(MODEL_SIZE)
        print("✓ Whisper model loaded")
    return _model


# ── Transcribe from file ──────────────────────────────────────────────────────
def transcribe_file(audio_path: str, language: str = "English") -> dict:
    """
    Transcribe any audio file using Whisper.
    Returns dict with transcript, language, duration.
    """
    model = load_model()
    lang_code = LANGUAGE_MAP.get(language, "en")

    print(f"Transcribing {audio_path} in {language}...")

    result = model.transcribe(
        audio_path,
        language=lang_code,
        task="transcribe",
        verbose=False,
        fp16=False          # fp16=False for CPU (most laptops)
    )

    transcript = result["text"].strip()
    duration   = result.get("duration", 0)

    print(f"✓ Transcribed {duration:.1f}s of audio")
    print(f"  Transcript: {transcript[:100]}...")

    return {
        "transcript" : transcript,
        "language"   : language,
        "duration"   : round(duration, 2),
        "segments"   : result.get("segments", []),
        "timestamp"  : datetime.now().isoformat()
    }


# ── Record from microphone ────────────────────────────────────────────────────
def record_audio(duration: int = CHUNK_DURATION,
                 save_path: str = None) -> str:
    """
    Record audio from microphone for `duration` seconds.
    Saves to a temp WAV file and returns the path.
    """
    print(f"🎙️ Recording for {duration} seconds...")
    print("   Speak now...")

    audio_data = sd.rec(
        int(duration * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype=np.float32
    )
    sd.wait()  # wait until recording is done
    print("✓ Recording complete")

    # Save to file
    if save_path is None:
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        save_path = tmp.name

    sf.write(save_path, audio_data, SAMPLE_RATE)
    print(f"✓ Audio saved to {save_path}")
    return save_path


# ── Record + transcribe in one call ──────────────────────────────────────────
def record_and_transcribe(duration: int = CHUNK_DURATION,
                          language: str = "English") -> dict:
    """
    Record from mic and immediately transcribe.
    Returns transcript dict.
    """
    audio_path = record_audio(duration=duration)
    result     = transcribe_file(audio_path, language=language)

    # Clean up temp file
    try:
        os.remove(audio_path)
    except:
        pass

    return result


# ── Streaming transcriber (real-time chunks) ──────────────────────────────────
class StreamingTranscriber:
    """
    Records audio in chunks and transcribes each chunk.
    Useful for long consultations — transcribes every 30 seconds.
    """

    def __init__(self, chunk_duration: int = 30, language: str = "English"):
        self.chunk_duration = chunk_duration
        self.language       = language
        self.is_running     = False
        self.transcript     = ""
        self.chunks         = []
        self._thread        = None

    def start(self):
        """Start background recording and transcription"""
        self.is_running = True
        self.transcript = ""
        self.chunks     = []
        self._thread    = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        print("✓ Streaming transcriber started")

    def stop(self) -> str:
        """Stop recording and return full transcript"""
        self.is_running = False
        if self._thread:
            self._thread.join(timeout=5)
        print("✓ Streaming transcriber stopped")
        return self.transcript.strip()

    def _run(self):
        """Background thread: record chunk → transcribe → append"""
        while self.is_running:
            path   = record_audio(duration=self.chunk_duration)
            result = transcribe_file(path, self.language)
            chunk_text = result["transcript"]

            if chunk_text:
                self.transcript += " " + chunk_text
                self.chunks.append({
                    "text"      : chunk_text,
                    "timestamp" : result["timestamp"]
                })
                print(f"  [Chunk] {chunk_text[:80]}...")

            try:
                os.remove(path)
            except:
                pass

    def get_current_transcript(self) -> str:
        return self.transcript.strip()


# ── Transcribe from bytes (for FastAPI upload) ────────────────────────────────
def transcribe_bytes(audio_bytes: bytes, language: str = "English") -> dict:
    """
    Transcribe audio from raw bytes (used in FastAPI endpoint).
    Saves bytes to temp file then transcribes.
    """
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp.write(audio_bytes)
    tmp.close()

    result = transcribe_file(tmp.name, language)

    try:
        os.remove(tmp.name)
    except:
        pass

    return result