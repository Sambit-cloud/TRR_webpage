import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials
from flask import Flask, render_template, request, send_from_directory

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')
ASSETS_DIR = os.path.join(BASE_DIR, 'Assets')

# ==========================
# CONFIGURATION
# ==========================
GMAIL_ADDRESS = "sambitprakash5789@gmail.com"
GMAIL_APP_PASSWORD = "your_app_password"

GOOGLE_SHEET_ID = "YOUR_GOOGLE_SHEET_ID"

# Paste contents of service-account.json here
GOOGLE_SERVICE_ACCOUNT = {
    "type": "service_account",
    "project_id": "xxxxx",
    "private_key_id": "xxxxx",
    "private_key": "-----BEGIN PRIVATE KEY-----\nYOUR_KEY\n-----END PRIVATE KEY-----\n",
    "client_email": "xxxx@xxxx.iam.gserviceaccount.com",
    "client_id": "xxxxxxxx",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/xxxx"
}

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)


# ==========================
# GOOGLE SHEETS
# ==========================
def get_sheet():
    creds = Credentials.from_service_account_info(
        GOOGLE_SERVICE_ACCOUNT,
        scopes=SCOPES
    )
    client = gspread.authorize(creds)
    return client.open_by_key(GOOGLE_SHEET_ID).sheet1


def ensure_sheet_headers(sheet):
    headers = [
        'Timestamp',
        'Type',
        'Name',
        'Email',
        'Roll/Company ID',
        'Branch/Industry',
        'Area of Interest',
        'Message'
    ]

    if sheet.row_values(1) != headers:
        sheet.insert_row(headers, 1)


# ==========================
# EMAIL
# ==========================
def send_email(name, email, app_type, field, dept, reason):
    msg = MIMEMultipart()
    msg['Subject'] = f"[TRR Website] New {app_type} Contact: {name}"
    msg['From'] = GMAIL_ADDRESS
    msg['To'] = GMAIL_ADDRESS
    msg['Reply-To'] = email

    body = f"""
New contact form submission on the TRR Electric website.

Type      : {app_type}
Name      : {name}
Email     : {email}
Branch    : {field}
Interest  : {dept}

Message:
{reason}

Reply directly to: {email}
"""

    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, GMAIL_ADDRESS, msg.as_string())


# ==========================
# ROUTES
# ==========================
@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory(ASSETS_DIR, filename)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/team')
def team_page():
    return render_template('team.html')


@app.route('/gallery')
def gallery_page():
    return render_template('gallery.html')


@app.route('/brochure')
def brochure_page():
    return render_template('brochure.html')


@app.route('/research')
def research_page():
    return render_template('research.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact_page():

    if request.method == 'POST':

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        app_type = request.form.get('applicant_type')
        name = request.form.get('name')
        email = request.form.get('email')
        user_id = request.form.get('user_id', '')
        field = request.form.get('field')
        dept = request.form.get('department')
        reason = request.form.get('reason')

        email_ok = False
        sheet_ok = False

        # Save to Google Sheets
        try:
            sheet = get_sheet()
            ensure_sheet_headers(sheet)

            sheet.append_row([
                timestamp,
                app_type,
                name,
                email,
                user_id,
                field,
                dept,
                reason
            ])

            sheet_ok = True
            print("Google Sheet updated")

        except Exception as e:
            print("Google Sheet Error:", e)

        # Send Email
        try:
            send_email(name, email, app_type, field, dept, reason)
            email_ok = True
            print("Email sent")

        except Exception as e:
            print("Email Error:", e)

        if email_ok:
            return render_template(
                'join.html',
                success=True,
                sheet_warning=not sheet_ok
            )

        return render_template(
            'join.html',
            failed=True
        )

    return render_template('join.html')


# ==========================
# MAIN
# ==========================
if __name__ == '__main__':
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True
    )