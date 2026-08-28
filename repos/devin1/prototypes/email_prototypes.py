"""
prototypes/email_prototypes.py
# Email prototypes project file
# This file demonstrates prototypes for handling email automation, notifications, and advanced email features.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
import imaplib
import email
import logging
from typing import List, Optional, Dict

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

class EmailAutomation:
    def __init__(self, smtp_server: str, smtp_port: int, imap_server: str, email_address: str, password: str):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.imap_server = imap_server
        self.email_address = email_address
        self.password = password
        self.smtp_connection = None
        self.imap_connection = None

    def connect_smtp(self):
        logging.info("Connecting to SMTP server...")
        try:
            self.smtp_connection = smtplib.SMTP(self.smtp_server, self.smtp_port)
            self.smtp_connection.starttls()
            self.smtp_connection.login(self.email_address, self.password)
            logging.info("Connected to SMTP server.")
        except Exception as e:
            logging.error(f"Error connecting to SMTP server: {e}")

    def connect_imap(self):
        logging.info("Connecting to IMAP server...")
        try:
            self.imap_connection = imaplib.IMAP4_SSL(self.imap_server)
            self.imap_connection.login(self.email_address, self.password)
            logging.info("Connected to IMAP server.")
        except Exception as e:
            logging.error(f"Error connecting to IMAP server: {e}")

    def send_email(self, recipient: str, subject: str, body: str, cc: Optional[List[str]] = None, bcc: Optional[List[str]] = None):
        logging.info("Sending email...")
        try:
            self.connect_smtp()
            msg = MIMEMultipart()
            msg['From'] = formataddr(("Automation System", self.email_address))
            msg['To'] = recipient
            msg['Subject'] = subject
            if cc:
                msg['Cc'] = ", ".join(cc)
            recipients = [recipient] + (cc if cc else []) + (bcc if bcc else [])
            msg.attach(MIMEText(body, 'plain'))
            self.smtp_connection.sendmail(self.email_address, recipients, msg.as_string())
            logging.info("Email sent successfully.")
        except Exception as e:
            logging.error(f"Error sending email: {e}")
        finally:
            if self.smtp_connection:
                self.smtp_connection.quit()

    def read_emails(self, folder: str = 'inbox', search_criteria: str = 'ALL') -> List[Dict]:
        logging.info(f"Reading emails from folder: {folder}")
        emails = []
        try:
            self.connect_imap()
            self.imap_connection.select(folder)
            status, messages = self.imap_connection.search(None, search_criteria)
            if status != "OK":
                logging.warning(f"No emails found with criteria: {search_criteria}")
                return []
            for num in messages[0].split():
                status, data = self.imap_connection.fetch(num, '(RFC822)')
                if status != "OK":
                    continue
                raw_email = data[0][1]
                msg = email.message_from_bytes(raw_email)
                email_details = {
                    "subject": msg.get("Subject"),
                    "from": msg.get("From"),
                    "to": msg.get("To"),
                    "date": msg.get("Date"),
                    "body": self._get_email_body(msg),
                }
                emails.append(email_details)
            logging.info(f"Retrieved {len(emails)} emails.")
        except Exception as e:
            logging.error(f"Error reading emails: {e}")
        finally:
            if self.imap_connection:
                self.imap_connection.logout()
        return emails

    def _get_email_body(self, msg):
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body += part.get_payload(decode=True).decode()
        else:
            body = msg.get_payload(decode=True).decode()
        return body

    def delete_email(self, folder: str = 'inbox', search_criteria: str = 'ALL'):
        logging.info(f"Deleting emails from folder: {folder} with criteria: {search_criteria}")
        try:
            self.connect_imap()
            self.imap_connection.select(folder)
            status, messages = self.imap_connection.search(None, search_criteria)
            if status != "OK":
                logging.warning("No emails to delete.")
                return
            for num in messages[0].split():
                self.imap_connection.store(num, '+FLAGS', '\\Deleted')
            self.imap_connection.expunge()
            logging.info("Emails deleted successfully.")
        except Exception as e:
            logging.error(f"Error deleting emails: {e}")
        finally:
            if self.imap_connection:
                self.imap_connection.logout()

# Example usage:
if __name__ == "__main__":
    email_bot = EmailAutomation(
        smtp_server="smtp.example.com",
        smtp_port=587,
        imap_server="imap.example.com",
        email_address="your_email@example.com",
        password="your_password"
    )

    email_bot.send_email(
        recipient="recipient@example.com",
        subject="Test Email",
        body="This is a test email sent by the automation script."
    )
    emails = email_bot.read_emails()
    print(f"Fetched {len(emails)} emails.")
    for email_data in emails:
        print(email_data)
