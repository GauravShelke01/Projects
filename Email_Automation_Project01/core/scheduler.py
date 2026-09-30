"""
core/scheduler.py
-----------------
A background thread that checks the schedules table every 20 seconds.
When the saved date and time is reached, the emails are sent
automatically using the owner's SMTP settings.
"""

import threading
import time
from datetime import datetime, timedelta

import schedule

from core import database
from core.mailer import send_bulk

_started = False


def check_schedules():
    now = datetime.now()

    for job in database.get_all_pending_schedules():
        try:
            run_at = datetime.strptime(job["run_at"], "%Y-%m-%d %H:%M")
        except ValueError:
            continue

        if now < run_at:
            continue

        user = database.get_user(job["user_id"])
        if not user:
            database.update_schedule(job["id"], status="Failed")
            continue

        print(f"[SCHEDULER] Running job #{job['id']} for {user['email']}")
        result = send_bulk(user, job["csv_file"], job["subject"], job["body"])

        if job["repeat_type"] == "daily":
            next_run = now.replace(hour=run_at.hour, minute=run_at.minute,
                                   second=0, microsecond=0) + timedelta(days=1)
            database.update_schedule(job["id"],
                                     run_at=next_run.strftime("%Y-%m-%d %H:%M"))
        else:
            database.update_schedule(
                job["id"], status="Completed" if result.get("success") else "Failed")


def _loop():
    schedule.every(20).seconds.do(check_schedules)
    while True:
        schedule.run_pending()
        time.sleep(1)


def start_scheduler():
    global _started
    if _started:
        return
    _started = True
    threading.Thread(target=_loop, daemon=True).start()
    print("[SCHEDULER] Background scheduler started (checks every 20 seconds)")
