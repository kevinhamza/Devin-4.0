# Devin/modules/ethics_legal_tools.py
# Purpose: A high-level facade that wraps Devin's AI-ethics auditing tools and
#          its "informational only" legal/compliance helpers into a single,
#          agent-callable interface.
#
# ---------------------------------------------------------------------------
# LEGAL DISCLAIMER (applies to every legal/*, cyber_law/*, and cross_border_*
# method on this facade): This facade and the modules it wraps provide
# INFORMATIONAL content and conceptual tooling only. NONE of it is legal
# advice, and NONE of it is a substitute for review by qualified legal
# counsel. Always consult a licensed attorney for actual compliance,
# authorization, or contractual decisions.
# ---------------------------------------------------------------------------
#
# Scope notes (see report for full detail):
#   - ai_ethics/consciousness_monitor/* and ai_ethics/neurosecurity/* are
#     explicitly out of scope per the task and are not touched here.
#   - legal/auto_compliance/regulation_gap_analyzer.py and policy_as_code.py
#     are skipped: both files' own headers state, verbatim, "HIGHLY
#     CONCEPTUAL AND EXTREMELY SIMPLIFIED" / "TOY EXAMPLE" and explicitly say
#     not to use them for any real compliance decision-making.
#   - Several of the wrapped modules ship with pre-existing bugs that make
#     them fail to import or to run, independent of anything in this facade
#     (missing `typing` imports causing NameError at import time, and -- more
#     seriously -- dataclasses whose fields are ordered with a defaulted
#     field before required fields, which is a hard `TypeError` at class
#     definition time in Python). Because this facade may only ADD new files
#     and must not modify the originals, each affected class is imported and
#     called as defensively as possible (broad try/except at both import time
#     and call time) so a broken upstream module disables just that one
#     feature instead of crashing the whole facade. Every such landmine is
#     called out inline below and summarized in the report.

import logging
from typing import Any, Dict, List, Optional

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

logger = logging.getLogger("EthicsLegalFacade")
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_h)
    logger.setLevel(logging.INFO)
logger.propagate = False

_LEGAL_DISCLAIMER = "Informational only; not legal advice. Consult qualified counsel."


def _unavailable(feature: str, error: Optional[Exception] = None) -> Dict[str, Any]:
    """Standard graceful-degradation response for a disabled sub-feature."""
    msg = f"'{feature}' is unavailable."
    if error is not None:
        msg += f" Reason: {error}"
    logger.warning(msg)
    return {"success": False, "error": msg}


# --- Optional low-level tool imports -- each is isolated and degrades gracefully ---

try:
    # NOTE: model_fairness.py's `_check_data` and `adjust_thresholds_per_group`
    # signatures use `Union[...]` / `Literal[...]` but the module never
    # imports `Union` or `Literal` from `typing` (and its body separately
    # calls `statistics.mean(...)` without importing `statistics`). This
    # raises NameError at class-definition (i.e. import) time as shipped.
    from ai_ethics.bias_mitigation.model_fairness import ModelFairnessAdjuster
    MODEL_FAIRNESS_AVAILABLE = True
except Exception as e:
    MODEL_FAIRNESS_AVAILABLE = False
    _model_fairness_import_error = e

try:
    # NOTE: dataset_debiasing.py's `resample_by_group` signature uses
    # `Literal[...]` but the module never imports `Literal` from `typing`.
    # Raises NameError at import time as shipped.
    from ai_ethics.bias_mitigation.dataset_debiasing import DatasetDebiaser
    DATASET_DEBIASER_AVAILABLE = True
except Exception as e:
    DATASET_DEBIASER_AVAILABLE = False
    _dataset_debiaser_import_error = e

try:
    from ai_ethics.bias_mitigation.impact_assessment import SocietalImpactAssessor
    IMPACT_ASSESSOR_AVAILABLE = True
except Exception as e:
    IMPACT_ASSESSOR_AVAILABLE = False
    _impact_assessor_import_error = e

try:
    from ai_ethics.fairness_audit import FairnessAuditor
    FAIRNESS_AUDITOR_AVAILABLE = True
except Exception as e:
    FAIRNESS_AUDITOR_AVAILABLE = False
    _fairness_auditor_import_error = e

try:
    from ai_ethics.transparency_portal import TransparencyPortal
    TRANSPARENCY_PORTAL_AVAILABLE = True
except Exception as e:
    TRANSPARENCY_PORTAL_AVAILABLE = False
    _transparency_portal_import_error = e

try:
    # NOTE: data_mapping.py's `ProcessingActivity` dataclass declares a field
    # with a default (`dpo_contact_details: Optional[str] = None`) followed
    # by required fields with no default (`purposes_of_processing: List[str]`
    # etc.). Python raises `TypeError: non-default argument ... follows
    # default argument` at class-definition (import) time for this. The file
    # also contains two full `class DevinDataMap:` definitions concatenated
    # (an apparent "Part 1 / Part 2" copy-paste artifact); the second
    # silently overwrites the first and omits `__init__`, so even if the
    # dataclass bug were fixed, `DevinDataMap()` would still be missing
    # `data_elements` / `data_recipients` / `processing_activities`. Both
    # bugs are pre-existing and unrelated to this facade.
    from legal.gdpr_compliance.data_mapping import DevinDataMap
    DATA_MAPPING_AVAILABLE = True
