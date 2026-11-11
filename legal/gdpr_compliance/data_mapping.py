# Devin/legal/gdpr_compliance/data_mapping.py
# Purpose: Defines and manages a conceptual data map for GDPR compliance,
#          including records of processing activities (ROPA - Article 30).

import logging
import os
import sys
import uuid
from enum import Enum, auto
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Literal, Union, Set, Any
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger("GDPRDataMapping")

# --- Enums ---

class DataCategory(Enum):
    USER_IDENTIFIERS = "User Identifiers & Authentication"
    CONTACT_INFORMATION = "Contact Information"
    USER_PROFILE_PREFERENCES = "User Profile & Preferences"
    USER_GENERATED_CONTENT_INPUT = "User-Generated Content & Inputs"
    USER_GENERATED_CONTENT_OUTPUT = "AI-Generated Content & Outputs for User"
    USAGE_ANALYTICS_INTERACTION = "Usage Analytics & Interaction Data"
    DEVICE_TECHNICAL_INFORMATION = "Device & Technical Information"
    LOCATION_DATA = "Location Data"
    FINANCIAL_PAYMENT_INFORMATION = "Financial & Payment Information"
    SUPPORT_COMMUNICATION = "Support & Communication Logs"
    THIRD_PARTY_INTEGRATION_DATA = "Third-Party Integration Data"
    EMPLOYEE_CONTRACTOR_DATA = "Employee/Contractor Data"
    MARKETING_PREFERENCES = "Marketing Preferences"
    LEGAL_CONSENT_RECORDS = "Legal & Consent Records"

class DataSensitivityLevel(Enum):
    PUBLIC = auto()
    INTERNAL = auto()
    CONFIDENTIAL_PII = auto()
    HIGHLY_SENSITIVE_PII = auto()
    STRICTLY_CONFIDENTIAL_SECRET = auto()

class LegalBasisProcessing(Enum):
    CONSENT = "Consent (Art. 6(1)(a))"
    CONTRACT = "Performance of a Contract (Art. 6(1)(b))"
    LEGAL_OBLIGATION = "Compliance with a Legal Obligation (Art. 6(1)(c))"
    VITAL_INTERESTS = "Protection of Vital Interests (Art. 6(1)(d))"
    PUBLIC_TASK = "Performance of a Public Task (Art. 6(1)(e))"
    LEGITIMATE_INTERESTS = "Legitimate Interests (Art. 6(1)(f))"
    EXPLICIT_CONSENT_SPECIAL = "Explicit Consent for Special Category Data (Art. 9(2)(a))"
    EMPLOYMENT_SOCIAL_SECURITY_LAW = "Employment, Social Security, Social Protection Law (Art. 9(2)(b))"

class RecipientType(Enum):
    INTERNAL_TEAM = "Internal Team/System"
    THIRD_PARTY_PROCESSOR = "Third-Party Data Processor"
    JOINT_CONTROLLER = "Joint Controller"
    INDEPENDENT_CONTROLLER = "Independent Controller"
    LEGAL_AUTHORITY = "Legal/Regulatory Authority"

# --- Dataclasses ---

@dataclass
class DataElement:
    element_id: str
    name: str
    description: str
    categories: Set[DataCategory]
    is_personal_data: bool
    is_special_category_data: bool = False
    sensitivity_level: DataSensitivityLevel = DataSensitivityLevel.CONFIDENTIAL_PII
    examples: List[str] = field(default_factory=list)
    source_systems: List[str] = field(default_factory=list)
    data_subject_types: List[str] = field(default_factory=list)

@dataclass
class DataRecipient:
    recipient_id: str
    name: str
    recipient_type: RecipientType
    location: Optional[str] = None
    data_transfer_mechanism: Optional[str] = None
    purpose_of_sharing: Optional[str] = None

@dataclass
class ProcessingActivity:
    """Represents a specific processing activity (ROPA entry)."""
    # Required fields (no defaults) must come first
    activity_id: str
    name: str
    description: str
    department_owner: str
    data_controller_details: str
    purposes_of_processing: List[str]
    legal_bases_for_processing: Set[LegalBasisProcessing]
    data_subject_categories: Set[str]
    data_retention_period: str
    # Optional / defaulted fields follow
    dpo_contact_details: Optional[str] = None
    data_elements_processed_ids: Set[str] = field(default_factory=set)
    data_recipients_ids: Set[str] = field(default_factory=set)
    transfers_to_third_country_or_international_org: bool = False
    third_country_or_org_name: Optional[str] = None
    safeguards_for_transfer: Optional[str] = None
    technical_organizational_security_measures: List[str] = field(default_factory=list)
    data_protection_impact_assessment_conducted: bool = False
    dpia_reference_or_date: Optional[str] = None
    last_reviewed_date: Optional[str] = None
    version: int = 1


