import pymysql

from app.classifier import build_normalized, classify, fingerprint
from app.config import Config
from app.db import get_connection
from app.validators import validate_record

FIELDS = ("full_name", "email", "phone", "city")


def clean_input(data):
    """Keep only known fields and turn each into a stripped string."""
    data = data if isinstance(data, dict) else {}
    out = {}
    for f in FIELDS:
        v = data.get(f)
        out[f] = "" if v is None else str(v).strip()
    return out


def _log(cur, record, result):
    # Every submission is logged, whatever the verdict (prepared statement: %s)
    cur.execute(
        "INSERT INTO audit_log (submitted_name, submitted_email, submitted_phone, submitted_city,"
        " verdict, reason, matched_record_id) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (record["full_name"][:255], record["email"][:255], record["phone"][:255], record["city"][:255],
         result["verdict"], result["reason"][:255], result["matched_record_id"]),
    )


def submit_record(data):
    record = clean_input(data)
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            norm = build_normalized(record)
            existing = []
            # Only look in the database if the data is valid (saves a query)
            if not validate_record(record):
                cur.execute(
                    "SELECT id, full_name, email_norm, phone_norm FROM records"
                    " WHERE email_norm = %s OR phone_norm = %s",
                    (norm["email_norm"], norm["phone_norm"]),
                )
                existing = cur.fetchall()

            result = classify(record, existing, Config.NAME_SIMILARITY_THRESHOLD)

            if result["verdict"] == "UNIQUE":
                try:
                    cur.execute(
                        "INSERT INTO records (full_name, email, email_norm, phone, phone_norm, city, fingerprint)"
                        " VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        (record["full_name"], record["email"], norm["email_norm"], record["phone"],
                         norm["phone_norm"], record["city"] or None, fingerprint(norm)),
                    )
                    result["record_id"] = cur.lastrowid
                except pymysql.err.IntegrityError:
                    # Race condition: another request inserted the same person a moment ago.
                    # The database UNIQUE key is our last safety net.
                    conn.rollback()
                    cur.execute(
                        "SELECT id FROM records WHERE email_norm = %s OR fingerprint = %s LIMIT 1",
                        (norm["email_norm"], fingerprint(norm)),
                    )
                    row = cur.fetchone()
                    result["verdict"] = "REDUNDANT"
                    result["reason"] = "blocked by database UNIQUE constraint (simultaneous duplicate)"
                    result["matched_record_id"] = row["id"] if row else None

            _log(cur, record, result)
            conn.commit()   # insert + audit log succeed or fail together
        return result
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def list_records(limit=50):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, full_name, email, phone, city, created_at FROM records"
                        " ORDER BY id DESC LIMIT %s", (limit,))
            return cur.fetchall()
    finally:
        conn.close()


def list_audit(limit=20):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, submitted_name, submitted_email, verdict, reason, matched_record_id,"
                        " created_at FROM audit_log ORDER BY id DESC LIMIT %s", (limit,))
            return cur.fetchall()
    finally:
        conn.close()


def get_stats():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT verdict, COUNT(*) AS n FROM audit_log GROUP BY verdict")
            counts = {"UNIQUE": 0, "REDUNDANT": 0, "FALSE_POSITIVE": 0}
            for row in cur.fetchall():
                counts[row["verdict"]] = row["n"]
            cur.execute("SELECT COUNT(*) AS n FROM records")
            counts["stored_records"] = cur.fetchone()["n"]
            return counts
    finally:
        conn.close()


def db_is_up():
    try:
        conn = get_connection()
        conn.close()
        return True
    except Exception:
        return False