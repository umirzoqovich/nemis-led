import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_PATH = "crm_leads.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Leads table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        phone TEXT NOT NULL,
        course TEXT,
        source TEXT DEFAULT 'Instagram Ads',
        ad_name TEXT,
        status TEXT DEFAULT 'NEW',
        notes TEXT DEFAULT '',
        assigned_to TEXT DEFAULT '',
        telegram_message_id INTEGER DEFAULT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Status change history logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS lead_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_id INTEGER NOT NULL,
        old_status TEXT,
        new_status TEXT,
        changed_by TEXT,
        note TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (lead_id) REFERENCES leads (id)
    )
    """)

    # Safe Schema Migrations (trial_date, cancel_reason)
    cursor.execute("PRAGMA table_info(leads)")
    existing_cols = [c[1] for c in cursor.fetchall()]
    if "trial_date" not in existing_cols:
        cursor.execute("ALTER TABLE leads ADD COLUMN trial_date TEXT DEFAULT NULL")
    if "cancel_reason" not in existing_cols:
        cursor.execute("ALTER TABLE leads ADD COLUMN cancel_reason TEXT DEFAULT NULL")

    conn.commit()
    conn.close()

def create_lead(
    full_name: str,
    phone: str,
    course: Optional[str] = "Umumiy",
    source: Optional[str] = "Instagram Ads",
    ad_name: Optional[str] = None,
    notes: Optional[str] = ""
) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    clean_phone = "".join(filter(str.isdigit, phone))

    # Smart Duplicate Check: Is this student already in DB with the same phone?
    cursor.execute("""
        SELECT id, full_name, status, notes FROM leads 
        WHERE REPLACE(REPLACE(REPLACE(phone, ' ', ''), '-', ''), '+', '') LIKE ?
        ORDER BY id DESC LIMIT 1
    """, (f"%{clean_phone[-9:] if len(clean_phone) >= 9 else clean_phone}%",))
    existing = cursor.fetchone()

    if existing:
        # Existing student re-applied from Target Ad (Hot Lead!)
        lead_id = existing["id"]
        old_note = existing["notes"] or ""
        updated_note = f"{old_note}\n[⚡ {now} - QAYTA MUROJAAT]: Targetdan yana ariza qoldirdi ({course}). {notes}".strip()
        cursor.execute("""
            UPDATE leads 
            SET notes = ?, status = 'NEW', updated_at = ?
            WHERE id = ?
        """, (updated_note, now, lead_id))
        
        cursor.execute("""
            INSERT INTO lead_logs (lead_id, old_status, new_status, changed_by, note, created_at)
            VALUES (?, ?, 'NEW', 'System', 'Qayta murojaat: O''quvchi targetdan 2-marta ariza qoldirdi', ?)
        """, (lead_id, existing["status"], now))
        conn.commit()
        lead = get_lead_by_id(lead_id)
        lead["is_reapplied"] = True
        conn.close()
        return lead

    # New unique lead
    cursor.execute("""
        INSERT INTO leads (full_name, phone, course, source, ad_name, status, notes, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, 'NEW', ?, ?, ?)
    """, (full_name.strip(), phone.strip(), course or "Umumiy", source or "Instagram Ads", ad_name or "Target kampaniya", notes or "", now, now))
    lead_id = cursor.lastrowid
    
    # Log initial creation
    cursor.execute("""
        INSERT INTO lead_logs (lead_id, old_status, new_status, changed_by, note, created_at)
        VALUES (?, NULL, 'NEW', 'System', 'Target orqali yangi lid yaratildi', ?)
    """, (lead_id, now))
    
    conn.commit()
    lead = get_lead_by_id(lead_id)
    lead["is_reapplied"] = False
    conn.close()
    return lead

def get_lead_by_id(lead_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def update_lead_status(
    lead_id: int,
    new_status: str,
    changed_by: str = "Admin",
    note: Optional[str] = None,
    trial_date: Optional[str] = None,
    cancel_reason: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    lead = get_lead_by_id(lead_id)
    if not lead:
        conn.close()
        return None
    
    old_status = lead["status"]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Build update fields
    updates = ["status = ?", "assigned_to = ?", "updated_at = ?"]
    params = [new_status, changed_by, now]

    if trial_date is not None:
        updates.append("trial_date = ?")
        params.append(trial_date)
    if cancel_reason is not None:
        updates.append("cancel_reason = ?")
        params.append(cancel_reason)

    params.append(lead_id)
    sql = f"UPDATE leads SET {', '.join(updates)} WHERE id = ?"
    cursor.execute(sql, tuple(params))
    
    log_note = note or f"Status {new_status} ga o'zgartirildi"
    if trial_date:
        log_note += f" (Sinov darsi: {trial_date})"
    if cancel_reason:
        log_note += f" (Rad etish sababi: {cancel_reason})"

    cursor.execute("""
        INSERT INTO lead_logs (lead_id, old_status, new_status, changed_by, note, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (lead_id, old_status, new_status, changed_by, log_note, now))
    
    conn.commit()
    updated = get_lead_by_id(lead_id)
    conn.close()
    return updated

