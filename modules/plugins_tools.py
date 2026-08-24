# Devin/modules/plugins_tools.py
# Purpose: A high-level facade that wraps the genuinely functional plugins in
#          plugins/ and community/ into a single, agent-callable interface.
#
# Scope notes (see report for full detail):
#   - plugins/gaming_assistant.py and plugins/voice_assistant.py are deliberately
#     NOT wrapped here: GamingAssistant's screen/mouse/keyboard automation fully
#     overlaps with the already-wired modules/automation_tools.py, and
#     VoiceAssistant's speech loop fully overlaps with the voice mode already
#     wired into modules/user_interaction_module.py. Wrapping either would just
#     be a second, redundant path to the same underlying capability.
#   - plugins/crypto_trading.py: only READ-ONLY market analysis methods (price
#     data, indicators, AI signal text) plus the pre-existing SIMULATED order
#     logger are wrapped. CryptoTrader contains no method that places a real
#     order or moves real funds as shipped (the real `exchange.create_order(...)`
#     call is commented out in `place_simulated_order`) -- there was therefore
#     nothing to exclude on that front, but this facade will never uncomment or
#     otherwise reach that code path.
#   - Several of the wrapped modules ship with pre-existing bugs (missing
#     `typing` imports, missing `random`/`time` imports used at call time,
#     etc.) that make them fail on import or on certain call paths. Since this
#     facade may only ADD new files, those upstream files are wrapped as
#     defensively as possible (broad try/except at both import time and call
#     time) rather than fixed. Each such landmine is called out inline below
#     and summarized in the report.

import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger("PluginsFacade")
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_h)
    logger.setLevel(logging.INFO)
logger.propagate = False


# --- Optional low-level tool imports -- each is isolated and degrades gracefully ---

try:
    from plugins.chatbot_tools import ChatbotTools
    CHATBOT_TOOLS_AVAILABLE = True
except Exception as e:  # pragma: no cover - environment dependent
    CHATBOT_TOOLS_AVAILABLE = False
    _chatbot_tools_import_error = e

try:
    # NOTE: plugins/seo_optimizer.py uses `Optional[...]` in a method signature
    # and calls `os.getenv(...)` without importing `typing.Optional` or `os` at
    # module level. This raises NameError at import time as shipped. We import
    # it defensively and disable SEO features if it fails.
    from plugins.seo_optimizer import SEO_Optimizer
    SEO_OPTIMIZER_AVAILABLE = True
except Exception as e:
    SEO_OPTIMIZER_AVAILABLE = False
    _seo_optimizer_import_error = e

try:
    from plugins.ai_composer import AIComposer
    AI_COMPOSER_AVAILABLE = True
except Exception as e:
    AI_COMPOSER_AVAILABLE = False
    _ai_composer_import_error = e

try:
    from plugins.copilot_integration import Copilot
    COPILOT_AVAILABLE = True
except Exception as e:
    COPILOT_AVAILABLE = False
    _copilot_import_error = e

try:
    from plugins.crypto_trading import CryptoTrader
    CRYPTO_TRADER_IMPORT_AVAILABLE = True
except Exception as e:
    CRYPTO_TRADER_IMPORT_AVAILABLE = False
    _crypto_trader_import_error = e

try:
    # NOTE: community/plugin_marketplace.py declares
    # `Literal['unverified', 'community', 'verified']` in the PluginManifest
    # TypedDict but never imports `Literal` from `typing`. This raises
    # NameError at import time as shipped, so this feature is currently
    # unavailable until that upstream bug is fixed. Imported defensively.
    from community.plugin_marketplace import PluginMarketplaceManager
    PLUGIN_MARKETPLACE_AVAILABLE = True
except Exception as e:
    PLUGIN_MARKETPLACE_AVAILABLE = False
    _plugin_marketplace_import_error = e

try:
    from community.bug_bounty import BugBountyManager, ReportStatus, SeverityLevel
    BUG_BOUNTY_AVAILABLE = True
except Exception as e:
    BUG_BOUNTY_AVAILABLE = False
    _bug_bounty_import_error = e


def _unavailable(feature: str, error: Optional[Exception] = None) -> Dict[str, Any]:
    """Standard graceful-degradation response for a disabled sub-feature."""
    msg = f"'{feature}' is unavailable."
    if error is not None:
        msg += f" Reason: {error}"
    logger.warning(msg)
    return {"success": False, "error": msg}


