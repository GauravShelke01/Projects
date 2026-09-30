"""
====================================================================
  view_database.py  --  View the database contents in the terminal
====================================================================

  How to run (inside the project folder):

      py view_database.py              -> everything
      py view_database.py users        -> registered accounts
      py view_database.py logs         -> email logs
      py view_database.py schedules    -> scheduled emails
      py view_database.py stats        -> summary statistics
      py view_database.py schema       -> table structure

  This file only READS data. It never deletes anything.
====================================================================
"""

import os
import sqlite3
import sys

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "email_automation.db")


def print_table(rows, headers, max_width=40):
    if not rows:
        print("   (no records found)\n")
        return

    data = [[str(c) if c is not None else "" for c in row] for row in rows]
    data = [[(c[:max_width - 1] + "~") if len(c) > max_width else c for c in row]
            for row in data]

    widths = [len(h) for h in headers]
    for row in data:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    line = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    print(line)
    print("| " + " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers)) + " |")
    print(line)
    for row in data:
        print("| " + " | ".join(row[i].ljust(widths[i]) for i in range(len(headers))) + " |")
    print(line)
    print(f"   Total rows: {len(data)}\n")


def connect():
    if not os.path.exists(DB):
        print("\nDatabase file not found:", DB)
        print("Run 'py app.py' once and create an account first.\n")
        sys.exit(1)
    return sqlite3.connect(DB)


def show_users(conn):
    print("=" * 78)
    print("  TABLE: users   (registered accounts and their sender settings)")
    print("=" * 78)
    print("  Note: login passwords are stored as one way hashes and are never shown.")
    print()
    rows = conn.execute(
        "SELECT id, name, email, sender_email, smtp_server, smtp_port, created_at "
        "FROM users ORDER BY id").fetchall()
    print_table(rows, ["ID", "NAME", "LOGIN EMAIL", "SENDER EMAIL",
                       "SMTP SERVER", "PORT", "CREATED AT"])


def show_logs(conn, limit=50):
    print("=" * 78)
    print(f"  TABLE: logs   (last {limit} emails)")
    print("=" * 78)
    rows = conn.execute(
        "SELECT l.id, u.email, l.name, l.email, l.status, l.created_at "
        "FROM logs l LEFT JOIN users u ON u.id = l.user_id "
        "ORDER BY l.id DESC LIMIT ?", (limit,)).fetchall()
    print_table(rows, ["ID", "ACCOUNT", "NAME", "RECIPIENT", "STATUS", "DATE AND TIME"])


def show_schedules(conn):
    print("=" * 78)
    print("  TABLE: schedules   (emails queued for later)")
    print("=" * 78)
    rows = conn.execute(
        "SELECT s.id, u.email, s.subject, s.csv_file, s.run_at, s.repeat_type, s.status "
        "FROM schedules s LEFT JOIN users u ON u.id = s.user_id "
        "ORDER BY s.id DESC").fetchall()
    print_table(rows, ["ID", "ACCOUNT", "SUBJECT", "FILE", "RUN AT", "REPEAT", "STATUS"])


def show_stats(conn):
    print("=" * 78)
    print("  STATISTICS")
    print("=" * 78)
    q = lambda sql: conn.execute(sql).fetchone()[0]

    users   = q("SELECT COUNT(*) FROM users")
    total   = q("SELECT COUNT(*) FROM logs")
    sent    = q("SELECT COUNT(*) FROM logs WHERE status='Sent'")
    failed  = q("SELECT COUNT(*) FROM logs WHERE status='Failed'")
    pending = q("SELECT COUNT(*) FROM schedules WHERE status='Pending'")
    pct = lambda x: f"{(x / total * 100):.1f}%" if total else "0.0%"

    print(f"   Registered users    : {users}")
    print(f"   Total emails logged : {total}")
    print(f"   Delivered (Sent)    : {sent}   ({pct(sent)})")
    print(f"   Failed              : {failed}   ({pct(failed)})")
    print(f"   Pending schedules   : {pending}\n")

    print("   --- Emails per account ---")
    print_table(conn.execute(
        "SELECT u.email, COUNT(l.id) FROM users u LEFT JOIN logs l ON l.user_id = u.id "
        "GROUP BY u.id ORDER BY COUNT(l.id) DESC").fetchall(),
        ["ACCOUNT", "EMAILS SENT"])


def show_schema(conn):
    print("=" * 78)
    print("  DATABASE SCHEMA")
    print("=" * 78)
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%'").fetchall()
    for (t,) in tables:
        print(f"\n   TABLE: {t}")
        cols = conn.execute(f"PRAGMA table_info({t})").fetchall()
        print_table([(c[0], c[1], c[2], "YES" if c[3] else "NO",
                      "YES" if c[5] else "NO") for c in cols],
                    ["#", "COLUMN NAME", "DATA TYPE", "NOT NULL", "PRIMARY KEY"])


if __name__ == "__main__":
    conn = connect()
    what = sys.argv[1].lower() if len(sys.argv) > 1 else "all"
    print(f"\nDatabase file: {DB}\n")

    if what.startswith("user"):
        show_users(conn)
    elif what.startswith("log"):
        show_logs(conn, 100)
    elif what.startswith("sched"):
        show_schedules(conn)
    elif what.startswith("stat"):
        show_stats(conn)
    elif what == "schema":
        show_schema(conn)
    else:
        show_stats(conn)
        show_users(conn)
        show_logs(conn, 20)
        show_schedules(conn)
        print("Tip: run 'py view_database.py schema' to see the table structure.\n")

    conn.close()
