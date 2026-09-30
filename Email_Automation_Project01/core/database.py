"""
core/database.py
----------------
All SQLite database work. Three tables:

  1) users      -> signup / login accounts + their SMTP settings
  2) logs       -> every email that was sent (per user)
  3) schedules  -> emails queued for a future date and time (per user)

Every log and schedule row stores a user_id, so one user can never
see another user's data.
"""

import base64
import hashlib
import sqlite3
from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from config import DATABASE, SECRET_KEY


# ------------------------------------------------------------------
#  Connection
# ------------------------------------------------------------------
def get_connection():
    conn = sqlite3.connect(DATABASE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Creates the tables if they do not exist yet."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            email           TEXT NOT NULL UNIQUE,
            password_hash   TEXT NOT NULL,
            sender_email    TEXT DEFAULT '',
            sender_password TEXT DEFAULT '',
            sender_name     TEXT DEFAULT '',
            smtp_server     TEXT DEFAULT 'smtp.gmail.com',
            smtp_port       INTEGER DEFAULT 587,
            created_at      TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            name       TEXT,
            email      TEXT NOT NULL,
            subject    TEXT,
            status     TEXT NOT NULL,
            message    TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS schedules (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            subject     TEXT,
            body        TEXT,
            csv_file    TEXT,
            run_at      TEXT NOT NULL,
            repeat_type TEXT DEFAULT 'once',
            status      TEXT DEFAULT 'Pending',
            created_at  TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    conn.commit()
    conn.close()


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ------------------------------------------------------------------
#  App password encoding
#  The SMTP app password must be readable again to send mail, so it
#  cannot be hashed. It is encoded with the secret key instead.
# ------------------------------------------------------------------
def _key_stream(length):
    key = hashlib.sha256(SECRET_KEY.encode()).digest()
    return (key * (length // len(key) + 1))[:length]


def encode_password(plain):
    if not plain:
        return ""
    raw = plain.encode()
    mixed = bytes(a ^ b for a, b in zip(raw, _key_stream(len(raw))))
    return base64.b64encode(mixed).decode()


def decode_password(stored):
    if not stored:
        return ""
    try:
        mixed = base64.b64decode(stored.encode())
        return bytes(a ^ b for a, b in zip(mixed, _key_stream(len(mixed)))).decode()
    except Exception:
        return ""


# ------------------------------------------------------------------
#  USERS  (signup / login)
# ------------------------------------------------------------------
def create_user(name, email, password):
    """Returns (user_id, None) on success or (None, 'error message')."""
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash, sender_name, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (name, email.lower(), generate_password_hash(password), name, _now()),
        )
        conn.commit()
        return cur.lastrowid, None
    except sqlite3.IntegrityError:
        return None, "An account with this email already exists."
    finally:
        conn.close()


def verify_user(email, password):
    """Checks the login details. Returns the user row or None."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE email = ?",
                       (email.lower(),)).fetchone()
    conn.close()
    if row and check_password_hash(row["password_hash"], password):
        return dict(row)
    return None


def get_user(user_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_sender_settings(user_id, sender_name, sender_email,
                           sender_password, smtp_server, smtp_port):
    """Saves the user's own email account used for sending."""
    conn = get_connection()
    if sender_password:
        conn.execute(
            "UPDATE users SET sender_name=?, sender_email=?, sender_password=?, "
            "smtp_server=?, smtp_port=? WHERE id=?",
            (sender_name, sender_email, encode_password(sender_password),
             smtp_server, smtp_port, user_id))
    else:
        conn.execute(
            "UPDATE users SET sender_name=?, sender_email=?, smtp_server=?, "
            "smtp_port=? WHERE id=?",
            (sender_name, sender_email, smtp_server, smtp_port, user_id))
    conn.commit()
    conn.close()


def change_password(user_id, new_password):
    conn = get_connection()
    conn.execute("UPDATE users SET password_hash=? WHERE id=?",
                 (generate_password_hash(new_password), user_id))
    conn.commit()
    conn.close()


# ------------------------------------------------------------------
#  LOGS
# ------------------------------------------------------------------
def add_log(user_id, name, email, subject, status, message=""):
    conn = get_connection()
    conn.execute(
        "INSERT INTO logs (user_id, name, email, subject, status, message, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user_id, name, email, subject, status, message, _now()))
    conn.commit()
    conn.close()


def get_logs(user_id, limit=300, status_filter="All", search=""):
    sql = "SELECT * FROM logs WHERE user_id = ?"
    params = [user_id]
    if status_filter and status_filter != "All":
        sql += " AND status = ?"
        params.append(status_filter)
    if search:
        sql += " AND (email LIKE ? OR name LIKE ?)"
        params += [f"%{search}%", f"%{search}%"]
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    conn = get_connection()
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def clear_logs(user_id):
    conn = get_connection()
    conn.execute("DELETE FROM logs WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def get_stats(user_id):
    """Numbers shown on the four dashboard cards."""
    conn = get_connection()
    one = lambda sql: conn.execute(sql, (user_id,)).fetchone()["c"]
    total   = one("SELECT COUNT(*) c FROM logs WHERE user_id=?")
    sent    = one("SELECT COUNT(*) c FROM logs WHERE user_id=? AND status='Sent'")
    failed  = one("SELECT COUNT(*) c FROM logs WHERE user_id=? AND status='Failed'")
    pending = one("SELECT COUNT(*) c FROM schedules WHERE user_id=? AND status='Pending'")
    conn.close()

    pct = lambda x: round((x / total) * 100, 1) if total else 0.0
    return {"total": total, "delivered": sent, "failed": failed, "pending": pending,
            "delivered_pct": pct(sent), "failed_pct": pct(failed)}


# ------------------------------------------------------------------
#  SCHEDULES
# ------------------------------------------------------------------
def add_schedule(user_id, subject, body, csv_file, run_at, repeat_type="once"):
    conn = get_connection()
    conn.execute(
        "INSERT INTO schedules (user_id, subject, body, csv_file, run_at, "
        "repeat_type, status, created_at) VALUES (?, ?, ?, ?, ?, ?, 'Pending', ?)",
        (user_id, subject, body, csv_file, run_at, repeat_type, _now()))
    conn.commit()
    conn.close()


def get_schedules(user_id):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM schedules WHERE user_id=? ORDER BY id DESC",
                        (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_pending_schedules():
    """Used by the background scheduler (all users)."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM schedules WHERE status='Pending'").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_schedule(schedule_id, status=None, run_at=None):
    conn = get_connection()
    if status:
        conn.execute("UPDATE schedules SET status=? WHERE id=?", (status, schedule_id))
    if run_at:
        conn.execute("UPDATE schedules SET run_at=? WHERE id=?", (run_at, schedule_id))
    conn.commit()
    conn.close()


def delete_schedule(user_id, schedule_id):
    conn = get_connection()
    conn.execute("DELETE FROM schedules WHERE id=? AND user_id=?",
                 (schedule_id, user_id))
    conn.commit()
    conn.close()
