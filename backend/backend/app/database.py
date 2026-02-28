"""
SQLite database for user registration and authentication.
"""
import sqlite3
import uuid
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).resolve().parent.parent / "users.db"


def get_db() -> sqlite3.Connection:
    """Get a database connection with row factory."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id              TEXT PRIMARY KEY,
            name            TEXT NOT NULL,
            phone           TEXT NOT NULL,
            consumer_id     TEXT UNIQUE,
            vehicle_number  TEXT,
            dl_number       TEXT,
            created_at      TEXT DEFAULT (datetime('now'))
        )
    """)
    
    # Sentinel: Violation Reports
    conn.execute("""
        CREATE TABLE IF NOT EXISTS violation_reports (
            id                  TEXT PRIMARY KEY,
            plate_number        TEXT,
            violation_type      TEXT NOT NULL,
            violation_description TEXT,
            formal_description  TEXT,
            location            TEXT,
            latitude            REAL,
            longitude           REAL,
            timestamp           TEXT,
            image_path          TEXT,
            is_authentic        INTEGER DEFAULT 1,
            confidence          REAL DEFAULT 0.0,
            status              TEXT DEFAULT 'pending',
            created_at          TEXT DEFAULT (datetime('now'))
        )
    """)
    
    # Sentinel: Vehicle Registry (Car-to-Phone database)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS vehicle_registry (
            id              TEXT PRIMARY KEY,
            plate_number    TEXT UNIQUE NOT NULL,
            owner_name      TEXT,
            owner_phone     TEXT NOT NULL,
            created_at      TEXT DEFAULT (datetime('now'))
        )
    """)
    
    # Disaster & Infrastructure Incidents
    conn.execute("""
        CREATE TABLE IF NOT EXISTS disaster_incidents (
            id                  TEXT PRIMARY KEY,
            category            TEXT NOT NULL,
            subcategory         TEXT NOT NULL,
            severity            TEXT NOT NULL,
            description         TEXT,
            detailed_description TEXT,
            location            TEXT,
            latitude            REAL,
            longitude           REAL,
            district            TEXT,
            landmarks           TEXT,
            extracted_text      TEXT,
            timestamp           TEXT,
            image_path          TEXT,
            is_valid            INTEGER DEFAULT 1,
            confidence          REAL DEFAULT 0.0,
            status              TEXT DEFAULT 'reported',
            recommended_authority TEXT,
            authorities_notified TEXT,
            created_at          TEXT DEFAULT (datetime('now')),
            updated_at          TEXT DEFAULT (datetime('now'))
        )
    """)
    
    # User Profiles
    conn.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            id              TEXT PRIMARY KEY,
            user_id         TEXT,
            name            TEXT NOT NULL,
            created_at      TEXT DEFAULT (datetime('now'))
        )
    """)
    
    # Utility Accounts linked to Profiles
    conn.execute("""
        CREATE TABLE IF NOT EXISTS utility_accounts (
            id              TEXT PRIMARY KEY,
            profile_id      TEXT NOT NULL,
            service_type    TEXT NOT NULL,
            consumer_id     TEXT NOT NULL,
            label           TEXT,
            number_plate    TEXT,
            created_at      TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE
        )
    """)
    
    conn.commit()
    conn.close()


