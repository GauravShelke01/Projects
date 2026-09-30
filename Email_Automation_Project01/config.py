"""
====================================================================
 config.py  --  Application settings
====================================================================
 NOTE: Email credentials are NOT stored here anymore.
 Every user adds their own sender email + app password from the
 Settings page after logging in. They are saved in the database.
====================================================================
"""

import os

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
DATA_FOLDER   = os.path.join(BASE_DIR, "data")
DATABASE      = os.path.join(BASE_DIR, "email_automation.db")

# Accepted recipient file types (CSV + Excel)
ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls"}

# Flask session
SECRET_KEY   = "email-automation-system-secret-key-change-me"
SESSION_DAYS = 365          # auto login for 1 year

# Default SMTP values shown on the Settings page
DEFAULT_SMTP_SERVER = "smtp.gmail.com"
DEFAULT_SMTP_PORT   = 587

# Gap between two emails in seconds (avoids spam blocking)
SEND_DELAY = 0.5

DEFAULT_SUBJECT = "Hello {{name}}, Special Offer Just For You!"
DEFAULT_BODY = """Hi {{name}},

We have an exclusive offer for you.
Visit our website to know more.

Best Regards,
Your Company"""