class PluginsFacade:
    """
    A single, simplified interface over Devin's real (non-conceptual) plugins:
    general chatbot utilities, SEO analysis, AI content/code composition,
    read-only crypto market analysis, and local plugin-marketplace / bug-bounty
    record-keeping.
    """

    def __init__(self, openai_api_key: Optional[str] = None, crypto_exchange_id: str = "binance"):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")

        # --- ChatbotTools (web search, calculator, time) ---
        self.chatbot_tools: Optional["ChatbotTools"] = None
        if CHATBOT_TOOLS_AVAILABLE:
            try:
                self.chatbot_tools = ChatbotTools(openai_api_key=self.openai_api_key)
            except Exception as e:
                logger.warning(f"ChatbotTools unavailable: {e}")
        else:
            logger.warning(f"ChatbotTools unavailable: {_chatbot_tools_import_error}")

        # --- SEO_Optimizer ---
        self.seo_optimizer: Optional["SEO_Optimizer"] = None
        if SEO_OPTIMIZER_AVAILABLE:
            try:
                self.seo_optimizer = SEO_Optimizer(openai_api_key=self.openai_api_key)
            except Exception as e:
                logger.warning(f"SEO_Optimizer unavailable: {e}")
        else:
            logger.warning(f"SEO_Optimizer unavailable: {_seo_optimizer_import_error}")

        # --- AIComposer (phishing/report/code-doc text generation) ---
        self.ai_composer: Optional["AIComposer"] = None
        if AI_COMPOSER_AVAILABLE and self.openai_api_key:
            try:
                self.ai_composer = AIComposer(openai_api_key=self.openai_api_key)
            except Exception as e:
                logger.warning(f"AIComposer unavailable: {e}")
        elif not AI_COMPOSER_AVAILABLE:
            logger.warning(f"AIComposer unavailable: {_ai_composer_import_error}")
        else:
            logger.warning("AIComposer unavailable: no OpenAI API key configured.")

        # --- Copilot (code generation/refinement) ---
        self.copilot: Optional["Copilot"] = None
        if COPILOT_AVAILABLE and self.openai_api_key:
            try:
                self.copilot = Copilot(openai_api_key=self.openai_api_key)
            except Exception as e:
                logger.warning(f"Copilot unavailable: {e}")
        elif not COPILOT_AVAILABLE:
            logger.warning(f"Copilot unavailable: {_copilot_import_error}")
        else:
            logger.warning("Copilot unavailable: no OpenAI API key configured.")

        # --- CryptoTrader (read-only market analysis only, see module docstring) ---
        self.crypto_trader: Optional["CryptoTrader"] = None
        if CRYPTO_TRADER_IMPORT_AVAILABLE:
            try:
                self.crypto_trader = CryptoTrader(exchange_id=crypto_exchange_id)
            except Exception as e:
                logger.warning(f"CryptoTrader unavailable: {e}")
        else:
            logger.warning(f"CryptoTrader unavailable: {_crypto_trader_import_error}")

        # --- PluginMarketplaceManager (local registry/install-state bookkeeping) ---
        self.plugin_marketplace: Optional["PluginMarketplaceManager"] = None
        if PLUGIN_MARKETPLACE_AVAILABLE:
            try:
                self.plugin_marketplace = PluginMarketplaceManager()
            except Exception as e:
                logger.warning(f"PluginMarketplaceManager unavailable: {e}")
        else:
            logger.warning(f"PluginMarketplaceManager unavailable: {_plugin_marketplace_import_error}")

        # --- BugBountyManager (local vulnerability-report case tracking) ---
        self.bug_bounty: Optional["BugBountyManager"] = None
        if BUG_BOUNTY_AVAILABLE:
            try:
                self.bug_bounty = BugBountyManager()
            except Exception as e:
                logger.warning(f"BugBountyManager unavailable: {e}")
        else:
            logger.warning(f"BugBountyManager unavailable: {_bug_bounty_import_error}")

        logger.info("PluginsFacade initialized.")

    # ------------------------------------------------------------------
    # ChatbotTools
    # ------------------------------------------------------------------

    def web_search(self, query: str, num_results: int = 3) -> Dict[str, Any]:
        """Searches the web, scrapes the top results, and returns a summary with sources."""
        if not self.chatbot_tools:
            return _unavailable("web_search")
        try:
            result = self.chatbot_tools.perform_web_search(query, num_results=num_results)
            return {"success": True, **result}
        except Exception as e:
            logger.error(f"web_search failed: {e}")
            return {"success": False, "error": str(e)}

    def calculate(self, expression: str) -> str:
        """Safely evaluates a mathematical expression and returns a human-readable result string."""
        if not self.chatbot_tools:
            return _unavailable("calculate")["error"]
        return self.chatbot_tools.calculate_expression(expression)

    def get_current_time(self, timezone_name: str = "UTC") -> str:
        """Returns the current time in the given IANA timezone name (e.g. 'Asia/Karachi')."""
        if not self.chatbot_tools:
            return _unavailable("get_current_time")["error"]
        return self.chatbot_tools.get_current_time(timezone_name)

    # ------------------------------------------------------------------
    # SEO_Optimizer
    # ------------------------------------------------------------------

    def analyze_page_seo(self, url: str, keyword: str) -> Dict[str, Any]:
        """Fetches a URL and analyzes on-page SEO factors (title, meta, headings, keyword density, missing alt text) for a target keyword."""
        if not self.seo_optimizer:
            return _unavailable("analyze_page_seo")
        analysis = self.seo_optimizer.analyze_onpage_seo(url, keyword)
        if analysis is None:
            return {"success": False, "error": f"Failed to fetch or analyze '{url}'."}
        return {"success": True, **analysis}

    def get_seo_recommendations(self, analysis: Dict[str, Any]) -> str:
        """Generates prioritized, AI-written SEO recommendations from an analyze_page_seo() result."""
        if not self.seo_optimizer:
            return _unavailable("get_seo_recommendations")["error"]
        return self.seo_optimizer.get_seo_recommendations(analysis) or "No recommendations generated."

    def generate_seo_title(self, original_title: str, keyword: str) -> str:
        """Generates an AI-optimized, keyword-rich title tag (under ~60 characters) for a page."""
        if not self.seo_optimizer:
            return _unavailable("generate_seo_title")["error"]
        return self.seo_optimizer.generate_seo_title(original_title, keyword) or "No title generated."

    # ------------------------------------------------------------------
    # AIComposer
    # ------------------------------------------------------------------

    def compose_content(self, content_type: str, context: Dict[str, Any]) -> str:
        """
        Generates text content from a template + LLM.

        content_type must be one of: 'phishing_email' (social-engineering email
        draft for an AUTHORIZED phishing simulation/pentest engagement only),
        'report_vulnerability_description' (formal pentest report writeup), or
        'code_documentation' (Markdown docs for a code snippet).

        context keys required per type:
          - phishing_email: target_name, target_department, sender_persona, subject, topic
          - report_vulnerability_description: vulnerability_name, severity, target_asset
          - code_documentation: code_snippet
        """
        if not self.ai_composer:
            return _unavailable("compose_content")["error"]
        result = self.ai_composer.compose(content_type, context)
        return result or "No content generated."

    # ------------------------------------------------------------------
    # Copilot
    # ------------------------------------------------------------------

    def generate_code(self, task_description: str, language: str = "python") -> str:
        """Generates a complete, syntax-validated script from a natural-language task description."""
        if not self.copilot:
            return _unavailable("generate_code")["error"]
        return self.copilot.generate_code(task_description, language=language) or "Code generation failed validation."

    def refine_code(self, original_code: str, refinement_request: str) -> str:
        """Modifies existing code per a natural-language refinement request; returns the full updated, syntax-validated script."""
        if not self.copilot:
            return _unavailable("refine_code")["error"]
        return self.copilot.refine_code(original_code, refinement_request) or "Code refinement failed validation."

    # ------------------------------------------------------------------
    # CryptoTrader -- READ-ONLY analysis only. See module docstring: no
    # method that executes a real trade or moves real funds is present in
    # the underlying plugin, so none was excluded, and none is wrapped here
    # beyond what is already read-only/simulated in the source file.
    # ------------------------------------------------------------------

    def crypto_get_market_data(self, symbol: str, timeframe: str = "1h", limit: int = 100) -> Dict[str, Any]:
        """Fetches historical OHLCV candles for a symbol (e.g. 'BTC/USDT') and adds technical indicators (EMA 50/200, RSI, MACD). Read-only; makes no trades."""
        if not self.crypto_trader:
            return _unavailable("crypto_get_market_data")
        df = self.crypto_trader.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        if df is None:
            return {"success": False, "error": f"Failed to fetch OHLCV data for '{symbol}'."}
        try:
            df = self.crypto_trader.add_technical_indicators(df)
        except Exception as e:
            logger.warning(f"Technical indicator calculation failed, returning raw candles: {e}")
        clean_df = df.astype(object).where(df.notnull(), None)
        return {"success": True, "symbol": symbol, "timeframe": timeframe, "candles": clean_df.to_dict(orient="records")}

    def crypto_get_ai_trading_signal(self, symbol: str, timeframe: str = "1h") -> str:
        """Generates an AI-written BUY/SELL/HOLD signal with a one-sentence rationale from current technical indicators. Informational only; does not place any trade."""
        if not self.crypto_trader:
            return _unavailable("crypto_get_ai_trading_signal")["error"]
        return self.crypto_trader.get_ai_trading_signal(symbol, timeframe=timeframe) or "No signal generated (AI Composer for crypto signals is not wired to a valid module in this codebase)."

    def crypto_log_simulated_order(self, symbol: str, side: str, amount: float, order_type: str = "market") -> str:
        """Logs a SIMULATED order (buy/sell) for record-keeping only. This NEVER places a real order or moves real funds -- the underlying plugin only logs; no exchange call is made."""
        if not self.crypto_trader:
            return _unavailable("crypto_log_simulated_order")["error"]
        self.crypto_trader.place_simulated_order(symbol, side, amount, order_type=order_type)
        return f"Simulated {side.upper()} order for {amount} {symbol} logged (no real order placed)."

    # ------------------------------------------------------------------
    # PluginMarketplaceManager -- local registry/install-state bookkeeping.
    # install_plugin/uninstall_plugin write to and delete from the local
    # filesystem (and, per the upstream docstring, is an explicitly
    # unvetted/unsandboxed conceptual installer) -- treat as dangerous.
    # ------------------------------------------------------------------

    def marketplace_list_plugins(self, filter_tag: Optional[str] = None, installed_only: bool = False) -> Dict[str, Any]:
        """Lists plugins from the local registry, optionally filtered by tag or limited to installed plugins."""
        if not self.plugin_marketplace:
            return _unavailable("marketplace_list_plugins")
        return {"success": True, "plugins": self.plugin_marketplace.list_available_plugins(filter_tag=filter_tag, installed_only=installed_only)}

    def marketplace_search_plugins(self, query: str) -> Dict[str, Any]:
        """Keyword-searches the local plugin registry by name, description, and tags."""
        if not self.plugin_marketplace:
            return _unavailable("marketplace_search_plugins")
        return {"success": True, "plugins": self.plugin_marketplace.search_plugins(query)}

    def marketplace_get_plugin_details(self, plugin_id: str) -> Dict[str, Any]:
        """Gets the full manifest for a specific plugin ID from the local registry."""
        if not self.plugin_marketplace:
            return _unavailable("marketplace_get_plugin_details")
        details = self.plugin_marketplace.get_plugin_details(plugin_id)
        if details is None:
            return {"success": False, "error": f"Plugin '{plugin_id}' not found."}
        return {"success": True, "plugin": details}

    def marketplace_install_plugin(self, plugin_id: str) -> Dict[str, Any]:
        """DANGEROUS: installs a plugin from the local registry -- creates directories, writes files, and would run `pip install` for the plugin's declared requirements. The underlying implementation explicitly warns it has no real security vetting or sandboxing."""
        if not self.plugin_marketplace:
            return _unavailable("marketplace_install_plugin")
        try:
            ok = self.plugin_marketplace.install_plugin(plugin_id)
            return {"success": ok}
        except Exception as e:
            logger.error(f"marketplace_install_plugin failed: {e}")
            return {"success": False, "error": str(e)}

    def marketplace_uninstall_plugin(self, plugin_id: str) -> Dict[str, Any]:
        """DANGEROUS: uninstalls a plugin and recursively deletes its install directory from the local filesystem."""
        if not self.plugin_marketplace:
            return _unavailable("marketplace_uninstall_plugin")
        try:
            ok = self.plugin_marketplace.uninstall_plugin(plugin_id)
            return {"success": ok}
        except Exception as e:
            logger.error(f"marketplace_uninstall_plugin failed: {e}")
            return {"success": False, "error": str(e)}

    # ------------------------------------------------------------------
    # BugBountyManager -- local vulnerability-report case tracking (JSON-file
    # persisted). No real payment/reward transfer occurs anywhere in the
    # underlying class; reward assignment only records an amount + note.
    # ------------------------------------------------------------------

    def bugbounty_submit_report(self, reporter_email: str, affected_component: str, vulnerability_type: str,
                                 severity: str, summary: str, description: str, reproduction_steps: str,
                                 potential_impact: Optional[str] = None) -> Dict[str, Any]:
        """Submits a new vulnerability report and returns its generated report ID."""
        if not self.bug_bounty:
            return _unavailable("bugbounty_submit_report")
        try:
            severity_enum = SeverityLevel(severity)
        except ValueError:
            return {"success": False, "error": f"Invalid severity '{severity}'. Must be one of {[s.value for s in SeverityLevel]}."}
        report_id = self.bug_bounty.submit_report(
            reporter_email=reporter_email, affected_component=affected_component,
            vulnerability_type=vulnerability_type, severity=severity_enum, summary=summary,
            description=description, reproduction_steps=reproduction_steps, potential_impact=potential_impact,
        )
        if report_id is None:
            return {"success": False, "error": "Submission failed (missing required fields)."}
        return {"success": True, "report_id": report_id}

    def bugbounty_get_report(self, report_id: str) -> Dict[str, Any]:
        """Retrieves the full details of a specific vulnerability report."""
        if not self.bug_bounty:
            return _unavailable("bugbounty_get_report")
        report = self.bug_bounty.get_report(report_id)
        if report is None:
            return {"success": False, "error": f"Report '{report_id}' not found."}
        return {"success": True, "report": report}

    def bugbounty_list_reports(self, status_filter: Optional[List[str]] = None, max_results: int = 100) -> Dict[str, Any]:
        """Lists report summaries, optionally filtered by one or more status names (e.g. 'Received', 'Resolved')."""
        if not self.bug_bounty:
            return _unavailable("bugbounty_list_reports")
        try:
            statuses = [ReportStatus(s) for s in status_filter] if status_filter else None
        except ValueError as e:
            return {"success": False, "error": f"Invalid status in filter: {e}"}
        return {"success": True, "reports": self.bug_bounty.list_reports(status_filter=statuses, max_results=max_results)}

    def bugbounty_update_report_status(self, report_id: str, new_status: str, internal_note: str, updating_user: str = "System") -> Dict[str, Any]:
        """Updates a vulnerability report's status and appends an internal audit note."""
        if not self.bug_bounty:
            return _unavailable("bugbounty_update_report_status")
        try:
            status_enum = ReportStatus(new_status)
        except ValueError:
            return {"success": False, "error": f"Invalid status '{new_status}'. Must be one of {[s.value for s in ReportStatus]}."}
        ok = self.bug_bounty.update_report_status(report_id, status_enum, internal_note, updating_user=updating_user)
        return {"success": ok}

    def bugbounty_assign_reward(self, report_id: str, amount: float, justification: str, assigning_user: str = "System") -> Dict[str, Any]:
        """Records a reward amount and justification against a report (record-keeping only -- does NOT transfer any funds)."""
        if not self.bug_bounty:
            return _unavailable("bugbounty_assign_reward")
        ok = self.bug_bounty.assign_reward(report_id, amount, justification, assigning_user=assigning_user)
        return {"success": ok}


# --- Example Usage ---
if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    print("=========================================================")
    print("=== Plugins Facade Demo ===")
    print("=========================================================")
    facade = PluginsFacade()
    print(facade.calculate("(2**10) / 4 - 50"))
    print(facade.get_current_time("UTC"))
    print("\n=========================================================")
    print("=== Plugins Facade Demo Complete ===")
    print("=========================================================")
