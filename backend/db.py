import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "medivoice.db"
)

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name  TEXT DEFAULT 'Unknown',
            language      TEXT DEFAULT 'English',
            transcript    TEXT,
            entities      TEXT,
            soap_note     TEXT,
            prescription  TEXT,
            created_at    TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    print("✓ Database initialized")

def save_session(patient_name, language, transcript,
                 entities, soap_note, prescription) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO sessions
        (patient_name, language, transcript, entities, soap_note, prescription, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        patient_name, language, transcript,
        json.dumps(entities), json.dumps(soap_note),
        prescription, datetime.now().isoformat()
    ))
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return session_id

def get_all_sessions() -> list:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, patient_name, language, created_at
        FROM sessions ORDER BY created_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_session_by_id(session_id: int) -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        data = dict(row)
        data["entities"]  = json.loads(data["entities"]  or "{}")
        data["soap_note"] = json.loads(data["soap_note"] or "{}")
        return data
    return None

def delete_session(session_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()
    return True