class DevinDataMap:
    """
    Manages the collection of data elements and processing activities for Devin.
    Serves as a conceptual in-memory GDPR data map / ROPA store.
    """

    def __init__(self):
        self.data_elements: Dict[str, DataElement] = {}
        self.data_recipients: Dict[str, DataRecipient] = {}
        self.processing_activities: Dict[str, ProcessingActivity] = {}
        self._load_all_definitions()
        logger.info("DevinDataMap initialized with conceptual data elements and processing activities.")

    def _add_data_element(self, de: DataElement):
        if de.element_id in self.data_elements:
            logger.warning(f"DataElement with ID '{de.element_id}' already exists. Overwriting.")
        self.data_elements[de.element_id] = de

    def _add_data_recipient(self, dr: DataRecipient):
        if dr.recipient_id in self.data_recipients:
            logger.warning(f"DataRecipient with ID '{dr.recipient_id}' already exists. Overwriting.")
        self.data_recipients[dr.recipient_id] = dr

    def _add_processing_activity(self, pa: ProcessingActivity):
        for de_id in pa.data_elements_processed_ids:
            if de_id not in self.data_elements:
                raise ValueError(
                    f"ProcessingActivity '{pa.activity_id}' references non-existent "
                    f"DataElement ID '{de_id}'. Define DataElements first."
                )
        for dr_id in pa.data_recipients_ids:
            if dr_id not in self.data_recipients:
                raise ValueError(
                    f"ProcessingActivity '{pa.activity_id}' references non-existent "
                    f"DataRecipient ID '{dr_id}'. Define DataRecipients first."
                )
        if pa.activity_id in self.processing_activities:
            logger.warning(f"ProcessingActivity with ID '{pa.activity_id}' already exists. Overwriting.")
        self.processing_activities[pa.activity_id] = pa

    def _load_all_definitions(self):
        """Loads all predefined data elements, recipients, and processing activities."""
        self._define_data_elements()
        self._define_data_recipients()
        self._define_processing_activities()
        logger.info(
            f"DevinDataMap fully loaded: {len(self.data_elements)} elements, "
            f"{len(self.data_recipients)} recipients, "
            f"{len(self.processing_activities)} activities."
        )

    def _define_data_elements(self):
        elements = [
            DataElement(element_id="DE001", name="User ID",
                        description="Unique identifier for a Devin user.",
                        categories={DataCategory.USER_IDENTIFIERS}, is_personal_data=True,
                        sensitivity_level=DataSensitivityLevel.CONFIDENTIAL_PII,
                        examples=["user_12345abc"],
                        source_systems=["Devin Auth Service", "User Database"],
                        data_subject_types=["Registered User"]),
            DataElement(element_id="DE002", name="Username/Login Handle",
                        description="User-chosen or assigned username.",
                        categories={DataCategory.USER_IDENTIFIERS}, is_personal_data=True,
                        sensitivity_level=DataSensitivityLevel.CONFIDENTIAL_PII,
                        examples=["john_doe", "devin_master"],
                        source_systems=["User Input", "Devin Auth Service"],
                        data_subject_types=["Registered User"]),
            DataElement(element_id="DE003", name="Hashed Password",
                        description="User's password, hashed and salted.",
                        categories={DataCategory.USER_IDENTIFIERS}, is_personal_data=True,
                        sensitivity_level=DataSensitivityLevel.HIGHLY_SENSITIVE_PII,
                        examples=["$2b$12$.... (bcrypt hash)"],
                        source_systems=["Devin Auth Service"],
                        data_subject_types=["Registered User"]),
            DataElement(element_id="DE004", name="Authentication Tokens",
                        description="OAuth tokens, session cookies, API keys.",
                        categories={DataCategory.USER_IDENTIFIERS}, is_personal_data=True,
                        sensitivity_level=DataSensitivityLevel.HIGHLY_SENSITIVE_PII,
                        examples=["jwt_token_string", "session_id_abc"],
                        source_systems=["Devin Auth Service", "Browser Storage"],
                        data_subject_types=["Registered User", "API User"]),
            DataElement(element_id="DE005", name="Email Address",
                        description="User's email address.",
                        categories={DataCategory.CONTACT_INFORMATION, DataCategory.USER_IDENTIFIERS},
                        is_personal_data=True,
                        sensitivity_level=DataSensitivityLevel.CONFIDENTIAL_PII,
                        examples=["jane.doe@example.com"],
                        source_systems=["User Input", "SSO Provider"],
                        data_subject_types=["Registered User", "Support Requester"]),
            DataElement(element_id="DE006", name="Phone Number",
                        description="User's phone number (optional).",
                        categories={DataCategory.CONTACT_INFORMATION}, is_personal_data=True,
                        sensitivity_level=DataSensitivityLevel.CONFIDENTIAL_PII,
                        examples=["+1-555-123-4567"],
                        source_systems=["User Input"],
                        data_subject_types=["Registered User"]),
            DataElement(element_id="DE007", name="Display Name",
                        description="User's chosen display name.",
                        categories={DataCategory.USER_PROFILE_PREFERENCES}, is_personal_data=True,
                        sensitivity_level=DataSensitivityLevel.CONFIDENTIAL_PII,
                        examples=["Jane D."],
                        source_systems=["User Input"],
                        data_subject_types=["Registered User"]),
            DataElement(element_id="DE008", name="User Preferences",
                        description="Application settings, language, theme, notification settings.",
                        categories={DataCategory.USER_PROFILE_PREFERENCES}, is_personal_data=False,
                        sensitivity_level=DataSensitivityLevel.INTERNAL,
                        examples=["{'theme':'dark', 'lang':'en'}"],
                        source_systems=["User Input", "Application"],
                        data_subject_types=["Registered User"]),
            DataElement(element_id="DE009", name="User Prompts & Queries",
                        description="Text, voice, or other inputs provided by the user to Devin.",
                        categories={DataCategory.USER_GENERATED_CONTENT_INPUT}, is_personal_data=True,
                        sensitivity_level=DataSensitivityLevel.CONFIDENTIAL_PII,
                        examples=["'Write python code for a web scraper'"],
                        source_systems=["User Interface", "API Input"],
                        data_subject_types=["Registered User"]),
            DataElement(element_id="DE010", name="Uploaded Files/Code by User",
                        description="Files, code snippets, or data uploaded by the user.",
                        categories={DataCategory.USER_GENERATED_CONTENT_INPUT}, is_personal_data=True,
                        sensitivity_level=DataSensitivityLevel.HIGHLY_SENSITIVE_PII,
                        examples=["my_project_code.zip", "financial_data.csv"],
                        source_systems=["User Interface Upload"],
                        data_subject_types=["Registered User"]),
            DataElement(element_id="DE011", name="Generated Code/Text by Devin",
                        description="Code, text, summaries generated by Devin based on user input.",
                        categories={DataCategory.USER_GENERATED_CONTENT_OUTPUT}, is_personal_data=False,
                        sensitivity_level=DataSensitivityLevel.INTERNAL,
                        examples=["def hello(): print('Hello')"],
                        source_systems=["Devin AI Core"],
                        data_subject_types=["Registered User"]),
            DataElement(element_id="DE012", name="Devin Action Logs/Execution Traces",
                        description="Logs of actions Devin takes on behalf of the user.",
                        categories={DataCategory.USER_GENERATED_CONTENT_OUTPUT,
                                    DataCategory.USAGE_ANALYTICS_INTERACTION},
                        is_personal_data=True,
                        sensitivity_level=DataSensitivityLevel.CONFIDENTIAL_PII,
                        examples=["Created file /tmp/user_code/script.py"],
                        source_systems=["Devin Agent Execution Environment"],
                        data_subject_types=["Registered User"]),
            DataElement(element_id="DE013", name="IP Address",
                        description="IP address of the user connecting to Devin.",
                        categories={DataCategory.DEVICE_TECHNICAL_INFORMATION,
                                    DataCategory.USAGE_ANALYTICS_INTERACTION},
                        is_personal_data=True,
                        sensitivity_level=DataSensitivityLevel.CONFIDENTIAL_PII,
                        examples=["192.168.1.100", "2001:db8::1"],
                        source_systems=["Web Server Logs", "Application Server"],
                        data_subject_types=["Registered User", "Website Visitor"]),
            DataElement(element_id="DE014", name="User-Agent String",
                        description="Browser/client user-agent information.",
                        categories={DataCategory.DEVICE_TECHNICAL_INFORMATION}, is_personal_data=True,
                        sensitivity_level=DataSensitivityLevel.CONFIDENTIAL_PII,
                        examples=["Mozilla/5.0 (...) Chrome/90.0"],
                        source_systems=["Web Server Logs"],
                        data_subject_types=["Registered User", "Website Visitor"]),
            DataElement(element_id="DE015", name="Interaction Timestamps & Events",
                        description="Timestamps of login, logout, feature usage, button clicks.",
                        categories={DataCategory.USAGE_ANALYTICS_INTERACTION}, is_personal_data=True,
                        sensitivity_level=DataSensitivityLevel.CONFIDENTIAL_PII,
                        examples=["'login_success': '2025-05-21T15:30:00Z'"],
                        source_systems=["Application Logs", "Analytics Service"],
                        data_subject_types=["Registered User"]),
            DataElement(element_id="DE016", name="Session ID",
                        description="Identifier for a user's session.",
                        categories={DataCategory.USAGE_ANALYTICS_INTERACTION,
                                    DataCategory.USER_IDENTIFIERS},
                        is_personal_data=True,
                        sensitivity_level=DataSensitivityLevel.CONFIDENTIAL_PII,
                        examples=["session_xyz789"],
                        source_systems=["Application Server", "Web Server"],
                        data_subject_types=["Registered User", "Website Visitor"]),
            DataElement(element_id="DE017", name="Third-Party Service Tokens",
                        description="Access/refresh tokens for integrated services like GitHub, Jira.",
                        categories={DataCategory.THIRD_PARTY_INTEGRATION_DATA,
                                    DataCategory.USER_IDENTIFIERS},
                        is_personal_data=True,
                        sensitivity_level=DataSensitivityLevel.HIGHLY_SENSITIVE_PII,
                        examples=["github_oauth_token_xxx"],
                        source_systems=["User Input (OAuth flow)", "Devin Integration Manager"],
                        data_subject_types=["Registered User"]),
            DataElement(element_id="DE018", name="Data Retrieved from Third-Party Services",
                        description="Content retrieved from integrated services.",
                        categories={DataCategory.THIRD_PARTY_INTEGRATION_DATA}, is_personal_data=True,
                        sensitivity_level=DataSensitivityLevel.CONFIDENTIAL_PII,
                        examples=["List of files in a GitHub repo", "Jira issue description"],
                        source_systems=["External APIs (GitHub, Jira, etc.)"],
                        data_subject_types=["Registered User"]),
            DataElement(element_id="DE019", name="Consent Records",
                        description="Records of user consent for specific processing activities.",
                        categories={DataCategory.LEGAL_CONSENT_RECORDS}, is_personal_data=True,
                        sensitivity_level=DataSensitivityLevel.CONFIDENTIAL_PII,
                        examples=["User 'user_123' consented to 'marketing_emails' on 2025-01-15."],
                        source_systems=["Consent Management Platform", "Application Database"],
                        data_subject_types=["Registered User", "Website Visitor"]),
            DataElement(element_id="DE020", name="Terms of Service Acceptance",
                        description="Record of user accepting ToS.",
                        categories={DataCategory.LEGAL_CONSENT_RECORDS}, is_personal_data=True,
                        sensitivity_level=DataSensitivityLevel.CONFIDENTIAL_PII,
                        examples=["User 'user_123' accepted ToS version 3.1 on 2025-01-10."],
                        source_systems=["Application Database"],
                        data_subject_types=["Registered User"]),
            DataElement(element_id="DE023", name="Support Ticket Content",
                        description="User's messages and attachments submitted via support channels.",
                        categories={DataCategory.SUPPORT_COMMUNICATION}, is_personal_data=True,
                        sensitivity_level=DataSensitivityLevel.CONFIDENTIAL_PII,
                        source_systems=["Support System (e.g., Zendesk, Intercom)", "Email"],
                        data_subject_types=["Registered User", "Support Requester"]),
        ]
        for el in elements:
            self._add_data_element(el)
        logger.info(f"Defined {len(self.data_elements)} conceptual data elements.")

    def _define_data_recipients(self):
        recipients = [
            DataRecipient(recipient_id="DR001", name="Devin Primary Application Database",
                          recipient_type=RecipientType.INTERNAL_TEAM,
                          location="Cloud Region (e.g., US-East-1)",
                          purpose_of_sharing="Core application functionality, data persistence."),
            DataRecipient(recipient_id="DR002", name="Devin Log Aggregation System (Loki)",
                          recipient_type=RecipientType.INTERNAL_TEAM,
                          location="Cloud Region",
                          purpose_of_sharing="Troubleshooting, monitoring, security auditing."),
            DataRecipient(recipient_id="DR003", name="Devin Analytics Platform",
                          recipient_type=RecipientType.INTERNAL_TEAM,
                          location="Cloud Region",
                          purpose_of_sharing="Product improvement, usage analysis."),
            DataRecipient(recipient_id="DR004", name="Devin Customer Support Team",
                          recipient_type=RecipientType.INTERNAL_TEAM,
                          location="Global",
                          purpose_of_sharing="Providing user support, resolving issues."),
            DataRecipient(recipient_id="DR005", name="Cloud Hosting Provider (e.g., AWS, GCP, Azure)",
                          recipient_type=RecipientType.THIRD_PARTY_PROCESSOR,
                          location="Configurable Cloud Regions",
                          data_transfer_mechanism="SCCs/BCRs/Adequacy",
                          purpose_of_sharing="Infrastructure hosting (compute, storage, networking)."),
            DataRecipient(recipient_id="DR006", name="LLM API Provider (e.g., OpenAI, Anthropic)",
                          recipient_type=RecipientType.THIRD_PARTY_PROCESSOR,
                          location="Primarily USA (check provider specifics)",
                          data_transfer_mechanism="SCCs/DPA",
                          purpose_of_sharing="Core AI text/code generation capabilities."),
            DataRecipient(recipient_id="DR007", name="Payment Processor (e.g., Stripe, PayPal)",
                          recipient_type=RecipientType.THIRD_PARTY_PROCESSOR,
                          location="Global/USA",
                          data_transfer_mechanism="SCCs/BCRs/PCI-DSS",
                          purpose_of_sharing="Processing subscription payments (if applicable)."),
            DataRecipient(recipient_id="DR008", name="Email Service Provider (e.g., SendGrid, Mailgun)",
                          recipient_type=RecipientType.THIRD_PARTY_PROCESSOR,
                          location="USA/Global",
                          data_transfer_mechanism="SCCs/DPA",
                          purpose_of_sharing="Sending transactional and marketing emails."),
            DataRecipient(recipient_id="DR009", name="Customer Support Platform (e.g., Zendesk)",
                          recipient_type=RecipientType.THIRD_PARTY_PROCESSOR,
                          location="USA/Global",
                          data_transfer_mechanism="SCCs/DPA",
                          purpose_of_sharing="Managing customer support interactions."),
            DataRecipient(recipient_id="DR010", name="Analytics Service (e.g., Mixpanel, Google Analytics)",
                          recipient_type=RecipientType.THIRD_PARTY_PROCESSOR,
                          location="USA/Global",
                          data_transfer_mechanism="SCCs/DPA",
                          purpose_of_sharing="Tracking user behavior for product improvement."),
        ]
        for dr in recipients:
            self._add_data_recipient(dr)
        logger.info(f"Defined {len(self.data_recipients)} conceptual data recipients.")

    def _define_processing_activities(self):
        activities = [
            ProcessingActivity(
                activity_id="PA001", name="User Account Registration",
                description="Collection and storage of user information to create and manage their Devin account.",
                department_owner="Engineering/Product",
                data_controller_details="Devin Corp, 123 AI Lane, Tech City, contact@devin.ai",
                dpo_contact_details="dpo@devin.ai (if applicable)",
                purposes_of_processing=[
                    "To provide user access to Devin services",
                    "Account management and security",
                    "Communication regarding the account",
                ],
                legal_bases_for_processing={LegalBasisProcessing.CONTRACT,
                                            LegalBasisProcessing.LEGITIMATE_INTERESTS},
                data_subject_categories={"Registered Users", "Prospective Users"},
                data_elements_processed_ids={"DE001", "DE002", "DE003", "DE005",
                                             "DE007", "DE013", "DE014", "DE020"},
                data_recipients_ids={"DR001", "DR002", "DR005", "DR008"},
                data_retention_period="Duration of account activity + 3 years for legal claims.",
                technical_organizational_security_measures=[
                    "Password hashing (bcrypt/scrypt)",
                    "HTTPS/TLS for data in transit",
                    "Role-based access control (RBAC)",
                    "Regular security patching",
                    "Data backup and recovery procedures",
                ],
                last_reviewed_date=datetime.now().strftime("%Y-%m-%d"),
            ),
            ProcessingActivity(
                activity_id="PA002", name="User Authentication & Session Management",
                description="Verifying user identity and managing user sessions for secure access.",
                department_owner="Engineering",
                data_controller_details="Devin Corp, 123 AI Lane, Tech City, contact@devin.ai",
                purposes_of_processing=[
                    "Securely authenticate users",
                    "Maintain user sessions",
                    "Prevent unauthorized access",
                ],
                legal_bases_for_processing={LegalBasisProcessing.CONTRACT,
                                            LegalBasisProcessing.LEGITIMATE_INTERESTS},
                data_subject_categories={"Registered Users"},
                data_elements_processed_ids={"DE001", "DE002", "DE003", "DE004", "DE013", "DE016"},
                data_recipients_ids={"DR001", "DR002", "DR005"},
                data_retention_period="Auth tokens: Session duration or token expiry. Session logs: 90 days.",
                technical_organizational_security_measures=[
                    "Secure token generation & storage",
                    "HTTPS/TLS",
                    "Brute-force protection",
                    "Session timeout policies",
                ],
                last_reviewed_date=datetime.now().strftime("%Y-%m-%d"),
            ),
            ProcessingActivity(
                activity_id="PA003", name="Processing User Prompts with LLM",
                description="Sending user prompts/queries and relevant context to an LLM API to generate responses.",
                department_owner="AI/ML Engineering",
                data_controller_details="Devin Corp, 123 AI Lane, Tech City, contact@devin.ai",
                purposes_of_processing=[
                    "To fulfill user requests for AI-generated content/actions",
                    "To provide core Devin AI functionality",
                ],
                legal_bases_for_processing={LegalBasisProcessing.CONTRACT},
                data_subject_categories={"Registered Users"},
                data_elements_processed_ids={"DE001", "DE009", "DE010", "DE018"},
                data_recipients_ids={"DR006", "DR002", "DR005"},
                transfers_to_third_country_or_international_org=True,
                third_country_or_org_name="LLM API Provider (e.g., USA)",
                safeguards_for_transfer="Standard Contractual Clauses (SCCs), Data Processing Addendum (DPA).",
                data_retention_period="Prompts: session scope unless saved by user. Logs: 90 days.",
                technical_organizational_security_measures=[
                    "API key security",
                    "Data minimization in prompts where possible",
                    "Review of LLM provider's data handling policies",
                    "HTTPS/TLS for API calls",
                ],
                data_protection_impact_assessment_conducted=True,
                dpia_reference_or_date="DPIA_LLM_Usage_v1_" + datetime.now().strftime("%Y%m%d"),
                last_reviewed_date=datetime.now().strftime("%Y-%m-%d"),
            ),
            ProcessingActivity(
                activity_id="PA004", name="Storing User-Generated Content",
                description="Storing content actively created or saved by the user within Devin.",
                department_owner="Engineering/Product",
                data_controller_details="Devin Corp, 123 AI Lane, Tech City, contact@devin.ai",
                purposes_of_processing=[
                    "To allow users to persist their work",
                    "To enable project continuity and collaboration",
                ],
                legal_bases_for_processing={LegalBasisProcessing.CONTRACT},
                data_subject_categories={"Registered Users"},
                data_elements_processed_ids={"DE001", "DE009", "DE010", "DE011", "DE012"},
                data_recipients_ids={"DR001", "DR005"},
                data_retention_period="As long as the user account is active and content is not deleted.",
                technical_organizational_security_measures=[
                    "Encryption at rest (AES-256)",
                    "Encryption in transit (HTTPS/TLS)",
                    "Access controls",
                    "Regular backups",
                ],
                last_reviewed_date=datetime.now().strftime("%Y-%m-%d"),
            ),
            ProcessingActivity(
                activity_id="PA005", name="Service Usage Analytics & Monitoring",
                description="Collecting and analyzing data about how users interact with Devin.",
                department_owner="Product/Engineering/Security",
                data_controller_details="Devin Corp, 123 AI Lane, Tech City, contact@devin.ai",
                purposes_of_processing=[
                    "To understand service usage patterns",
                    "To identify popular features and areas for improvement",
                    "To detect and prevent fraudulent or abusive activity",
                    "To monitor system performance and stability",
                ],
                legal_bases_for_processing={LegalBasisProcessing.LEGITIMATE_INTERESTS,
                                            LegalBasisProcessing.CONTRACT},
                data_subject_categories={"Registered Users", "Website Visitors"},
                data_elements_processed_ids={"DE001", "DE013", "DE014", "DE015", "DE016", "DE008"},
                data_recipients_ids={"DR002", "DR003", "DR005", "DR010"},
                data_retention_period="Aggregated analytics: Indefinitely (anonymized). Raw logs: 90-180 days.",
                technical_organizational_security_measures=[
                    "Pseudonymization/anonymization where possible for analytics",
                    "Data minimization",
                    "Secure storage and access controls for logs",
                    "Regular review of analytics data for PII leakage",
                ],
                last_reviewed_date=datetime.now().strftime("%Y-%m-%d"),
            ),
            ProcessingActivity(
                activity_id="PA006", name="Customer Support Management",
                description="Processing user data to provide customer support and resolve issues.",
                department_owner="Support",
                data_controller_details="Devin Corp, 123 AI Lane, Tech City, contact@devin.ai",
                purposes_of_processing=[
                    "To respond to user inquiries",
                    "To troubleshoot problems",
                    "To improve customer service",
                ],
                legal_bases_for_processing={LegalBasisProcessing.CONTRACT,
                                            LegalBasisProcessing.LEGITIMATE_INTERESTS},
                data_subject_categories={"Registered Users", "Support Requesters"},
                data_elements_processed_ids={"DE001", "DE005", "DE006", "DE009",
                                             "DE012", "DE015", "DE023"},
                data_recipients_ids={"DR004", "DR009", "DR002"},
                data_retention_period="Support tickets: 2 years after resolution.",
                technical_organizational_security_measures=[
                    "Access controls for support platform",
                    "Secure communication channels",
                    "Training for support staff on data privacy",
                ],
                last_reviewed_date=datetime.now().strftime("%Y-%m-%d"),
            ),
        ]
        for act in activities:
            self._add_processing_activity(act)
        logger.info(f"Defined {len(self.processing_activities)} conceptual processing activities.")

    # --- Getter Methods ---

    def get_data_element_by_id(self, element_id: str) -> Optional[DataElement]:
        return self.data_elements.get(element_id)

    def get_data_recipient_by_id(self, recipient_id: str) -> Optional[DataRecipient]:
        return self.data_recipients.get(recipient_id)

    def get_processing_activity_by_id(self, activity_id: str) -> Optional[ProcessingActivity]:
        return self.processing_activities.get(activity_id)

    # --- Query and Reporting ---

    def find_activities_using_data_element(self, element_id: str) -> List[ProcessingActivity]:
        if element_id not in self.data_elements:
            logger.warning(f"Data element ID '{element_id}' not found in the map.")
            return []
        return [
            activity for activity in self.processing_activities.values()
            if element_id in activity.data_elements_processed_ids
        ]

    def find_elements_in_activity(self, activity_id: str) -> List[DataElement]:
        activity = self.get_processing_activity_by_id(activity_id)
        if not activity:
            logger.warning(f"Processing activity ID '{activity_id}' not found.")
            return []
        return [
            self.data_elements[el_id]
            for el_id in activity.data_elements_processed_ids
            if el_id in self.data_elements
        ]

    def generate_ropa_summary_text(self, activity_id: Optional[str] = None) -> str:
        report_lines = ["=" * 30 + " Record of Processing Activities (ROPA) Summary " + "=" * 30]
        activities_to_report: List[ProcessingActivity] = []
        if activity_id:
            activity = self.get_processing_activity_by_id(activity_id)
            if activity:
                activities_to_report.append(activity)
            else:
                return f"No processing activity found with ID: {activity_id}"
        else:
            activities_to_report = list(self.processing_activities.values())
            report_lines.append(f"Summary for all {len(activities_to_report)} processing activities.")

        if not activities_to_report:
            return "No processing activities to report on."

        for i, activity in enumerate(activities_to_report):
            report_lines.append(f"\n--- Activity {i+1}: {activity.name} (ID: {activity.activity_id}) ---")
            report_lines.append(f"  Description: {activity.description}")
            report_lines.append(f"  Owner Department: {activity.department_owner}")
            report_lines.append(f"  Controller: {activity.data_controller_details}")
            if activity.dpo_contact_details:
                report_lines.append(f"  DPO Contact: {activity.dpo_contact_details}")
            report_lines.append(f"  Purposes: {'; '.join(activity.purposes_of_processing)}")
            report_lines.append(f"  Legal Bases: {', '.join(lb.value for lb in activity.legal_bases_for_processing)}")
            report_lines.append(f"  Data Subject Categories: {', '.join(activity.data_subject_categories)}")
            report_lines.append("  Data Elements Processed:")
            for el_id in activity.data_elements_processed_ids:
                element = self.get_data_element_by_id(el_id)
                if element:
                    report_lines.append(
                        f"    - {element.name} (ID: {el_id}, "
                        f"Categories: {[cat.name for cat in element.categories]}, "
                        f"PII: {element.is_personal_data}, "
                        f"Sensitivity: {element.sensitivity_level.name})"
                    )
            report_lines.append("  Data Recipients:")
            for rec_id in activity.data_recipients_ids:
                recipient = self.get_data_recipient_by_id(rec_id)
                if recipient:
                    report_lines.append(
                        f"    - {recipient.name} (ID: {rec_id}, "
                        f"Type: {recipient.recipient_type.name}, "
                        f"Location: {recipient.location or 'N/A'})"
                    )
            if activity.transfers_to_third_country_or_international_org:
                report_lines.append(
                    f"  International Transfer: Yes, to {activity.third_country_or_org_name or 'unspecified'}"
                )
                report_lines.append(f"    Safeguards: {activity.safeguards_for_transfer or 'Not specified'}")
            else:
                report_lines.append("  International Transfer: No")
            report_lines.append(f"  Retention Period: {activity.data_retention_period}")
            measures = '; '.join(activity.technical_organizational_security_measures)
            report_lines.append(f"  Security Measures: {measures or 'Not specified'}")
            report_lines.append(
                f"  DPIA Conducted: {'Yes' if activity.data_protection_impact_assessment_conducted else 'No'}"
            )
            if activity.data_protection_impact_assessment_conducted and activity.dpia_reference_or_date:
                report_lines.append(f"    DPIA Reference: {activity.dpia_reference_or_date}")
            report_lines.append(
                f"  Last Reviewed: {activity.last_reviewed_date or 'N/A'}, Version: {activity.version}"
            )
        return "\n".join(report_lines)

    def export_map_as_dict(self) -> Dict[str, Any]:
        return {
            "data_elements": {el_id: asdict(el) for el_id, el in self.data_elements.items()},
            "data_recipients": {rec_id: asdict(rec) for rec_id, rec in self.data_recipients.items()},
            "processing_activities": {
                act_id: asdict(act) for act_id, act in self.processing_activities.items()
            },
        }


