import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Optional
import tempfile
import json
import shutil

from transcriber    import transcribe_file
from nlp_extractor  import extract_entities, format_entities_summary
from note_generator import generate_soap_note, generate_prescription, format_soap_display
from db import init_db, save_session, get_all_sessions, get_session_by_id, delete_session# ── App setup ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title="MediVoice API",
    description="AI-powered clinical documentation assistant",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

init_db()

# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"app": "MediVoice API", "version": "1.0.0", "status": "running"}

@app.get("/health")
def health():
    return {"status": "healthy"}

# ── Pydantic models ───────────────────────────────────────────────────────────
class TranscriptRequest(BaseModel):
    transcript   : str
    language     : Optional[str] = "English"
    patient_name : Optional[str] = "Unknown"

# ── Route 1: Process raw transcript ──────────────────────────────────────────
@app.post("/process-transcript")
async def process_transcript(request: TranscriptRequest):
    try:
        transcript = request.transcript.strip()
        if not transcript:
            raise HTTPException(status_code=400, detail="Transcript is empty")

        entities     = extract_entities(transcript)
        soap_note    = generate_soap_note(transcript, entities)
        prescription = generate_prescription(soap_note)
        summary      = format_soap_display(soap_note)

        session_id = save_session(
            patient_name = request.patient_name,
            language     = request.language,
            transcript   = transcript,
            entities     = entities,
            soap_note    = soap_note,
            prescription = prescription
        )

        return {
            "session_id"  : session_id,
            "transcript"  : transcript,
            "entities"    : entities,
            "soap_note"   : soap_note,
            "prescription": prescription,
            "summary"     : summary
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── Route 2: Upload audio file ────────────────────────────────────────────────
@app.post("/process-audio")
async def process_audio(
    file         : UploadFile = File(...),
    language     : str        = Form("English"),
    patient_name : str        = Form("Unknown")
):
    try:
        suffix = os.path.splitext(file.filename)[1] or ".wav"
        tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        shutil.copyfileobj(file.file, tmp)
        tmp.close()

        transcription = transcribe_file(tmp.name, language=language)
        transcript    = transcription["transcript"]
        os.unlink(tmp.name)

        if not transcript.strip():
            raise HTTPException(status_code=400, detail="Empty transcription")

        entities     = extract_entities(transcript)
        soap_note    = generate_soap_note(transcript, entities)
        prescription = generate_prescription(soap_note)
        summary      = format_soap_display(soap_note)

        session_id = save_session(
            patient_name = patient_name,
            language     = language,
            transcript   = transcript,
            entities     = entities,
            soap_note    = soap_note,
            prescription = prescription
        )

        return {
            "session_id"  : session_id,
            "transcript"  : transcript,
            "entities"    : entities,
            "soap_note"   : soap_note,
            "prescription": prescription,
            "summary"     : summary,
            "duration"    : transcription.get("duration", 0)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── Route 3: Get all sessions ─────────────────────────────────────────────────
@app.get("/sessions")
def list_sessions():
    try:
        sessions = get_all_sessions()
        return {"sessions": sessions, "count": len(sessions)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── Route 4: Get single session ───────────────────────────────────────────────
@app.get("/sessions/{session_id}")
def get_session(session_id: int):
    session = get_session_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

# ── Route 5: Delete session ───────────────────────────────────────────────────
@app.delete("/sessions/{session_id}")
def remove_session(session_id: int):
    delete_session(session_id)
    return {"message": f"Session {session_id} deleted"}

# ── Route 6: Export PDF ───────────────────────────────────────────────────────
@app.get("/sessions/{session_id}/export-pdf")
def export_pdf(session_id: int):
    try:
        from fpdf import FPDF

        session = get_session_by_id(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        soap = session["soap_note"]
        s    = soap.get("subjective", {})
        o    = soap.get("objective",  {})
        a    = soap.get("assessment", {})
        p    = soap.get("plan",       {})
        m    = soap.get("metadata",   {})

        pdf = FPDF()
        pdf.add_page()
        pdf.set_margins(15, 15, 15)

        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, "MEDIVOICE CLINICAL NOTE", align="C", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, f"Date: {m.get('note_date','')}   Time: {m.get('note_time','')}", align="C", ln=True)
        pdf.cell(0, 6, f"Patient: {session.get('patient_name','Unknown')}", align="C", ln=True)
        pdf.ln(4)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(4)

        def section(title):
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 8, title, ln=True)
            pdf.set_font("Helvetica", "", 10)

        def field(label, value):
            if value and value != "Not mentioned":
                pdf.set_font("Helvetica", "B", 10)
                pdf.cell(45, 6, f"{label}:", ln=False)
                pdf.set_font("Helvetica", "", 10)
                pdf.multi_cell(0, 6, str(value))

        section("S — SUBJECTIVE")
        field("Chief Complaint", s.get("chief_complaint",""))
        field("HPI",             s.get("history_of_present_illness",""))
        field("Past History",    s.get("past_medical_history",""))
        meds = s.get("medications", [])
        field("Medications", ", ".join(meds) if isinstance(meds, list) else str(meds))
        field("Allergies",       s.get("allergies",""))
        pdf.ln(3)

        section("O — OBJECTIVE")
        vitals = o.get("vitals", {})
        field("Temperature",    vitals.get("temperature","Not recorded"))
        field("Blood Pressure", vitals.get("blood_pressure","Not recorded"))
        field("Pulse",          vitals.get("pulse","Not recorded"))
        field("Examination",    o.get("physical_examination",""))
        pdf.ln(3)

        section("A — ASSESSMENT")
        field("Primary Dx",  a.get("primary_diagnosis",""))
        field("Severity",    a.get("severity",""))
        field("Impression",  a.get("clinical_impression",""))
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, "ICD-10 Codes:", ln=True)
        pdf.set_font("Helvetica", "", 10)
        for code in a.get("icd10_codes", []):
            pdf.cell(0, 5, f"  {code.get('code','?')} - {code.get('description','?')}", ln=True)
        pdf.ln(3)

        section("P — PLAN")
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, "Medications:", ln=True)
        pdf.set_font("Helvetica", "", 10)
        for med in p.get("medications", []):
            pdf.cell(0, 5, f"  * {med}", ln=True)
        field("Follow Up",      p.get("follow_up",""))
        field("Patient Advice", p.get("patient_education",""))
        field("Precautions",    p.get("precautions",""))

        pdf.ln(5)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(3)
        pdf.set_font("Helvetica", "I", 9)
        pdf.cell(0, 5, "Generated by MediVoice AI", align="C", ln=True)

        pdf_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", f"soap_note_{session_id}.pdf"
        )
        pdf.output(pdf_path)

        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=f"soap_note_{session_id}.pdf"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    # ── Route 7: Enhanced PDF export ─────────────────────────────────────────────
@app.get("/sessions/{session_id}/pdf")
def export_enhanced_pdf(session_id: int):
    """Export professional PDF using pdf_exporter module"""
    try:
        from pdf_exporter import generate_pdf

        session = get_session_by_id(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        pdf_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", f"medivoice_note_{session_id}.pdf"
        )

        generate_pdf(session, pdf_path)

        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=f"medivoice_note_{session_id}.pdf"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Route 8: Send SMS summary ─────────────────────────────────────────────────
@app.post("/sessions/{session_id}/send-sms")
def send_sms(session_id: int, phone: str):
    """Send SOAP summary SMS to doctor's phone"""
    try:
        from sms_sender import send_soap_summary_sms

        session = get_session_by_id(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        result = send_soap_summary_sms(
            soap_note    = session["soap_note"],
            to_phone     = phone,
            patient_name = session.get("patient_name", "Patient")
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)