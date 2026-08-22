# Devin/legal/cross_border_data_flow/ccpa_compliance.py
# Purpose: Provides INFORMATIONAL content and conceptual considerations related to
#          CCPA/CPRA, including aspects of data flows and service provider obligations.
# WARNING: THIS IS NOT LEGAL ADVICE. CONSULT LEGAL PROFESSIONALS FOR CCPA/CPRA COMPLIANCE.

# ################################################################################## #
# ## --- ⚠️ EXTREMELY IMPORTANT LEGAL DISCLAIMER ⚠️ --- ## #
# ## THIS SCRIPT DOES NOT PROVIDE LEGAL ADVICE OR MAKE LEGAL DETERMINATIONS.      ## #
# ## INFORMATION HEREIN IS FOR ILLUSTRATIVE AND EDUCATIONAL PURPOSES ONLY.        ## #
# ## CCPA/CPRA IS A COMPLEX LAW AND IS SUBJECT TO CHANGE. ALWAYS CONSULT THE      ## #
# ## OFFICIAL TEXT OF THE LAW, REGULATIONS BY THE CALIFORNIA PRIVACY PROTECTION   ## #
# ## AGENCY (CPPA), AND QUALIFIED LEGAL PROFESSIONALS FOR ANY CCPA/CPRA           ## #
# ## COMPLIANCE MATTERS. RELYING ON THIS SCRIPT FOR COMPLIANCE IS AT YOUR OWN RISK.## #
# ################################################################################## #

import logging
from typing import Dict, List, Optional

# Configure basic logging
logger = logging.getLogger("CCPAComplianceAdvisor")
if not logger.handlers: # Prevent duplicate handlers
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)