except Exception as e:
    DATA_MAPPING_AVAILABLE = False
    _data_mapping_import_error = e

try:
    # NOTE: dsar_handler.py imports `.data_mapping` (broken, see above) and
    # separately defines its own `DSARCase` dataclass with the identical
    # defaulted-field-before-required-field bug (`case_id` has a default,
    # followed by required `subject_identifier`/`request_type`). Either bug
    # alone makes this module fail to import as shipped; dsar_handler.py's
    # own `except ImportError` guard around the data_mapping import does not
    # catch this because the underlying failure is a TypeError, not an
    # ImportError.
    from legal.gdpr_compliance.dsar_handler import DSARHandler, DSARRequestType, DSARStatus
    from legal.gdpr_compliance.data_mapping import DevinDataMap as _DevinDataMapForDSAR
    DSAR_AVAILABLE = True
except Exception as e:
    DSAR_AVAILABLE = False
    _dsar_import_error = e

try:
    # NOTE: cfaa_compliance.py's `AuthorizationRecord` dataclass has the same
    # defaulted-field-before-required-field bug (`auth_id` has a default,
    # followed by several required fields). TypeError at import time.
    from legal.pentest_laws.cfaa_compliance import CFAAComplianceManager, AuthorizationRecord, AuthorizationStatus, PentestActionCategory
    CFAA_AVAILABLE = True
except Exception as e:
    CFAA_AVAILABLE = False
    _cfaa_import_error = e

try:
    # NOTE: legal/pentest_laws/eula_generator.py (the canonical file per this
    # facade's instructions -- see report re: the duplicate "(delete another
    # file of same name)" file) is itself an incomplete "Part 1" fragment: it
    # defines EULASection + DevinEULAOutlineGenerator.__init__ and only the
    # first 4 of a planned 17 EULA sections, and never defines a
    # document-assembly method. This facade adds its own rendering method
    # below (does not modify the original file) so the sections that DO
    # exist upstream are still usable.
    from legal.pentest_laws.eula_generator import DevinEULAOutlineGenerator
    EULA_GENERATOR_AVAILABLE = True
except Exception as e:
    EULA_GENERATOR_AVAILABLE = False
    _eula_generator_import_error = e

try:
    from cyber_law.warrant_generator import PentestAuthorizationDoc
    WARRANT_GENERATOR_AVAILABLE = True
except Exception as e:
    WARRANT_GENERATOR_AVAILABLE = False
    _warrant_generator_import_error = e

try:
    from cyber_law.cross_border_data_router import DataRouter
    DATA_ROUTER_AVAILABLE = True
except Exception as e:
    DATA_ROUTER_AVAILABLE = False
    _data_router_import_error = e

try:
    from modules.all_ais_modules import AIAgent
    AI_AGENT_AVAILABLE = True
except Exception as e:
    AI_AGENT_AVAILABLE = False
    _ai_agent_import_error = e

try:
    from cross_border_data_flow.ccpa_compliance import CCPAComplianceAdvisor
    CCPA_ADVISOR_AVAILABLE = True
except Exception as e:
    CCPA_ADVISOR_AVAILABLE = False
    _ccpa_advisor_import_error = e

try:
    from legal.cross_border_data_flow.gdpr_adequacy import GDPRDataTransferAdvisor
    GDPR_ADEQUACY_AVAILABLE = True
except Exception as e:
    GDPR_ADEQUACY_AVAILABLE = False
    _gdpr_adequacy_import_error = e


