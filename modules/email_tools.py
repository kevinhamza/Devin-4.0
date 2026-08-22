# # Devin/modules/email_tools.py
# # Purpose: Provides a suite of tools for automating email management,
# #          including sending emails via SMTP and receiving/managing via IMAP.
# # Automates email management 📧

# import logging
# import uuid
# import time
# import random
# from dataclasses import dataclass, field
# from typing import List, Dict, Any, Optional, Union
# from pathlib import Path

# # Configure basic logging
# logger = logging.getLogger("EmailTools")
# if not logger.handlers:
#     _console_handler = logging.StreamHandler()
#     _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
#     logger.addHandler(_console_handler)
#     logger.setLevel(logging.INFO)

# @dataclass
# class EmailAttachment:
#     """Represents an email attachment."""
#     filename: str
#     content: bytes
#     content_type: str # e.g., 'application/pdf', 'image/png'

# @dataclass
# class EmailMessage:
#     """Represents a structured email message, for both sending and receiving."""
#     message_id: Optional[str] = None # UID from IMAP server
#     from_address: Optional[str] = None
#     to_addresses: List[str] = field(default_factory=list)
#     cc_addresses: List[str] = field(default_factory=list)
#     subject: str = ""
#     body_text: str = ""
#     body_html: Optional[str] = None
#     attachments: List[EmailAttachment] = field(default_factory=list)
#     received_date: Optional[str] = None

# class EmailClient:
#     """
#     A conceptual client for sending and receiving emails.
#     Wraps smtplib and imaplib functionality.
#     """
#     def __init__(self,
#                  imap_server: str,
#                  smtp_server: str,
#                  email_address: str,
#                  password_placeholder: str,
#                  imap_port: int = 993,
#                  smtp_port: int = 587):
#         """
#         Initializes the client with server details and credentials.
#         """
#         self.imap_server = imap_server
#         self.smtp_server = smtp_server
#         self.email_address = email_address
#         self.password = password_placeholder
#         self.imap_port = imap_port
#         self.smtp_port = smtp_port

#         self.smtp_connection_conceptual: Optional[Dict] = None
#         self.imap_connection_conceptual: Optional[Dict] = None
        
#         logger.info(f"EmailClient initialized for user '{self.email_address}'.")
#         logger.warning("All email operations are conceptual and do not use real credentials or connections.")

#     # --- SMTP (Sending) Methods ---
#     def connect_smtp_conceptual(self) -> bool:
#         """Conceptually connects and authenticates to the SMTP server."""
#         if self.smtp_connection_conceptual:
#             logger.info("Already connected to SMTP server.")
#             return True
#         logger.info(f"CONCEPTUAL SMTP: Connecting to '{self.smtp_server}:{self.smtp_port}'...")
#         # Real-world:
#         # server = smtplib.SMTP(self.smtp_server, self.smtp_port)
#         # server.starttls()
#         # server.login(self.email_address, self.password)
#         self.smtp_connection_conceptual = {"status": "connected", "server": self.smtp_server}
#         logger.info("  Conceptual SMTP connection successful.")
#         return True

#     def disconnect_smtp_conceptual(self) -> None:
#         """Conceptually disconnects from the SMTP server."""
#         if not self.smtp_connection_conceptual:
#             return
#         logger.info("CONCEPTUAL SMTP: Disconnecting from server...")
#         # Real-world: server.quit()
#         self.smtp_connection_conceptual = None
#         logger.info("  Conceptual SMTP connection closed.")

#     def send_email_conceptual(self, email: EmailMessage) -> bool:
#         """
#         Conceptually composes and sends an email.
#         """
#         if not self.smtp_connection_conceptual:
#             logger.error("Cannot send email: Not connected to SMTP server.")
#             return False

