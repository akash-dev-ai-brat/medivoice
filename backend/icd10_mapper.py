import json
import os
import re


def load_icd10_db() -> dict:
    base_dir  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_path = os.path.join(base_dir, "data", "icd10_codes.json")
    with open(json_path, "r") as f:
        return json.load(f)


def get_codes_for_symptoms(symptoms: list) -> list:
    """Return ICD-10 codes for a list of symptoms"""
    db     = load_icd10_db()
    result = []
    for symptom in symptoms:
        symptom_lower = symptom.lower()
        if symptom_lower in db:
            result.append({
                "symptom"    : symptom,
                "code"       : db[symptom_lower]["code"],
                "description": db[symptom_lower]["description"]
            })
        else:
            # Fuzzy match — check if symptom contains a key
            for key, val in db.items():
                if key in symptom_lower or symptom_lower in key:
                    result.append({
                        "symptom"    : symptom,
                        "code"       : val["code"],
                        "description": val["description"]
                    })
                    break
    return result


def search_icd10(query: str) -> list:
    """Search ICD-10 database by keyword"""
    db      = load_icd10_db()
    query   = query.lower()
    results = []
    for key, val in db.items():
        if query in key or query in val["description"].lower():
            results.append({
                "symptom"    : key,
                "code"       : val["code"],
                "description": val["description"]
            })
    return results