class CCPAComplianceAdvisor:
    """
    Provides informational content and conceptual tools related to CCPA/CPRA.
    This class is NOT a substitute for legal advice.
    """

    def __init__(self):
        logger.critical(
            "CCPAComplianceAdvisor initialized. "
            "REMINDER: All information provided is conceptual and for educational purposes. "
            "It MUST be verified with official sources and legal counsel for actual compliance."
        )

    def get_ccpa_cpra_key_definitions(self) -> Dict[str, str]:
        """
        Provides simplified explanations of some key CCPA/CPRA definitions.
        These are illustrative and not exhaustive legal definitions.
        """
        return {
            "Personal Information (PI)": "Information that identifies, relates to, describes, is reasonably capable of being associated with, or could reasonably be linked, directly or indirectly, with a particular California resident or household. Broadly defined.",
            "Business": "A for-profit entity doing business in California that meets certain thresholds (e.g., revenue, number of consumers/households whose PI is processed, or percentage of revenue from selling/sharing PI).",
            "Service Provider": "A for-profit entity that processes PI on behalf of a Business pursuant to a written contract. The contract must prohibit retaining, using, or disclosing PI for any purpose other than the specific business purposes specified in the contract, or as otherwise permitted by CCPA/CPRA.",
            "Contractor": "Similar to a Service Provider, an entity to whom a Business makes PI available for a business purpose pursuant to a written contract with specific limitations.",
            "Third Party": "An entity that is not the Business collecting the PI, nor a Service Provider or Contractor to that Business. Disclosures to Third Parties often trigger 'sale' or 'share' implications.",
            "Sale": "Selling, renting, releasing, disclosing, disseminating, making available, transferring, or otherwise communicating PI by a Business to a Third Party for monetary or other valuable consideration.",
            "Share / Sharing": "Sharing, renting, releasing, disclosing, disseminating, making available, transferring, or otherwise communicating PI by a Business to a Third Party for cross-context behavioral advertising, whether or not for monetary or other valuable consideration.",
            "Cross-Context Behavioral Advertising": "Targeting of advertising to a consumer based on the consumer’s PI obtained from the consumer’s activity across businesses, distinctly-branded websites, applications, or services, other than the business... with which the consumer intentionally interacts.",
            "Sensitive Personal Information (SPI)": "A specific subset of PI that requires additional protections and may allow consumers to limit its use and disclosure (e.g., SSN, financial account info, precise geolocation, genetic data, racial/ethnic origin, religious beliefs, sexual orientation, health information, biometric information for identification, contents of mail/email/texts unless the business is the intended recipient).",
            "Business Purpose": "A purpose for which a Business collects or uses PI, such as auditing, security, debugging, short-term transient use, performing services on behalf of the business (e.g., customer service, order fulfillment), internal research, and activities to verify or maintain quality or safety.",
            "Commercial Purpose": "To advance a person’s commercial or economic interests, such as by inducing a person to buy, rent, lease, join, subscribe to, provide, or exchange products, goods, property, information, or services, or enabling or effecting, directly or indirectly, a commercial transaction."
        }

    def get_consumer_rights_summary(self) -> List[Dict[str, str]]:
        """
        Provides a summary of key consumer rights under CCPA/CPRA.
        This is illustrative and not exhaustive.
        """
        return [
            {"right": "Right to Know/Access", "description": "Consumers can request to know what PI a business has collected about them, the sources, purposes for collection, and categories of third parties with whom it's shared/sold."},
            {"right": "Right to Delete", "description": "Consumers can request the deletion of their PI held by a business and its service providers, subject to certain exceptions."},
            {"right": "Right to Opt-Out of Sale/Sharing", "description": "Consumers can direct a business not to 'sell' or 'share' their PI for cross-context behavioral advertising. Businesses must provide a 'Do Not Sell or Share My Personal Information' link."},
            {"right": "Right to Correct Inaccurate Information", "description": "Consumers can request correction of inaccurate PI that a business holds about them."},
            {"right": "Right to Limit Use and Disclosure of Sensitive Personal Information (SPI)", "description": "Consumers can direct businesses to only use their SPI for limited, specified purposes (e.g., to provide requested services) and not for inferring characteristics. Businesses must provide a 'Limit the Use of My Sensitive Personal Information' link if applicable."},
            {"right": "Right to Non-Discrimination/Retaliation", "description": "Businesses cannot discriminate against consumers for exercising their CCPA/CPRA rights (e.g., by denying goods/services or charging different prices, unless related to value provided)."},
            {"right": "Right to Data Portability", "description": "Consumers can request a copy of their PI in a portable and, to the extent technically feasible, readily usable format that allows them to transmit it to another entity."}
        ]

    def get_service_provider_contractual_considerations(self) -> List[str]:
        """
        Lists conceptual considerations for contracts when Devin (or the entity providing Devin)
        acts as a 'Service Provider' under CCPA/CPRA.
        """
        return [
            "**Written Contract:** Is there a written contract between the Business (client) and the Service Provider (Devin's provider)?",
            "**Business Purposes:** Does the contract clearly specify the limited and specific business purpose(s) for which the Service Provider is processing PI on behalf of the Business?",
            "**Prohibitions:** Does the contract explicitly prohibit the Service Provider from:",
            "  - Selling or Sharing the PI received from the Business?",
            "  - Retaining, using, or disclosing the PI for any purpose other than the specified business purposes in the contract?",
            "  - Retaining, using, or disclosing the PI outside of the direct business relationship between the Service Provider and the Business?",
            "  - Combining PI received from one Business with PI received from other Businesses or collected from its own interactions (unless expressly permitted by CPRA regulations, e.g., for security purposes)?",
            "**Assistance with Consumer Rights Requests:** Does the contract require the Service Provider to assist the Business in responding to consumer rights requests (e.g., access, deletion)?",
            "**Data Security:** Does the contract require the Service Provider to implement reasonable security measures to protect the PI?",
            "**Sub-Processors (Sub-Service Providers):** Does the contract outline requirements for the Service Provider engaging sub-processors, including:",
            "  - Notifying the Business of sub-processors?",
            "  - Flowing down equivalent contractual obligations to sub-processors?",
            "**Audit Rights:** Does the contract grant the Business rights to take reasonable steps to ensure the Service Provider is using PI consistently with the Business's obligations under CCPA/CPRA (e.g., through audits, certifications)?",
            "**Breach Notification:** Does the contract require the Service Provider to notify the Business of any data breaches involving the PI?",
            "**Certification of Compliance:** Does the contract require the Service Provider to certify compliance with its contractual obligations?"
        ]

    def get_data_flow_ccpa_questions_for_devin(self) -> List[str]:
        """
        Conceptual questions related to data flows and CCPA/CPRA for a tool like Devin.
        """
        return [
            f"**1. Identifying Personal Information (PI):** What PI (as defined by CCPA/CPRA) does {self.get_ccpa_cpra_key_definitions()['Business']} (the entity providing Devin) collect, process, or generate, directly or indirectly related to California residents (users, employees, etc.)?",
            f"**2. Role of {self.get_ccpa_cpra_key_definitions()['Business']}:** Is {self.get_ccpa_cpra_key_definitions()['Business']} acting as a 'Business', 'Service Provider', 'Contractor', or 'Third Party' under CCPA/CPRA with respect to different data processing activities?",
            "  - If acting as a 'Service Provider' for other Businesses (Devin's clients), are appropriate contracts in place meeting all CCPA/CPRA requirements for service providers?",
            "**3. 'Sale' or 'Share' of PI:**",
            "  - Is any PI being 'sold' (exchanged for monetary or other valuable consideration) to third parties?",
            "  - Is any PI being 'shared' (disclosed for cross-context behavioral advertising) with third parties?",
            "  - If so, are opt-out mechanisms ('Do Not Sell or Share My Personal Information' link) and processes in place?",
            "**4. Use of Sensitive Personal Information (SPI):**",
            "  - Is any SPI being collected or processed?",
            "  - If so, is its use limited to purposes that do not require offering a 'Limit the Use of My Sensitive Personal Information' link, or is such a link provided if use goes beyond those exceptions?",
            "**5. Data Transfers to Other Entities (Service Providers, Third Parties):**",
            "  - When PI is transferred from Devin (or its provider) to another entity (e.g., an LLM API provider, cloud storage, analytics service):",
            "    - What is the CCPA/CPRA role of that receiving entity (Service Provider, Contractor, Third Party)?",
            "    - If the recipient is a Service Provider/Contractor, is there a compliant written contract in place that restricts their use of the PI to specified business purposes and prohibits selling/sharing?",
            "    - If the recipient is a Third Party, does this constitute a 'sale' or 'share' requiring consumer opt-out rights or consent?",
            "**6. Consumer Rights Fulfillment:**",
            "  - Are there processes in place to receive, verify, and respond to consumer rights requests (Know, Delete, Correct, Opt-Out, Limit Use of SPI, Portability) within the CCPA/CPRA mandated timeframes?",
            "  - How are these rights handled for data processed by Devin, including data passed to/from any integrated services or sub-processors?",
            "**7. Data Minimization & Purpose Limitation:** Is PI collection limited to what is reasonably necessary and proportionate to achieve the purposes for which it was collected or processed? Is PI not retained longer than reasonably necessary for disclosed purposes?",
            "**8. Security:** Are reasonable security procedures and practices implemented to protect PI?",
            "**9. Privacy Policy & Notices:** Is there a CCPA/CPRA-compliant privacy policy and are necessary notices at collection provided to California residents?",
            f"**10. Training:** Are personnel handling PI of California residents trained on CCPA/CPRA requirements and internal data handling policies?"
        ]

