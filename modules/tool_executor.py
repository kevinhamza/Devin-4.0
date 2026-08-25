# Devin/modules/tool_executor.py
# Purpose: The central dispatcher for executing tool calls from the AI agent.
#          It maps tool names to Python functions and handles execution.

import inspect
import logging
from typing import Dict, Any, List, Callable, Optional

# --- Import all tool-providing modules ---
from modules.all_ais_modules import AIAgent
from security.security_dashboard import SecurityDashboard
from modules.cloud_integration_services import CloudServicesManager
from modules.pentesting_tools.pentesting_facade import PentestingFacade
from modules.pentesting_tools.hexstrike_client import HexStrikeClient
from modules.automation_tools import DesktopAutomator, WebAutomator
from modules.system_monitor_module import SystemMonitorFacade
from modules.mobile_integration_module import MobileFacade
from modules.os_operations.universal_operations import UniversalOSOperator
from modules.os_operations.self_operating_computer_tool import operate_computer, SOC_AVAILABLE
from modules.knowledge_retrieval.code_retriever import CodeRetriever
from modules.data_logger import DataLogger
from modules.code_execution import CodeExecutor # For execute_shell, etc.

# Configure basic logging
logger = logging.getLogger("ToolExecutor")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)
logger.propagate = False

# --- Extended-capability facades ---
# Each of these wraps a previously-unwired top-level directory. Imports are
# individually guarded so a broken/optional dependency in one facade can't
# take down tool registration for every other one.
def _optional_import(module_path: str, class_name: str):
    try:
        module = __import__(module_path, fromlist=[class_name])
        return getattr(module, class_name)
    except Exception as e:
        logger.warning(f"Extended capability '{class_name}' unavailable ({module_path}): {e}")
        return None

PluginsFacade = _optional_import("modules.plugins_tools", "PluginsFacade")
EthicsLegalFacade = _optional_import("modules.ethics_legal_tools", "EthicsLegalFacade")
RealityEngineFacade = _optional_import("modules.reality_xr_tools", "RealityEngineFacade")
XRFacade = _optional_import("modules.xr_tools", "XRFacade")
PlatformOpsFacade = _optional_import("modules.platform_ops_tools", "PlatformOpsFacade")
QuantumFacade = _optional_import("modules.quantum_tools", "QuantumFacade")
PrivacyFacade = _optional_import("modules.privacy_tools", "PrivacyFacade")
ResilienceFacade = _optional_import("modules.resilience_tools", "ResilienceFacade")
ThreatIntelFacade = _optional_import("modules.threat_intel_tools", "ThreatIntelFacade")
CyberRangeFacade = _optional_import("modules.cyber_range_tools", "CyberRangeFacade")
ConsentedFaceRecognizer = _optional_import("modules.face_recognition_tools", "ConsentedFaceRecognizer")