if __name__ == "__main__":
    print("=" * 57)
    print("=== Running GDPR Data Mapping Prototype ===")
    print("=" * 57)

    devin_data_map = DevinDataMap()

    print(f"\nTotal Data Elements Defined: {len(devin_data_map.data_elements)}")
    print(f"Total Data Recipients Defined: {len(devin_data_map.data_recipients)}")
    print(f"Total Processing Activities Defined: {len(devin_data_map.processing_activities)}")

    email_element_id = "DE005"
    activities_with_email = devin_data_map.find_activities_using_data_element(email_element_id)
    el = devin_data_map.get_data_element_by_id(email_element_id)
    print(f"\n--- Processing Activities involving '{el.name if el else email_element_id}': ---")
    for activity in activities_with_email:
        print(f"  - Activity: {activity.name} (ID: {activity.activity_id})")

    llm_activity_id = "PA003"
    elements_in_llm_activity = devin_data_map.find_elements_in_activity(llm_activity_id)
    act = devin_data_map.get_processing_activity_by_id(llm_activity_id)
    print(f"\n--- Data Elements in '{act.name if act else llm_activity_id}': ---")
    for element in elements_in_llm_activity:
        print(f"  - Element: {element.name} (ID: {element.element_id})")

    print("\n--- ROPA Summary for 'User Account Registration' (PA001) ---")
    print(devin_data_map.generate_ropa_summary_text(activity_id="PA001"))

    logger.info(
        "This data map is a conceptual representation. "
        "It requires continuous review and updates for GDPR compliance."
    )
    print("\n" + "=" * 57)
    print("=== GDPR Data Mapping Prototype Complete ===")
    print("=" * 57)
