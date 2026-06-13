import streamlit as st
import requests
import json
import os
import sounddevice as sd
import soundfile as sf
import numpy as np
import tempfile
from datetime import datetime

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MediVoice",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── API base URL ──────────────────────────────────────────────────────────────
API_URL = "http://localhost:8000"

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1a73e8, #0d47a1);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: #f8f9fa;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    .soap-section {
        background: #ffffff;
        border-left: 4px solid #1a73e8;
        padding: 1rem 1.5rem;
        border-radius: 0 8px 8px 0;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .icd-badge {
        display: inline-block;
        background: #e3f2fd;
        color: #1565c0;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 13px;
        margin: 3px;
        font-weight: 500;
    }
    .symptom-badge {
        display: inline-block;
        background: #fce4ec;
        color: #c62828;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 13px;
        margin: 3px;
    }
    .success-box {
        background: #e8f5e9;
        border: 1px solid #81c784;
        border-radius: 8px;
        padding: 1rem;
        color: #2e7d32;
    }
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)


# ── Helper: check API ─────────────────────────────────────────────────────────
def check_api():
    try:
        r = requests.get(f"{API_URL}/health", timeout=3)
        return r.status_code == 200
    except:
        return False


# ── Helper: call process-transcript API ──────────────────────────────────────
def process_transcript(transcript, language, patient_name):
    try:
        r = requests.post(
            f"{API_URL}/process-transcript",
            json={
                "transcript"  : transcript,
                "language"    : language,
                "patient_name": patient_name
            },
            timeout=60
        )
        if r.status_code == 200:
            return r.json(), None
        return None, r.json().get("detail", "Unknown error")
    except Exception as e:
        return None, str(e)


# ── Helper: get all sessions ──────────────────────────────────────────────────
def get_sessions():
    try:
        r = requests.get(f"{API_URL}/sessions", timeout=5)
        if r.status_code == 200:
            return r.json().get("sessions", [])
    except:
        pass
    return []


# ── Helper: record audio ──────────────────────────────────────────────────────
def record_audio_clip(duration=30, sample_rate=16000):
    audio = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype=np.float32
    )
    sd.wait()
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    sf.write(tmp.name, audio, sample_rate)
    return tmp.name


