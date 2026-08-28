# Devin/prototypes/email_prototypes.py
# Purpose: Prototype implementations for sending and reading emails.

import os
import smtplib # For sending email via SMTP
import ssl # For secure connections
import logging
import mimetypes # For guessing attachment types
from email.message import EmailMessage # Modern way to create email messages
# Older approach used email.mime.multipart etc. EmailMessage is generally preferred.
from typing import Dict, Any, List, Optional, Sequence, Tuple

# --- Conceptual Import for IMAP ---
try:
    import imaplib
    IMAPLIB_AVAILABLE = True
except ImportError:
    imaplib = None # type: ignore
    IMAPLIB_AVAILABLE = False
    print("Warning: 'imaplib' not found. Email reading prototypes disabled.")
# --- End Conceptual Import ---

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger("EmailPrototype")


class EmailPrototype:
    """
    Conceptual prototype for sending emails via SMTP and potentially reading via IMAP.
    Requires configuration of email server details and secure handling of credentials.
    """

    def __init__(self,
                 smtp_host: Optional[str] = None,
                 smtp_port: Optional[int] = None, # Common: 587 (TLS), 465 (SSL)
                 smtp_user_env_var: str = "DEVIN_SMTP_USER",
                 smtp_password_env_var: str = "DEVIN_SMTP_PASSWORD", # Use App Password for Gmail/Outlook!
                 imap_host: Optional[str] = None,
                 imap_port: Optional[int] = 993, # Common IMAP SSL port
                 imap_user_env_var: str = "DEVIN_IMAP_USER", # Can be same as SMTP
                 imap_password_env_var: str = "DEVIN_IMAP_PASSWORD"): # Can be same as SMTP
        """
        Initializes the EmailPrototype.

        Args:
            smtp_host (Optional[str]): SMTP server hostname (e.g., 'smtp.gmail.com'). Read from env if None.
            smtp_port (Optional[int]): SMTP server port. Read from env or use default.
            smtp_user_env_var (str): Environment variable name holding the SMTP username.
            smtp_password_env_var (str): Environment variable name holding the SMTP password/app password.
            imap_host (Optional[str]): IMAP server hostname (e.g., 'imap.gmail.com'). Read from env if None.
            imap_port (Optional[int]): IMAP server port. Read from env or use default.
            imap_user_env_var (str): Environment variable name holding the IMAP username.
            imap_password_env_var (str): Environment variable name holding the IMAP password/app password.

        *** Credentials MUST be stored securely in environment variables or a secrets manager. ***
        """
        self.smtp_host = smtp_host or os.environ.get("DEVIN_SMTP_HOST")
        self.smtp_port = smtp_port or int(os.environ.get("DEVIN_SMTP_PORT", 587)) # Default to 587 (TLS)
        self.smtp_user_env_var = smtp_user_env_var
        self.smtp_password_env_var = smtp_password_env_var

        self.imap_host = imap_host or os.environ.get("DEVIN_IMAP_HOST")
        self.imap_port = imap_port or int(os.environ.get("DEVIN_IMAP_PORT", 993)) # Default to 993 (IMAP SSL)
        self.imap_user_env_var = imap_user_env_var
        self.imap_password_env_var = imap_password_env_var

        logger.info("EmailPrototype initialized.")
        if not self.smtp_host: logger.warning("SMTP host not configured.")
        if not self.imap_host: logger.warning("IMAP host not configured.")

    def _load_credentials(self, user_env_var: str, pass_env_var: str) -> Optional[Tuple[str, str]]:
        """Loads credentials securely from environment variables."""
        username = os.environ.get(user_env_var)
        password = os.environ.get(pass_env_var)

        if not username or not password:
            logger.error(f"Credentials not found in environment variables: {user_env_var}, {pass_env_var}")
            return None
        return username, password

    # --- Sending Email (SMTP) ---

    def send_email(self,
                   sender_email: str, # Should match the authenticated user or be allowed by server
                   recipient_emails: Union[str, List[str]],
                   subject: str,
                   body_text: Optional[str] = None,
                   body_html: Optional[str] = None,
                   attachments: Optional[List[str]] = None) -> bool:
        """
        Sends an email using SMTP with TLS/SSL.

        Args:
            sender_email (str): The 'From' email address.
            recipient_emails (Union[str, List[str]]): A single recipient email or a list of recipients.
            subject (str): The email subject line.
            body_text (Optional[str]): Plain text content of the email.
            body_html (Optional[str]): HTML content of the email. If provided, email will likely be multipart/alternative.
            attachments (Optional[List[str]]): List of file paths to attach to the email.

        Returns:
            bool: True if the email was sent successfully, False otherwise.
        """
        if not self.smtp_host:
             logger.error("Cannot send email: SMTP host not configured.")
             return False
        if not body_text and not body_html:
             logger.error("Cannot send email: No body content (text or html) provided.")
             return False

        logger.info(f"Attempting to send email. Subject: '{subject}' To: {recipient_emails}")

        creds = self._load_credentials(self.smtp_user_env_var, self.smtp_password_env_var)
        if not creds:
             return False # Error logged in helper
        smtp_user, smtp_password = creds

        recipients = [recipient_emails] if isinstance(recipient_emails, str) else recipient_emails
        if not recipients:
             logger.error("No recipients provided.")
             return False

        # --- Create the Email Message using email.message ---
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = ", ".join(recipients) # Comma-separated string for header
        msg.set_content(body_text or "Please enable HTML viewing to see this email.") # Set plain text fallback

        # Add HTML part if provided (creates multipart/alternative)
        if body_html:
            msg.add_alternative(body_html, subtype='html')

        # Add Attachments if provided
        if attachments:
            logger.info(f"  - Attaching {len(attachments)} files...")
            for file_path in attachments:
                if not os.path.exists(file_path):
                    logger.warning(f"    - Attachment not found, skipping: {file_path}")
                    continue
                try:
                    # Guess the MIME type
                    ctype, encoding = mimetypes.guess_type(file_path)
                    if ctype is None or encoding is not None:
                        # Use generic binary type if guess fails
                        ctype = 'application/octet-stream'
                    maintype, subtype = ctype.split('/', 1)

                    logger.debug(f"    - Attaching {os.path.basename(file_path)} as {maintype}/{subtype}")
                    with open(file_path, 'rb') as fp:
                        msg.add_attachment(fp.read(),
                                           maintype=maintype,
                                           subtype=subtype,
                                           filename=os.path.basename(file_path))
                except Exception as e:
                     logger.error(f"    - Error attaching file {file_path}: {e}")
                     # Decide whether to continue sending without attachment or fail? Failing for now.
                     # return False

        # --- Connect and Send using smtplib ---
        logger.info(f"Connecting to SMTP server: {self.smtp_host}:{self.smtp_port}")
        context = ssl.create_default_context() # Use secure defaults
        server = None
        try:
            if self.smtp_port == 465: # Use SMTP_SSL for port 465
                 logger.debug("  - Using SMTP_SSL connection.")
                 server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, context=context, timeout=30)
            else: # Assume port 587 or other requires STARTTLS
                 logger.debug("  - Using SMTP connection with STARTTLS.")
                 server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30)
                 server.starttls(context=context) # Upgrade to secure connection

            # Login
            logger.debug(f"  - Logging in as {smtp_user}...")
            server.login(smtp_user, smtp_password)
            logger.info("  - SMTP Login successful.")

            # Send
            logger.info(f"  - Sending email to: {recipients}...")
            # send_message handles correct encoding and headers vs sendmail
            server.send_message(msg)
            logger.info("Email sent successfully.")
            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP Authentication failed for user {smtp_user}: {e.smtp_code} {e.smtp_error}")
            logger.error("  - Check username, password/app password, and ensure less secure app access is enabled if required (e.g., Gmail).")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP Error occurred: {e}")
            return False
        except ssl.SSLError as e:
             logger.error(f"SSL Error occurred during SMTP connection: {e}")
             return False
        except socket.gaierror:
             logger.error(f"DNS Resolution failed for SMTP host: {self.smtp_host}")
             return False
        except Exception as e:
            logger.exception("An unexpected error occurred during email sending.") # Log full traceback
            return False
        finally:
            if server:
                try:
                    server.quit()
                    logger.debug("  - SMTP connection closed.")
                except: pass # Ignore errors during quit
                  
