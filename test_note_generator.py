import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

from nlp_extractor   import extract_entities, format_entities_summary
from note_generator  import generate_soap_note, generate_prescription, format_soap_display
import json

# ── Sample transcript ─────────────────────────────────────────────────────────
TRANSCRIPT = """
Doctor: Good morning! What brings you in today?
Patient: Doctor, I've been having fever for the past 3 days along with 
         a severe headache and mild cough.
Doctor: Any other symptoms? Nausea or vomiting?
Patient: A little nausea but no vomiting.
Doctor: Any allergies to medications?
Patient: No known allergies.
Doctor: Are you on any medications currently?
Patient: I've been taking paracetamol 500mg twice a day for the fever.
Doctor: Let me check your vitals. Temperature is 101.2°F, blood pressure 
        120/80 mmhg, pulse 88 bpm.
Doctor: I think you have viral fever. I'll prescribe some medications.
Patient: Okay doctor. How many days will it take to recover?
Doctor: Should be fine in 3-5 days. Come back if fever persists beyond 5 days.
"""

print("=" * 60)
print("     MediVoice — SOAP Note Generator Test")
print("=" * 60)

# Step 1 — Extract entities
print("\nStep 1: Extracting clinical entities...")
entities = extract_entities(TRANSCRIPT)
print(format_entities_summary(entities))

# Step 2 — Generate SOAP note
print("\nStep 2: Generating SOAP note via Claude API...")
print("(This takes 5-10 seconds...)\n")

try:
    soap_note = generate_soap_note(TRANSCRIPT, entities)

    # Display formatted note
    print(format_soap_display(soap_note))

    # Step 3 — Generate prescription
    print("\nStep 3: Generating prescription...")
    prescription = generate_prescription(soap_note)
    print("\n--- PRESCRIPTION ---")
    print(prescription)

    # Step 4 — Save raw JSON
    with open("data/test_soap_note.json", "w") as f:
        json.dump(soap_note, f, indent=2)
    print("\n✓ SOAP note saved to data/test_soap_note.json")

    print("\n" + "=" * 60)
    print("✓ Phase 4 complete! Claude API working perfectly.")
    print("  Ready for Phase 5 — FastAPI Backend")
    print("=" * 60)

except Exception as e:
    print(f"\n✗ Error: {e}")
    print("\nCheck your ANTHROPIC_API_KEY in .env file")