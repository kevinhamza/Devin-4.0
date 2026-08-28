# Devin/legal/cross_border_data_flow/gdpr_adequacy.py
# Purpose: Provides INFORMATIONAL content and conceptual checks related to GDPR
#          adequacy decisions and international data transfers.
# WARNING: THIS IS NOT LEGAL ADVICE. CONSULT OFFICIAL EU SOURCES & LEGAL PROFESSIONALS.

# ################################################################################## #
# ## --- ⚠️ EXTREMELY IMPORTANT LEGAL DISCLAIMER ⚠️ --- ## #
# ## THIS SCRIPT DOES NOT PROVIDE LEGAL ADVICE OR MAKE LEGAL DETERMINATIONS.      ## #
# ## INFORMATION HEREIN IS FOR ILLUSTRATIVE AND EDUCATIONAL PURPOSES ONLY.        ## #
# ## ADEQUACY DECISIONS ARE MADE BY THE EUROPEAN COMMISSION AND ARE SUBJECT TO    ## #
# ## CHANGE. ALWAYS CONSULT OFFICIAL EU SOURCES (E.G., THE EU OFFICIAL JOURNAL,  ## #
# ## EUROPEAN COMMISSION'S WEBSITE) AND QUALIFIED LEGAL PROFESSIONALS FOR ANY     ## #
# ## DATA TRANSFER COMPLIANCE MATTERS. RELYING ON THIS SCRIPT FOR COMPLIANCE      ## #
# ## IS AT YOUR OWN RISK.                                                         ## #
# ################################################################################## #

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Union, Tuple

# Configure basic logging
logger = logging.getLogger("GDPRDataTransferAdvisor")
# Basic configuration for this module's logger, if not handled globally
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)

