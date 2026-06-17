<div align="center">


# 🩺 MediVoice

### AI-Powered Ambient Clinical Scribe — Speak. Document. Done.

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-UI-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Whisper](https://img.shields.io/badge/OpenAI-Whisper-412991?style=flat&logo=openai&logoColor=white)](https://openai.com/research/whisper)
[![LLaMA](https://img.shields.io/badge/LLaMA_3.3_70B-Groq-F55036?style=flat)](https://groq.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen)](https://github.com/akash-dev-ai-brat/medivoice)

**MediVoice** converts doctor-patient consultation transcripts into structured, professional clinical notes in seconds — extracting symptoms, vitals, medications, and automatically mapping diagnoses to ICD-10 codes using a full NLP + LLM pipeline.

> 💡 **Impact:** Doctors spend up to 35% of their working hours on documentation. MediVoice gives that time back.

[Report Bug](https://github.com/akash-dev-ai-brat/medivoice/issues) · [Request Feature](https://github.com/akash-dev-ai-brat/medivoice/issues) · [View API Docs](#api-endpoints)

</div>

---

## 📌 Table of Contents
- [Problem Statement](#problem)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [System Architecture](#architecture)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [API Endpoints](#api-endpoints)
- [How It Works](#how-it-works)
- [Screenshots](#screenshots)
- [Limitations & Disclaimer](#limitations)
- [Future Improvements](#future-improvements)
- [Author](#author)

---

## 🏥 Problem Statement <a name="problem"></a>

Clinical documentation is one of the biggest sources of physician burnout worldwide. Doctors are required to manually transcribe consultation notes — often after hours — pulling focus away from actual patient care.

**MediVoice acts as an ambient AI scribe:** the consultation happens naturally, and a structured, ICD-10 coded clinical record is generated automatically — ready to review, edit, and export as a professional PDF.

---

## ✨ Features <a name="features"></a>

- 🎙️ **Speech-to-text transcription** — locally-run OpenAI Whisper; no audio data leaves your machine
- 🧬 **Clinical NLP pipeline** — medspaCy extracts symptoms, medications, vitals, allergies, and durations from free text
- 🏷️ **ICD-10 code mapping** — automatic diagnosis code assignment from a curated reference database
- 📋 **SOAP note generation** — LLaMA 3.3 70B (via Groq) produces structured Subjective / Objective / Assessment / Plan notes
- 📄 **PDF export** — one-click professional clinical note download
- 🌐 **Multilingual support** — English, Hindi, Bengali
- 🗂️ **Session history dashboard** — all consultations stored locally in SQLite with a searchable session log
- ⚡ **REST API backend** — FastAPI with full Swagger docs at `/docs`

---

## 🛠️ Tech Stack <a name="tech-stack"></a>

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Speech-to-Text | OpenAI Whisper (local) | Audio transcription — runs offline |
| Clinical NLP | medspaCy + custom extractors | Entity extraction from transcript |
| Note Generation | LLaMA 3.3 70B via Groq API | SOAP note synthesis |
| Backend | FastAPI + Uvicorn | REST API server |
| Frontend | Streamlit | Interactive UI dashboard |
| Database | SQLite | Local session persistence |
| PDF Export | fpdf2 | Clinical note PDF generation |
| Language | Python 3.10+ | — |

---

## 🏗️ System Architecture <a name="architecture"></a>

```
Audio / Text Input
       │
       ▼
┌─────────────────────────────────────┐
│          FastAPI Backend            │
│                                     │
│  ┌──────────┐   ┌────────────────┐  │
│  │ Whisper  │   │  medspaCy NLP  │  │
│  │ (local)  │──▶│  Entity Extractor│ │
│  └──────────┘   └───────┬────────┘  │
│                         │           │
│              ┌──────────▼─────────┐ │
│              │  ICD-10 Mapper     │ │
│              └──────────┬─────────┘ │
│                         │           │
│              ┌──────────▼─────────┐ │
│              │  LLaMA 3.3 70B     │ │
│              │  (Groq API)        │ │
│              │  SOAP Note Gen     │ │
│              └──────────┬─────────┘ │
│                         │           │
│         ┌───────────────┴──────┐    │
│         │  SQLite Session DB   │    │
│         └───────────────┬──────┘    │
└─────────────────────────┼───────────┘
                          │
                          ▼
              ┌───────────────────┐
              │  Streamlit UI     │
              │  + PDF Export     │
              └───────────────────┘
```

---

## 📁 Project Structure <a name="project-structure"></a>

```
medivoice/
├── backend/
│   ├── main.py              # FastAPI server — routes & app entry point
│   ├── transcriber.py       # Whisper speech-to-text pipeline
│   ├── nlp_extractor.py     # medspaCy clinical entity extraction
│   ├── note_generator.py    # SOAP note generation via LLaMA / Groq
│   ├── pdf_exporter.py      # Clinical PDF generation (fpdf2)
│   ├── icd10_mapper.py      # ICD-10 diagnosis code lookup
│   └── db.py                # SQLite session persistence layer
├── frontend/
│   └── app.py               # Streamlit UI — dashboard & controls
├── data/
│   └── icd10_codes.json     # Curated ICD-10 reference database
├── assets/                  # Screenshots for README
├── .env.example             # Environment variable template
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Start <a name="quick-start"></a>

**Prerequisites:** Python 3.10+, a free [Groq API key](https://console.groq.com)

**1. Clone the repository**
```bash
git clone https://github.com/akash-dev-ai-brat/medivoice.git
cd medivoice
```

**2. Create and activate a virtual environment**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

**4. Configure environment variables**
```bash
cp .env.example .env
```
Open `.env` and add your key:
```env
GROQ_API_KEY=your_groq_api_key_here
```
Get a free key at [console.groq.com](https://console.groq.com) — no credit card required.

**5. Start the backend**
```bash
cd backend
python main.py
```
API runs at `http://localhost:8000` · Swagger docs at `http://localhost:8000/docs`

**6. Start the frontend** (new terminal)
```bash
streamlit run frontend/app.py
```
App available at `http://localhost:8501`

---

## 🔌 API Endpoints <a name="api-endpoints"></a>

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/process-transcript` | Generate SOAP note from a text transcript |
| `POST` | `/process-audio` | Generate SOAP note from an uploaded audio file |
| `GET` | `/sessions` | List all saved consultation sessions |
| `GET` | `/sessions/{id}` | Retrieve a specific session's full data |
| `GET` | `/sessions/{id}/pdf` | Download the SOAP note as a formatted PDF |

Full interactive API documentation available at `http://localhost:8000/docs` (Swagger UI).

---

## ⚙️ How It Works <a name="how-it-works"></a>

```
Step 1 — Input
  Doctor provides consultation transcript via:
  • Typed / pasted text
  • Audio file → Whisper transcribes locally

Step 2 — Clinical NLP (medspaCy)
  Extracts structured entities:
  • Symptoms        → "chest pain", "shortness of breath"
  • Medications     → "Metformin 500mg"
  • Vitals          → "BP 140/90", "HR 88 bpm"
  • Durations       → "for the past 3 days"
  • Allergies       → "penicillin allergy"

Step 3 — ICD-10 Mapping
  Extracted diagnoses are matched to standardized codes:
  • "hypertension" → I10
  • "type 2 diabetes" → E11

Step 4 — SOAP Note Generation (LLaMA 3.3 70B via Groq)
  Transcript + entities → structured clinical note:
  • Subjective   (patient's reported symptoms)
  • Objective    (vitals, observations)
  • Assessment   (diagnosis + ICD-10 codes)
  • Plan         (medications, follow-up, referrals)

Step 5 — Output
  • Note displayed in Streamlit dashboard
  • Session saved to SQLite
  • One-click PDF export
```

---

## 📸 Screenshots <a name="screenshots"></a>

<p align="center">
  <img src="assets/Screenshot 2026-06-13 155406.png" alt="MediVoice Dashboard" width="800"/>
  <br/><em>Main Dashboard</em>
</p>

<p align="center">
  <img src="assets/Screenshot 2026-06-13 155922.png" alt="Transcript Input" width="800"/>
  <br/><em>Transcript Input Interface</em>
</p>

<p align="center">
  <img src="assets/Screenshot 2026-06-13 160021.png" alt="Clinical NLP Extraction" width="800"/>
  <br/><em>Clinical NLP Entity Extraction</em>
</p>

<p align="center">
  <img src="assets/Screenshot 2026-06-13 160059.png" alt="SOAP Note Output" width="800"/>
  <br/><em>Generated SOAP Note with ICD-10 Codes</em>
</p>

<p align="center">
  <img src="assets/Screenshot 2026-06-13 160155.png" alt="PDF Export" width="800"/>
  <br/><em>PDF Export & Session History</em>
</p>

---

## ⚠️ Limitations & Disclaimer <a name="limitations"></a>

> **This is a research prototype and is NOT intended for clinical use without further security, compliance, and regulatory review.**

- Patient data is stored locally in SQLite — suitable for demos and development only
- ICD-10 mapping covers a curated subset of common conditions; not exhaustive
- SOAP note quality depends on Groq API availability and transcript clarity
- Not validated for HIPAA compliance in its current form

---

## 🔮 Future Improvements <a name="future-improvements"></a>

- [ ] Real-time live audio streaming (instead of file upload)
- [ ] Offline LLM support (local LLaMA via Ollama)
- [ ] FHIR-compliant data export for EHR integration
- [ ] Expand ICD-10 coverage to full WHO catalogue
- [ ] Doctor review + edit workflow before PDF finalization
- [ ] Role-based access control and audit logging

---

## 👤 Author <a name="author"></a>

<div align="center">
  Made with ❤️ by <a href="https://github.com/akash-dev-ai-brat">Akash Nath</a><br>
  B.Tech — Artificial Intelligence & Data Science<br><br>
  <a href="https://www.linkedin.com/in/akash-nath-5aa816293/">
    <img src="https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=flat&logo=linkedin&logoColor=white"/>
  </a>
  &nbsp;
  <a href="https://github.com/akash-dev-ai-brat">
    <img src="https://img.shields.io/badge/GitHub-Follow-181717?style=flat&logo=github&logoColor=white"/>
  </a>
</div>
