import os
import json
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# ── Groq client (free) ────────────────────────────────────────────────────────
_client = None

def get_client():
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in .env file")
        _client = Groq(api_key=api_key)
    return _client


# ── Main SOAP note generator ──────────────────────────────────────────────────
def generate_soap_note(transcript: str, entities: dict) -> dict:
    client = get_client()
    entity_context = _build_entity_context(entities)

    prompt = f"""You are an experienced clinical documentation assistant helping a doctor write a SOAP note.

Below is a doctor-patient consultation transcript and extracted clinical entities.

TRANSCRIPT:
{transcript.strip()}

EXTRACTED CLINICAL DATA:
{entity_context}

Generate a complete, professional SOAP note in the following exact JSON format:
{{
    "subjective": {{
        "chief_complaint": "Main reason for visit in patient's own words",
        "history_of_present_illness": "Detailed narrative of the complaint",
        "past_medical_history": "Any mentioned chronic conditions",
        "medications": ["list", "of", "current", "medications"],
        "allergies": "Drug allergies or NKDA",
        "review_of_systems": "Other systems mentioned"
    }},
    "objective": {{
        "vitals": {{
            "temperature": "value or not recorded",
            "blood_pressure": "value or not recorded",
            "pulse": "value or not recorded",
            "spo2": "value or not recorded",
            "weight": "value or not recorded"
        }},
        "physical_examination": "Examination findings mentioned or not performed",
        "investigations": "Any tests or investigations mentioned"
    }},
    "assessment": {{
        "primary_diagnosis": "Most likely diagnosis",
        "differential_diagnosis": ["other", "possible", "diagnoses"],
        "icd10_codes": [
            {{"code": "R50.9", "description": "Fever unspecified"}}
        ],
        "severity": "Mild / Moderate / Severe",
        "clinical_impression": "Brief clinical summary"
    }},
    "plan": {{
        "medications": ["medication 1 with dose", "medication 2 with dose"],
        "investigations_ordered": ["any tests ordered"],
        "referrals": "Any referrals or none",
        "follow_up": "Follow up instructions",
        "patient_education": "What patient was advised",
        "precautions": "Warning signs to watch for"
    }},
    "metadata": {{
        "note_date": "{datetime.now().strftime('%Y-%m-%d')}",
        "note_time": "{datetime.now().strftime('%H:%M')}",
        "generated_by": "MediVoice AI"
    }}
}}

Rules:
- Return ONLY valid JSON, no extra text, no markdown backticks
- Use "Not mentioned" for fields not in the transcript
- Be concise but clinically accurate
- Never invent information not present in the transcript"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000,
        temperature=0.3
    )

    raw_text = response.choices[0].message.content.strip()

    # Clean JSON if model wraps in backticks
    if "```" in raw_text:
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
    raw_text = raw_text.strip()

    return json.loads(raw_text)


# ── Prescription generator ────────────────────────────────────────────────────
def generate_prescription(soap_note: dict, patient_name: str = "Patient") -> str:
    client = get_client()

    plan       = soap_note.get("plan", {})
    assessment = soap_note.get("assessment", {})

    prompt = f"""Generate a clean, professional prescription based on:

Diagnosis: {assessment.get('primary_diagnosis', '')}
Medications: {json.dumps(plan.get('medications', []))}
Follow up: {plan.get('follow_up', 'As needed')}
Precautions: {plan.get('precautions', 'None')}
Patient Education: {plan.get('patient_education', 'None')}

Format with these sections:
1. Diagnosis
2. Rx (Medications with dose and frequency)
3. Instructions to patient
4. Follow-up date
5. Warning signs — when to return immediately

Plain text only. Be concise and professional."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=600,
        temperature=0.3
    )

    return response.choices[0].message.content.strip()