# Example Usage
if __name__ == "__main__":
    print("======================================================================")
    print("=== CCPA/CPRA Compliance Advisor - Conceptual Information ===")
    print("=== WARNING: THIS IS FOR ILLUSTRATION ONLY - NOT LEGAL ADVICE! ===")
    print("======================================================================")

    advisor = CCPAComplianceAdvisor()

    print("\n--- Key CCPA/CPRA Definitions (Illustrative) ---")
    definitions = advisor.get_ccpa_cpra_key_definitions()
    for term, definition in list(definitions.items())[:3]: # Print first 3 for brevity
        print(f"**{term}:** {definition}")
    print("...")

    print("\n--- Summary of Consumer Rights under CCPA/CPRA (Illustrative) ---")
    rights = advisor.get_consumer_rights_summary()
    for right_info in rights[:3]: # Print first 3
        print(f"- **{right_info['right']}:** {right_info['description']}")
    print("...")

    print("\n--- Conceptual Considerations for Service Provider Contracts (CCPA/CPRA) ---")
    sp_considerations = advisor.get_service_provider_contractual_considerations()
    for i, consideration in enumerate(sp_considerations[:3]): # Print first 3
        print(f"{i+1}. {consideration}")
    print("...")

    print("\n--- Conceptual Data Flow Questions for CCPA/CPRA (for a tool like Devin) ---")
    flow_questions = advisor.get_data_flow_ccpa_questions_for_devin()
    for i, question in enumerate(flow_questions[:3]): # Print first 3
        print(question)
    print("...")

    print("\n" + "#"*70)
    print("## FINAL REMINDER: The information generated by this script is illustrative ##")
    print("## and NOT a substitute for professional legal advice.                      ##")
    print("## Always consult official CCPA/CPRA text, CPPA regulations, and qualified ##")
    print("## legal counsel for compliance with California privacy laws.               ##")
    print("#"*70)
    print("\n======================================================================")
    print("=== CCPA/CPRA Compliance Advisor Prototype Complete ===")
    print("======================================================================")
