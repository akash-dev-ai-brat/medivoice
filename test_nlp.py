import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

from nlp_extractor import extract_entities, format_entities_summary
from icd10_mapper  import get_codes_for_symptoms, search_icd10

# ── Sample transcripts ────────────────────────────────────────────────────────
TRANSCRIPTS = {
    "English": """
        Patient is a 35 year old male presenting with fever for 3 days,
        headache, and mild cough. No known allergies. Temperature is 101°F.
        Currently taking paracetamol 500mg twice daily. Blood pressure 120/80 mmhg.
        Patient denies vomiting or diarrhea.
    """,

    "Hindi_translated": """
        Patient is a 28 year old female with complaints of severe headache
        since yesterday, nausea, dizziness, and back pain. She is allergic to
        penicillin. Currently on metformin 500mg for diabetes. Pulse 88 bpm.
        No fever. Weight 60 kg.
    """,

    "Complex": """
        45 year old male patient with high blood pressure and diabetes.
        Presenting with chest pain, shortness of breath, and fatigue for
        2 weeks. Currently on amlodipine 5mg and metformin 1000mg.
        No known drug allergy. Blood pressure 150/95 mmhg. Pulse 92 bpm.
        Patient also complains of insomnia and anxiety.
    """
}

print("=" * 60)
print("   MediVoice — NLP Extractor Test")
print("=" * 60)

for name, transcript in TRANSCRIPTS.items():
    print(f"\n{'─' * 60}")
    print(f"Test: {name}")
    print(f"{'─' * 60}")
    print(f"Transcript:\n{transcript.strip()}\n")

    entities = extract_entities(transcript)

    print("Extracted Entities:")
    print(format_entities_summary(entities))

    print(f"\nRaw ICD-10 codes:")
    for code in entities["icd10_codes"]:
        print(f"  {code['code']} — {code['description']} ({code['symptom']})")

    if entities["spacy_entities"]:
        print(f"\nmedspaCy entities:")
        for ent in entities["spacy_entities"][:5]:
            print(f"  [{ent['label']}] {ent['text']}")

print("\n" + "=" * 60)
print("Test 2: ICD-10 Search")
print("=" * 60)

results = search_icd10("pain")
print(f"\nAll conditions matching 'pain':")
for r in results:
    print(f"  {r['code']} — {r['description']}")

print("\n" + "=" * 60)
print("✓ All NLP tests complete! Ready for Phase 4.")
print("=" * 60)