# ── Helper: render SOAP note ──────────────────────────────────────────────────
def render_soap_note(soap_note, entities):
    s = soap_note.get("subjective", {})
    o = soap_note.get("objective",  {})
    a = soap_note.get("assessment", {})
    p = soap_note.get("plan",       {})
    m = soap_note.get("metadata",   {})

    # Metric summary row
    col1, col2, col3, col4 = st.columns(4)
    symptoms_count = len(entities.get("symptoms", []))
    icd_count      = len(a.get("icd10_codes", []))
    meds_count     = len(p.get("medications", []))
    severity       = a.get("severity", "—")

    col1.metric("🤒 Symptoms",     symptoms_count)
    col2.metric("🏷️ ICD-10 Codes", icd_count)
    col3.metric("💊 Medications",  meds_count)
    col4.metric("⚠️ Severity",     severity)

    st.markdown("---")

    # S — Subjective
    st.markdown("### 📋 S — Subjective")
    with st.container():
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Chief Complaint**")
            st.info(s.get("chief_complaint", "—"))
            st.markdown("**Past Medical History**")
            st.write(s.get("past_medical_history", "—"))
        with c2:
            st.markdown("**History of Present Illness**")
            st.write(s.get("history_of_present_illness", "—"))
            st.markdown("**Allergies**")
            allergy = s.get("allergies", "—")
            if "NKDA" in str(allergy) or "no known" in str(allergy).lower():
                st.success(f"✓ {allergy}")
            else:
                st.warning(f"⚠️ {allergy}")

        meds = s.get("medications", [])
        if meds:
            st.markdown("**Current Medications**")
            med_cols = st.columns(min(len(meds), 3))
            for i, med in enumerate(meds):
                med_cols[i % 3].markdown(f"💊 `{med}`")

    st.markdown("---")

    # O — Objective
    st.markdown("### 🔬 O — Objective")
    vitals = o.get("vitals", {})
    v1, v2, v3, v4, v5 = st.columns(5)
    v1.metric("🌡️ Temp",   vitals.get("temperature",    "—"))
    v2.metric("❤️ BP",     vitals.get("blood_pressure", "—"))
    v3.metric("💓 Pulse",  vitals.get("pulse",          "—"))
    v4.metric("🫁 SpO2",   vitals.get("spo2",           "—"))
    v5.metric("⚖️ Weight", vitals.get("weight",         "—"))

    if o.get("physical_examination") and o["physical_examination"] != "Not mentioned":
        st.markdown(f"**Examination:** {o['physical_examination']}")

    st.markdown("---")

    # A — Assessment
    st.markdown("### 🩺 A — Assessment")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Primary Diagnosis**")
        st.error(f"🔴 {a.get('primary_diagnosis', '—')}")
        st.markdown("**Clinical Impression**")
        st.write(a.get("clinical_impression", "—"))
    with c2:
        diffs = a.get("differential_diagnosis", [])
        if diffs:
            st.markdown("**Differential Diagnoses**")
            for d in diffs:
                st.markdown(f"• {d}")

    icd_codes = a.get("icd10_codes", [])
    if icd_codes:
        st.markdown("**ICD-10 Codes**")
        badges = ""
        for code in icd_codes:
            badges += f'<span class="icd-badge">🏷️ {code.get("code","?")} — {code.get("description","?")}</span>'
        st.markdown(badges, unsafe_allow_html=True)

    symptoms = entities.get("symptoms", [])
    if symptoms:
        st.markdown("**Extracted Symptoms**")
        badges = ""
        for s_item in symptoms:
            badges += f'<span class="symptom-badge">🤒 {s_item}</span>'
        st.markdown(badges, unsafe_allow_html=True)

    st.markdown("---")

    # P — Plan
    st.markdown("### 💊 P — Plan")
    plan_meds = p.get("medications", [])
    if plan_meds:
        st.markdown("**Prescribed Medications**")
        for med in plan_meds:
            st.markdown(f"- 💊 {med}")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Follow Up**")
        st.info(p.get("follow_up", "—"))
        st.markdown("**Referrals**")
        st.write(p.get("referrals", "None"))
    with c2:
        st.markdown("**Patient Education**")
        st.write(p.get("patient_education", "—"))
        st.markdown("**⚠️ Precautions**")
        st.warning(p.get("precautions", "—"))

    inv = p.get("investigations_ordered", [])
    if inv and inv != ["Not mentioned"]:
        st.markdown("**Investigations Ordered**")
        for i in inv:
            st.markdown(f"- 🧪 {i}")

    st.markdown("---")
    st.caption(f"Generated by MediVoice AI • {m.get('note_date','')} {m.get('note_time','')}")


