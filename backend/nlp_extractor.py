import medspacy
import json
import os
import re
from typing import Optional

# ── Load medspaCy model ───────────────────────────────────────────────────────
_nlp = None

def load_nlp():
    """Load medspaCy pipeline once and cache it"""
    global _nlp
    if _nlp is None:
        print("Loading medspaCy pipeline...")
        _nlp = medspacy.load()
        print("✓ medspaCy loaded")
    return _nlp


# ── Load ICD-10 lookup ────────────────────────────────────────────────────────
def load_icd10() -> dict:
    """Load ICD-10 codes from JSON file"""
    base_dir  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_path = os.path.join(base_dir, "data", "icd10_codes.json")
    with open(json_path, "r") as f:
        return json.load(f)


# ── Keyword-based symptom extractor ──────────────────────────────────────────
SYMPTOM_KEYWORDS = [
    "fever", "cough", "headache", "chest pain", "shortness of breath",
    "fatigue", "nausea", "vomiting", "diarrhea", "abdominal pain",
    "back pain", "sore throat", "runny nose", "dizziness", "rash",
    "joint pain", "high blood pressure", "diabetes", "asthma",
    "anxiety", "depression", "insomnia", "urinary tract infection",
    "ear pain", "eye pain", "weakness", "swelling", "weight loss",
    "weight gain", "loss of appetite", "difficulty breathing",
    "palpitations", "numbness", "tingling", "blurred vision",
    "frequent urination", "painful urination", "cold", "flu",
    "body ache", "muscle pain", "neck pain", "knee pain"
]

MEDICATION_KEYWORDS = [
    "paracetamol", "ibuprofen", "aspirin", "metformin", "insulin",
    "amoxicillin", "azithromycin", "ciprofloxacin", "omeprazole",
    "pantoprazole", "atorvastatin", "amlodipine", "metoprolol",
    "lisinopril", "cetirizine", "loratadine", "salbutamol",
    "prednisolone", "dexamethasone", "clopidogrel", "warfarin",
    "losartan", "ramipril", "glipizide", "gabapentin", "sertraline",
    "fluoxetine", "alprazolam", "diazepam", "ranitidine", "antacid",
    "multivitamin", "vitamin d", "vitamin c", "iron", "calcium",
    "tablet", "capsule", "syrup", "injection", "mg", "ml"
]

DURATION_PATTERNS = [
    r"\d+\s*(day|days|week|weeks|month|months|hour|hours|year|years)",
    r"(since|for|past|last)\s+\d+\s*(day|days|week|weeks|month|months)",
    r"(since|for|past|last)\s+(yesterday|morning|night|evening|a week|a month)",
    r"(yesterday|this morning|last night|last week|recently|suddenly)"
]

VITALS_PATTERNS = {
    "temperature" : r"(\d+\.?\d*)\s*(°f|°c|fahrenheit|celsius|degrees|degree|f\b)",
    "blood_pressure": r"(\d{2,3})\s*/\s*(\d{2,3})\s*(mmhg|mm hg)?",
    "pulse"       : r"(\d{2,3})\s*(bpm|beats per minute|pulse)",
    "spo2"        : r"(\d{2,3})\s*(%|percent|spo2|oxygen)",
    "weight"      : r"(\d{2,3})\s*(kg|kilograms|pounds|lbs)",
    "age"         : r"(\d{1,3})\s*(year|yr|years)\s*(old|age)?"
}