def update_lead_telegram_msg_id(lead_id: int, message_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE leads SET telegram_message_id = ? WHERE id = ?", (message_id, lead_id))
    conn.commit()
    conn.close()

def add_lead_note(lead_id: int, note: str, author: str = "Admin") -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO lead_logs (lead_id, old_status, new_status, changed_by, note, created_at)
        VALUES (?, NULL, NULL, ?, ?, ?)
    """, (lead_id, author, note, now))
    
    # Update notes in leads table
    cursor.execute("SELECT notes FROM leads WHERE id = ?", (lead_id,))
    row = cursor.fetchone()
    old_note = row[0] if row and row[0] else ""
    combined_notes = f"{old_note}\n[{now} - {author}]: {note}".strip()
    cursor.execute("UPDATE leads SET notes = ?, updated_at = ? WHERE id = ?", (combined_notes, now, lead_id))
    
    conn.commit()
    conn.close()
    return get_lead_by_id(lead_id)

def get_lead_timeline(lead_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM lead_logs WHERE lead_id = ? ORDER BY id DESC", (lead_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_all_leads(
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:

    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM leads WHERE 1=1"
    params = []

    if status and status != "ALL":
        query += " AND status = ?"
        params.append(status)

    if search:
        query += " AND (full_name LIKE ? OR phone LIKE ? OR course LIKE ?)"
        s = f"%{search}%"
        params.extend([s, s, s])

    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_lead_stats() -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM leads")
    total = cursor.fetchone()[0]
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("SELECT COUNT(*) FROM leads WHERE created_at LIKE ?", (f"{today_str}%",))
    today_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT status, COUNT(*) FROM leads GROUP BY status")
    status_counts = dict(cursor.fetchall())
    
    cursor.execute("SELECT course, COUNT(*) FROM leads GROUP BY course ORDER BY COUNT(*) DESC LIMIT 5")
    course_counts = dict(cursor.fetchall())
    
    conn.close()
    
    new_count = status_counts.get("NEW", 0)
    contacted_count = status_counts.get("CONTACTED", 0)
    trial_count = status_counts.get("TRIAL_SCHEDULED", 0) + status_counts.get("TRIAL_ATTENDED", 0)
    paid_count = status_counts.get("PAID", 0)
    cancelled_count = status_counts.get("CANCELLED", 0)
    
    conversion = round((paid_count / total * 100), 1) if total > 0 else 0.0

    return {
        "total": total,
        "today": today_count,
        "new": new_count,
        "contacted": contacted_count,
        "trial": trial_count,
        "paid": paid_count,
        "cancelled": cancelled_count,
        "conversion": conversion,
        "by_status": status_counts,
        "by_course": course_counts
    }