# Ensure logger, EmailMessage, and other necessary components from Part 1 are conceptually available
import logging
logger = logging.getLogger("EmailPrototype") # Ensure logger is accessible

import os
import smtplib
import ssl
import mimetypes
from email.message import EmailMessage
from email.utils import formatdate
from typing import Dict, Any, List, Optional, Sequence, Tuple, Union

# Conceptual Import for IMAP
try:
    import imaplib
    IMAPLIB_AVAILABLE = True
except ImportError:
    imaplib = None # type: ignore
    IMAPLIB_AVAILABLE = False
    # print("Warning: 'imaplib' not found. Email reading prototypes disabled (from Part 1).") # Already printed in Part 1

# For parsing email bodies if fetched
from email import policy
from email.parser import BytesParser


# --- Continue EmailPrototype Class ---
class EmailPrototype:
    # (Assume __init__, _load_credentials, and send_email from Part 1 are here)

    # --- Reading Email (IMAP - Conceptual Placeholders) ---
    # Interacting with IMAP is complex due to varying server responses,
    # MIME structures, character encodings, etc. These are highly simplified.

    def _connect_imap_placeholder(self) -> Optional[Any]:
        """
        Conceptually connects to an IMAP server using SSL.
        Returns a conceptual IMAP connection object or None on error.
        """
        if not IMAPLIB_AVAILABLE:
            logger.error("Cannot connect to IMAP: imaplib library not available.")
            return None
        if not self.imap_host:
            logger.error("Cannot connect to IMAP: IMAP host not configured.")
            return None

        logger.info(f"Conceptually connecting to IMAP server: {self.imap_host}:{self.imap_port}")
        creds = self._load_credentials(self.imap_user_env_var, self.imap_password_env_var)
        if not creds:
             return None # Error logged in helper
        imap_user, imap_password = creds

        # --- Conceptual imaplib Call ---
        try:
            # mail = imaplib.IMAP4_SSL(self.imap_host, self.imap_port)
            # status, response = mail.login(imap_user, imap_password)
            # if status == 'OK':
            #     logger.info("IMAP login successful.")
            #     return mail # Return the imaplib connection object
            # else:
            #     logger.error(f"IMAP login failed: {response}")
            #     return None
            # Simulate connection
            mock_connection = {"user": imap_user, "host": self.imap_host, "_selected_mailbox": None}
            logger.info(f"  - Conceptual IMAP connection successful for {imap_user}.")
            return mock_connection
        except Exception as e:
            logger.error(f"Failed to connect or login to IMAP server {self.imap_host}: {e}")
            return None
        # --- End Conceptual ---

    def _disconnect_imap_placeholder(self, imap_conn: Optional[Any]):
        """Conceptually closes the IMAP connection and logs out."""
        if not imap_conn: return
        logger.info(f"Conceptually disconnecting from IMAP server: {imap_conn.get('host', 'Unknown')}")
        # --- Conceptual imaplib Call ---
        # try:
        #     if imap_conn._selected_mailbox: # Ensure mailbox is closed if selected
        #          imap_conn.close()
        #     imap_conn.logout()
        #     logger.info("  - IMAP logout successful.")
        # except Exception as e:
        #     logger.error(f"Error during IMAP logout/close: {e}")
        # --- End Conceptual ---
        logger.info("  - Conceptual IMAP disconnection complete.")


    def search_emails_placeholder(self,
                                  imap_conn: Any,
                                  mailbox: str = "INBOX",
                                  criteria: str = "ALL") -> Optional[List[str]]:
        """
        Conceptually searches for emails in a mailbox matching criteria.

        Args:
            imap_conn: Conceptual IMAP connection object.
            mailbox (str): Name of the mailbox to search (e.g., "INBOX", "Sent").
            criteria (str): IMAP search criteria (e.g., "ALL", "UNSEEN", "FROM sender@example.com",
                              "SUBJECT \"Important\"", "SINCE 01-Jan-2023").

        Returns:
            Optional[List[str]]: List of email message IDs (as strings), or None on error.
        """
        if not imap_conn: logger.error("IMAP search failed: No connection."); return None
        logger.info(f"Conceptually searching mailbox '{mailbox}' with criteria: '{criteria}'")
        # --- Conceptual imaplib Call ---
        # try:
        #     status, select_data = imap_conn.select(f'"{mailbox}"', readonly=True) # Select mailbox
        #     if status != 'OK':
        #         logger.error(f"Failed to select mailbox '{mailbox}': {select_data}")
        #         return None
        #     imap_conn._selected_mailbox = mailbox # Track selected state
        #
        #     status, msg_ids_bytes = imap_conn.search(None, criteria) # Search
        #     if status != 'OK':
        #         logger.error(f"Email search failed: {msg_ids_bytes}")
        #         return None
        #
        #     # msg_ids_bytes is a list containing a single string of space-separated IDs, e.g., [b'1 2 3']
        #     msg_ids_str_list = msg_ids_bytes[0].decode().split()
        #     logger.info(f"  - Found {len(msg_ids_str_list)} email IDs matching criteria.")
        #     return msg_ids_str_list
        #
        # except Exception as e:
        #     logger.error(f"Error searching emails in mailbox '{mailbox}': {e}")
        #     return None
        # --- End Conceptual ---
        # Simulate finding some email IDs
        num_found = random.randint(0, 5)
        simulated_ids = [str(random.randint(1000, 2000)) for _ in range(num_found)]
        logger.info(f"  - Conceptually found {len(simulated_ids)} email IDs: {simulated_ids}")
        imap_conn["_selected_mailbox"] = mailbox # Update mock connection state
        return simulated_ids

    def fetch_email_placeholder(self, imap_conn: Any, email_id_str: str, part: str = "(RFC822)") -> Optional[bytes]:
        """
        Conceptually fetches the content of a specific email message.

        Args:
            imap_conn: Conceptual IMAP connection object.
            email_id_str (str): The message ID (as a string) to fetch.
            part (str): The part of the message to fetch (e.g., "(RFC822)" for full message,
                        "(BODY[TEXT])" for text body, "(BODY[HEADER.FIELDS (SUBJECT FROM)])" for specific headers).

        Returns:
            Optional[bytes]: The raw email data as bytes, or None on error.
        """
        if not imap_conn: logger.error("IMAP fetch failed: No connection."); return None
        logger.info(f"Conceptually fetching email ID '{email_id_str}', part '{part}'...")
        # --- Conceptual imaplib Call ---
        # try:
        #     status, msg_data = imap_conn.fetch(email_id_str, part)
        #     if status != 'OK':
        #         logger.error(f"Failed to fetch email ID '{email_id_str}': {msg_data}")
        #         return None
        #
        #     # msg_data is a list of tuples, typically [(b'id (FLAGS (...) BODY[...] {size}', b'raw_email_content'), b')']
        #     # We need the raw email content, which is usually item[1] of the first tuple in item[0] if item[0] is a tuple
        #     raw_email = None
        #     for response_part in msg_data:
        #         if isinstance(response_part, tuple) and len(response_part) > 1 and isinstance(response_part[1], bytes):
        #             raw_email = response_part[1]
        #             break
        #     if raw_email:
        #          logger.info(f"  - Successfully fetched raw email data (length {len(raw_email)} bytes).")
        #          return raw_email
        #     else:
        #          logger.warning(f"  - Could not extract raw email data from fetch response: {msg_data}")
        #          return None
        #
        # except Exception as e:
        #     logger.error(f"Error fetching email ID '{email_id_str}': {e}")
        #     return None
        # --- End Conceptual ---
        # Simulate fetching a dummy email
        simulated_raw_email = (
            f"Subject: Test Email {email_id_str}\n"
            f"From: sender@example.com\n"
            f"To: recipient@example.com\n\n"
            f"This is a simulated email body for message ID {email_id_str}.\n"
            f"Requested part: {part}"
        ).encode('utf-8')
        logger.info(f"  - Conceptually fetched raw email data (length {len(simulated_raw_email)} bytes).")
        return simulated_raw_email

    def parse_email_message_placeholder(self, raw_email_bytes: bytes) -> Optional[Dict[str, Any]]:
        """
        Conceptually parses raw email bytes into a structured dictionary.
        Uses email.parser.BytesParser.

        Args:
            raw_email_bytes (bytes): The raw email content.

        Returns:
            Optional[Dict[str, Any]]: A dictionary with 'subject', 'from', 'to', 'date',
                                     'body_text', 'body_html', 'attachments_info'.
        """
        if not raw_email_bytes: return None
        logger.info(f"Conceptually parsing raw email message (length {len(raw_email_bytes)} bytes)...")
        # --- Conceptual email library Usage ---
        try:
            # Use the modern `policy` for better default handling
            msg = BytesParser(policy=policy.default).parsebytes(raw_email_bytes)

            parsed = {
                "subject": msg.get("Subject", "N/A"),
                "from": msg.get("From", "N/A"),
                "to": msg.get("To", "N/A"),
                "date": msg.get("Date", "N/A"),
                "message_id": msg.get("Message-ID", "N/A"),
                "body_text": None,
                "body_html": None,
                "attachments_info": [] # List of {'filename': str, 'content_type': str, 'size': int}
            }

            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))

                    if "attachment" in content_disposition:
                        filename = part.get_filename()
                        if filename:
                             parsed["attachments_info"].append({
                                 "filename": filename,
                                 "content_type": content_type,
                                 "size": len(part.get_payload(decode=True))
                             })
                    elif content_type == "text/plain" and "attachment" not in content_disposition:
                        charset = part.get_content_charset() or 'utf-8'
                        parsed["body_text"] = part.get_payload(decode=True).decode(charset, errors='replace')
                    elif content_type == "text/html" and "attachment" not in content_disposition:
                        charset = part.get_content_charset() or 'utf-8'
                        parsed["body_html"] = part.get_payload(decode=True).decode(charset, errors='replace')
            else: # Not multipart, assume plain text or html directly
                content_type = msg.get_content_type()
                charset = msg.get_content_charset() or 'utf-8'
                payload = msg.get_payload(decode=True)
                if payload:
                    if content_type == "text/plain":
                        parsed["body_text"] = payload.decode(charset, errors='replace')
                    elif content_type == "text/html":
                        parsed["body_html"] = payload.decode(charset, errors='replace')

            logger.info("  - Email message parsed successfully (conceptually).")
            return parsed
        except Exception as e:
            logger.error(f"Error parsing email message: {e}")
            return None
        # --- End Conceptual ---


