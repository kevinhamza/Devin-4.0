# Devin/community/bug_bounty.py # Manages vulnerability reporting

import uuid
import datetime
import json
import os
import logging
from enum import Enum
from typing import Dict, Any, List, Optional, TypedDict, Literal

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Enums and Data Structures ---

class ReportStatus(str, Enum):
    RECEIVED = "Received"
    TRIAGING = "Triaging"
    VALIDATING = "Validating"
    INVALID = "Invalid"
    DUPLICATE = "Duplicate"
    INFORMATIVE = "Informative"
    FIX_IN_PROGRESS = "Fix in Progress"
    RESOLVED = "Resolved"
    REWARD_PENDING = "Reward Pending"
    REWARDED = "Rewarded"

class SeverityLevel(str, Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    INFORMATIONAL = "Informational"

class VulnerabilityReport(TypedDict):
    """Structure for storing vulnerability report details."""
    report_id: str
    submission_timestamp_utc: str
    reporter_email: str # Or username/ID. Handle PII carefully.
    reporter_pgp_key: Optional[str] # For secure communication
    affected_component: str # e.g., "API Gateway Auth", "Web UI", "Reasoning Engine"
    vulnerability_type: str # e.g., "SQL Injection", "XSS", "RCE", "Information Disclosure"
    severity_assessment: SeverityLevel # Reporter's assessment
    summary: str
    description: str # Detailed description
    reproduction_steps: str
    potential_impact: str
    attachments: List[str] # List of paths/references to attached files (proofs, logs)
    status: ReportStatus
    internal_notes: List[Dict[str, Any]] # e.g., {'timestamp': '...', 'user': 'triage_team', 'note': '...'}
    assigned_ticket_id: Optional[str] # e.g., JIRA or GitHub Issue ID
    reward_amount: Optional[float]
    resolved_timestamp_utc: Optional[str]


# --- Bug Bounty Manager ---

class BugBountyManager:
    """
    Manages the lifecycle of vulnerability reports submitted through a bug bounty program.

    Handles submission, status tracking, and basic management.
    NOTE: This is a conceptual skeleton. A real implementation requires:
        - Persistent storage (database, secure file system).
        - Secure handling of reporter PII and report details.
        - Integration with communication channels (email/Slack for notifications).
        - Integration with internal issue trackers.
        - Robust authorization for status updates/reward assignment.
        - Potential integration with payment systems for rewards.
    """
    # Using simple file persistence for skeleton example (NOT production recommended)
    DEFAULT_STORAGE_PATH = "./data/bug_bounty_reports.json"

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initializes the BugBountyManager.

        Args:
            storage_path (Optional[str]): Path to the file used for storing reports (JSON format).
                                          Defaults to DEFAULT_STORAGE_PATH. If None, uses in-memory only.
        """
        self.storage_path = storage_path or self.DEFAULT_STORAGE_PATH
        self.reports: Dict[str, VulnerabilityReport] = {} # In-memory store {report_id: report_data}
        self._load_reports()
        logger.info(f"BugBountyManager initialized. Storage: {'In-Memory' if not self.storage_path else self.storage_path}")

    def _load_reports(self):
        """Loads reports from the storage file (if configured)."""
        if not self.storage_path or not os.path.exists(self.storage_path):
            logger.info("No persistent report file found or specified. Starting with empty in-memory store.")
            return
        try:
            with open(self.storage_path, 'r') as f:
                self.reports = json.load(f)
            logger.info(f"Loaded {len(self.reports)} reports from '{self.storage_path}'.")
        except (IOError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load reports from '{self.storage_path}': {e}. Starting fresh.")
            self.reports = {} # Reset if loading fails

    def _save_reports(self):
        """Saves the current reports to the storage file (if configured)."""
        if not self.storage_path:
            return # In-memory only
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump(self.reports, f, indent=2)
            # logger.debug(f"Saved {len(self.reports)} reports to '{self.storage_path}'.") # Can be verbose
        except IOError as e:
            logger.error(f"Failed to save reports to '{self.storage_path}': {e}")


    def submit_report(self,
                      reporter_email: str,
                      affected_component: str,
                      vulnerability_type: str,
                      severity: SeverityLevel,
                      summary: str,
                      description: str,
                      reproduction_steps: str,
                      potential_impact: Optional[str] = None,
                      attachments: Optional[List[str]] = None,
                      reporter_pgp_key: Optional[str] = None) -> Optional[str]:
        """
        Submits a new vulnerability report.

        Args:
            reporter_email (str): Email (or identifier) of the reporter.
            affected_component (str): Component/feature affected.
            vulnerability_type (str): Type of vulnerability.
            severity (SeverityLevel): Reporter's assessed severity.
            summary (str): Brief summary/title.
            description (str): Detailed description.
            reproduction_steps (str): Steps to reproduce the vulnerability.
            potential_impact (Optional[str]): Reporter's view on potential impact.
            attachments (Optional[List[str]]): List of references to attached files.
            reporter_pgp_key (Optional[str]): PGP key for secure replies.

        Returns:
            Optional[str]: The unique ID assigned to the report, or None if submission failed.
        """
        logger.info(f"Receiving new vulnerability report submission from: {reporter_email}")
        # --- Basic Input Validation ---
        if not all([reporter_email, affected_component, vulnerability_type, severity, summary, description, reproduction_steps]):
            logger.error("Submission failed: Missing required fields.")
            return None
        try:
            # Validate severity enum
            severity_enum = SeverityLevel(severity)
        except ValueError:
            logger.error(f"Submission failed: Invalid severity level '{severity}'. Must be one of {list(SeverityLevel)}.")
            return None

        # --- Create Report ---
        report_id = f"DVR-{uuid.uuid4().hex[:8].upper()}" # Devin Vulnerability Report ID
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

        report: VulnerabilityReport = {
            "report_id": report_id,
            "submission_timestamp_utc": timestamp,
            "reporter_email": reporter_email, # Handle PII appropriately
            "reporter_pgp_key": reporter_pgp_key,
            "affected_component": affected_component,
            "vulnerability_type": vulnerability_type,
            "severity_assessment": severity_enum,
            "summary": summary,
            "description": description,
            "reproduction_steps": reproduction_steps,
            "potential_impact": potential_impact or "Not specified.",
            "attachments": attachments or [],
            "status": ReportStatus.RECEIVED,
            "internal_notes": [],
            "assigned_ticket_id": None,
            "reward_amount": None,
            "resolved_timestamp_utc": None
        }

        # --- Store Report ---
        self.reports[report_id] = report
        self._save_reports() # Persist change

        logger.info(f"Report '{report_id}' submitted successfully.")

        # --- Placeholder: Send Acknowledgement ---
        # Send an email or notification to the reporter confirming receipt.
        # If PGP key provided, consider encrypting communication.
        self._send_notification(
            recipient=reporter_email,
            subject=f"Devin Bug Bounty: Report Received ({report_id})",
            body=f"Thank you for your submission '{summary}'. Your report ID is {report_id}. We will review it shortly.",
            pgp_key=reporter_pgp_key
        )
        # --- End Placeholder ---

        # --- Placeholder: Notify Internal Team ---
        self._notify_internal_team(
            channel="#security-bug-bounty", # Example Slack channel
            message=f"New Bug Bounty Report Received: ID={report_id}, Severity={severity}, Summary='{summary}'"
        )
        # --- End Placeholder ---

        return report_id

    def get_report(self, report_id: str) -> Optional[VulnerabilityReport]:
        """Retrieves the full details of a specific report."""
        logger.debug(f"Retrieving report details for ID: {report_id}")
        report = self.reports.get(report_id)
        if not report:
             logger.warning(f"Report ID '{report_id}' not found.")
        return report

    def get_report_status(self, report_id: str) -> Optional[ReportStatus]:
        """Gets the current status of a report."""
        report = self.get_report(report_id)
        return report['status'] if report else None

    def list_reports(self, status_filter: Optional[List[ReportStatus]] = None, max_results: int = 100) -> List[Dict[str, Any]]:
        """Lists reports, optionally filtered by status. Returns summaries."""
        logger.info(f"Listing reports (Filter: {status_filter}, Max: {max_results})...")
        results = []
        count = 0
        # Iterate in reverse chronological order (approximated by insertion order here)
        for report_id, report in reversed(self.reports.items()):
            if count >= max_results:
                break
            if status_filter is None or report['status'] in status_filter:
                # Return only summary info for listing
                results.append({
                    "report_id": report_id,
                    "summary": report['summary'],
                    "status": report['status'],
                    "severity": report['severity_assessment'],
                    "reporter": report['reporter_email'], # Consider anonymizing in public lists
                    "submitted_at": report['submission_timestamp_utc']
                })
                count += 1
        logger.info(f"Found {len(results)} reports matching criteria.")
        return results

    def update_report_status(self, report_id: str, new_status: ReportStatus, internal_note: str, updating_user: str = "System") -> bool:
        """
        Updates the status of a report and adds an internal note.
        Requires authorization in a real system.
        """
        logger.info(f"Attempting to update status for report '{report_id}' to '{new_status}' by user '{updating_user}'.")
        if report_id not in self.reports:
            logger.error(f"Update failed: Report ID '{report_id}' not found.")
            return False

        # --- Placeholder: Authorization Check ---
        # if not has_permission(updating_user, 'update_bug_report'):
        #     logger.error(f"Update failed: User '{updating_user}' lacks permission.")
        #     return False
        # --- End Placeholder ---

        try:
            status_enum = ReportStatus(new_status) # Validate status
        except ValueError:
            logger.error(f"Update failed: Invalid status value '{new_status}'.")
            return False

        report = self.reports[report_id]
        old_status = report['status']
        report['status'] = status_enum
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        note_entry = {
            "timestamp": timestamp,
            "user": updating_user,
            "action": f"Status changed from {old_status} to {status_enum}",
            "note": internal_note
        }
        report['internal_notes'].append(note_entry)

        if status_enum == ReportStatus.RESOLVED:
            report['resolved_timestamp_utc'] = timestamp

        self._save_reports() # Persist change
        logger.info(f"Successfully updated status for report '{report_id}' to '{status_enum}'.")

        # --- Placeholder: Notify Reporter (Optional) ---
        # self._send_notification(
        #     recipient=report['reporter_email'],
        #     subject=f"Devin Bug Bounty: Update on Report {report_id}",
        #     body=f"The status of your report '{report['summary']}' has been updated to: {status_enum}.\n\nNote: {internal_note}",
        #     pgp_key=report['reporter_pgp_key']
        # )
        # --- End Placeholder ---

        return True

    def assign_reward(self, report_id: str, amount: float, justification: str, assigning_user: str = "System") -> bool:
        """Assigns a reward amount to a validated report."""
        logger.info(f"Attempting to assign reward for report '{report_id}' by user '{assigning_user}'.")
         # --- Placeholder: Authorization Check ---
        if report_id not in self.reports:
            logger.error(f"Reward assignment failed: Report ID '{report_id}' not found.")
            return False

        report = self.reports[report_id]
        # Check if report is in a state eligible for reward (e.g., Resolved, Validating)
        if report['status'] not in [ReportStatus.RESOLVED, ReportStatus.VALIDATING, ReportStatus.FIX_IN_PROGRESS, ReportStatus.REWARD_PENDING]:
             logger.warning(f"Cannot assign reward: Report '{report_id}' is in status '{report['status']}'. Expected resolved/valid.")
             # return False # Or allow assignment regardless of status?

        report['reward_amount'] = amount
        report['status'] = ReportStatus.REWARD_PENDING # Update status
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        note_entry = {
             "timestamp": timestamp,
             "user": assigning_user,
             "action": f"Reward of {amount} assigned.",
             "note": justification
        }
        report['internal_notes'].append(note_entry)
        self._save_reports()
        logger.info(f"Reward of {amount} assigned to report '{report_id}'. Status set to '{ReportStatus.REWARD_PENDING}'.")

        # --- Placeholder: Trigger Payment Process ---
        # self._trigger_reward_payment(report_id, report['reporter_email'], amount)
        # --- End Placeholder ---

        return True

    # --- Placeholder Notification/Integration Methods ---
    def _send_notification(self, recipient: str, subject: str, body: str, pgp_key: Optional[str] = None):
        """Placeholder: Sends notification (e.g., email) to reporter."""
        logger.info(f"Placeholder: Sending notification to {recipient} (Subject: {subject})")
        if pgp_key: logger.info("  - (Conceptual: Would encrypt using provided PGP key)")
        # Integrate with an actual email service (e.g., using smtplib, SendGrid API)

    def _notify_internal_team(self, channel: str, message: str):
        """Placeholder: Sends notification to internal team (e.g., Slack)."""
        logger.info(f"Placeholder: Sending internal notification to {channel}: {message}")
        # Integrate with Slack API, MS Teams, etc.

    def _create_issue_ticket(self, report: VulnerabilityReport) -> Optional[str]:
         """Placeholder: Creates issue in tracker (Jira, GitHub Issues)."""
         logger.info(f"Placeholder: Creating issue ticket for report {report['report_id']}...")
         # Integrate with Jira/GitHub API
         ticket_id = f"DEVIN-{random.randint(1000, 9999)}" # Simulate ID
         logger.info(f"  - Conceptual ticket created: {ticket_id}")
         return ticket_id


# Example Usage (conceptual)
if __name__ == "__main__":
    print("\n--- Bug Bounty Manager Example ---")

    # Use a temporary file for this example run
    temp_storage = "./temp_bounty_reports.json"
    if os.path.exists(temp_storage): os.remove(temp_storage)

    manager = BugBountyManager(storage_path=temp_storage)

    # Submit a report
    report_id_1 = manager.submit_report(
        reporter_email="researcher@example.com",
        affected_component="API Gateway Auth Middleware",
        vulnerability_type="Improper Authentication",
        severity=SeverityLevel.HIGH,
        summary="JWT validation bypass possible via crafted token",
        description="Detailed steps on how the signature check can be bypassed...",
        reproduction_steps="1. Craft token...\n2. Send request...\n3. Observe bypass.",
        potential_impact="Unauthorized access to protected API endpoints.",
        attachments=["/path/to/proof_of_concept.py", "/path/to/logs.txt"] # Conceptual paths
    )
    print(f"Submitted Report 1 ID: {report_id_1}")

    # Submit another report
    report_id_2 = manager.submit_report(
        reporter_email="tester@example.org",
        affected_component="Web UI",
        vulnerability_type="Cross-Site Scripting (XSS)",
        severity=SeverityLevel.MEDIUM,
        summary="Reflected XSS in search results page",
        description="The search query parameter is not properly sanitized...",
        reproduction_steps="1. Go to /search?q=<script>alert(1)</script>\n2. Observe alert box.",
    )
    print(f"Submitted Report 2 ID: {report_id_2}")

    # List received reports
    print("\nListing 'Received' reports:")
    received_reports = manager.list_reports(status_filter=[ReportStatus.RECEIVED])
    for r in received_reports:
        print(f"  - ID: {r['report_id']}, Summary: {r['summary']}, Reporter: {r['reporter']}")

    # Update status of the first report
    if report_id_1:
        print(f"\nUpdating status for {report_id_1}:")
        update_ok = manager.update_report_status(
            report_id=report_id_1,
            new_status=ReportStatus.VALIDATING,
            internal_note="Assigned to security team lead for validation.",
            updating_user="triage_bot"
        )
        print(f"Update successful: {update_ok}")
        print(f"New status: {manager.get_report_status(report_id_1)}")

    # Assign reward conceptually
    if report_id_1:
        print(f"\nAssigning reward for {report_id_1}:")
        reward_ok = manager.assign_reward(
            report_id=report_id_1,
            amount=500.00,
            justification="Critical authentication bypass confirmed.",
            assigning_user="security_lead"
        )
        print(f"Assign reward successful: {reward_ok}")
        print(f"New status: {manager.get_report_status(report_id_1)}")


    # Verify persistence (conceptual)
    print("\nReloading manager to check persistence...")
    del manager # Delete instance
    manager_reloaded = BugBountyManager(storage_path=temp_storage)
    print(f"Number of reports after reload: {len(manager_reloaded.reports)}")
    reloaded_report = manager_reloaded.get_report(report_id_1)
    if reloaded_report:
        print(f"Status of reloaded report {report_id_1}: {reloaded_report['status']}")


    # Clean up temp file
    if os.path.exists(temp_storage): os.remove(temp_storage)

    print("\n--- End Example ---")
