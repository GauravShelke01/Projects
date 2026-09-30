"""
====================================================================
  app.py  --  EMAIL AUTOMATION SYSTEM  (Flask backend)
====================================================================
  Run     :  py app.py       ->  http://127.0.0.1:5000
  Languages used : Python (backend) + HTML/CSS (frontend). No JavaScript.
====================================================================
"""

import csv
import io
import os
from datetime import datetime, timedelta
from functools import wraps

from flask import (Flask, flash, g, redirect, render_template, request,
                   send_file, session, url_for)
from werkzeug.utils import secure_filename

import config
from core import database
from core.mailer import render_text, send_bulk, send_single
from core.reader import get_summary, list_files, load_recipients
from core.scheduler import start_scheduler

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
app.permanent_session_lifetime = timedelta(days=config.SESSION_DAYS)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024        # 8 MB upload limit

os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(config.DATA_FOLDER, exist_ok=True)
database.init_db()

if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or __name__ != "__main__":
    start_scheduler()


# ==================================================================
#  AUTHENTICATION HELPERS
# ==================================================================
def login_required(view):
    """Pages wrapped with this can only be opened after logging in."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not g.user:
            flash("Please log in to continue.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapper


@app.before_request
def load_logged_in_user():
    """Runs before every request and loads the user from the session cookie."""
    user_id = session.get("user_id")
    g.user = database.get_user(user_id) if user_id else None


@app.context_processor
def inject_globals():
    return {"user": g.get("user"), "year": datetime.now().year}


def allowed_file(filename):
    return "." in filename and \
        filename.rsplit(".", 1)[1].lower() in config.ALLOWED_EXTENSIONS


# ==================================================================
#  MODULE 1 : SIGN UP / LOGIN / LOGOUT
# ==================================================================
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if g.user:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name    = request.form.get("name", "").strip()
        email   = request.form.get("email", "").strip()
        pwd     = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        if not name or not email or not pwd:
            flash("Please fill in all the fields.", "error")
        elif len(pwd) < 6:
            flash("Password must be at least 6 characters long.", "error")
        elif pwd != confirm:
            flash("The two passwords do not match.", "error")
        else:
            user_id, error = database.create_user(name, email, pwd)
            if error:
                flash(error, "error")
            else:
                session.permanent = True
                session["user_id"] = user_id
                flash(f"Welcome {name}! Your account has been created.", "success")
                return redirect(url_for("settings_page"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if g.user:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        pwd   = request.form.get("password", "")
        user  = database.verify_user(email, pwd)

        if user:
            # Permanent session = the browser stays logged in next time
            session.permanent = True
            session["user_id"] = user["id"]
            flash(f"Welcome back, {user['name']}!", "success")
            return redirect(url_for("dashboard"))
        flash("Wrong email or password.", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


# ==================================================================
#  MODULE 2 : DASHBOARD
# ==================================================================
@app.route("/")
@login_required
def dashboard():
    stats = database.get_stats(g.user["id"])
    logs = database.get_logs(g.user["id"], limit=8)
    pending = [s for s in database.get_schedules(g.user["id"])
               if s["status"] == "Pending"][:5]
    return render_template("dashboard.html", stats=stats, logs=logs,
                           schedules=pending, active="dashboard")


# ==================================================================
#  MODULE 3 : COMPOSE  (bulk send + single send + preview)
# ==================================================================
@app.route("/compose", methods=["GET", "POST"])
@login_required
def compose():
    files    = list_files()
    selected = request.values.get("csv_file") or request.values.get("file") or \
        ("demo_recipients.csv" if "demo_recipients.csv" in files
         else (files[0] if files else ""))
    subject = request.form.get("subject", config.DEFAULT_SUBJECT)
    body    = request.form.get("body", config.DEFAULT_BODY)
    preview = None

    if request.method == "POST":
        action = request.form.get("action", "")

        # ---- Preview using the first recipient in the file ----
        if action == "preview":
            recipients, error = load_recipients(selected)
            if error or not recipients:
                flash(error or "The selected file has no rows.", "error")
            else:
                data = {k: v for k, v in recipients[0].items()
                        if not k.startswith("_")}
                preview = {"to": data.get("email", "-"),
                           "subject": render_text(subject, data),
                           "body": render_text(body, data)}

        # ---- Send to everybody in the file ----
        elif action == "send":
            if not selected:
                flash("Please choose a recipient file first.", "error")
            elif not subject.strip() or not body.strip():
                flash("Subject and message are both required.", "error")
            else:
                result = send_bulk(g.user, selected, subject, body)
                if not result["success"]:
                    flash(result["error"], "error")
                else:
                    flash(f"Finished. Sent: {result['sent']}, "
                          f"Failed: {result['failed']}, "
                          f"Skipped invalid: {result['skipped']}.",
                          "success" if result["sent"] else "error")
                    return redirect(url_for("logs_page"))

    summary = get_summary(selected) if selected else None
    return render_template("compose.html", files=files, selected=selected,
                           summary=summary, subject=subject, body=body,
                           preview=preview, active="compose")


@app.route("/send-single", methods=["POST"])
@login_required
def send_single_email():
    """Single email form that sits under the recipients file panel."""
    to_email = request.form.get("to_email", "").strip()
    subject  = request.form.get("single_subject", "").strip()
    body     = request.form.get("single_body", "").strip()
    back     = request.form.get("back", "compose")

    if not to_email or not subject or not body:
        flash("Recipient, subject and message are all required.", "error")
    else:
        ok, message = send_single(g.user, to_email, subject, body)
        flash(message, "success" if ok else "error")

    return redirect(url_for(back))


# ==================================================================
#  MODULE 4 : RECIPIENTS  (CSV + Excel upload)
# ==================================================================
@app.route("/recipients")
@login_required
def recipients_page():
    files = list_files()
    selected = request.args.get("file") or (files[0] if files else "")
    rows, error = load_recipients(selected) if selected else ([], None)
    summary = get_summary(selected) if selected else None
    return render_template("recipients.html", files=files, selected=selected,
                           rows=rows, error=error, summary=summary,
                           active="recipients")


@app.route("/upload", methods=["POST"])
@login_required
def upload_file():
    file = request.files.get("datafile")
    if not file or file.filename == "":
        flash("No file was selected.", "error")
        return redirect(url_for("recipients_page"))

    if not allowed_file(file.filename):
        flash("Only .csv, .xlsx and .xls files are allowed.", "error")
        return redirect(url_for("recipients_page"))

    filename = secure_filename(file.filename)
    file.save(os.path.join(config.UPLOAD_FOLDER, filename))
    flash(f"'{filename}' was uploaded successfully.", "success")
    return redirect(url_for("recipients_page", file=filename))


# ==================================================================
#  MODULE 5 : SCHEDULE
# ==================================================================
@app.route("/schedule", methods=["GET", "POST"])
@login_required
def schedule_page():
    if request.method == "POST":
        subject  = request.form.get("subject", "").strip()
        body     = request.form.get("body", "").strip()
        csv_file = request.form.get("csv_file", "")
        run_at   = request.form.get("run_at", "").replace("T", " ")[:16]
        repeat   = request.form.get("repeat_type", "once")

        if not (subject and body and csv_file and run_at):
            flash("All fields are required.", "error")
        else:
            database.add_schedule(g.user["id"], subject, body, csv_file,
                                  run_at, repeat)
            flash(f"Email scheduled for {run_at}.", "success")
        return redirect(url_for("schedule_page"))

    return render_template("schedule.html", files=list_files(),
                           schedules=database.get_schedules(g.user["id"]),
                           default_subject=config.DEFAULT_SUBJECT,
                           default_body=config.DEFAULT_BODY, active="schedule")


@app.route("/schedule/delete/<int:sid>")
@login_required
def schedule_delete(sid):
    database.delete_schedule(g.user["id"], sid)
    flash("Schedule deleted.", "success")
    return redirect(url_for("schedule_page"))


# ==================================================================
#  MODULE 6 : LOGS
# ==================================================================
@app.route("/logs")
@login_required
def logs_page():
    status = request.args.get("status", "All")
    search = request.args.get("search", "").strip()
    logs = database.get_logs(g.user["id"], 300, status, search)
    return render_template("logs.html", logs=logs,
                           stats=database.get_stats(g.user["id"]),
                           status=status, search=search, active="logs")


@app.route("/logs/clear")
@login_required
def logs_clear():
    database.clear_logs(g.user["id"])
    flash("All logs were cleared.", "success")
    return redirect(url_for("logs_page"))


@app.route("/logs/export")
@login_required
def logs_export():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Name", "Email", "Subject", "Status", "Message", "Date and Time"])
    for log in database.get_logs(g.user["id"], 5000):
        writer.writerow([log["id"], log["name"], log["email"], log["subject"],
                         log["status"], log["message"], log["created_at"]])
    return send_file(io.BytesIO(output.getvalue().encode()), mimetype="text/csv",
                     as_attachment=True, download_name="email_logs.csv")


# ==================================================================
#  MODULE 7 : SETTINGS  (the user adds their own sending email here)
# ==================================================================
@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings_page():
    if request.method == "POST":
        database.update_sender_settings(
            g.user["id"],
            request.form.get("sender_name", "").strip(),
            request.form.get("sender_email", "").strip(),
            request.form.get("sender_password", "").strip(),
            request.form.get("smtp_server", config.DEFAULT_SMTP_SERVER).strip(),
            int(request.form.get("smtp_port") or config.DEFAULT_SMTP_PORT))
        flash("Sender settings saved. Your emails will now be sent from this address.",
              "success")
        return redirect(url_for("settings_page"))

    return render_template("settings.html", cfg=config, active="settings")


@app.route("/settings/password", methods=["POST"])
@login_required
def change_password():
    new = request.form.get("new_password", "")
    if len(new) < 6:
        flash("Password must be at least 6 characters long.", "error")
    else:
        database.change_password(g.user["id"], new)
        flash("Account password updated.", "success")
    return redirect(url_for("settings_page"))


# ==================================================================
if __name__ == "__main__":
    print("=" * 62)
    print("  EMAIL AUTOMATION SYSTEM")
    print("  Open your browser at  ->  http://127.0.0.1:5000")
    print("=" * 62)
    app.run(host="0.0.0.0", port=5000, debug=True)