# --- Main Execution Block (Example Usage) ---
if __name__ == "__main__":
    print("===========================================")
    print("=== Running Email Interaction Prototypes ===")
    print("===========================================")
    print("(Note: Relies on conceptual implementations. SMTP/IMAP requires correct server details & credentials in env vars)")

    # Ensure necessary environment variables are set for actual testing:
    # DEVIN_SMTP_HOST, DEVIN_SMTP_PORT, DEVIN_SMTP_USER, DEVIN_SMTP_PASSWORD
    # DEVIN_IMAP_HOST, DEVIN_IMAP_PORT, DEVIN_IMAP_USER, DEVIN_IMAP_PASSWORD
    # (Use App Passwords for services like Gmail/Outlook)

    email_proto = EmailPrototype()

    # --- Send Email Example ---
    print("\n--- [Conceptual SMTP Send Example] ---")
    # Replace with your actual sender/recipient for testing if SMTP is configured
    sender = os.environ.get(email_proto.smtp_user_env_var, "sender@example.com")
    recipient = "recipient@example.com" # Test recipient
    subject = f"Devin Prototype Test Email - {time.strftime('%Y-%m-%d %H:%M:%S')}"
    text_body = "Hello from the Devin Email Prototype!\nThis is a plain text message."
    html_body = """
    <html><body>
        <h2>Hello from the Devin Email Prototype!</h2>
        <p>This is an <b>HTML</b> message with some formatting.</p>
        <p>Timestamp: {timestamp}</p>
    </body></html>
    """.format(timestamp=datetime.datetime.now().isoformat())

    # Create dummy attachment file for testing
    dummy_attach_path = "/tmp/devin_email_attachment.txt"
    try:
        with open(dummy_attach_path, "w") as f: f.write("This is a test attachment.")
        attachments_to_send = [dummy_attach_path]
        print(f"Created dummy attachment: {dummy_attach_path}")
    except IOError as e:
        print(f"Could not create dummy attachment: {e}")
        attachments_to_send = None

    # Send the email
    if email_proto.smtp_host and os.environ.get(email_proto.smtp_user_env_var):
        send_success = email_proto.send_email(
            sender_email=sender,
            recipient_emails=recipient,
            subject=subject,
            body_text=text_body,
            body_html=html_body,
            attachments=attachments_to_send
        )
        print(f"Conceptual email send attempt successful: {send_success}")
    else:
        print("Skipping SMTP send example: SMTP host or credentials not configured in environment.")

    if attachments_to_send and os.path.exists(dummy_attach_path):
        os.remove(dummy_attach_path) # Clean up dummy attachment


    # --- Read Email Example (Highly Conceptual IMAP) ---
    print("\n--- [Conceptual IMAP Read Example] ---")
    if not IMAPLIB_AVAILABLE:
         print("imaplib not available. Skipping IMAP examples.")
    elif not email_proto.imap_host or not os.environ.get(email_proto.imap_user_env_var):
         print("Skipping IMAP example: IMAP host or credentials not configured in environment.")
    else:
        imap_connection = email_proto._connect_imap_placeholder()
        if imap_connection:
            print("\nSearching for emails (conceptual)...")
            # Search criteria example: unseen emails with "Devin" in subject
            # email_ids = email_proto.search_emails_placeholder(imap_connection, criteria='(UNSEEN SUBJECT "Devin")')
            email_ids = email_proto.search_emails_placeholder(imap_connection, criteria='ALL')

            if email_ids:
                print(f"Found conceptual email IDs: {email_ids[:3]} (showing first 3)")
                # Fetch the first found email (conceptual)
                if email_ids[0]:
                    raw_email = email_proto.fetch_email_placeholder(imap_connection, email_ids[0])
                    if raw_email:
                        print(f"\nFetched raw email data (ID: {email_ids[0]}, Length: {len(raw_email)} bytes)")
                        # Parse the raw email
                        parsed_email = email_proto.parse_email_message_placeholder(raw_email)
                        if parsed_email:
                             print("\nParsed Email (Conceptual):")
                             print(f"  From: {parsed_email['from']}")
                             print(f"  To: {parsed_email['to']}")
                             print(f"  Subject: {parsed_email['subject']}")
                             print(f"  Date: {parsed_email['date']}")
                             print(f"  Body (Text, first 100 chars): {parsed_email['body_text'][:100] if parsed_email['body_text'] else 'N/A'}...")
                             print(f"  Attachments: {len(parsed_email['attachments_info'])}")
                             for att in parsed_email['attachments_info']: print(f"    - {att['filename']} ({att['content_type']})")
                        else:
                             print("Failed to parse fetched email.")
                    else:
                         print("Failed to fetch email content.")
            else:
                print("No matching emails found (conceptual).")

            email_proto._disconnect_imap_placeholder(imap_connection)
        else:
            print("Failed to establish conceptual IMAP connection.")


    print("\n===========================================")
    print("=== Email Prototypes Complete ===")
    print("===========================================")