class GDPRDataTransferAdvisor:
    """
    Provides informational content and conceptual tools related to GDPR
    international data transfers and adequacy decisions.
    """
    # --- ⚠️ DISCLAIMER FOR CLASS USAGE ⚠️ --- #
    # This class and its methods are for informational purposes only.
    # Do not rely on this for actual GDPR compliance.

    def __init__(self):
        self.conceptual_adequate_jurisdictions: Dict[str, Dict[str, str]] = {}
        self._load_conceptual_adequacy_list_info()
        logger.critical(
            "GDPRDataTransferAdvisor initialized. "
            "REMINDER: All information provided is conceptual, potentially outdated, "
            "and MUST be verified with official EU sources and legal counsel."
        )

    def _load_conceptual_adequacy_list_info(self):
        """
        Loads a CONCEPTUAL AND ILLUSTRATIVE list of jurisdictions that have, at some point,
        been recognized by the European Commission as providing an adequate level of data protection.
        THIS LIST IS FOR DEMONSTRATION ONLY, IS NOT EXHAUSTIVE, AND WILL BECOME OUTDATED.
        ALWAYS CHECK THE OFFICIAL EUROPEAN COMMISSION WEBSITE FOR THE CURRENT LIST.
        """
        self.conceptual_adequate_jurisdictions = {
            # Format: "ISO_CODE": {"name": "Country Name", "decision_info": "Conceptual reference/date - VERIFY OFFICIALLY!", "scope": "Specifics of decision - VERIFY!"}
            "AD": {"name": "Andorra", "decision_info": "EC Decision 2010/625/EU (VERIFY!)", "scope": "General (VERIFY!)"},
            "AR": {"name": "Argentina", "decision_info": "EC Decision 2003/490/EC (VERIFY!)", "scope": "General (VERIFY!)"},
            "CA": {"name": "Canada", "decision_info": "EC Decision 2002/2/EC (VERIFY!)", "scope": "Only for personal data processed by entities subject to PIPEDA (VERIFY!)"},
            "CH": {"name": "Switzerland", "decision_info": "EC Decision 2000/518/EC, revised (VERIFY!)", "scope": "General (VERIFY!)"},
            "FO": {"name": "Faroe Islands", "decision_info": "EC Decision 2010/146/EU (VERIFY!)", "scope": "General (VERIFY!)"},
            "GG": {"name": "Guernsey", "decision_info": "EC Decision 2003/821/EC (VERIFY!)", "scope": "General (VERIFY!)"},
            "IL": {"name": "Israel", "decision_info": "EC Decision 2011/61/EU (VERIFY!)", "scope": "Limited to certain types of data transfers (VERIFY!)"},
            "IM": {"name": "Isle of Man", "decision_info": "EC Decision 2004/411/EC (VERIFY!)", "scope": "General (VERIFY!)"},
            "JP": {"name": "Japan", "decision_info": "EC Decision (EU) 2019/419 (VERIFY!)", "scope": "Only for personal data processed by private-sector operators subject to APPI, with supplementary rules (VERIFY!)"},
            "JE": {"name": "Jersey", "decision_info": "EC Decision 2008/393/EC (VERIFY!)", "scope": "General (VERIFY!)"},
            "NZ": {"name": "New Zealand", "decision_info": "EC Decision 2013/65/EU (VERIFY!)", "scope": "General (VERIFY!)"},
            "KR": {"name": "Republic of Korea (South Korea)", "decision_info": "EC Decision (EU) 2022/254 (VERIFY!)", "scope": "General, with some specific considerations (VERIFY!)"},
            "GB": {"name": "United Kingdom", "decision_info": "EC Decisions (EU) 2021/1772 & 2021/1773 (VERIFY!)", "scope": "General, under GDPR and Law Enforcement Directive, time-limited (sunset clause) initially (VERIFY!)"},
            "UY": {"name": "Uruguay", "decision_info": "EC Decision 2012/484/EU (VERIFY!)", "scope": "General (VERIFY!)"},
            "US": {"name": "United States", "decision_info": "EU-U.S. Data Privacy Framework (DPF) (VERIFY!)", "scope": "Only for data transfers to U.S. organizations certified under the DPF (VERIFY!) - Successor to Privacy Shield. Status requires constant monitoring."}
        }
        logger.warning(
            f"Loaded a CONCEPTUAL & ILLUSTRATIVE list of {len(self.conceptual_adequate_jurisdictions)} jurisdictions. "
            f"This list was last 'updated' conceptually on {datetime.now(timezone.utc).strftime('%Y-%m-%d')} "
            "for this script's generation and IS NOT AUTHORITATIVE. ALWAYS verify with official EU sources."
        )

    def check_conceptual_adequacy(self, country_iso_code: str) -> Dict[str, Union[str, bool, None]]:
        """
        Checks a country code against the *conceptual and illustrative* list of adequate jurisdictions.
        Returns a dictionary with status and notes.
        THIS IS NOT A LEGAL DETERMINATION.
        """
        country_iso_code = country_iso_code.upper()
        if country_iso_code in self.conceptual_adequate_jurisdictions:
            info = self.conceptual_adequate_jurisdictions[country_iso_code]
            return {
                "country_code": country_iso_code,
                "name": info["name"],
                "is_conceptually_adequate_in_list": True,
                "illustrative_decision_info": info["decision_info"],
                "illustrative_scope": info["scope"],
                "critical_reminder": "VERIFY WITH OFFICIAL, CURRENT EUROPEAN COMMISSION SOURCES. Adequacy status and scope can change."
            }
        else:
            return {
                "country_code": country_iso_code,
                "is_conceptually_adequate_in_list": False,
                "illustrative_decision_info": None,
                "illustrative_scope": None,
                "critical_reminder": f"Country code '{country_iso_code}' not found in this script's illustrative list or no current broad adequacy decision may exist. VERIFY with official EU sources and consider alternative transfer mechanisms if transferring from EEA. This check is NOT exhaustive or authoritative."
            }

    def list_common_alternative_transfer_mechanisms(self) -> List[Dict[str, str]]:
        """
        Lists common alternative mechanisms for transferring personal data outside the EEA
        when an adequacy decision is not in place. INFORMATIONAL ONLY.
        """
        return [
            {
                "mechanism": "Standard Contractual Clauses (SCCs)",
                "description": "Model data protection clauses adopted by the European Commission (or a supervisory authority and then approved by the Commission). These are contractual commitments between the data exporter and data importer regarding data protection. Often require a Transfer Impact Assessment (TIA).",
                "gdpr_article_reference": "Article 46(2)(c) and (d)",
                "key_consideration": "Requires careful implementation, due diligence on the importer, and a TIA. Different modules for different controller/processor relationships. VERIFY latest versions from EC."
            },
            {
                "mechanism": "Binding Corporate Rules (BCRs)",
                "description": "Data protection policies adhered to by a group of undertakings or enterprises for intra-group transfers of personal data to controllers or processors in third countries. Must be approved by a competent supervisory authority.",
                "gdpr_article_reference": "Article 46(2)(b) and Article 47",
                "key_consideration": "Complex and lengthy approval process, suitable for large multinational groups."
            },
            {
                "mechanism": "Codes of Conduct and Certifications",
                "description": "Approved codes of conduct or certification mechanisms, together with binding and enforceable commitments of the controller or processor in the third country to apply the appropriate safeguards.",
                "gdpr_article_reference": "Article 46(2)(e) and (f)",
                "key_consideration": "Less common in practice currently for broad transfers, but developing."
            },
            {
                "mechanism": "Derogations for Specific Situations (Article 49)",
                "description": "Used in specific, non-repetitive situations, such as explicit consent of the data subject for a specific transfer, transfer necessary for a contract, important reasons of public interest, etc.",
                "gdpr_article_reference": "Article 49",
                "key_consideration": "Strictly interpreted and should not be used for regular, systematic transfers. Each derogation has specific conditions."
            }
        ]

    def get_pre_transfer_assessment_questions(self) -> List[str]:
        """
        Provides a list of conceptual questions to consider before transferring
        personal data subject to GDPR outside the EEA. NOT EXHAUSTIVE.
        """
        return [
            "1. What specific personal data is being transferred?",
            "2. What are the categories of data subjects involved?",
            "3. To which third country (non-EEA) or international organization is the data being transferred?",
            "4. What is the purpose of this international data transfer?",
            "5. **Adequacy Decision:** Does the European Commission currently recognize this third country (or specific sector/territory within it) as providing an adequate level of data protection? (VERIFY OFFICIAL EC LIST)",
            "6. **Appropriate Safeguards (if no adequacy decision):**",
            "   - Are Standard Contractual Clauses (SCCs) in place between the data exporter and importer? Which version? Which modules?",
            "   - Has a Transfer Impact Assessment (TIA) / Data Transfer Impact Assessment (DTIA) been conducted to assess the laws and practices of the third country and the effectiveness of the SCCs in that context?",
            "   - Are Binding Corporate Rules (BCRs) applicable and approved for this transfer (for intra-group transfers)?",
            "   - Is an approved Code of Conduct or Certification Mechanism being used with binding commitments?",
            "7. **Derogations (if no adequacy or appropriate safeguards):**",
            "   - Does a specific derogation under GDPR Article 49 apply (e.g., explicit informed consent for this specific transfer, necessity for contract performance with the data subject)? Are the conditions for the derogation strictly met? Is this a non-repetitive transfer?",
            "8. What are the details of the data importer (recipient) in the third country?",
            "9. What technical and organizational measures (TOMs) will be in place to protect the data during transit and once processed in the third country?",
            "10. How will data subject rights be upheld in relation to the transferred data?",
            "11. What are the mechanisms for onward transfers from this importer to other entities or countries?",
            "12. Is the data transfer documented in the Record of Processing Activities (ROPA)?",
            "13. Has legal counsel specializing in data protection reviewed and approved this specific international data transfer arrangement?",
            "14. What are the procedures if the chosen transfer mechanism is invalidated or deemed insufficient in the future?"
        ]