#         # In a real system, you'd use the 'email' package to build a MIME message
#         # from the EmailMessage object, handling multipart for text/html and attachments.
#         logger.info(f"CONCEPTUAL SMTP: Building and sending email...")
#         logger.info(f"  From: {self.email_address}")
#         logger.info(f"  To: {', '.join(email.to_addresses)}")
#         logger.info(f"  Subject: {email.subject}")
#         logger.info(f"  Attachments: {[att.filename for att in email.attachments]}")
#         # Real-world: server.send_message(mime_message)
#         logger.info("  Conceptual email sent successfully.")
#         return True

#     # --- IMAP (Receiving) Methods ---
#     def connect_imap_conceptual(self) -> bool:
#         """Conceptually connects and authenticates to the IMAP server."""
#         if self.imap_connection_conceptual:
#             logger.info("Already connected to IMAP server.")
#             return True
#         logger.info(f"CONCEPTUAL IMAP: Connecting to '{self.imap_server}:{self.imap_port}'...")
#         # Real-world:
#         # server = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
#         # server.login(self.email_address, self.password)
#         self.imap_connection_conceptual = {"status": "connected", "server": self.imap_server, "selected_mailbox": None}
#         logger.info("  Conceptual IMAP connection successful.")
#         return True

#     def disconnect_imap_conceptual(self) -> None:
#         """Conceptually disconnects from the IMAP server."""
#         if not self.imap_connection_conceptual:
#             return
#         logger.info("CONCEPTUAL IMAP: Disconnecting from server...")
#         # Real-world: server.logout()
#         self.imap_connection_conceptual = None
#         logger.info("  Conceptual IMAP connection closed.")

#     def search_emails_conceptual(self, criteria: str = 'UNSEEN', mailbox: str = 'INBOX') -> List[str]:
#         """
#         Conceptually searches for emails in a mailbox.
        
#         Args:
#             criteria (str): IMAP search criteria (e.g., 'UNSEEN', 'FROM "someone@example.com"').
#             mailbox (str): The mailbox/folder to search in.
        
#         Returns:
#             List[str]: A list of conceptual message UIDs.
#         """
#         if not self.imap_connection_conceptual:
#             logger.error("Cannot search emails: Not connected to IMAP server.")
#             return []
        
#         # Select mailbox
#         logger.info(f"CONCEPTUAL IMAP: Selecting mailbox '{mailbox}'...")
#         # Real-world: server.select(mailbox)
#         self.imap_connection_conceptual["selected_mailbox"] = mailbox
        
#         logger.info(f"CONCEPTUAL IMAP: Searching for emails with criteria: {criteria}")
#         # Real-world: typ, data = server.search(None, criteria)
#         # Simulate finding a few emails
#         num_found = random.randint(0, 5)
#         logger.info(f"  Found {num_found} conceptual emails.")
#         return [str(random.randint(1000, 2000)) for _ in range(num_found)]

#     def fetch_email_conceptual(self, message_uid: str) -> Optional[EmailMessage]:
#         """Conceptually fetches a single email by its UID and parses it."""
#         if not self.imap_connection_conceptual:
#             logger.error("Cannot fetch email: Not connected to IMAP server.")
#             return None
        
#         logger.info(f"CONCEPTUAL IMAP: Fetching email UID '{message_uid}'...")
#         # Real-world: typ, data = server.fetch(message_uid, '(RFC822)')
#         # and then parse data[0][1] with email.message_from_bytes()
        
#         # Simulate parsing a fetched email
#         from_addr = random.choice(["jira@example.com", "notifications@github.com", "teammate@example.com"])
#         subject = random.choice(["[JIRA] Bug #DEV-123 Opened", "Re: Project Status Update", "Your weekly analytics report"])
        
#         return EmailMessage(
#             message_id=message_uid,
#             from_address=from_addr,
#             to_addresses=[self.email_address],
#             subject=subject,
#             body_text=f"This is the conceptual body of the email with subject: '{subject}'.\n\nIt contains details about the topic.",
#             attachments=[EmailAttachment("report.pdf", b"dummy_pdf_content", "application/pdf")] if "report" in subject else [],
#             received_date="simulated_datetime"
#         )

