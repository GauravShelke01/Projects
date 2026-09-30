"""
core/reader.py
--------------
Reads the recipient list from a CSV file OR an Excel file (.xlsx / .xls)
using pandas, and validates every email address with a regular expression.
"""

import os
import re

import pandas as pd

from config import DATA_FOLDER, UPLOAD_FOLDER

EMAIL_REGEX = re.compile(r"^[\w\.\+\-]+@[\w\-]+\.[\w\.\-]{2,}$")


def is_valid_email(email):
    return bool(EMAIL_REGEX.match(str(email).strip()))


def find_file(filename):
    """Looks for the file inside uploads/ first, then data/."""
    for folder in (UPLOAD_FOLDER, DATA_FOLDER):
        path = os.path.join(folder, filename)
        if os.path.exists(path):
            return path
    return None


def list_files():
    """All CSV and Excel files available in the two folders."""
    files = []
    for folder in (UPLOAD_FOLDER, DATA_FOLDER):
        if os.path.isdir(folder):
            files += [f for f in os.listdir(folder)
                      if f.lower().endswith((".csv", ".xlsx", ".xls"))]
    return sorted(set(files))


def load_recipients(filename):
    """
    Returns (list_of_recipients, error_message).
    Each recipient is a dictionary and also carries a '_valid' flag.
    """
    path = find_file(filename)
    if not path:
        return [], f"File '{filename}' was not found."

    try:
        if path.lower().endswith(".csv"):
            df = pd.read_csv(path)                      # CSV file
        else:
            df = pd.read_excel(path)                    # Excel file
    except ImportError:
        return [], "Excel support needs the openpyxl package. Run: py -m pip install openpyxl"
    except Exception as e:
        return [], f"Could not read the file: {e}"

    df.columns = [str(c).strip().lower() for c in df.columns]

    if "email" not in df.columns:
        return [], "The file must contain a column named 'email'."

    df = df.fillna("")
    records = df.to_dict("records")

    for r in records:
        r["email"] = str(r.get("email", "")).strip()
        r["_valid"] = is_valid_email(r["email"])
        if "name" not in r or not str(r["name"]).strip():
            r["name"] = r["email"].split("@")[0].title()

    return records, None


def get_summary(filename):
    """Total / valid / invalid counts plus the available placeholder columns."""
    records, error = load_recipients(filename)
    if error:
        return {"total": 0, "valid": 0, "invalid": 0, "columns": [], "error": error}

    valid = sum(1 for r in records if r["_valid"])
    columns = [c for c in records[0].keys() if not c.startswith("_")] if records else []
    return {"total": len(records), "valid": valid, "invalid": len(records) - valid,
            "columns": columns, "error": None}