# Example Usage
if __name__ == "__main__":
    print("======================================================================")
    print("=== GDPR International Data Transfer Advisor - Conceptual Info ===")
    print("=== WARNING: THIS IS FOR ILLUSTRATION ONLY - NOT LEGAL ADVICE! ===")
    print("======================================================================")

    advisor = GDPRDataTransferAdvisor()

    # --- Example: Conceptual Adequacy Check ---
    print("\n--- Conceptual Adequacy Check (Illustrative & Potentially Outdated) ---")
    countries_to_check = ["CH", "US", "IN", "CA", "AU"] # Switzerland, USA, India, Canada, Australia
    for code in countries_to_check:
        adequacy_status = advisor.check_conceptual_adequacy(code)
        print(f"Country: {adequacy_status.get('name', code)}")
        print(f"  In Illustrative Adequate List: {adequacy_status['is_conceptually_adequate_in_list']}")
        if adequacy_status['is_conceptually_adequate_in_list']:
            print(f"  Illustrative Info: {adequacy_status['illustrative_decision_info']}")
            print(f"  Illustrative Scope: {adequacy_status['illustrative_scope']}")
        print(f"  Reminder: {adequacy_status['critical_reminder']}\n")

    # --- Example: List Common Alternative Transfer Mechanisms ---
    print("\n--- Common Alternative Transfer Mechanisms (Informational) ---")
    mechanisms = advisor.list_common_alternative_transfer_mechanisms()
    for mech in mechanisms:
        print(f"Mechanism: {mech['mechanism']} (Ref: {mech['gdpr_article_reference']})")
        print(f"  Description: {mech['description']}")
        print(f"  Key Consideration: {mech['key_consideration']}\n")

    # --- Example: Pre-Transfer Assessment Questions ---
    print("\n--- Conceptual Pre-Transfer Assessment Questions ---")
    questions = advisor.get_pre_transfer_assessment_questions()
    for i, question in enumerate(questions):
        print(question)

    print("\n" + "#"*70)
    print("## FINAL REMINDER: The information generated by this script is illustrative, ##")
    print("## potentially outdated, and NOT a substitute for professional legal advice. ##")
    print("## Always consult official European Commission sources and qualified legal   ##")
    print("## counsel for GDPR compliance and international data transfer decisions.  ##")
    print("#"*70)
    print("\n======================================================================")
    print("=== GDPR Data Transfer Advisor Prototype Complete ===")
    print("======================================================================")