class EthicsLegalFacade:
    """
    A single, simplified interface over Devin's AI-ethics auditing tools
    (fairness audits, decision explanations, impact assessment reporting)
    and its informational-only legal/compliance helpers (GDPR/CCPA/CFAA
    reference tooling, authorization/DSAR record-keeping, and document
    outline generators). See the module-level LEGAL DISCLAIMER above.
    """

    def __init__(self):
        # --- AI ethics ---
        self.model_fairness_adjuster: Optional["ModelFairnessAdjuster"] = None
        if MODEL_FAIRNESS_AVAILABLE:
            try:
                self.model_fairness_adjuster = ModelFairnessAdjuster()
            except Exception as e:
                logger.warning(f"ModelFairnessAdjuster unavailable: {e}")
        else:
            logger.warning(f"ModelFairnessAdjuster unavailable: {_model_fairness_import_error}")

        self.dataset_debiaser: Optional["DatasetDebiaser"] = None
        if DATASET_DEBIASER_AVAILABLE:
            try:
                self.dataset_debiaser = DatasetDebiaser()
            except Exception as e:
                logger.warning(f"DatasetDebiaser unavailable: {e}")
        else:
            logger.warning(f"DatasetDebiaser unavailable: {_dataset_debiaser_import_error}")

        self.impact_assessor: Optional["SocietalImpactAssessor"] = None
        if IMPACT_ASSESSOR_AVAILABLE:
            try:
                self.impact_assessor = SocietalImpactAssessor()
            except Exception as e:
                logger.warning(f"SocietalImpactAssessor unavailable: {e}")
        else:
            logger.warning(f"SocietalImpactAssessor unavailable: {_impact_assessor_import_error}")

        self.fairness_auditor: Optional["FairnessAuditor"] = None
        if FAIRNESS_AUDITOR_AVAILABLE:
            try:
                self.fairness_auditor = FairnessAuditor(sensitive_attributes=[])
            except Exception as e:
                logger.warning(f"FairnessAuditor unavailable: {e}")
        else:
            logger.warning(f"FairnessAuditor unavailable: {_fairness_auditor_import_error}")

        self.transparency_portal: Optional["TransparencyPortal"] = None
        if TRANSPARENCY_PORTAL_AVAILABLE:
            try:
                self.transparency_portal = TransparencyPortal(log_service="devin_internal", memory_service="devin_internal")
            except Exception as e:
                logger.warning(f"TransparencyPortal unavailable: {e}")
        else:
            logger.warning(f"TransparencyPortal unavailable: {_transparency_portal_import_error}")

        # --- GDPR data mapping / DSAR ---
        self.data_map: Optional["DevinDataMap"] = None
        if DATA_MAPPING_AVAILABLE:
            try:
                self.data_map = DevinDataMap()
            except Exception as e:
                logger.warning(f"DevinDataMap unavailable: {e}")
        else:
            logger.warning(f"DevinDataMap unavailable: {_data_mapping_import_error}")

        self.dsar_handler: Optional["DSARHandler"] = None
        if DSAR_AVAILABLE:
            try:
                # Reuse the same (possibly broken/placeholder) data map instance;
                # DSARHandler only warns and degrades if it isn't a real DevinDataMap.
                dm = self.data_map if self.data_map is not None else _DevinDataMapForDSAR()
                self.dsar_handler = DSARHandler(data_map=dm)
            except Exception as e:
                logger.warning(f"DSARHandler unavailable: {e}")
        else:
            logger.warning(f"DSARHandler unavailable: {_dsar_import_error}")

        # --- Pentest law / authorization tracking ---
        self.cfaa_manager: Optional["CFAAComplianceManager"] = None
        if CFAA_AVAILABLE:
            try:
                self.cfaa_manager = CFAAComplianceManager()
            except Exception as e:
                logger.warning(f"CFAAComplianceManager unavailable: {e}")
        else:
            logger.warning(f"CFAAComplianceManager unavailable: {_cfaa_import_error}")

        self.eula_generator: Optional["DevinEULAOutlineGenerator"] = None
        if EULA_GENERATOR_AVAILABLE:
            try:
                self.eula_generator = DevinEULAOutlineGenerator()
            except Exception as e:
                logger.warning(f"DevinEULAOutlineGenerator unavailable: {e}")
        else:
            logger.warning(f"DevinEULAOutlineGenerator unavailable: {_eula_generator_import_error}")

        # --- Data routing / cross-border advisors ---
        self.data_router: Optional["DataRouter"] = None
        if DATA_ROUTER_AVAILABLE and AI_AGENT_AVAILABLE:
            try:
                self.data_router = DataRouter(ai_agent=AIAgent())
            except Exception as e:
                logger.warning(f"DataRouter unavailable: {e}")
        else:
            err = _data_router_import_error if not DATA_ROUTER_AVAILABLE else _ai_agent_import_error
            logger.warning(f"DataRouter unavailable: {err}")

        self.ccpa_advisor: Optional["CCPAComplianceAdvisor"] = None
        if CCPA_ADVISOR_AVAILABLE:
            try:
                self.ccpa_advisor = CCPAComplianceAdvisor()
            except Exception as e:
                logger.warning(f"CCPAComplianceAdvisor unavailable: {e}")
        else:
            logger.warning(f"CCPAComplianceAdvisor unavailable: {_ccpa_advisor_import_error}")

        self.gdpr_adequacy_advisor: Optional["GDPRDataTransferAdvisor"] = None
        if GDPR_ADEQUACY_AVAILABLE:
            try:
                self.gdpr_adequacy_advisor = GDPRDataTransferAdvisor()
            except Exception as e:
                logger.warning(f"GDPRDataTransferAdvisor unavailable: {e}")
        else:
            logger.warning(f"GDPRDataTransferAdvisor unavailable: {_gdpr_adequacy_import_error}")

        logger.info("EthicsLegalFacade initialized.")

    # ==================================================================
    # AI Ethics: bias mitigation
    # ==================================================================

    def fairness_adjust_thresholds(self, scores: List[float], labels: List[int], sensitive_features: List[str],
                                    fairness_goal: str = "equal_opportunity", positive_label: int = 1) -> Dict[str, Any]:
        """Computes a per-group classification threshold aiming to equalize a fairness metric (e.g. Equal Opportunity / TPR) across groups. Returns {group: threshold}."""
        if not self.model_fairness_adjuster or not PANDAS_AVAILABLE:
            return _unavailable("fairness_adjust_thresholds")
        try:
            thresholds = self.model_fairness_adjuster.adjust_thresholds_per_group(
                scores=pd.Series(scores), labels=pd.Series(labels), sensitive_features=pd.Series(sensitive_features),
                fairness_goal=fairness_goal, positive_label=positive_label,
            )
            return {"success": True, "thresholds": dict(thresholds)}
        except Exception as e:
            logger.error(f"fairness_adjust_thresholds failed: {e}")
            return {"success": False, "error": str(e)}

    def fairness_apply_adjusted_thresholds(self, scores: List[float], sensitive_features: List[str], thresholds: Dict[str, float]) -> Dict[str, Any]:
        """Applies previously computed per-group thresholds to scores to produce final binary predictions."""
        if not self.model_fairness_adjuster or not PANDAS_AVAILABLE:
            return _unavailable("fairness_apply_adjusted_thresholds")
        try:
            preds = self.model_fairness_adjuster.apply_adjusted_thresholds(pd.Series(scores), pd.Series(sensitive_features), thresholds)
            return {"success": True, "predictions": list(preds)}
        except Exception as e:
            logger.error(f"fairness_apply_adjusted_thresholds failed: {e}")
            return {"success": False, "error": str(e)}

    def dataset_resample_by_group(self, records: List[Dict[str, Any]], sensitive_attribute_col: str,
                                   strategy: str = "oversample", target_balance: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
        """Resamples a dataset (list of row dicts) to balance representation across groups defined by a sensitive attribute column. strategy: 'oversample' or 'undersample'."""
        if not self.dataset_debiaser or not PANDAS_AVAILABLE:
            return _unavailable("dataset_resample_by_group")
        try:
            df = self.dataset_debiaser.resample_by_group(pd.DataFrame(records), sensitive_attribute_col, strategy=strategy, target_balance=target_balance)
            return {"success": True, "records": df.to_dict(orient="records")}
        except Exception as e:
            logger.error(f"dataset_resample_by_group failed: {e}")
            return {"success": False, "error": str(e)}

    def dataset_calculate_instance_weights(self, records: List[Dict[str, Any]], sensitive_attribute_col: str, label_col: str) -> Dict[str, Any]:
        """Calculates inverse-frequency instance weights per row so each group carries roughly equal total weight during model training."""
        if not self.dataset_debiaser or not PANDAS_AVAILABLE:
            return _unavailable("dataset_calculate_instance_weights")
        try:
            weights = self.dataset_debiaser.calculate_instance_weights(pd.DataFrame(records), sensitive_attribute_col, label_col)
            return {"success": True, "weights": list(weights)}
        except Exception as e:
            logger.error(f"dataset_calculate_instance_weights failed: {e}")
            return {"success": False, "error": str(e)}

    def ethics_generate_impact_assessment_report(self, system_description: str, stakeholders: List[Dict[str, Any]],
                                                  use_cases: List[Dict[str, Any]], identified_harms: List[Dict[str, Any]],
                                                  identified_benefits: Optional[List[Dict[str, Any]]] = None,
                                                  mitigation_strategies: Optional[List[Dict[str, Any]]] = None,
                                                  overall_risk_assessment: str = "", recommendations: Optional[List[str]] = None,
                                                  assessor_name: str = "Devin") -> Dict[str, Any]:
        """
        Compiles pre-gathered stakeholder/use-case/harm data into a structured
        societal impact assessment report. (The upstream interactive
        stakeholder/use-case/harm-gathering wizards are not wrapped -- they
        are stub prompts that never terminate; callers must supply
        `stakeholders`, `use_cases`, and `identified_harms` themselves,
        matching the Stakeholder/UseCase/PotentialHarm shapes.)
        """
        if not self.impact_assessor:
            return _unavailable("ethics_generate_impact_assessment_report")
        import datetime as _dt
        import uuid as _uuid
        try:
            report = self.impact_assessor.generate_assessment_report({
                # A report_id is always supplied here to avoid an upstream bug:
                # generate_assessment_report() falls back to `random.randint(...)`
                # for the report_id when one isn't provided, but that module never
                # imports `random`, which would raise NameError.
                "report_id": f"SIA-{_dt.date.today().isoformat()}-{_uuid.uuid4().hex[:6].upper()}",
                "system_description": system_description,
                "stakeholders": stakeholders,
                "use_cases": use_cases,
                "identified_harms": identified_harms,
                "identified_benefits": identified_benefits or [],
                "mitigation_strategies": mitigation_strategies or [],
                "overall_risk_assessment": overall_risk_assessment,
                "recommendations": recommendations or [],
                "assessor_info": {"name": assessor_name, "date": _dt.date.today().isoformat()},
            })
            return {"success": True, "report": report}
        except Exception as e:
            logger.error(f"ethics_generate_impact_assessment_report failed: {e}")
            return {"success": False, "error": str(e)}

    # ==================================================================
    # AI Ethics: fairness auditing & transparency
    # ==================================================================

    def ethics_audit_model_predictions(self, records: List[Dict[str, Any]], label_column: str, prediction_column: str,
                                        sensitive_feature_column: Optional[str] = None) -> Dict[str, Any]:
        """Audits already-computed model predictions (a list of row dicts containing label + prediction columns) for accuracy and, if a sensitive feature column is given, per-group disparities (demographic parity, equal opportunity)."""
        if not self.fairness_auditor or not PANDAS_AVAILABLE:
            return _unavailable("ethics_audit_model_predictions")
        try:
            if sensitive_feature_column and sensitive_feature_column not in self.fairness_auditor.sensitive_attributes:
                self.fairness_auditor.sensitive_attributes.append(sensitive_feature_column)
            df = pd.DataFrame(records)
            results = self.fairness_auditor.audit_model_behavior(
                model=lambda features: None, test_dataset=df, label_column=label_column,
                prediction_column=prediction_column, sensitive_feature_column=sensitive_feature_column,
            )
            return {"success": True, "results": results}
        except Exception as e:
            logger.error(f"ethics_audit_model_predictions failed: {e}")
            return {"success": False, "error": str(e)}

    def ethics_audit_output_bias(self, outputs: List[str]) -> Dict[str, Any]:
        """Runs lightweight heuristic bias/sentiment/stereotype-keyword checks over a list of AI-generated text outputs."""
        if not self.fairness_auditor:
            return _unavailable("ethics_audit_output_bias")
        try:
            return {"success": True, "results": self.fairness_auditor.audit_output_bias(outputs)}
        except Exception as e:
            logger.error(f"ethics_audit_output_bias failed: {e}")
            return {"success": False, "error": str(e)}

    def ethics_audit_data_representation(self, records: List[Dict[str, Any]], sensitive_feature_column: str) -> Dict[str, Any]:
        """Audits a dataset (list of row dicts) for representation counts/percentages across groups defined by a sensitive attribute column."""
        if not self.fairness_auditor or not PANDAS_AVAILABLE:
            return _unavailable("ethics_audit_data_representation")
        try:
            if sensitive_feature_column not in self.fairness_auditor.sensitive_attributes:
                self.fairness_auditor.sensitive_attributes.append(sensitive_feature_column)
            results = self.fairness_auditor.audit_data_representation(pd.DataFrame(records), sensitive_feature_column)
            return {"success": True, "results": results}
        except Exception as e:
            logger.error(f"ethics_audit_data_representation failed: {e}")
            return {"success": False, "error": str(e)}

    def ethics_explain_decision(self, decision_id: str, method: Optional[str] = None) -> Dict[str, Any]:
        """
        Explains a logged AI decision (reasoning trace / fired rules / model
        attribution). NOTE: the underlying TransparencyPortal has no real log
        service wired into this codebase -- it only recognizes a handful of
        hardcoded demo decision IDs ('decision_abc', 'decision_xyz',
        'decision_rule_based'). It is wrapped as-is since it does not crash,
        but it will not explain arbitrary real decision IDs until a real log
        service is integrated upstream.
        """
        if not self.transparency_portal:
            return _unavailable("ethics_explain_decision")
        try:
            explanation = self.transparency_portal.explain_decision(decision_id, desired_method=method)
            if explanation is None:
                return {"success": False, "error": f"No explanation available for decision '{decision_id}' (only demo IDs are recognized: decision_abc, decision_xyz, decision_rule_based)."}
            return {"success": True, "explanation": explanation}
        except Exception as e:
            logger.error(f"ethics_explain_decision failed: {e}")
            return {"success": False, "error": str(e)}

    # ==================================================================
    # GDPR: data mapping (ROPA) and DSAR case management
    # ==================================================================

    def gdpr_find_activities_using_data_element(self, element_id: str) -> Dict[str, Any]:
        """Finds all processing activities (ROPA entries) that involve a given data element ID. Informational only; not legal advice. Consult qualified counsel."""
        if not self.data_map:
            return _unavailable("gdpr_find_activities_using_data_element")
        try:
            activities = self.data_map.find_activities_using_data_element(element_id)
            return {"success": True, "activities": [a.activity_id for a in activities]}
        except Exception as e:
            logger.error(f"gdpr_find_activities_using_data_element failed: {e}")
            return {"success": False, "error": str(e)}

    def gdpr_find_elements_in_activity(self, activity_id: str) -> Dict[str, Any]:
        """Finds all data elements processed by a given processing activity ID. Informational only; not legal advice. Consult qualified counsel."""
        if not self.data_map:
            return _unavailable("gdpr_find_elements_in_activity")
        try:
            elements = self.data_map.find_elements_in_activity(activity_id)
            return {"success": True, "elements": [e.element_id for e in elements]}
        except Exception as e:
            logger.error(f"gdpr_find_elements_in_activity failed: {e}")
            return {"success": False, "error": str(e)}

    def gdpr_generate_ropa_summary(self, activity_id: Optional[str] = None) -> str:
        """Generates a textual Record of Processing Activities (ROPA) summary for one or all activities. Informational only; not legal advice. Consult qualified counsel."""
        if not self.data_map:
            return _unavailable("gdpr_generate_ropa_summary")["error"]
        try:
            return self.data_map.generate_ropa_summary_text(activity_id=activity_id)
        except Exception as e:
            logger.error(f"gdpr_generate_ropa_summary failed: {e}")
            return f"Error generating ROPA summary: {e}"

    def dsar_submit_request(self, subject_identifier: str, request_type: str, request_details: Optional[str] = None) -> Dict[str, Any]:
        """Opens a new Data Subject Access Request case. request_type is one of: 'ACCESS', 'PORTABILITY', 'RECTIFICATION', 'ERASURE', 'RESTRICTION_OF_PROCESSING', 'OBJECTION_TO_PROCESSING'. Informational only; not legal advice. Consult qualified counsel."""
        if not self.dsar_handler:
            return _unavailable("dsar_submit_request")
        try:
            req_type_enum = DSARRequestType[request_type.upper()]
        except KeyError:
            return {"success": False, "error": f"Invalid request_type '{request_type}'. Must be one of {[t.name for t in DSARRequestType]}."}
        try:
            case_id = self.dsar_handler.submit_request(subject_identifier, req_type_enum, request_details=request_details)
            return {"success": True, "case_id": case_id}
        except Exception as e:
            logger.error(f"dsar_submit_request failed: {e}")
            return {"success": False, "error": str(e)}

    def dsar_confirm_identity_verified(self, case_id: str, method: str, verifier: str = "ComplianceTeam") -> Dict[str, Any]:
        """Marks a DSAR case's identity-verification step as complete. Informational only; not legal advice. Consult qualified counsel."""
        if not self.dsar_handler:
            return _unavailable("dsar_confirm_identity_verified")
        return {"success": self.dsar_handler.confirm_identity_verified(case_id, method, verifier=verifier)}

    def dsar_process_next_stage(self, case_id: str, completed_by: str = "ComplianceTeam") -> Dict[str, Any]:
        """
        Advances a DSAR case to its next lifecycle stage. NOTE: the upstream
        data-discovery step (`_discover_personal_data_placeholder`) calls
        `random.random()` without importing `random`, which raises NameError
        once a case reaches the GATHERING_DATA stage -- caught here and
        surfaced as a failed result rather than crashing the caller.
        Informational only; not legal advice. Consult qualified counsel.
        """
        if not self.dsar_handler:
            return _unavailable("dsar_process_next_stage")
        try:
            ok = self.dsar_handler.process_dsar_stage(case_id, current_stage_completed_by=completed_by)
            return {"success": ok}
        except Exception as e:
            logger.error(f"dsar_process_next_stage failed (likely upstream 'random' import bug): {e}")
            return {"success": False, "error": str(e)}

    def dsar_deliver_report(self, case_id: str, delivery_method: str, actor: str = "ComplianceTeam") -> Dict[str, Any]:
        """Marks a DSAR case's compiled report as delivered to the data subject. Informational only; not legal advice. Consult qualified counsel."""
        if not self.dsar_handler:
            return _unavailable("dsar_deliver_report")
        return {"success": self.dsar_handler.deliver_report_placeholder(case_id, delivery_method, actor=actor)}

    def dsar_get_case_status(self, case_id: str) -> Dict[str, Any]:
        """Gets the current status of a DSAR case. Informational only; not legal advice. Consult qualified counsel."""
        if not self.dsar_handler:
            return _unavailable("dsar_get_case_status")
        status = self.dsar_handler.get_case_status(case_id)
        if status is None:
            return {"success": False, "error": f"Case '{case_id}' not found."}
        return {"success": True, "status": status.value}

    def dsar_get_case_details(self, case_id: str) -> Dict[str, Any]:
        """Gets the full details (including audit log) of a DSAR case. Informational only; not legal advice. Consult qualified counsel."""
        if not self.dsar_handler:
            return _unavailable("dsar_get_case_details")
        case = self.dsar_handler.get_case_details(case_id)
        if case is None:
            return {"success": False, "error": f"Case '{case_id}' not found."}
        return {"success": True, "case": case}

    # ==================================================================
    # Pentest authorization / CFAA compliance tracking
    # ==================================================================

    def cfaa_add_authorization(self, target_systems_description: str, target_identifiers: List[str],
                                client_organization_name: str, client_contact_name: str, client_contact_email: str,
                                authorization_document_reference: str, scope_of_work_summary: str,
                                authorized_action_categories: List[str], start_datetime_utc: str, end_datetime_utc: str,
                                explicitly_out_of_scope: Optional[List[str]] = None, status: str = "ACTIVE") -> Dict[str, Any]:
        """
        Logs a written-authorization record for a pentest engagement, so
        subsequent actions can be checked against it before Devin acts on a
        target. `start_datetime_utc`/`end_datetime_utc` are ISO-8601
        timestamps; `authorized_action_categories` are PentestActionCategory
        names (e.g. 'RECONNAISSANCE_ACTIVE', 'VULNERABILITY_ASSESSMENT').
        This tool helps track authorization; it does NOT constitute or
        replace an actual signed legal agreement. Informational only; not
        legal advice. Consult qualified counsel.
        """
        if not self.cfaa_manager:
            return _unavailable("cfaa_add_authorization")
        import datetime as _dt
        try:
            categories = {PentestActionCategory[c.upper()] for c in authorized_action_categories}
            record = AuthorizationRecord(
                target_systems_description=target_systems_description, target_identifiers=target_identifiers,
                client_organization_name=client_organization_name, client_contact_name=client_contact_name,
                client_contact_email=client_contact_email, authorization_document_reference=authorization_document_reference,
                scope_of_work_summary=scope_of_work_summary, authorized_action_categories=categories,
                explicitly_out_of_scope=explicitly_out_of_scope or [],
                start_datetime_utc=_dt.datetime.fromisoformat(start_datetime_utc),
                end_datetime_utc=_dt.datetime.fromisoformat(end_datetime_utc),
                status=AuthorizationStatus[status.upper()],
            )
            ok = self.cfaa_manager.add_authorization(record)
            return {"success": ok, "auth_id": record.auth_id if ok else None}
        except Exception as e:
            logger.error(f"cfaa_add_authorization failed: {e}")
            return {"success": False, "error": str(e)}

    def cfaa_is_action_authorized(self, target_identifier: str, action_category: str) -> Dict[str, Any]:
        """Checks whether a specific pentest action category is currently authorized (in scope, active, not expired) for a target. Informational only; not legal advice. Consult qualified counsel."""
        if not self.cfaa_manager:
            return _unavailable("cfaa_is_action_authorized")
        try:
            category = PentestActionCategory[action_category.upper()]
            authorized = self.cfaa_manager.is_action_authorized(target_identifier, category)
            return {"success": True, "authorized": authorized}
        except Exception as e:
            logger.error(f"cfaa_is_action_authorized failed: {e}")
            return {"success": False, "error": str(e)}

    def cfaa_get_summary_and_reminders(self) -> str:
        """Returns a plain-text summary of key CFAA (US computer-access-law) considerations for a pentester. Informational only; not legal advice. Consult qualified counsel."""
        if not CFAA_AVAILABLE:
            return _unavailable("cfaa_get_summary_and_reminders")["error"]
        return CFAAComplianceManager.get_cfaa_summary_and_reminders_text()

    def cfaa_get_pre_engagement_checklist(self) -> str:
        """Returns a plain-text pre-engagement checklist for pentest authorization and scoping. Informational only; not legal advice. Consult qualified counsel."""
        if not CFAA_AVAILABLE:
            return _unavailable("cfaa_get_pre_engagement_checklist")["error"]
        return CFAAComplianceManager.generate_pre_engagement_checklist_text()

    def legal_generate_eula_outline(self, software_name: str = "Devin AI Assistant",
                                     company_name: str = "[Your Company Name Here]",
                                     effective_date: str = "[Date]", version: str = "1.0.0") -> Dict[str, Any]:
        """
        Generates a EULA outline (section titles, placeholder clause text, and
        legal-review considerations) for an AI tool like Devin. NOTE: the
        upstream file only defines the first 4 of a planned 17 sections
        (Introduction, License Grant, Restrictions, User Responsibilities);
        this method renders whatever sections are present. This produces a
        TEMPLATE/OUTLINE only, not a legally binding document. Informational
        only; not legal advice. Consult qualified counsel.
        """
        if not self.eula_generator and not EULA_GENERATOR_AVAILABLE:
            return _unavailable("legal_generate_eula_outline")
        try:
            gen = DevinEULAOutlineGenerator(software_name=software_name, company_name=company_name,
                                             effective_date=effective_date, version=version)
        except Exception as e:
            return _unavailable("legal_generate_eula_outline", e)
        lines = [f"CONCEPTUAL EULA OUTLINE & CONSIDERATIONS for {gen.software_name} (v{gen.version})",
                 f"Provided by: {gen.company_name}  |  Effective date (placeholder): {gen.effective_date}",
                 "THIS IS A TEMPLATE/OUTLINE ONLY -- NOT A LEGALLY BINDING DOCUMENT. " + _LEGAL_DISCLAIMER, ""]
        for section in gen.sections:
            lines.append(f"--- {section.title} ---")
            if section.introduction:
                lines.append(section.introduction)
            for clause in section.placeholder_clauses:
                lines.append(f"  * {clause}")
            if section.key_considerations:
                lines.append("  Key considerations for counsel:")
                for c in section.key_considerations:
                    lines.append(f"    - {c}")
            lines.append("")
        return {"success": True, "section_count": len(gen.sections), "outline_text": "\n".join(lines)}

    def legal_generate_pentest_authorization_pdf(self, client_name: str, client_address: str, consultant_name: str,
                                                  target_scope: List[str], start_date: str, end_date: str,
                                                  output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Generates a formal PDF penetration-testing authorization agreement
        document from engagement details and writes it to disk. This is a
        document TEMPLATE to be signed by both parties; it is not itself a
        binding agreement until executed. Informational only; not legal
        advice. Consult qualified counsel.
        """
        if not WARRANT_GENERATOR_AVAILABLE:
            return _unavailable("legal_generate_pentest_authorization_pdf", _warrant_generator_import_error)
        try:
            doc = PentestAuthorizationDoc(client_name=client_name, client_address=client_address,
                                           consultant_name=consultant_name, target_scope=target_scope,
                                           start_date=start_date, end_date=end_date)
            path = output_path or f"Pentest_Authorization_{client_name.replace(' ', '_')}.pdf"
            doc.generate_pdf(path)
            return {"success": True, "output_path": path}
        except Exception as e:
            logger.error(f"legal_generate_pentest_authorization_pdf failed: {e}")
            return {"success": False, "error": str(e)}

    # ==================================================================
    # Cross-border data routing / CCPA / GDPR adequacy advisors
    # ==================================================================

    def legal_get_data_routing_recommendation(self, data_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Uses an LLM to infer the likely data-protection jurisdiction of a payload (EU/GDPR, California/CCPA, Pakistan/PDPL, or general) and recommends a compliant storage region. Informational only; not legal advice. Consult qualified counsel."""
        if not self.data_router:
            return _unavailable("legal_get_data_routing_recommendation")
        try:
            return {"success": True, "decision": self.data_router.get_routing_decision(data_payload)}
        except Exception as e:
            logger.error(f"legal_get_data_routing_recommendation failed: {e}")
            return {"success": False, "error": str(e)}

    def legal_ccpa_get_key_definitions(self) -> Dict[str, str]:
        """Returns simplified, illustrative explanations of key CCPA/CPRA terms (Personal Information, Business, Service Provider, Sale, Share, SPI, etc). Informational only; not legal advice. Consult qualified counsel."""
        if not self.ccpa_advisor:
            return _unavailable("legal_ccpa_get_key_definitions")
        return self.ccpa_advisor.get_ccpa_cpra_key_definitions()

    def legal_ccpa_get_consumer_rights_summary(self) -> List[Dict[str, str]]:
        """Returns a summary of consumer rights under CCPA/CPRA (know/access, delete, opt-out, correct, limit SPI use, non-discrimination, portability). Informational only; not legal advice. Consult qualified counsel."""
        if not self.ccpa_advisor:
            return [_unavailable("legal_ccpa_get_consumer_rights_summary")]
        return self.ccpa_advisor.get_consumer_rights_summary()

    def legal_ccpa_get_service_provider_considerations(self) -> List[str]:
        """Returns conceptual contractual considerations for when Devin's provider acts as a CCPA/CPRA 'Service Provider'. Informational only; not legal advice. Consult qualified counsel."""
        if not self.ccpa_advisor:
            return [_unavailable("legal_ccpa_get_service_provider_considerations")["error"]]
        return self.ccpa_advisor.get_service_provider_contractual_considerations()

    def legal_ccpa_get_data_flow_questions(self) -> List[str]:
        """Returns a checklist of CCPA/CPRA-relevant data-flow questions to consider for a tool like Devin. Informational only; not legal advice. Consult qualified counsel."""
        if not self.ccpa_advisor:
            return [_unavailable("legal_ccpa_get_data_flow_questions")["error"]]
        return self.ccpa_advisor.get_data_flow_ccpa_questions_for_devin()

    def legal_gdpr_check_adequacy(self, country_iso_code: str) -> Dict[str, Any]:
        """Checks a country's 2-letter ISO code against an illustrative, potentially outdated list of EU GDPR adequacy decisions. Always verify against the official European Commission list. Informational only; not legal advice. Consult qualified counsel."""
        if not self.gdpr_adequacy_advisor:
            return _unavailable("legal_gdpr_check_adequacy")
        return {"success": True, **self.gdpr_adequacy_advisor.check_conceptual_adequacy(country_iso_code)}

    def legal_gdpr_list_transfer_mechanisms(self) -> List[Dict[str, str]]:
        """Lists common GDPR international-data-transfer mechanisms (SCCs, BCRs, Codes of Conduct, Article 49 derogations). Informational only; not legal advice. Consult qualified counsel."""
        if not self.gdpr_adequacy_advisor:
            return [_unavailable("legal_gdpr_list_transfer_mechanisms")]
        return self.gdpr_adequacy_advisor.list_common_alternative_transfer_mechanisms()

    def legal_gdpr_get_pre_transfer_questions(self) -> List[str]:
        """Returns a checklist of questions to consider before transferring GDPR-covered personal data outside the EEA. Informational only; not legal advice. Consult qualified counsel."""
        if not self.gdpr_adequacy_advisor:
            return [_unavailable("legal_gdpr_get_pre_transfer_questions")["error"]]
        return self.gdpr_adequacy_advisor.get_pre_transfer_assessment_questions()


# --- Example Usage ---
if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    print("=========================================================")
    print("=== Ethics & Legal Facade Demo ===")
    print("=========================================================")
    facade = EthicsLegalFacade()
    print(facade.ethics_audit_output_bias(["The new programmer said he finished the task."]))
    print(facade.legal_ccpa_get_consumer_rights_summary()[:1])
    print("\n=========================================================")
    print("=== Ethics & Legal Facade Demo Complete ===")
    print("=========================================================")