def extract_entities(transcript: str) -> dict:
    """
    Extract clinical entities from transcript:
    - symptoms
    - medications
    - duration
    - vitals
    - age & gender
    - allergies
    - ICD-10 codes
    """
    text_lower = transcript.lower()
    nlp        = load_nlp()
    icd10      = load_icd10()

    # ── medspaCy NLP ─────────────────────────────────────────────────────────
    doc = nlp(transcript)

    # ── Extract symptoms ──────────────────────────────────────────────────────
    symptoms = []
    for keyword in SYMPTOM_KEYWORDS:
        if keyword in text_lower:
            # Check it's not negated (e.g. "no fever", "denies cough")
            pattern = rf"(no|not|denies|without|absent)\s+{keyword}"
            if not re.search(pattern, text_lower):
                symptoms.append(keyword)

    # Remove duplicates
    symptoms = list(dict.fromkeys(symptoms))

    # ── Extract medications ───────────────────────────────────────────────────
    medications = []
    for med in MEDICATION_KEYWORDS:
        if med in text_lower and med not in ["mg", "ml", "tablet", "capsule", "syrup", "injection"]:
            medications.append(med)

    # Extract dosage context
    dosage_pattern = r"(\w+)\s+(\d+\.?\d*\s*mg|\d+\.?\d*\s*ml)"
    dosages = re.findall(dosage_pattern, text_lower)
    med_with_dose = [f"{d[0]} {d[1]}" for d in dosages]

    # ── Extract duration ──────────────────────────────────────────────────────
    durations = []
    for pattern in DURATION_PATTERNS:
        matches = re.findall(pattern, text_lower)
        for match in matches:
            if isinstance(match, tuple):
                durations.append(" ".join(match).strip())
            else:
                durations.append(match.strip())

    durations = list(dict.fromkeys(durations))[:3]

    # ── Extract vitals ────────────────────────────────────────────────────────
    vitals = {}
    for vital, pattern in VITALS_PATTERNS.items():
        match = re.search(pattern, text_lower)
        if match:
            vitals[vital] = match.group(0).strip()

    # ── Extract age ───────────────────────────────────────────────────────────
    age = None
    age_match = re.search(r"(\d{1,3})\s*(year|yr|years)\s*(old)?", text_lower)
    if age_match:
        age = int(age_match.group(1))

    # ── Extract gender ────────────────────────────────────────────────────────
    gender = None
    if any(w in text_lower for w in ["male", "man", "boy", "mr", "he ", "his "]):
        gender = "Male"
    elif any(w in text_lower for w in ["female", "woman", "girl", "mrs", "ms", "she ", "her "]):
        gender = "Female"

    # ── Extract allergies ─────────────────────────────────────────────────────
    allergies = []
    allergy_pattern = r"(allergic to|allergy to|no known allergy|nka)\s*([a-zA-Z\s,]+)?"
    allergy_match = re.search(allergy_pattern, text_lower)
    if allergy_match:
        if "no known" in allergy_match.group(0) or "nka" in allergy_match.group(0):
            allergies = ["NKDA"]
        elif allergy_match.group(2):
            allergies = [allergy_match.group(2).strip()]

    # ── Map symptoms to ICD-10 ────────────────────────────────────────────────
    icd10_codes = []
    for symptom in symptoms:
        if symptom in icd10:
            icd10_codes.append({
                "symptom"    : symptom,
                "code"       : icd10[symptom]["code"],
                "description": icd10[symptom]["description"]
            })

    # ── medspaCy named entities ───────────────────────────────────────────────
    spacy_entities = []
    for ent in doc.ents:
        spacy_entities.append({
            "text"  : ent.text,
            "label" : ent.label_
        })

    return {
        "symptoms"       : symptoms,
        "medications"    : medications,
        "med_with_dose"  : med_with_dose,
        "durations"      : durations,
        "vitals"         : vitals,
        "age"            : age,
        "gender"         : gender,
        "allergies"      : allergies,
        "icd10_codes"    : icd10_codes,
        "spacy_entities" : spacy_entities
    }


def format_entities_summary(entities: dict) -> str:
    """Format extracted entities into readable summary"""
    lines = []

    if entities["age"] or entities["gender"]:
        demo = []
        if entities["age"]:    demo.append(f"{entities['age']} years old")
        if entities["gender"]: demo.append(entities["gender"])
        lines.append(f"Patient    : {', '.join(demo)}")

    if entities["symptoms"]:
        lines.append(f"Symptoms   : {', '.join(entities['symptoms'])}")

    if entities["durations"]:
        lines.append(f"Duration   : {', '.join(entities['durations'])}")

    if entities["vitals"]:
        vitals_str = ", ".join([f"{k}: {v}" for k, v in entities["vitals"].items()])
        lines.append(f"Vitals     : {vitals_str}")

    if entities["medications"]:
        lines.append(f"Medications: {', '.join(entities['medications'])}")

    if entities["allergies"]:
        lines.append(f"Allergies  : {', '.join(entities['allergies'])}")

    if entities["icd10_codes"]:
        codes_str = ", ".join([f"{c['code']} ({c['symptom']})" for c in entities["icd10_codes"]])
        lines.append(f"ICD-10     : {codes_str}")

    return "\n".join(lines)