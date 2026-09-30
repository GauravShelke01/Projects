# Email Automation System — Python Web Application

A college mini project built with **Python (Flask) + HTML + CSS only**.
It sends **real personalised emails** to a list of recipients loaded from a
**CSV or Excel** file, supports **single emails**, **scheduling**, and keeps a
complete **delivery log** for every registered user.

> **Languages used: Python (backend) and HTML/CSS (frontend). No JavaScript at all.**

---

## Main Features

| # | Feature |
|---|---------|
| 1 | **Sign up / Log in** — every user gets a private account |
| 2 | **Automatic login** — you stay signed in for one year on the same browser |
| 3 | **Your own sender email** — add your Gmail / Outlook address in Settings and all mail is sent from it |
| 4 | **Real email sending** through SMTP (`smtplib`) — no simulation |
| 5 | **Bulk email** from a **CSV or Excel** file with `{{placeholders}}` |
| 6 | **Single email** form placed right under the recipients panel |
| 7 | **Email scheduling** for a future date and time (once or daily) |
| 8 | **Logs and delivery status** — search, filter, export to CSV |
| 9 | **Private data** — one user can never see another user's logs |

---

## Project Structure

```
email_automation_project/
│
├── app.py                  <- MAIN FILE (run this one)
├── config.py               <- application settings
├── view_database.py        <- see the database in the terminal
├── requirements.txt
├── START_PROJECT.bat       <- one click setup + run (Windows)
├── README.md
├── INSTALL_HELP.md         <- fixes for "pip is not recognized"
│
├── core/                   <- BACKEND (Python)
│   ├── database.py         <- SQLite: users, logs, schedules
│   ├── mailer.py           <- smtplib + Jinja2 personalisation
│   ├── reader.py           <- pandas: reads CSV and Excel files
│   └── scheduler.py        <- background thread for scheduled mail
│
├── templates/              <- FRONTEND (HTML + Jinja2)
│   ├── base.html           login.html      signup.html
│   ├── dashboard.html      compose.html    recipients.html
│   └── schedule.html       logs.html       settings.html
│
├── static/css/style.css    <- FRONTEND (CSS)
│
├── data/                   <- sample recipient files
│   ├── demo_recipients.csv    (15 rows, 13 valid + 2 invalid)
│   ├── demo_recipients.xlsx   (same data as an Excel file)
│   └── sample_recipients.csv  (10 rows)
│
└── uploads/                <- files you upload are stored here
```

---

## How To Run

### Step 1 — Install Python
Download **Python 3.10 or newer** from https://www.python.org/downloads/
and tick **"Add python.exe to PATH"** during installation.

### Step 2 — Open the folder in VS Code
`File -> Open Folder -> email_automation_project`, then open a terminal
with `Ctrl + ~`.

### Step 3 — Install the required packages
```bash
py -m pip install flask pandas jinja2 schedule openpyxl
```
or
```bash
py -m pip install -r requirements.txt
```

> If you see **"pip is not recognized"**, use `py -m pip` instead of `pip`.
> Full help is in **INSTALL_HELP.md**.

### Step 4 — Start the application
```bash
py app.py
```
Then open **http://127.0.0.1:5000** in your browser.

> **Easiest option:** just double click **START_PROJECT.bat**. It installs
> everything, starts the server and opens the browser for you.

---

## First Time Setup (important)

1. Open http://127.0.0.1:5000 — you will see the **Login** page
2. Click **Create one** and sign up with your name, email and a password
3. You are taken to **Settings**. Add the email address you want to send **from**:
   - **Sender Email Address** — for example `yourname@gmail.com`
   - **App Password** — the 16 character Google app password (see below)
   - **SMTP Server** — `smtp.gmail.com`, **Port** — `587`
4. Click **Save Sender Settings**, then **Send Test Email** to check it works
5. Go to **Compose Email** and start sending

### How to get a Gmail App Password
1. Open https://myaccount.google.com -> **Security**
2. Turn on **2-Step Verification** (this is required)
3. Search for **"App passwords"**
4. Choose App = **Mail**, Device = **Other**, name it "Python Project"
5. Copy the 16 character code and paste it into the Settings page

> Your normal Gmail password will **not** work. Google blocks it for security.

Other providers:

| Provider | SMTP Server | Port |
|----------|-------------|------|
| Gmail | smtp.gmail.com | 587 |
| Outlook / Hotmail | smtp.office365.com | 587 |
| Yahoo | smtp.mail.yahoo.com | 587 |

---

## Pages of the Website

| Page | What it does |
|------|--------------|
| **Login / Sign Up** | Create an account, log in, stay logged in automatically |
| **Dashboard** | Sent / Delivered / Pending / Failed counters and recent activity |
| **Compose Email** | Bulk email form on the left, recipients file and **single email** form on the right |
| **Recipients** | Upload CSV or Excel, view the list with Valid / Invalid tags, plus a **single email** form |
| **Schedule** | Pick a date and time, the background scheduler sends it for you |
| **Logs** | Every email with status, search, filter, export to CSV |
| **Settings** | Your sender email, SMTP settings, test email, change password |

