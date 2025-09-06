import sqlite3
import json

DB_NAME = "candidates.db"

def init_db():
    """Initializes the database and creates the candidates table if it doesn't exist."""
    with sqlite3.connect(DB_NAME, timeout=10) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                summary TEXT,
                skills_json TEXT,
                experience_json TEXT,
                education_json TEXT,
                linkedin_json TEXT
            )
        """)
        conn.commit()

def add_or_update_candidate(profile_data, candidate_id=None):
    """Adds a new candidate or updates an existing one by ID."""
    # Ensure everything is a string or JSON string
    name = str(profile_data.get("name", "N/A"))
    email = str(profile_data.get("email") or "")
    phone = str(profile_data.get("phone") or "")
    summary = str(profile_data.get("summary") or "")
    skills_json = json.dumps(profile_data.get("skills") or [])
    experience_json = json.dumps(profile_data.get("experience") or [])
    education_json = json.dumps(profile_data.get("education") or [])
    linkedin_json = json.dumps(profile_data.get("linkedin_profile") or "")

    with sqlite3.connect(DB_NAME, timeout=10) as conn:
        cursor = conn.cursor()
        if candidate_id:
            # Update by id
            cursor.execute("""
                UPDATE candidates
                SET name=?, email=?, phone=?, summary=?, skills_json=?, experience_json=?, education_json=?, linkedin_json=?
                WHERE id=?
            """, (name, email, phone, summary, skills_json, experience_json, education_json, linkedin_json, candidate_id))
        else:
            # Insert new
            cursor.execute("""
                INSERT INTO candidates (name, email, phone, summary, skills_json, experience_json, education_json, linkedin_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, email, phone, summary, skills_json, experience_json, education_json, linkedin_json))
        conn.commit()

def get_all_candidate_names():
    """Get all candidate names."""
    with sqlite3.connect(DB_NAME, timeout=10) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM candidates ORDER BY name")
        return [row[0] for row in cursor.fetchall()]

def safe_load_json(value, default):
    """Safely load JSON from database, always returning a consistent type."""
    if not value:
        return default
    try:
        if isinstance(value, str):
            parsed = json.loads(value)
            if isinstance(parsed, str) and isinstance(default, list):
                return [s.strip() for s in parsed.split(",") if s.strip()]
            return parsed
        return value
    except Exception:
        return default

def get_candidate_by_name(name):
    """Get full profile for a candidate by name."""
    with sqlite3.connect(DB_NAME, timeout=10) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM candidates WHERE name=?", (name,))
        row = cursor.fetchone()

    if not row:
        return None

    return {
        "id": row[0],   # return ID too
        "name": row[1],
        "email": row[2],
        "phone": row[3],
        "summary": row[4],
        "skills": safe_load_json(row[5], []),
        "experience": safe_load_json(row[6], []),
        "education": safe_load_json(row[7], []),
        "linkedin_profile": safe_load_json(row[8], "")
    }

def delete_candidate_by_id(candidate_id):
    """Delete candidate by ID."""
    with sqlite3.connect(DB_NAME, timeout=10) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM candidates WHERE id=?", (candidate_id,))
        conn.commit()

def delete_candidate_by_name(name):
    """Delete candidate by name (legacy)."""
    with sqlite3.connect(DB_NAME, timeout=10) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM candidates WHERE name=?", (name,))
        conn.commit()