# ── Main app ──────────────────────────────────────────────────────────────────
def main():

    # Header
    st.markdown("""
    <div class="main-header">
        <h1 style="margin:0; font-size:2rem;">🏥 MediVoice</h1>
        <p style="margin:0; opacity:0.85;">AI-Powered Ambient Clinical Scribe — Speak. Document. Done.</p>
    </div>
    """, unsafe_allow_html=True)

    # API status
    api_ok = check_api()
    if api_ok:
        st.success("✅ API Connected — MediVoice backend is running")
    else:
        st.error("❌ API not running — Start the backend: `cd backend && python main.py`")
        st.stop()

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/stethoscope.png", width=80)
        st.markdown("## ⚙️ Settings")

        patient_name = st.text_input("👤 Patient Name", value="Patient")
        language     = st.selectbox("🌐 Language",
                                    ["English", "Hindi", "Bengali"],
                                    index=0)

        st.markdown("---")
        st.markdown("## 📁 Past Sessions")
        sessions = get_sessions()
        if sessions:
            st.markdown(f"**{len(sessions)} session(s) saved**")
            for s in sessions[:5]:
                with st.expander(f"#{s['id']} — {s['patient_name']}"):
                    st.write(f"📅 {s['created_at'][:10]}")
                    st.write(f"🌐 {s['language']}")
                    if st.button(f"📄 Load Session #{s['id']}", key=f"load_{s['id']}"):
                        st.session_state["load_session"] = s["id"]
                    st.markdown(f"[📥 PDF](http://localhost:8000/sessions/{s['id']}/pdf)")
        else:
            st.info("No sessions yet")

        st.markdown("---")
        st.caption("MediVoice v1.0 | Built for hackathon")

    # ── Main tabs ─────────────────────────────────────────────────────────────
    tab1, tab2, tab3 = st.tabs([
        "🎙️ Record & Transcribe",
        "📝 Paste Transcript",
        "📊 Session History"
    ])

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 1 — Record
    # ─────────────────────────────────────────────────────────────────────────
    with tab1:
        st.markdown("### 🎙️ Live Consultation Recording")
        st.info("Click **Start Recording**, speak the consultation, then click **Stop & Process**")

        col1, col2, col3 = st.columns(3)
        duration = col1.slider("⏱️ Recording duration (seconds)", 10, 120, 30)

        if col2.button("🔴 Start Recording", type="primary", use_container_width=True):
            with st.spinner(f"Recording for {duration} seconds... Speak now!"):
                try:
                    audio_path = record_audio_clip(duration=duration)
                    st.session_state["audio_path"] = audio_path
                    st.success("✅ Recording saved! Click 'Process Recording' to generate note.")
                except Exception as e:
                    st.error(f"Recording failed: {e}")

        if "audio_path" in st.session_state:
            if col3.button("⚡ Process Recording", type="primary", use_container_width=True):
                with st.spinner("Transcribing audio with Whisper..."):
                    try:
                        with open(st.session_state["audio_path"], "rb") as f:
                            files = {"file": ("recording.wav", f, "audio/wav")}
                            data  = {"language": language, "patient_name": patient_name}
                            r     = requests.post(f"{API_URL}/process-audio",
                                                  files=files, data=data, timeout=120)
                        if r.status_code == 200:
                            result = r.json()
                            st.session_state["result"] = result
                            st.success("✅ Note generated successfully!")
                        else:
                            st.error(f"API error: {r.json().get('detail','Unknown')}")
                    except Exception as e:
                        st.error(f"Error: {e}")

        if "result" in st.session_state:
            result = st.session_state["result"]
            st.markdown("---")
            st.markdown("### 📄 Generated Clinical Note")

            with st.expander("📝 Raw Transcript", expanded=False):
                st.write(result.get("transcript", ""))

            render_soap_note(result["soap_note"], result["entities"])

            sid = result["session_id"]
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown(f"[📥 Download PDF](http://localhost:8000/sessions/{sid}/pdf)")
                st.caption("Professional formatted PDF")
            with col2:
                with st.expander("💊 View Prescription"):
                    st.text(result.get("prescription", ""))
            with col3:
                phone = st.text_input("📱 SMS to doctor",
                                      placeholder="+91XXXXXXXXXX",
                                      key=f"phone_tab1_{sid}")
                if st.button("📲 Send SMS", key=f"sms_tab1_{sid}"):
                    if phone:
                        r = requests.post(
                            f"{API_URL}/sessions/{sid}/send-sms",
                            params={"phone": phone}
                        )
                        sms_result = r.json()
                        if sms_result.get("status") == "sent":
                            st.success("✅ SMS sent!")
                        elif sms_result.get("status") == "skipped":
                            st.info(f"ℹ️ {sms_result.get('reason')}")
                        else:
                            st.warning(f"SMS: {sms_result.get('reason','')}")
                    else:
                        st.warning("Enter phone number first")

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 2 — Paste Transcript
    # ─────────────────────────────────────────────────────────────────────────
    with tab2:
        st.markdown("### 📝 Paste or Type Consultation Transcript")

        st.markdown("**Quick Demo Scripts:**")
        d1, d2, d3 = st.columns(3)

        demo_en = """Doctor: Good morning! What brings you in?
Patient: Doctor, I've had fever for 3 days, headache and mild cough.
Doctor: Any nausea or vomiting?
Patient: A little nausea but no vomiting.
Doctor: Any allergies?
Patient: No known allergies.
Doctor: Any medications?
Patient: Paracetamol 500mg twice a day.
Doctor: Temperature is 101.2°F, BP 120/80 mmhg, pulse 88 bpm.
Doctor: You have viral fever. I'll prescribe medications.
Patient: How long to recover?
Doctor: 3-5 days. Return if fever persists beyond 5 days."""

        demo_hi = """Doctor: Namaste! Aaj kya takleef hai?
Patient: Doctor, 3 din se bukhar hai, sar dard aur khasi hai.
Doctor: Koi allergy hai?
Patient: Nahi, koi allergy nahi hai.
Doctor: Abhi koi dawai le rahe hain?
Patient: Paracetamol 500mg le raha hoon.
Doctor: Temperature 101°F hai, BP 120/80 hai.
Doctor: Viral fever hai. Dawai likhta hoon.
Patient: Kitne din mein theek hoga?
Doctor: 3-5 din mein. Agar bukhar na utare toh wapas aana."""

        demo_complex = """Doctor: Good morning! Please describe your symptoms.
Patient: I'm a 45 year old male. I have chest pain and shortness of breath for 2 weeks.
         Also feeling very fatigued. I have high blood pressure and diabetes.
Doctor: Any medications?
Patient: Amlodipine 5mg and Metformin 1000mg daily.
Doctor: Any allergies?
Patient: No known drug allergies.
Doctor: BP is 150/95 mmhg, pulse 92 bpm. I'm ordering an ECG.
Doctor: I'm referring you to cardiology. Continue your medications."""

        if d1.button("🇬🇧 English Demo", use_container_width=True):
            st.session_state["demo_text"] = demo_en
        if d2.button("🇮🇳 Hindi Demo", use_container_width=True):
            st.session_state["demo_text"] = demo_hi
        if d3.button("🫀 Complex Case", use_container_width=True):
            st.session_state["demo_text"] = demo_complex

        default_text = st.session_state.get("demo_text", "")
        transcript = st.text_area(
            "Consultation Transcript",
            value=default_text,
            height=250,
            placeholder="Paste doctor-patient conversation here..."
        )

        col1, col2 = st.columns([1, 3])
        generate_btn = col1.button("⚡ Generate SOAP Note",
                                   type="primary",
                                   use_container_width=True,
                                   disabled=not transcript.strip())

        if generate_btn and transcript.strip():
            with st.spinner("Extracting entities and generating SOAP note..."):
                result, error = process_transcript(transcript, language, patient_name)

            if error:
                st.error(f"Error: {error}")
            else:
                st.session_state["tab2_result"] = result
                st.success(f"✅ Note generated! Session ID: {result['session_id']}")

        if "tab2_result" in st.session_state:
            result = st.session_state["tab2_result"]
            st.markdown("---")
            st.markdown("### 📄 Generated Clinical Note")

            with st.expander("🧬 Extracted Clinical Entities", expanded=False):
                entities = result["entities"]
                e1, e2, e3 = st.columns(3)
                e1.markdown("**Symptoms**\n\n" + "\n".join([f"• {s}" for s in entities.get("symptoms", [])]))
                e2.markdown("**Medications**\n\n" + "\n".join([f"• {m}" for m in entities.get("medications", [])]))
                e3.markdown("**Vitals**\n\n" + "\n".join([f"• {k}: {v}" for k, v in entities.get("vitals", {}).items()]))

            render_soap_note(result["soap_note"], result["entities"])

            # ── Phase 7 updated section ───────────────────────────────────────
            col1, col2, col3 = st.columns(3)
            sid = result["session_id"]

            with col1:
                st.markdown(f"[📥 Download PDF](http://localhost:8000/sessions/{sid}/pdf)")
                st.caption("Professional formatted PDF")
            with col2:
                with st.expander("💊 Prescription"):
                    st.text(result.get("prescription", ""))
                with st.expander("📋 Raw JSON"):
                    st.json(result["soap_note"])
            with col3:
                phone = st.text_input("📱 SMS to doctor",
                                      placeholder="+91XXXXXXXXXX",
                                      key=f"phone_{sid}")
                if st.button("📲 Send SMS", key=f"sms_{sid}"):
                    if phone:
                        r = requests.post(
                            f"{API_URL}/sessions/{sid}/send-sms",
                            params={"phone": phone}
                        )
                        sms_result = r.json()
                        if sms_result.get("status") == "sent":
                            st.success("✅ SMS sent!")
                        elif sms_result.get("status") == "skipped":
                            st.info(f"ℹ️ {sms_result.get('reason')}")
                        else:
                            st.warning(f"SMS: {sms_result.get('reason','')}")
                    else:
                        st.warning("Enter phone number first")

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 3 — Session History
    # ─────────────────────────────────────────────────────────────────────────
    with tab3:
        st.markdown("### 📊 Consultation History")

        if st.button("🔄 Refresh"):
            st.rerun()

        sessions = get_sessions()
        if not sessions:
            st.info("No sessions yet. Generate a note to see it here.")
        else:
            st.success(f"**{len(sessions)} consultation(s) on record**")

            for session in sessions:
                with st.expander(
                    f"#{session['id']} — {session['patient_name']} "
                    f"({session['language']}) — {session['created_at'][:10]}"
                ):
                    col1, col2, col3 = st.columns(3)
                    col1.markdown(f"**Patient:** {session['patient_name']}")
                    col2.markdown(f"**Language:** {session['language']}")
                    col3.markdown(f"**Date:** {session['created_at'][:10]}")
                    col1.markdown(
                        f"[📥 Download PDF](http://localhost:8000/sessions/{session['id']}/pdf)"
                    )


if __name__ == "__main__":
    main()