# ── Format SOAP note for display ──────────────────────────────────────────────
def format_soap_display(soap_note: dict) -> str:
    s = soap_note.get("subjective", {})
    o = soap_note.get("objective",  {})
    a = soap_note.get("assessment", {})
    p = soap_note.get("plan",       {})
    m = soap_note.get("metadata",   {})

    lines = []
    lines.append("=" * 60)
    lines.append("           MEDIVOICE CLINICAL NOTE")
    lines.append(f"  Date: {m.get('note_date','')}  Time: {m.get('note_time','')}")
    lines.append("=" * 60)

    lines.append("\nS — SUBJECTIVE")
    lines.append(f"  Chief Complaint : {s.get('chief_complaint','')}")
    lines.append(f"  HPI             : {s.get('history_of_present_illness','')}")
    lines.append(f"  Past History    : {s.get('past_medical_history','')}")
    meds = s.get('medications', [])
    lines.append(f"  Medications     : {', '.join(meds) if isinstance(meds, list) else meds}")
    lines.append(f"  Allergies       : {s.get('allergies','')}")
    lines.append(f"  Review of Sys   : {s.get('review_of_systems','')}")

    lines.append("\nO — OBJECTIVE")
    vitals = o.get("vitals", {})
    lines.append(f"  Temperature     : {vitals.get('temperature','Not recorded')}")
    lines.append(f"  Blood Pressure  : {vitals.get('blood_pressure','Not recorded')}")
    lines.append(f"  Pulse           : {vitals.get('pulse','Not recorded')}")
    lines.append(f"  SpO2            : {vitals.get('spo2','Not recorded')}")
    lines.append(f"  Weight          : {vitals.get('weight','Not recorded')}")
    lines.append(f"  Examination     : {o.get('physical_examination','')}")
    lines.append(f"  Investigations  : {o.get('investigations','')}")

    lines.append("\nA — ASSESSMENT")
    lines.append(f"  Primary Dx      : {a.get('primary_diagnosis','')}")
    lines.append(f"  Severity        : {a.get('severity','')}")
    lines.append(f"  Impression      : {a.get('clinical_impression','')}")
    diffs = a.get('differential_diagnosis', [])
    lines.append(f"  Differentials   : {', '.join(diffs) if isinstance(diffs, list) else diffs}")

    lines.append("\n  ICD-10 Codes:")
    for code in a.get("icd10_codes", []):
        lines.append(f"    {code.get('code','?')} — {code.get('description','?')}")

    lines.append("\nP — PLAN")
    lines.append("  Medications:")
    for med in p.get("medications", []):
        lines.append(f"    • {med}")
    inv = p.get('investigations_ordered', [])
    lines.append(f"  Investigations  : {', '.join(inv) if isinstance(inv, list) else inv}")
    lines.append(f"  Referrals       : {p.get('referrals','')}")
    lines.append(f"  Follow Up       : {p.get('follow_up','')}")
    lines.append(f"  Patient Advice  : {p.get('patient_education','')}")
    lines.append(f"  Precautions     : {p.get('precautions','')}")

    lines.append("\n" + "=" * 60)
    lines.append("       Generated by MediVoice AI")
    lines.append("=" * 60)

    return "\n".join(lines)


# ── Helper ────────────────────────────────────────────────────────────────────
def _build_entity_context(entities: dict) -> str:
    lines = []
    if entities.get("age"):
        lines.append(f"Age: {entities['age']} years")
    if entities.get("gender"):
        lines.append(f"Gender: {entities['gender']}")
    if entities.get("symptoms"):
        lines.append(f"Symptoms: {', '.join(entities['symptoms'])}")
    if entities.get("durations"):
        lines.append(f"Duration: {', '.join(entities['durations'])}")
    if entities.get("vitals"):
        for k, v in entities["vitals"].items():
            lines.append(f"{k.replace('_',' ').title()}: {v}")
    if entities.get("medications"):
        lines.append(f"Medications: {', '.join(entities['medications'])}")
    if entities.get("med_with_dose"):
        lines.append(f"Dosages: {', '.join(entities['med_with_dose'])}")
    if entities.get("allergies"):
        lines.append(f"Allergies: {', '.join(entities['allergies'])}")
    if entities.get("icd10_codes"):
        codes = [f"{c['code']} ({c['symptom']})" for c in entities["icd10_codes"]]
        lines.append(f"ICD-10: {', '.join(codes)}")
    return "\n".join(lines)