def create_user(name: str, phone: str, consumer_id: str,
                vehicle_number: str = None, dl_number: str = None) -> dict:
    """Insert a new user and return the user dict."""
    conn = get_db()
    user_id = str(uuid.uuid4())
    try:
        conn.execute(
            """INSERT INTO users (id, name, phone, consumer_id, vehicle_number, dl_number)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, name.strip(), phone.strip(),
             consumer_id.strip() if consumer_id else None,
             vehicle_number.strip() if vehicle_number else None,
             dl_number.strip() if dl_number else None),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise ValueError("A user with this Consumer ID already exists.")
    user = dict(conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone())
    conn.close()
    return user


def find_user_by_identifier(identifier: str, identifier_type: str) -> dict | None:
    """
    Look up a user by one of their unique identifiers.
    identifier_type: 'challan' (consumer_id) | 'vehicle' (vehicle_number) | 'dl' (dl_number)
    """
    column_map = {
        "challan": "consumer_id",
        "vehicle": "vehicle_number",
        "dl": "dl_number",
    }
    column = column_map.get(identifier_type)
    if not column:
        return None

    conn = get_db()
    row = conn.execute(
        f"SELECT * FROM users WHERE {column} = ? COLLATE NOCASE", (identifier.strip(),)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ─────────────────────────────────────────────────────────────────────────────
# Sentinel Database Operations
# ─────────────────────────────────────────────────────────────────────────────

def create_violation_report(
    plate_number: str | None,
    violation_type: str,
    violation_description: str,
    formal_description: str,
    location: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    timestamp: str | None = None,
    image_path: str | None = None,
    is_authentic: bool = True,
    confidence: float = 0.0,
    status: str = "pending"
) -> dict:
    """Create a new violation report."""
    conn = get_db()
    report_id = str(uuid.uuid4())
    conn.execute(
        """INSERT INTO violation_reports 
           (id, plate_number, violation_type, violation_description, formal_description,
            location, latitude, longitude, timestamp, image_path, is_authentic, confidence, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (report_id, plate_number, violation_type, violation_description, formal_description,
         location, latitude, longitude, timestamp, image_path, 
         1 if is_authentic else 0, confidence, status)
    )
    conn.commit()
    row = conn.execute("SELECT * FROM violation_reports WHERE id = ?", (report_id,)).fetchone()
    conn.close()
    return dict(row)


def get_all_violation_reports() -> list[dict]:
    """Get all violation reports ordered by creation date."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM violation_reports ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_violation_report(report_id: str) -> dict | None:
    """Get a single violation report by ID."""
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM violation_reports WHERE id = ?", (report_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def update_violation_status(report_id: str, status: str) -> dict | None:
    """Update the status of a violation report."""
    conn = get_db()
    conn.execute(
        "UPDATE violation_reports SET status = ? WHERE id = ?",
        (status, report_id)
    )
    conn.commit()
    row = conn.execute("SELECT * FROM violation_reports WHERE id = ?", (report_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def add_registry_entry(plate_number: str, owner_name: str | None, owner_phone: str) -> dict:
    """Add a vehicle to the registry."""
    conn = get_db()
    entry_id = str(uuid.uuid4())
    try:
        conn.execute(
            """INSERT INTO vehicle_registry (id, plate_number, owner_name, owner_phone)
               VALUES (?, ?, ?, ?)""",
            (entry_id, plate_number.upper().strip(), owner_name, owner_phone.strip())
        )
        conn.commit()
    except sqlite3.IntegrityError:
        # Update existing entry
        conn.execute(
            """UPDATE vehicle_registry SET owner_name = ?, owner_phone = ? 
               WHERE plate_number = ?""",
            (owner_name, owner_phone.strip(), plate_number.upper().strip())
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM vehicle_registry WHERE plate_number = ?", 
            (plate_number.upper().strip(),)
        ).fetchone()
        conn.close()
        return dict(row)
    
    row = conn.execute("SELECT * FROM vehicle_registry WHERE id = ?", (entry_id,)).fetchone()
    conn.close()
    return dict(row)


def find_registry_by_plate(plate_number: str) -> dict | None:
    """Look up owner by plate number in the registry."""
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM vehicle_registry WHERE plate_number = ? COLLATE NOCASE",
        (plate_number.strip(),)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_registry_entries() -> list[dict]:
    """Get all registry entries."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM vehicle_registry ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_registry_entry(entry_id: str) -> bool:
    """Delete a registry entry."""
    conn = get_db()
    cursor = conn.execute("DELETE FROM vehicle_registry WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()
    return cursor.rowcount > 0


# ─────────────────────────────────────────────────────────────────────────────
# Disaster & Infrastructure Incident Operations
# ─────────────────────────────────────────────────────────────────────────────

def create_disaster_incident(
    category: str,
    subcategory: str,
    severity: str,
    description: str,
    detailed_description: str | None = None,
    location: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    district: str | None = None,
    landmarks: str | None = None,
    extracted_text: list | None = None,
    timestamp: str | None = None,
    image_path: str | None = None,
    is_valid: bool = True,
    confidence: float = 0.0,
    status: str = "reported",
    recommended_authority: str | None = None
) -> dict:
    """Create a new disaster incident report."""
    import json
    conn = get_db()
    incident_id = str(uuid.uuid4())
    extracted_text_json = json.dumps(extracted_text or [])
    
    conn.execute(
        """INSERT INTO disaster_incidents 
           (id, category, subcategory, severity, description, detailed_description,
            location, latitude, longitude, district, landmarks, extracted_text,
            timestamp, image_path, is_valid, confidence, status, recommended_authority)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (incident_id, category, subcategory, severity, description, detailed_description,
         location, latitude, longitude, district, landmarks, extracted_text_json,
         timestamp, image_path, 1 if is_valid else 0, confidence, status, recommended_authority)
    )
    conn.commit()
    row = conn.execute("SELECT * FROM disaster_incidents WHERE id = ?", (incident_id,)).fetchone()
    conn.close()
    return _parse_incident_row(row)


def get_all_disaster_incidents() -> list[dict]:
    """Get all disaster incidents ordered by creation date."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM disaster_incidents ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [_parse_incident_row(row) for row in rows]


def get_active_disaster_incidents() -> list[dict]:
    """Get active (non-resolved/rejected) disaster incidents."""
    conn = get_db()
    rows = conn.execute(
        """SELECT * FROM disaster_incidents 
           WHERE status NOT IN ('resolved', 'rejected')
           ORDER BY 
               CASE severity 
                   WHEN 'P1' THEN 1 
                   WHEN 'P2' THEN 2 
                   WHEN 'P3' THEN 3 
                   WHEN 'P4' THEN 4 
               END,
               created_at DESC"""
    ).fetchall()
    conn.close()
    return [_parse_incident_row(row) for row in rows]


def get_disaster_incident(incident_id: str) -> dict | None:
    """Get a single disaster incident by ID."""
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM disaster_incidents WHERE id = ?", (incident_id,)
    ).fetchone()
    conn.close()
    return _parse_incident_row(row) if row else None


def update_disaster_incident_status(incident_id: str, status: str, authorities_notified: list | None = None) -> dict | None:
    """Update the status of a disaster incident."""
    import json
    conn = get_db()
    
    if authorities_notified:
        conn.execute(
            "UPDATE disaster_incidents SET status = ?, authorities_notified = ?, updated_at = datetime('now') WHERE id = ?",
            (status, json.dumps(authorities_notified), incident_id)
        )
    else:
        conn.execute(
            "UPDATE disaster_incidents SET status = ?, updated_at = datetime('now') WHERE id = ?",
            (status, incident_id)
        )
    
    conn.commit()
    row = conn.execute("SELECT * FROM disaster_incidents WHERE id = ?", (incident_id,)).fetchone()
    conn.close()
    return _parse_incident_row(row) if row else None


def get_disaster_incidents_by_district(district: str) -> list[dict]:
    """Get all incidents for a specific district."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM disaster_incidents WHERE district = ? ORDER BY created_at DESC",
        (district,)
    ).fetchall()
    conn.close()
    return [_parse_incident_row(row) for row in rows]


def get_disaster_incident_stats() -> dict:
    """Get statistics about disaster incidents."""
    conn = get_db()
    
    # Count by status
    status_rows = conn.execute(
        "SELECT status, COUNT(*) as count FROM disaster_incidents GROUP BY status"
    ).fetchall()
    
    # Count by severity
    severity_rows = conn.execute(
        "SELECT severity, COUNT(*) as count FROM disaster_incidents GROUP BY severity"
    ).fetchall()
    
    # Count by category
    category_rows = conn.execute(
        "SELECT category, COUNT(*) as count FROM disaster_incidents GROUP BY category"
    ).fetchall()
    
    # Recent 24h count
    recent_count = conn.execute(
        "SELECT COUNT(*) FROM disaster_incidents WHERE created_at > datetime('now', '-24 hours')"
    ).fetchone()[0]
    
    conn.close()
    
    return {
        "by_status": {row["status"]: row["count"] for row in status_rows},
        "by_severity": {row["severity"]: row["count"] for row in severity_rows},
        "by_category": {row["category"]: row["count"] for row in category_rows},
        "last_24h": recent_count,
        "total": sum(row["count"] for row in status_rows)
    }


def _parse_incident_row(row) -> dict:
    """Parse a database row into an incident dict."""
    import json
    if not row:
        return None
    d = dict(row)
    # Parse JSON fields
    if d.get("extracted_text"):
        try:
            d["extracted_text"] = json.loads(d["extracted_text"])
        except:
            d["extracted_text"] = []
    else:
        d["extracted_text"] = []
    
    if d.get("authorities_notified"):
        try:
            d["authorities_notified"] = json.loads(d["authorities_notified"])
        except:
            d["authorities_notified"] = []
    else:
        d["authorities_notified"] = []
    
    d["is_valid"] = bool(d.get("is_valid", 1))
    return d


# ─────────────────────────────────────────────────────────────────────────────
# Profile & Account Database Operations
# ─────────────────────────────────────────────────────────────────────────────

def create_profile(name: str, user_id: str = None) -> dict:
    """Create a new profile."""
    conn = get_db()
    profile_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO profiles (id, user_id, name) VALUES (?, ?, ?)",
        (profile_id, user_id, name.strip())
    )
    conn.commit()
    row = conn.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,)).fetchone()
    conn.close()
    return _parse_profile_row(row)


def get_all_profiles(user_id: str = None) -> list:
    """Get all profiles, optionally filtered by user_id."""
    conn = get_db()
    if user_id:
        rows = conn.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM profiles").fetchall()
    conn.close()
    return [_parse_profile_row(row) for row in rows]


def get_profile(profile_id: str) -> dict | None:
    """Get a single profile by ID."""
    conn = get_db()
    row = conn.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,)).fetchone()
    conn.close()
    return _parse_profile_row(row)


def delete_profile(profile_id: str) -> bool:
    """Delete a profile and all its linked accounts."""
    conn = get_db()
    # Delete linked accounts first
    conn.execute("DELETE FROM utility_accounts WHERE profile_id = ?", (profile_id,))
    cursor = conn.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))
    conn.commit()
    conn.close()
    return cursor.rowcount > 0


def create_account(profile_id: str, service_type: str, consumer_id: str, 
                   label: str = None, number_plate: str = None) -> dict:
    """Create a utility account linked to a profile."""
    conn = get_db()
    account_id = str(uuid.uuid4())
    conn.execute(
        """INSERT INTO utility_accounts (id, profile_id, service_type, consumer_id, label, number_plate) 
           VALUES (?, ?, ?, ?, ?, ?)""",
        (account_id, profile_id, service_type, consumer_id, label, number_plate)
    )
    conn.commit()
    row = conn.execute("SELECT * FROM utility_accounts WHERE id = ?", (account_id,)).fetchone()
    conn.close()
    return _parse_account_row(row)


def get_profile_accounts(profile_id: str) -> list:
    """Get all accounts linked to a profile."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM utility_accounts WHERE profile_id = ?", 
        (profile_id,)
    ).fetchall()
    conn.close()
    return [_parse_account_row(row) for row in rows]


def delete_account(account_id: str) -> bool:
    """Delete a utility account."""
    conn = get_db()
    cursor = conn.execute("DELETE FROM utility_accounts WHERE id = ?", (account_id,))
    conn.commit()
    conn.close()
    return cursor.rowcount > 0


def _parse_profile_row(row) -> dict | None:
    """Parse a profile row and include its accounts."""
    if not row:
        return None
    profile = dict(row)
    # Get accounts for this profile
    profile["accounts"] = get_profile_accounts(profile["id"])
    return profile


def _parse_account_row(row) -> dict | None:
    """Parse an account row."""
    if not row:
        return None
    return dict(row)


# Auto-initialise on import
init_db()
