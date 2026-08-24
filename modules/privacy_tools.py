# Devin/modules/privacy_tools.py
# Purpose: A high-level facade that orchestrates Devin's privacy toolkit --
#          differential privacy, PII detection/anonymization, and GDPR-style
#          data portability exports -- into a single, agent-friendly interface.

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

# --- Import the low-level privacy tools this facade will manage ---
# Each underlying module already guards its own optional third-party
# dependency (diffprivlib, presidio, Faker, spaCy) with try/except
# ImportError internally and only raises when the class is instantiated,
# never on import -- but we guard the imports here too so a missing/renamed
# submodule can never take the facade (and, via main.py, the whole
# assistant) down with it.

try:
    from privacy.differential_privacy import DifferentialPrivacy
    _HAS_DP_MOD = True
except ImportError:
    _HAS_DP_MOD = False

try:
    from privacy.data_obfuscation import DataObfuscator
    _HAS_OBFUSCATION_MOD = True
except ImportError:
    _HAS_OBFUSCATION_MOD = False

try:
    from privacy.gdpr_data_portability import DataPortabilityTool
    _HAS_PORTABILITY_MOD = True
except ImportError:
    _HAS_PORTABILITY_MOD = False
except Exception:
    # gdpr_data_portability.py's own optional import of VulnerabilityManager
    # (used only for its __main__ demo, guarded there with `except
    # ImportError`) pulls in modules/pentesting_tools/os_fingerprint_scanner.py,
    # which has an unrelated pre-existing bug (a bare `Dict` type annotation
    # on a dataclass field with no `typing` import) that raises NameError
    # instead of ImportError when that optional chain is broken. That bug
    # lives in a shared pentesting_tools/ file outside this facade's scope
    # (not one we're directly wrapping, and other work may be touching that
    # area in parallel), so it isn't fixed here. DataPortabilityTool itself
    # has no real dependency on VulnerabilityManager, so we retry the import
    # once with that one optional name pre-stubbed out, purely to route
    # around the unrelated NameError -- this changes nothing for any code
    # that already imported the real module successfully (setdefault only).
    try:
        import sys
        import types

        class _VulnerabilityManagerUnavailable:
            """Stand-in used only to short-circuit gdpr_data_portability.py's
            unrelated, demo-only optional import; never used by this facade."""
            def __init__(self, *args, **kwargs):
                raise ImportError("VulnerabilityManager unavailable (see modules/privacy_tools.py comment).")

        _stub = types.ModuleType("modules.pentesting_tools.vulnerability_management")
        _stub.VulnerabilityManager = _VulnerabilityManagerUnavailable
        sys.modules.setdefault("modules.pentesting_tools.vulnerability_management", _stub)

        from privacy.gdpr_data_portability import DataPortabilityTool
        _HAS_PORTABILITY_MOD = True
    except Exception:
        _HAS_PORTABILITY_MOD = False

# Configure basic logging
logger = logging.getLogger("PrivacyFacade")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)
logger.propagate = False