#     def mark_email_as_read_conceptual(self, message_uid: str) -> bool:
#         """Conceptually marks an email as read (removes the \Seen flag)."""
#         if not self.imap_connection_conceptual: return False
#         logger.info(f"CONCEPTUAL IMAP: Marking email UID '{message_uid}' as read.")
#         # Real-world: server.store(message_uid, '+FLAGS', '\\Seen')
#         return True

#     def delete_email_conceptual(self, message_uid: str) -> bool:
#         """Conceptually marks an email for deletion."""
#         if not self.imap_connection_conceptual: return False
#         logger.info(f"CONCEPTUAL IMAP: Marking email UID '{message_uid}' for deletion.")
#         # Real-world:
#         # server.store(message_uid, '+FLAGS', '\\Deleted')
#         # server.expunge() # To permanently delete
#         return True

# # --- Example Usage ---
# if __name__ == "__main__":
#     print("=========================================================")
#     print("=== Email Tools Module Prototype 📧 ===")
#     print("=========================================================")
    
#     # Initialize the client with dummy details
#     email_client = EmailClient(
#         imap_server="imap.example.com",
#         smtp_server="smtp.example.com",
#         email_address="devin@example.com",
#         password_placeholder="CONCEPTUAL_APP_PASSWORD"
#     )

#     # --- 1. Send an Email ---
#     print("\n--- Sending a conceptual status report email ---")
#     email_client.connect_smtp_conceptual()
    
#     report_attachment = EmailAttachment(
#         filename="status_report.txt",
#         content=b"All systems are operating normally.",
#         content_type="text/plain"
#     )
#     email_to_send = EmailMessage(
#         to_addresses=["project-manager@example.com"],
#         subject=f"Devin Daily Status Report - {time.strftime('%Y-%m-%d')}",
#         body_text="Please find the daily status report attached.",
#         attachments=[report_attachment]
#     )
#     email_client.send_email_conceptual(email_to_send)
#     email_client.disconnect_smtp_conceptual()

#     # --- 2. Check and Read Emails ---
#     print("\n\n--- Checking for and reading new conceptual emails ---")
#     email_client.connect_imap_conceptual()
    
#     # Search for unseen emails
#     unread_email_uids = email_client.search_emails_conceptual(criteria='UNSEEN')
    
#     if not unread_email_uids:
#         print("  No new conceptual emails found.")
#     else:
#         print(f"  Found {len(unread_email_uids)} new emails. Fetching the first one...")
        
#         # Fetch the first unread email
#         first_email_uid = unread_email_uids[0]
#         fetched_email = email_client.fetch_email_conceptual(first_email_uid)
        
#         if fetched_email:
#             print("\n  --- Fetched Email Details ---")
#             print(f"  From: {fetched_email.from_address}")
#             print(f"  To: {', '.join(fetched_email.to_addresses)}")
#             print(f"  Subject: {fetched_email.subject}")
#             print("  Body (first 50 chars):")
#             print(f"    '{fetched_email.body_text[:50]}...'")
#             if fetched_email.attachments:
#                 print(f"  Attachments: {[att.filename for att in fetched_email.attachments]}")
#             print("  ---------------------------")
            
#             # Mark the email as read and then delete it
#             email_client.mark_email_as_read_conceptual(first_email_uid)
#             email_client.delete_email_conceptual(first_email_uid)
            
#     email_client.disconnect_imap_conceptual()

#     print("\n=========================================================")
#     print("=== Email Tools Prototype Complete ===")
#     print("=========================================================")



# Devin/modules/email_tools.py
# Purpose: A functional, production-ready suite of tools for automating email
#          management using smtplib and imaplib.

import logging
import os
import smtplib
import imaplib
import time
import uuid
from email.message import EmailMessage
from email.parser import BytesParser
from email import policy
from dataclasses import dataclass, field
from typing import List, Optional

# Configure basic logging
logger = logging.getLogger("EmailTools")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False

@dataclass
class EmailAttachment:
    filename: str
    content: bytes
    maintype: str
    subtype: str

