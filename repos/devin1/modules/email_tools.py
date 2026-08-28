# modules/email_tools.py

import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging
from typing import List, Optional

class EmailManager:
    """
    Automates email management, including sending, reading, and organizing emails.
    """
    def __init__(self, smtp_server: str, smtp_port: int, imap_server: str, email_address: str, email_password: str):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.imap_server = imap_server
        self.email_address = email_address
        self.email_password = email_password

    def send_email(self, recipient: str, subject: str, body: str, attachments: Optional[List[str]] = None):
        """
        Sends an email with optional attachments.
        """
        try:
            message = MIMEMultipart()
            message['From'] = self.email_address
            message['To'] = recipient
            message['Subject'] = subject

            message.attach(MIMEText(body, 'plain'))

            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as f:
                            attachment = email.mime.application.MIMEApplication(f.read())
                            attachment.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(file_path)}"')
                            message.attach(attachment)

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_address, self.email_password)
                server.send_message(message)

            logging.info("Email sent successfully to %s", recipient)

        except Exception as e:
            logging.error("Failed to send email: %s", e)

    def read_emails(self, folder: str = "INBOX", search_criteria: str = "ALL") -> List[dict]:
        """
        Reads emails from the specified folder using IMAP.
        """
        emails = []
        try:
            with imaplib.IMAP4_SSL(self.imap_server) as mail:
                mail.login(self.email_address, self.email_password)
                mail.select(folder)

                result, data = mail.search(None, search_criteria)
                if result == "OK":
                    for num in data[0].split():
                        result, msg_data = mail.fetch(num, '(RFC822)')
                        if result == "OK":
                            raw_email = msg_data[0][1]
                            msg = email.message_from_bytes(raw_email)
                            email_content = {
                                'From': msg.get('From'),
                                'Subject': msg.get('Subject'),
                                'Body': self._get_email_body(msg),
                            }
                            emails.append(email_content)
        except Exception as e:
            logging.error("Failed to read emails: %s", e)
        return emails

    def _get_email_body(self, msg: email.message.Message) -> str:
        """
        Extracts the email body from a message object.
        """
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    return part.get_payload(decode=True).decode()
        else:
            return msg.get_payload(decode=True).decode()
        return ""

    def organize_emails(self, folder: str = "INBOX", criteria: str = "ALL", move_to: str = "Processed"):
        """
        Moves emails matching criteria to a specified folder.
        """
        try:
            with imaplib.IMAP4_SSL(self.imap_server) as mail:
                mail.login(self.email_address, self.email_password)
                mail.select(folder)

                result, data = mail.search(None, criteria)
                if result == "OK":
                    for num in data[0].split():
                        mail.store(num, '+X-GM-LABELS', move_to)
                        mail.store(num, '+FLAGS', '\\Deleted')
                    mail.expunge()
                    logging.info("Emails moved to folder: %s", move_to)
        except Exception as e:
            logging.error("Failed to organize emails: %s", e)

# Example Usage:
# if __name__ == "__main__":
#     email_manager = EmailManager(
#         smtp_server="smtp.gmail.com",
#         smtp_port=587,
#         imap_server="imap.gmail.com",
#         email_address="your_email@gmail.com",
#         email_password="your_password"
#     )
#     email_manager.send_email("recipient@example.com", "Test Subject", "This is a test email.")
#     inbox_emails = email_manager.read_emails()
#     print(inbox_emails)
