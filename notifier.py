import smtplib
import csv
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

import pandas as pd

LOG_FILE = "notification_log.csv"


def _cfg(key: str, default: str = "") -> str:
    val = os.environ.get(key)
    if val:
        return val
    try:
        import notification_config as nc
        return getattr(nc, key, default)
    except ImportError:
        return default


def _send_email(to_address: str, subject: str, body_html: str) -> bool:
    smtp_host = _cfg("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(_cfg("SMTP_PORT", "587"))
    smtp_user = _cfg("SMTP_USER")
    smtp_pass = _cfg("SMTP_PASS")
    from_addr = _cfg("FROM_EMAIL", smtp_user)

    if not smtp_user or not smtp_pass:
        print(f"[notifier] SMTP not configured — skipping {to_address}")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_address
    msg.attach(MIMEText(body_html, "html"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(from_addr, to_address, msg.as_string())
        return True
    except Exception as e:
        print(f"[notifier] Failed: {e}")
        return False


def _fine_email(row):
    content = f"""
    <p>Dear {row['user_id']},</p>

    <p>
        This is to inform you that the book issued under your account has been returned 
        after the due date. As per the library policy, a late return fine has been applied.
    </p>

    <table style="border-collapse:collapse;width:100%;margin:15px 0;font-size:14px;">
        <tr style="background:#f2f2f2;">
            <td style="padding:8px;border:1px solid #ddd;">Book ID</td>
            <td style="padding:8px;border:1px solid #ddd;"><b>{row['book_id']}</b></td>
        </tr>
        <tr>
            <td style="padding:8px;border:1px solid #ddd;">Record ID</td>
            <td style="padding:8px;border:1px solid #ddd;">{row['record_id']}</td>
        </tr>
        <tr style="background:#f2f2f2;">
            <td style="padding:8px;border:1px solid #ddd;">Fine Amount</td>
            <td style="padding:8px;border:1px solid #ddd;"><b>Rs. {int(row['fine'])}</b></td>
        </tr>
    </table>

    <p>
        Kindly clear the outstanding fine at the library counter at the earliest 
        to avoid any inconvenience in future borrowings.
    </p>

    <p>Thank you for your cooperation.</p>

    <p>
        Regards,<br>
        <b>Library Management Team</b><br>
    </p>
    """

    subject = f"Library Notice: Overdue Book Fine (Rs. {int(row['fine'])}) - {row['book_id']}"
    return subject, content


def _log(notification_type, user_id, record_id, email, subject, success):
    file_exists = os.path.isfile(LOG_FILE)

    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow([
                "Timestamp", "Type", "User ID", "Record ID",
                "Email", "Subject", "Status"
            ])

        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            notification_type,
            user_id,
            record_id,
            email,
            subject,
            "Sent" if success else "Failed"
        ])


def send_fine_notices(fine_report: pd.DataFrame):
    print("\n[notifier] Sending fine notices...")

    late_df = fine_report[fine_report["late_return"] == True]
    sent = 0

    for _, row in late_df.iterrows():
        email = str(row.get("email", "")).strip()
        if not email:
            continue

        subject, body = _fine_email(row)
        ok = _send_email(email, subject, body)

        _log("fine", row["user_id"], row["record_id"], email, subject, ok)

        if ok:
            sent += 1

    print(f"[notifier] Sent {sent}/{len(late_df)} fine emails")