class ToolExecutor:
    """
    Manages and executes all available tools for the AGI.
    """
    def __init__(self, **kwargs: Any):
        self.tools: Dict[str, Dict[str, Any]] = {}
        self._initialize_dependencies(kwargs)
        self._register_all_tools()
        logger.info(f"ToolExecutor initialized with {len(self.tools)} tools.")

    def _initialize_dependencies(self, managers: Dict[str, Any]):
        """Store all the manager/facade instances passed in."""
        self.ai_agent: AIAgent = managers.get("ai_agent")
        self.security_dashboard: SecurityDashboard = managers.get("security_dashboard")
        self.cloud_manager: CloudServicesManager = managers.get("cloud_services_manager")
        self.pentesting_facade: PentestingFacade = managers.get("pentesting_facade")
        self.hexstrike_client: HexStrikeClient = managers.get("hexstrike_client", HexStrikeClient())
        self.desktop_automator: DesktopAutomator = managers.get("desktop_automator")
        self.web_automator: WebAutomator = managers.get("web_automator")
        self.system_monitor: SystemMonitorFacade = managers.get("system_monitor_facade")
        self.mobile_facade: MobileFacade = managers.get("mobile_facade")
        self.os_operator: UniversalOSOperator = managers.get("os_operator")
        self.code_retriever: CodeRetriever = managers.get("code_retriever")
        self.data_logger: DataLogger = managers.get("data_logger")
        self.code_executor: CodeExecutor = managers.get("code_executor", CodeExecutor())
        # --- Ported OpenClaw Managers ---
        self.messaging_gateway = managers.get("messaging_gateway")
        self.canvas_server = managers.get("canvas_server")
        
        # --- Extended Capability Managers ---
        self.robotics_manager = managers.get("robotics_manager")
        self.social_manager = managers.get("social_manager")
        self.email_client = managers.get("email_client")
        self.hashing_tools = managers.get("hashing_tools")
        self.symmetric_crypto = managers.get("symmetric_crypto")
        self.asymmetric_crypto = managers.get("asymmetric_crypto")

    _TYPE_MAP = {
        str: "string", int: "integer", float: "number",
        bool: "boolean", dict: "object", list: "array",
    }

    def _infer_schema(self, function: Callable) -> Dict[str, Any]:
        """
        Builds a JSON schema for a tool's parameters from its function
        signature, since the AI providers otherwise have no way to know what
        arguments a tool expects and can only guess.
        """
        try:
            signature = inspect.signature(function)
        except (TypeError, ValueError):
            return {"type": "object", "properties": {}}

        properties: Dict[str, Any] = {}
        required: List[str] = []
        for param_name, param in signature.parameters.items():
            if param_name == "self" or param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                continue
            json_type = self._TYPE_MAP.get(param.annotation, "string")
            properties[param_name] = {"type": json_type}
            if param.default is inspect.Parameter.empty:
                required.append(param_name)

        schema: Dict[str, Any] = {"type": "object", "properties": properties}
        if required:
            schema["required"] = required
        return schema

    def _register_tool(self, name: str, function: Callable, description: str, is_dangerous: bool = False):
        """Registers a single tool in the tool registry."""
        self.tools[name] = {
            "function": function,
            "description": description,
            "is_dangerous": is_dangerous,
            "parameters": self._infer_schema(function),
        }

    def _register_facade_tools(self, facade: Any, dangerous: Optional[set] = None, skip: Optional[set] = None):
        """
        Registers every public method of a facade as a tool, using the first
        line of each method's docstring as its description. Used for the
        extended-capability facades, which are large enough (dozens of
        methods each) that hand-writing one `_register_tool(...)` call per
        method the way the original facades above do would just be the same
        information restated -- the method name and docstring already are
        the tool name and description.
        """
        if facade is None:
            return
        dangerous = dangerous or set()
        skip = skip or set()
        for name, method in inspect.getmembers(facade, predicate=inspect.ismethod):
            if name.startswith("_") or name in skip:
                continue
            doc = inspect.getdoc(method)
            description = doc.split("\n")[0].strip() if doc else f"Calls {facade.__class__.__name__}.{name}."
            self._register_tool(name, method, description, is_dangerous=name in dangerous)

    def _register_all_tools(self):
        """Registers all public methods from the facades and managers as tools."""
        # --- Code Execution ---
        self._register_tool("execute_shell", lambda command: self.code_executor.execute_code("shell", command), "Executes a shell command.", is_dangerous=True)
        self._register_tool("execute_python", lambda code: self.code_executor.execute_code("python", code), "Executes a block of Python code.", is_dangerous=True)
        
        # --- Cloud Services ---
        if self.cloud_manager:
            self._register_tool("list_vms", self.cloud_manager.list_vms, "Lists virtual machines from a cloud provider (aws, gcp, azure).")
            self._register_tool("stop_vm", self.cloud_manager.stop_vm, "Stops a specific virtual machine.", is_dangerous=True)

        # --- File System & OS ---
        if self.os_operator:
            self._register_tool("list_files", self.os_operator.list_directory, "Lists files in a specified directory.")
            self._register_tool("read_file", self.os_operator.read_file, "Reads the content of a specified file.")
            self._register_tool("write_file", self.os_operator.write_file, "Writes content to a specified file.", is_dangerous=True)

        # --- Desktop Automation ---
        if self.desktop_automator:
            self._register_tool("open_application", self.desktop_automator.open_application, "Opens an application by name using the OS-native run/search dialog.")
            self._register_tool("move_mouse", self.desktop_automator.move_mouse_to, "Moves the mouse to specific (x, y) coordinates.")
            self._register_tool("click_mouse", self.desktop_automator.mouse_click, "Clicks the mouse (left or right).")
            self._register_tool("type_text", self.desktop_automator.type_text, "Types text on the keyboard.")
            self._register_tool("take_screenshot", self.desktop_automator.take_screenshot, "Takes a screenshot of the current screen.")
            self._register_tool("close_application", self.desktop_automator.close_application, "Terminates a running application by (partial) process name.", is_dangerous=True)
            self._register_tool("lock_system", self.desktop_automator.lock_system, "Locks the current desktop session.")
            self._register_tool("restart_system", self.desktop_automator.restart_system, "Restarts the computer. Irreversible and immediately disruptive.", is_dangerous=True)
            self._register_tool("shutdown_system", self.desktop_automator.shutdown_system, "Shuts down the computer. Irreversible and immediately disruptive.", is_dangerous=True)

        # --- Pentesting ---
        # PentestingFacade was wired to real scanners earlier this session
        # (it used to silently mock every scan) but was never actually
        # exposed here, so the agent could never call it as a tool at all.
        if self.pentesting_facade:
            self._register_tool("run_full_pentest_scan", self.pentesting_facade.run_full_scan, "Runs a full pentest scan (port scan + web security headers + default error page check) against a target host.", is_dangerous=True)
        # hexstrike-ai (~150 security tools) runs as its own server process;
        # this dispatches to it over HTTP if one is running, and reports
        # clearly if it isn't rather than silently failing.
        self._register_tool("run_hexstrike_command", self.hexstrike_client.run_security_tool_command, "Runs a security-tool command (e.g. 'nmap -sV target.com') via the hexstrike-ai server's 150+ tool arsenal.", is_dangerous=True)

        # --- Vision-Based Computer Operation (self-operating-computer) ---
        # Unlike move_mouse/click_mouse above (which need exact coordinates the
        # AI has no way to know), this drives the screen by actually looking
        # at it, so it can complete open-ended objectives on unfamiliar UIs.
        if SOC_AVAILABLE:
            self._register_tool(
                "operate_computer",
                operate_computer,
                "Autonomously operates the real screen (looks at it, clicks, types) to complete an open-ended objective, e.g. 'open Chrome and search for X'. Requires a real display -- does nothing useful in a headless environment.",
                is_dangerous=True,
            )

        # --- Web Automation ---
        if self.web_automator:
            self._register_tool("navigate_to_url", self.web_automator.navigate_to_url, "Opens a web browser and navigates to a specific URL.")
            self._register_tool("scrape_web_page", self.web_automator.scrape_visible_text, "Scrapes all visible text from the current web page.")
            self._register_tool("scrape_text_from_elements", self.web_automator.scrape_text_from_elements, "Scrapes the text of every element matching a locator, e.g. ['tag name', 'h1'].")
        
        # --- OpenClaw Ported Tools ---
        if self.messaging_gateway:
            self._register_tool("send_message", self.messaging_gateway.send_message, "Sends a message via a specified channel (e.g., 'Telegram') to a recipient.")
        
        if self.canvas_server:
            self._register_tool("update_canvas", self.canvas_server.log, "Updates the live visual canvas with a message and status level (info, success, error).")
            self._register_tool("clear_canvas", self.canvas_server.clear, "Clears all content from the live visual canvas.")
            
        # --- Robotics Tools ---
        if self.robotics_manager:
            self._register_tool("robot_move_relative", self.robotics_manager.move_relative, "Moves the robot relative to its current position.")
            self._register_tool("robot_rotate_relative", self.robotics_manager.rotate_relative, "Rotates the robot by a specific angle.")
            self._register_tool("robot_stop", self.robotics_manager.trigger_emergency_stop, "Triggers an emergency stop on the robot.", is_dangerous=True)
            
        # --- Social Media Tools ---
        if self.social_manager:
            self._register_tool("search_social_media", self.social_manager.search_posts, "Searches for posts on Twitter or Reddit.")
            self._register_tool("post_social_media_update", self.social_manager.post_update, "Posts a status update to Facebook, Instagram, or LinkedIn (Instagram requires an image_url).", is_dangerous=True)
            self._register_tool("get_social_media_feed", self.social_manager.get_feed, "Fetches the authenticated user's own recent posts from Facebook or Instagram.")
            
        # --- Email Tools ---
        if self.email_client:
            self._register_tool("send_email", self.email_client.send_email, "Sends an email via SMTP.", is_dangerous=True)
            self._register_tool("search_emails", self.email_client.search_emails, "Searches for emails via IMAP.")
            
        # --- Crypto Tools ---
        if self.hashing_tools:
            self._register_tool("hash_data", self.hashing_tools.hash_data, "Hashes data using a specified algorithm (sha256, etc.).")
        if self.symmetric_crypto:
            self._register_tool("encrypt_data", self.symmetric_crypto.encrypt, "Encrypts data using symmetric encryption.")
            self._register_tool("decrypt_data", self.symmetric_crypto.decrypt, "Decrypts data using symmetric encryption.")

        # --- Extended Capabilities: Plugins & Community ---
        if PluginsFacade:
            try:
                self._register_facade_tools(
                    PluginsFacade(),
                    dangerous={"marketplace_install_plugin", "marketplace_uninstall_plugin", "compose_content"},
                )
            except Exception as e:
                logger.warning(f"PluginsFacade unavailable: {e}")

        # --- Extended Capabilities: Ethics, Legal & Compliance (informational only, not legal advice) ---
        if EthicsLegalFacade:
            try:
                self._register_facade_tools(EthicsLegalFacade())
            except Exception as e:
                logger.warning(f"EthicsLegalFacade unavailable: {e}")

        # --- Extended Capabilities: Reality Engine (web/dark-web crawling, IoT, geolocation) ---
        if RealityEngineFacade:
            try:
                self._register_facade_tools(
                    RealityEngineFacade(),
                    dangerous={"crawl_dark_web_page", "renew_dark_web_tor_identity", "set_iot_device_power", "set_iot_bulb_color", "discover_iot_devices"},
                )
            except Exception as e:
                logger.warning(f"RealityEngineFacade unavailable: {e}")

        # --- Extended Capabilities: XR / Unity bridge & spatial reasoning ---
        if XRFacade:
            try:
                self._register_facade_tools(XRFacade())
            except Exception as e:
                logger.warning(f"XRFacade unavailable: {e}")

        # --- Extended Capabilities: Platform Ops (monitoring, licensing, MLOps drift detection, fairness) ---
        if PlatformOpsFacade:
            try:
                self._register_facade_tools(PlatformOpsFacade())
            except Exception as e:
                logger.warning(f"PlatformOpsFacade unavailable: {e}")

        # --- Extended Capabilities: Quantum computing sim & post-quantum crypto ---
        if QuantumFacade:
            try:
                self._register_facade_tools(QuantumFacade())
            except Exception as e:
                logger.warning(f"QuantumFacade unavailable: {e}")

        # --- Consented Face Recognition ---
        # Matches faces only against a closed set of people explicitly added
        # via add_known_face() -- never attempts to identify anyone outside
        # that set (see modules/face_recognition_tools.py for why).
        if ConsentedFaceRecognizer:
            try:
                self._register_facade_tools(ConsentedFaceRecognizer())
            except Exception as e:
                logger.warning(f"ConsentedFaceRecognizer unavailable: {e}")

        # --- Extended Capabilities: Privacy (differential privacy, PII redaction, GDPR export) ---
        if PrivacyFacade:
            try:
                self._register_facade_tools(PrivacyFacade())
            except Exception as e:
                logger.warning(f"PrivacyFacade unavailable: {e}")

        # --- Extended Capabilities: Resilience (digital twins, chaos engineering, backup/rollback) ---
        if ResilienceFacade:
            try:
                self._register_facade_tools(
                    ResilienceFacade(),
                    dangerous={"rollback_to_snapshot", "restore_from_backup", "register_monitored_process", "start_process_watchdog"},
                )
            except Exception as e:
                logger.warning(f"ResilienceFacade unavailable: {e}")

        # --- Extended Capabilities: Threat Intelligence (read-only lookups: MITRE ATT&CK,
        # VirusTotal, IOC feeds, attack-surface recon -- same risk tier as the existing
        # PentestingFacade scan tool above). Deliberately excludes the malware sandbox
        # (executes untrusted files) and cyber_range's red-team/ransomware-sim content.
        if ThreatIntelFacade:
            try:
                self._register_facade_tools(ThreatIntelFacade(), dangerous={"analyze_attack_surface"})
            except Exception as e:
                logger.warning(f"ThreatIntelFacade unavailable: {e}")

        # --- Extended Capabilities: Cyber Range (CTF training + defensive blue-team simulation).
        # Deliberately excludes cyber_range's red-team/ai_red_team/cyber_battle_simulator content.
        if CyberRangeFacade:
            try:
                self._register_facade_tools(CyberRangeFacade())
            except Exception as e:
                logger.warning(f"CyberRangeFacade unavailable: {e}")


    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Returns a list of tool schemas for the AI to use."""
        return [
            {"name": name, "description": data["description"], "parameters": data["parameters"]}
            for name, data in self.tools.items()
        ]

    def is_dangerous(self, tool_name: str) -> bool:
        """Checks if a tool is flagged as potentially dangerous."""
        return self.tools.get(tool_name, {}).get("is_dangerous", False)

    def execute_tool(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """Finds and executes the requested tool with the given parameters."""
        tool_name = tool_call.get("tool")
        parameters = tool_call.get("parameters", {})

        if not tool_name:
            return {"status": "error", "message": "Tool call is missing the 'tool' key."}
            
        if tool_name not in self.tools:
            return {"status": "error", "message": f"Tool '{tool_name}' not found."}
            
        if not isinstance(parameters, dict):
            return {"status": "error", "message": "Tool 'parameters' must be a dictionary."}

        tool_info = self.tools[tool_name]
        function_to_execute = tool_info["function"]

        logger.info(f"Executing tool '{tool_name}' with parameters: {parameters}")
        
        try:
            # Execute the function with keyword argument unpacking
            result = function_to_execute(**parameters)
            return {"status": "success", "result": result}
        except TypeError as e:
            # This often happens if the AI provides incorrect or missing parameters
            logger.error(f"TypeError during tool execution for '{tool_name}': {e}")
            return {"status": "error", "message": f"Incorrect parameters provided for tool '{tool_name}'. Error: {e}"}
        except Exception as e:
            # Catch any other exception from the tool itself
            logger.error(f"An unexpected error occurred in tool '{tool_name}': {e}", exc_info=True)
            return {"status": "error", "message": f"Tool '{tool_name}' failed with an unexpected error: {e}"}

# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== Tool Executor Demo 🛠️ ===")
    print("=========================================================")

    # 1. Create Mocks for all dependencies
    class MockManager:
        def list_vms(self, provider: str):
            print(f"--- MOCK: Listing VMs for {provider}... ---")
            return [{"name": "mock-vm-1", "status": "running"}]
        def navigate_to_url(self, url: str):
            print(f"--- MOCK: Navigating to {url}... ---")
            return {"status": "complete"}

    mock_manager = MockManager()
    
    # 2. Instantiate the real ToolExecutor with the mocks
    executor = ToolExecutor(
        cloud_services_manager=mock_manager,
        web_automator=mock_manager # The mock has methods for both
        # other mocks would be passed here
    )

    # 3. Show the "menu" of tools the AI can use
    print("\n--- Available Tools for AI Agent ---")
    import json
    print(json.dumps(executor.get_available_tools(), indent=2))
    
    # 4. Demonstrate executing various tool calls
    print("\n--- Demonstrating Tool Execution ---")
    
    # a) Valid tool call
    print("\n1. Executing a valid tool call...")
    valid_call = {"tool": "list_vms", "parameters": {"provider": "AWS"}}
    result = executor.execute_tool(valid_call)
    print(f"   Result -> {result}")
    
    # b) Dangerous tool call
    print("\n2. Checking a dangerous tool...")
    dangerous_tool_name = "execute_shell"
    is_dangerous = executor.is_dangerous(dangerous_tool_name)
    print(f"   Is '{dangerous_tool_name}' dangerous? -> {is_dangerous}")
    
    # c) Non-existent tool
    print("\n3. Executing a non-existent tool call...")
    invalid_call = {"tool": "delete_database", "parameters": {}}
    result = executor.execute_tool(invalid_call)
    print(f"   Result -> {result}")
    
    # d) Tool with incorrect parameters
    print("\n4. Executing a tool with incorrect parameters...")
    bad_param_call = {"tool": "list_vms", "parameters": {"provider": "AWS"}}
    result = executor.execute_tool(bad_param_call)
    print(f"   Result -> {result}")

    print("\n=========================================================")
    print("=== Tool Executor Demo Complete ===")
    print("=========================================================")
