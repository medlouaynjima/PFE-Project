import smtplib
from email.mime.text import MIMEText
from typing import List


def send_support_email_mailhog(
    subject: str,
    body: str,
    to_emails: List[str],
    smtp_server: str = "localhost",
    smtp_port: int = 1025,
    from_email: str = "noreply@isante.tn"
) -> bool:
    """
    Send an email through MailHog (local SMTP server).
    
    Args:
        subject: Email subject
        body: Email content
        to_emails: List of recipients
        smtp_server: MailHog SMTP server (default: localhost)
        smtp_port: MailHog SMTP port (default: 1025)
        from_email: Sender address
    
    Returns:
        bool: True if success, False otherwise
    """
    try:
        # Create MIME message
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = from_email
        msg["To"] = ", ".join(to_emails)

        # Connect to MailHog
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.sendmail(from_email, to_emails, msg.as_string())

        print(f"[SUCCESS] Email sent via MailHog to {to_emails}")
        return True

    except Exception as e:
        print(f"[ERROR] Failed to send via MailHog: {str(e)}")
        return False