@dataclass
class ParsedEmail:
    uid: str
    from_address: str
    to_addresses: List[str]
    subject: str
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    attachments: List[EmailAttachment] = field(default_factory=list)

class EmailClient:
    """A client for sending (SMTP) and receiving (IMAP) emails."""
    def __init__(self, imap_server: str, smtp_server: str, email_address: str, password: str):
        self.imap_server_host = imap_server
        self.smtp_server_host = smtp_server
        self.email_address = email_address
        self.password = password
        
        self.smtp_server: Optional[smtplib.SMTP] = None
        self.imap_server: Optional[imaplib.IMAP4_SSL] = None
        logger.info(f"EmailClient initialized for user '{self.email_address}'.")

    # --- SMTP (Sending) Methods ---
    def connect_smtp(self, port: int = 587) -> bool:
        try:
            logger.info(f"Connecting to SMTP server {self.smtp_server_host}:{port}...")
            self.smtp_server = smtplib.SMTP(self.smtp_server_host, port)
            self.smtp_server.starttls()
            self.smtp_server.login(self.email_address, self.password)
            logger.info("SMTP connection successful.")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to SMTP server: {e}")
            self.smtp_server = None
            return False

    def disconnect_smtp(self):
        if self.smtp_server:
            self.smtp_server.quit()
            self.smtp_server = None
            logger.info("SMTP connection closed.")

    def send_email(self, to_addresses: List[str], subject: str, body_text: str, attachments: Optional[List[EmailAttachment]] = None):
        if not self.smtp_server:
            raise ConnectionError("Not connected to an SMTP server. Call connect_smtp() first.")
        
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = self.email_address
        msg['To'] = ", ".join(to_addresses)
        msg.set_content(body_text)

        if attachments:
            for att in attachments:
                msg.add_attachment(att.content, maintype=att.maintype, subtype=att.subtype, filename=att.filename)
        
        self.smtp_server.send_message(msg)
        logger.info(f"Email sent to {', '.join(to_addresses)} with subject '{subject}'.")

    # --- IMAP (Receiving) Methods ---
    def connect_imap(self, port: int = 993) -> bool:
        try:
            logger.info(f"Connecting to IMAP server {self.imap_server_host}:{port}...")
            self.imap_server = imaplib.IMAP4_SSL(self.imap_server_host, port)
            self.imap_server.login(self.email_address, self.password)
            logger.info("IMAP connection successful.")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to IMAP server: {e}")
            self.imap_server = None
            return False

    def disconnect_imap(self):
        if self.imap_server:
            self.imap_server.logout()
            self.imap_server = None
            logger.info("IMAP connection closed.")

    def search_emails(self, criteria: str = 'UNSEEN', mailbox: str = 'INBOX') -> List[str]:
        if not self.imap_server:
            raise ConnectionError("Not connected to an IMAP server. Call connect_imap() first.")
        
        self.imap_server.select(f'"{mailbox}"')
        _, data = self.imap_server.search(None, criteria)
        return data[0].split()

    def fetch_email(self, uid: str) -> Optional[ParsedEmail]:
        if not self.imap_server:
            raise ConnectionError("Not connected to an IMAP server. Call connect_imap() first.")

        _, data = self.imap_server.fetch(uid, '(RFC822)')
        if data[0] is None: return None

        raw_email = data[0][1]
        email_message = BytesParser(policy=policy.default).parsebytes(raw_email)
        
        body_text = None
        attachments = []
        for part in email_message.walk():
            if part.get_content_type() == "text/plain" and "attachment" not in part.get("Content-Disposition", ""):
                body_text = part.get_payload(decode=True).decode()
            elif part.get_content_maintype() != 'multipart' and part.get('Content-Disposition') is not None:
                attachments.append(EmailAttachment(
                    filename=part.get_filename(),
                    content=part.get_payload(decode=True),
                    maintype=part.get_content_maintype(),
                    subtype=part.get_content_subtype()
                ))

        return ParsedEmail(
            uid=uid,
            from_address=email_message['From'],
            to_addresses=email_message['To'].split(', '),
            subject=email_message['Subject'],
            body_text=body_text,
            attachments=attachments
        )

    def delete_email(self, uid: str):
        if not self.imap_server:
            raise ConnectionError("Not connected to an IMAP server. Call connect_imap() first.")
        self.imap_server.store(uid, '+FLAGS', '\\Deleted')
        self.imap_server.expunge()
        logger.info(f"Email with UID {uid} has been deleted.")

# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== Integrated Email Tools Module (Live Demo) 📧 ===")
    print("=========================================================")
    
    # --- PREREQUISITES ---
    EMAIL = os.getenv("DEVIN_EMAIL_ADDRESS")
    PASSWORD = os.getenv("DEVIN_EMAIL_PASSWORD") # IMPORTANT: Use an App Password!
    SMTP_HOST = os.getenv("DEVIN_SMTP_SERVER") # e.g., "smtp.gmail.com"
    IMAP_HOST = os.getenv("DEVIN_IMAP_SERVER") # e.g., "imap.gmail.com"
    
    if not all([EMAIL, PASSWORD, SMTP_HOST, IMAP_HOST]):
        print("\n!!! ERROR: Missing one or more required environment variables for the live demo.")
        print("Please set the following environment variables:")
        print("  - DEVIN_EMAIL_ADDRESS")
        print("  - DEVIN_EMAIL_PASSWORD (Use an App Password for services like Gmail/Outlook)")
        print("  - DEVIN_SMTP_SERVER (e.g., smtp.gmail.com)")
        print("  - DEVIN_IMAP_SERVER (e.g., imap.gmail.com)")
    else:
        client = EmailClient(
            imap_server=IMAP_HOST,
            smtp_server=SMTP_HOST,
            email_address=EMAIL,
            password=PASSWORD
        )
        
        # This demo will send an email to itself, then find it, read it, and delete it.
        try:
            # --- 1. Send an Email ---
            print("\n--- 1. Sending a test email to self... ---")
            if client.connect_smtp():
                test_subject = f"Devin Email Tools Test - {uuid.uuid4().hex[:8]}"
                attachment = EmailAttachment(
                    filename="test_attachment.txt",
                    content=b"This is a test attachment from Devin.",
                    maintype="text",
                    subtype="plain"
                )
                client.send_email(
                    to_addresses=[EMAIL],
                    subject=test_subject,
                    body_text="This is a live test of the EmailClient module.",
                    attachments=[attachment]
                )
                client.disconnect_smtp()

                # --- 2. Check for the Email ---
                print("\n--- 2. Checking for the test email via IMAP... ---")
                time.sleep(10) # Give the email time to arrive

                if client.connect_imap():
                    # Search specifically for the email we just sent
                    uids = client.search_emails(criteria=f'(SUBJECT "{test_subject}")')
                    if not uids:
                        print("[FAILURE] Could not find the test email in the inbox.")
                    else:
                        print(f"[SUCCESS] Found the test email with UID: {uids[0].decode()}")
                        
                        # --- 3. Fetch and Verify Email ---
                        print("\n--- 3. Fetching and verifying the email... ---")
                        email = client.fetch_email(uids[0])
                        if email and email.subject == test_subject and email.attachments:
                            print(f"  - Subject: '{email.subject}' (Correct!)")
                            print(f"  - Body: '{email.body_text}'")
                            print(f"  - Attachment Filename: '{email.attachments[0].filename}' (Correct!)")
                            
                            # --- 4. Delete the Email ---
                            print("\n--- 4. Deleting the test email... ---")
                            client.delete_email(uids[0])
                            print("[SUCCESS] Test email cleaned up.")
                        else:
                            print("[FAILURE] Fetched email content did not match what was sent.")

                    client.disconnect_imap()
        except Exception as e:
            logger.error(f"The live demo failed with an unexpected error: {e}", exc_info=True)

    print("\n=========================================================")
    print("=== Email Tools Prototype Complete ===")
    print("=========================================================")
