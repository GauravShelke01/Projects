"""
core/mailer.py
--------------
Sends REAL emails through an SMTP server using Python's smtplib.

Each logged-in user stores their own sender email and app password in
the Settings page, so every email is sent from that user's own account.

Jinja2 replaces the placeholders such as {{name}} and {{city}} with the
real values coming from the CSV / Excel row.
"""

import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from jinja2 import Template

import config
from core import database
from core.reader import load_recipients


# ------------------------------------------------------------------
#  1. Personalisation with Jinja2
# ------------------------------------------------------------------
def render_text(template_string, data):
    try:
        return Template(template_string).render(**data)
    except Exception:
        return template_string


def to_html(text):
    body = text.replace("\n", "<br>")
    return (f'<html><body style="font-family:Arial,Helvetica,sans-serif;'
            f'font-size:15px;color:#222;line-height:1.6">{body}'
            f'<hr style="border:none;border-top:1px solid #e5e7eb;margin:22px 0">'
            f'<p style="font-size:12px;color:#888">Sent using the Python '
            f'Email Automation System</p></body></html>')


# ------------------------------------------------------------------
#  2. SMTP connection
# ------------------------------------------------------------------
def open_connection(user):
    """
    Opens a real SMTP connection with the user's saved settings.
    Returns (server, None) or (None, 'error message').
    """
    sender   = (user.get("sender_email") or "").strip()
    password = database.decode_password(user.get("sender_password") or "")
    host     = (user.get("smtp_server") or config.DEFAULT_SMTP_SERVER).strip()
    port     = int(user.get("smtp_port") or config.DEFAULT_SMTP_PORT)

    if not sender:
        return None, ("No sender email configured. Open Settings and add the "
                      "email address you want to send from.")

    try:
        if port == 465:
            server = smtplib.SMTP_SSL(host, port, timeout=25)
        else:
            server = smtplib.SMTP(host, port, timeout=25)
            server.ehlo()
            if server.has_extn("starttls"):
                server.starttls()
                server.ehlo()
        # Log in only when the server actually asks for authentication.
        # (Gmail, Outlook and Yahoo all do.)
        if password and server.has_extn("auth"):
            server.login(sender, password)
        return server, None

    except smtplib.SMTPAuthenticationError:
        return None, ("Login failed. Check the sender email and the 16 digit "
                      "app password in Settings.")
    except Exception as e:
        return None, f"Could not connect to {host}:{port} - {e}"


def send_one(server, user, to_email, subject, body):
    """Sends a single message over an already open connection."""
    sender = user["sender_email"]
    name   = user.get("sender_name") or sender

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{name} <{sender}>"
    msg["To"] = to_email
    msg.attach(MIMEText(body, "plain"))
    msg.attach(MIMEText(to_html(body), "html"))

    server.sendmail(sender, to_email, msg.as_string())


# ------------------------------------------------------------------
#  3. Single email
# ------------------------------------------------------------------
def send_single(user, to_email, subject, body):
    """Sends one email to one address. Returns (True/False, message)."""
    server, error = open_connection(user)
    if error:
        database.add_log(user["id"], "", to_email, subject, "Failed", error)
        return False, error

    try:
        send_one(server, user, to_email, subject, body)
        database.add_log(user["id"], "", to_email, subject, "Sent",
                         "Email delivered to the SMTP server")
        return True, f"Email sent successfully to {to_email}"
    except Exception as e:
        database.add_log(user["id"], "", to_email, subject, "Failed", str(e))
        return False, f"Failed to send: {e}"
    finally:
        try:
            server.quit()
        except Exception:
            pass


# ------------------------------------------------------------------
#  4. Bulk email from a CSV / Excel file
# ------------------------------------------------------------------
def send_bulk(user, filename, subject_template, body_template):
    """Sends a personalised email to every recipient in the file."""
    recipients, error = load_recipients(filename)
    if error:
        return {"success": False, "error": error, "sent": 0, "failed": 0, "skipped": 0}

    server, error = open_connection(user)
    if error:
        return {"success": False, "error": error, "sent": 0, "failed": 0, "skipped": 0}

    sent = failed = skipped = 0
    try:
        for r in recipients:
            email = r["email"]

            if not r["_valid"]:
                skipped += 1
                database.add_log(user["id"], r.get("name", ""), email,
                                 subject_template, "Failed",
                                 "Invalid email address, skipped")
                continue

            data    = {k: v for k, v in r.items() if not k.startswith("_")}
            subject = render_text(subject_template, data)
            body    = render_text(body_template, data)

            try:
                send_one(server, user, email, subject, body)
                sent += 1
                database.add_log(user["id"], r.get("name", ""), email, subject,
                                 "Sent", "Email delivered to the SMTP server")
            except Exception as e:
                failed += 1
                database.add_log(user["id"], r.get("name", ""), email, subject,
                                 "Failed", str(e))

            time.sleep(config.SEND_DELAY)
    finally:
        try:
            server.quit()
        except Exception:
            pass

    return {"success": True, "error": None, "total": len(recipients),
            "sent": sent, "failed": failed, "skipped": skipped}