class PrivacyFacade:
    """
    A single, simplified interface to Devin's privacy toolchain: applying
    differential privacy to statistical queries, detecting/anonymizing PII
    in free text, and exporting a user/project's data for GDPR-style data
    portability requests.

    All three underlying capabilities are real, working Python (statistics,
    NLP-based PII detection, and sqlite/csv/zip data export respectively).
    Each degrades gracefully if its optional third-party dependency isn't
    installed: the corresponding component is disabled (logged as a
    warning) and its methods return None instead of raising.
    """

    def __init__(self):
        # --- Differential privacy (requires 'diffprivlib') ---
        self.differential_privacy: Optional["DifferentialPrivacy"] = None
        if _HAS_DP_MOD:
            try:
                self.differential_privacy = DifferentialPrivacy()
            except ImportError as e:
                logger.warning(f"Differential privacy unavailable: {e}")
        else:
            logger.warning("privacy.differential_privacy module not found; differential privacy disabled.")

        # --- PII detection/anonymization (requires presidio-analyzer,
        # presidio-anonymizer, Faker, spaCy + the 'en_core_web_lg' model) ---
        self.data_obfuscator: Optional["DataObfuscator"] = None
        if _HAS_OBFUSCATION_MOD:
            try:
                self.data_obfuscator = DataObfuscator()
            except ImportError as e:
                logger.warning(f"PII detection/anonymization unavailable: {e}")
            except OSError as e:
                # DataObfuscator raises OSError (re-raised from spaCy) when
                # the required 'en_core_web_lg' model isn't downloaded.
                logger.warning(f"PII detection/anonymization unavailable (spaCy model missing): {e}")
        else:
            logger.warning("privacy.data_obfuscation module not found; PII tools disabled.")

        # --- GDPR data portability (pure stdlib: sqlite3/json/csv/zipfile,
        # always available) -- DataPortabilityTool instances are opened
        # per-call with the caller's db paths, so nothing is constructed
        # eagerly here.
        self._portability_available = _HAS_PORTABILITY_MOD
        if not self._portability_available:
            logger.warning("privacy.gdpr_data_portability module not found; data export disabled.")

        logger.info("PrivacyFacade initialized.")

    # ------------------------------------------------------------------
    # Differential privacy
    # ------------------------------------------------------------------

    def get_private_mean(
        self, data: List[float], epsilon: float, min_bound: float, max_bound: float
    ) -> Optional[float]:
        """
        Computes a differentially private mean of a numerical dataset.

        Args:
            data: The numbers to average.
            epsilon: Privacy budget (> 0); smaller = more privacy/noise.
            min_bound: Known lower bound of the data's possible values.
            max_bound: Known upper bound of the data's possible values.

        Returns:
            The noisy, differentially private mean, or None if
            diffprivlib isn't installed or epsilon is invalid.
        """
        if not self.differential_privacy:
            logger.error("Differential privacy unavailable ('diffprivlib' not installed).")
            return None
        try:
            return float(self.differential_privacy.get_private_mean(data, epsilon, (min_bound, max_bound)))
        except Exception as e:
            logger.error(f"Private mean calculation failed: {e}")
            return None

    def get_private_histogram(self, data: List[str], epsilon: float) -> Optional[Dict[str, float]]:
        """
        Computes a differentially private histogram (noisy counts per
        category) of a categorical dataset.

        Args:
            data: The categorical values to count.
            epsilon: Privacy budget (> 0); smaller = more privacy/noise.

        Returns:
            A dict of category -> noisy count, or None on failure.
        """
        if not self.differential_privacy:
            logger.error("Differential privacy unavailable ('diffprivlib' not installed).")
            return None
        try:
            counts = self.differential_privacy.get_private_histogram(data, epsilon)
            return {str(k): float(v) for k, v in counts.items()}
        except Exception as e:
            logger.error(f"Private histogram calculation failed: {e}")
            return None

    # ------------------------------------------------------------------
    # PII detection & anonymization
    # ------------------------------------------------------------------

    def analyze_pii(self, text: str) -> Optional[List[Dict[str, Any]]]:
        """
        Detects Personally Identifiable Information (PII) in text.

        Returns:
            A list of {"entity_type", "start", "end", "score"} dicts, one
            per detected PII span, or None if the PII stack isn't installed.
        """
        if not self.data_obfuscator:
            logger.error("PII detection unavailable (presidio/spaCy not installed or model missing).")
            return None
        try:
            results = self.data_obfuscator.analyze_pii(text)
            return [
                {
                    "entity_type": r.entity_type,
                    "start": r.start,
                    "end": r.end,
                    "score": float(r.score),
                }
                for r in results
            ]
        except Exception as e:
            logger.error(f"PII analysis failed: {e}")
            return None

    def redact_pii(self, text: str) -> Optional[str]:
        """Replaces detected PII in text with its entity type (e.g. '<PERSON>')."""
        if not self.data_obfuscator:
            logger.error("PII redaction unavailable (presidio/spaCy not installed or model missing).")
            return None
        try:
            return self.data_obfuscator.redact(text)
        except Exception as e:
            logger.error(f"PII redaction failed: {e}")
            return None

    def pseudonymize_pii(self, text: str) -> Optional[str]:
        """Replaces detected PII in text with realistic fake data (via Faker)."""
        if not self.data_obfuscator:
            logger.error("PII pseudonymization unavailable (presidio/Faker/spaCy not installed or model missing).")
            return None
        try:
            return self.data_obfuscator.pseudonymize_with_faker(text)
        except Exception as e:
            logger.error(f"PII pseudonymization failed: {e}")
            return None

    # ------------------------------------------------------------------
    # GDPR data portability
    # ------------------------------------------------------------------

    def export_project_data(
        self, db_paths: Dict[str, str], project_id: int, output_dir: str
    ) -> Optional[Dict[str, Any]]:
        """
        Exports all data for a given project ID to JSON/CSV files and
        packages them into a zip archive, for GDPR-style data portability.

        Args:
            db_paths: Map of data-source name to its SQLite DB file path.
                      Must include a 'vuln_db' entry (see
                      privacy.gdpr_data_portability.DataPortabilityTool).
            project_id: The ID of the project whose data should be exported.
            output_dir: Directory to write the exported JSON/CSV files into
                        (the final zip archive is written alongside it,
                        named 'project_{project_id}_export.zip').

        Returns:
            {"output_dir": str, "zip_path": str} on success, or None on
            failure (e.g. project not found, or DB file missing).
        """
        if not self._portability_available:
            logger.error("Data portability unavailable (gdpr_data_portability module missing).")
            return None
        tool = None
        try:
            resolved_db_paths = {name: Path(path) for name, path in db_paths.items()}
            out_dir = Path(output_dir)
            tool = DataPortabilityTool(db_paths=resolved_db_paths)
            tool.export_project_data(project_id=project_id, output_dir=out_dir)
            zip_path = out_dir.parent / f"project_{project_id}_export.zip"
            if not zip_path.is_file():
                logger.error("Data export failed: expected archive was not created.")
                return None
            return {"output_dir": str(out_dir), "zip_path": str(zip_path)}
        except Exception as e:
            logger.error(f"Data export failed: {e}")
            return None
        finally:
            if tool:
                tool.close_connections()


# --- Example Usage ---
if __name__ == "__main__":
    import json

    print("=========================================================")
    print("=== Privacy Facade Demo ===")
    print("=========================================================")

    facade = PrivacyFacade()

    print("\n--- Differential privacy (requires diffprivlib) ---")
    print(facade.get_private_mean([25, 31, 45, 62, 28], epsilon=1.0, min_bound=18, max_bound=100))

    print("\n--- PII detection (requires presidio + spaCy model) ---")
    sample = "Contact John Doe at john.doe@email.com or (555) 867-5309."
    print(json.dumps(facade.analyze_pii(sample), indent=2))
    print(facade.redact_pii(sample))

    print("\n=========================================================")
    print("=== Privacy Facade Demo Complete ===")
    print("=========================================================")