---

## Placeholders (Personalisation)

Every column of your file becomes a placeholder.

File columns: `name, email, city, company, offer`

```
Subject : Hello {{name}}, {{offer}} just for you!

Message : Hi {{name}},
          {{company}} has a special offer for our customers in {{city}}.
          Enjoy {{offer}} on your next order.

          Best Regards,
          Marketing Team
```

Result for the first row:
> **Hello Rahul Deshmukh, 30% OFF just for you!**
> Hi Rahul Deshmukh, TechNova Solutions has a special offer for our customers
> in Aurangabad. Enjoy 30% OFF on your next order.

### File format
The file must contain a column named **email**. Everything else is optional.

```csv
name,email,city,company,offer
Rahul Deshmukh,rahul.deshmukh@example.com,Aurangabad,TechNova Solutions,30% OFF
```

Accepted file types: **.csv**, **.xlsx**, **.xls**

---

## How To View The Database

The project uses SQLite. The file is **`email_automation.db`** and it is
created automatically the first time you run the app.

Three tables:

| Table | What it stores |
|-------|----------------|
| `users` | accounts, hashed login passwords and each user's SMTP settings |
| `logs` | every email that was sent, with status and timestamp |
| `schedules` | emails queued for a future date and time |

### Option 1 — Inside the website
Open the **Logs** page. You get search, filters, export and clear.

### Option 2 — `view_database.py` (best for the viva)
```bash
py view_database.py              # everything
py view_database.py users        # registered accounts
py view_database.py logs         # email logs
py view_database.py schedules    # scheduled emails
py view_database.py stats        # summary statistics
py view_database.py schema       # table structure
```

### Option 3 — DB Browser for SQLite (graphical, looks like Excel)
1. Download from https://sqlitebrowser.org/dl/
2. Open Database -> select `email_automation.db`
3. Click the **Browse Data** tab and choose a table

### Option 4 — VS Code
Install the **SQLite Viewer** extension and click on the `.db` file.

> Do not open the `.db` file in Notepad. It is a binary file.

---

## Common Errors

| Error | Solution |
|-------|----------|
| `pip is not recognized` | Use `py -m pip install ...` — see INSTALL_HELP.md |
| `ModuleNotFoundError: flask` | `py -m pip install -r requirements.txt` |
| `No sender email configured` | Open Settings and add your sender email |
| `Login failed. Check the sender email and app password` | The app password is wrong, or 2-Step Verification is off |
| Excel file will not open | `py -m pip install openpyxl` |
| `Port 5000 is in use` | Change `port=5000` to `port=5001` at the bottom of app.py |
| Scheduled email did not go out | The app must stay running for the scheduler to work |
| Emails land in spam | Normal for a new sender. Ask the recipient to mark it as "Not spam" |

---

## Viva Questions and Answers

**What is SMTP?**
Simple Mail Transfer Protocol, the standard protocol used to send email.
This project connects to `smtp.gmail.com` on port 587 and secures the
connection with STARTTLS before logging in.

**Which languages did you use?**
Python for the backend and HTML with CSS for the frontend. There is no
JavaScript in the project — every action is a normal HTML form that is
processed on the server by Flask.

**How does the login system work?**
Passwords are hashed with Werkzeug's `generate_password_hash` (PBKDF2) and
only the hash is stored. On login the hash is compared, and the user id is
saved in a signed Flask session cookie. The session is marked permanent with
a lifetime of 365 days, so the user is logged in automatically next time.

**How is one user's data kept private?**
The `logs` and `schedules` tables both have a `user_id` column, and every
query filters on the logged in user's id.

**How does personalisation work?**
Jinja2 compiles the subject and body as templates and renders them once per
recipient using that row as the data, so `{{name}}` becomes the real name.

**How do you read Excel files?**
pandas `read_excel()` with the openpyxl engine, and `read_csv()` for CSV.
Both return a DataFrame which is converted to a list of dictionaries.

**What happens if one email fails?**
Each send is inside its own try/except block, so one failure does not stop
the loop. The error message is written to the logs table as "Failed".

**Why an app password and not the normal password?**
Google disabled password login for third party apps. An app password is a
separate 16 character key that can be revoked at any time.

---

## Technologies Used

| Layer | Technology |
|-------|-----------|
| Frontend | HTML5, CSS3, Jinja2 templates |
| Backend | Python 3, Flask |
| Email | smtplib, email.mime |
| Data | pandas (CSV + Excel), openpyxl, re |
| Database | SQLite3 |
| Security | Werkzeug password hashing, signed session cookies |
| Scheduling | schedule, threading |

---

## Future Scope
- File attachments (PDF and images)
- Open and click tracking
- Rich text email editor
- Charts and analytics on the dashboard
- Cloud deployment
