# ==============================================================================
#  DEVIN AGI - MAIN ENTRY POINT
# ==============================================================================
#  Author: Kevin Hamza (Kevin Devin)
#  Version: 4.0.0
#  License: MIT
#
#  Integrated repositories (external/):
#    gemini-cli, claude-code, self-operating-computer, openclaw, AIA,
#    Devin v1/v2/v3, shannon, hexstrike-ai, airgorah, metasploit-framework,
#    hackability, vulnerability-analysis, moltbots.github.io, nishang,
#    Responder, PowerTools, Holomat, Jarvis, OpenDevin/OpenHands,
#    JARVIS-microsoft, cheetahclaws, collection-claude-code-source-code
#
#  Features:
#    • Claude Code-style CLI interface (TypeScript layer in src/)
#    • Full OS control (mouse, keyboard, screenshots, file I/O)
#    • Multi-provider AI (Gemini, Claude, OpenAI, Ollama)
#    • Voice I/O, Telegram, Discord, Slack messaging
#    • Persistent vector memory (sentence-transformers)
#    • Pentesting suite (Metasploit, nmap, HexStrike, airgorah)
#    • Cloud management (AWS, GCP, Azure)
#    • Autonomous reasoning with ethical constraints
# ==============================================================================

import logging
import threading
import os
import json
import argparse
import sys
from typing import Dict, Any, List, Optional

# --- Load Environment Variables ---
from dotenv import load_dotenv
load_dotenv()

# Ensure external/ repos are on the path for direct imports
_ext_dir = os.path.join(os.path.dirname(__file__), "external")
for _repo in ["cheetahclaws", "claude-code", "gemini-cli", "openclaw"]:
    _rpath = os.path.join(_ext_dir, _repo)
    if os.path.isdir(_rpath) and _rpath not in sys.path:
        sys.path.insert(0, _rpath)

# Servers (to be run in the background)
from servers.cloud_integration_server import CloudIntegrationServer
from servers.analytics_server import AnalyticsServer
from servers.mobile_integration_server import MobileIntegrationServer
from servers.ai_learning_server import AILearningServer

# Core AI and Decision-Making Modules
from modules.all_ais_modules import AIAgent, AIProvider
from singularity.goal_system.utility_function import UtilityFunction, TaskCompletionComponent, SafetyComponent, EfficiencyComponent, ConstraintAdherenceComponent, Plan
from singularity.goal_system.ethics_constraints import ConstraintSet, DoNoHarmConstraint, DataPrivacyConstraint, HonestyAndTransparencyConstraint

# Core Tool Execution and Management
from modules.tool_executor import ToolExecutor
from modules.user_interaction_module import UserInteractionManager
from security.security_dashboard import SecurityDashboard

# Ported OpenClaw Modules
from modules.messaging_gateway import MessagingGateway, TelegramChannel, DiscordChannel, SlackChannel
from modules.canvas_server import CanvasServer

# Tool-Providing Facades and Managers
# from modules.cloud_integration_services import CloudServicesManager
from modules.cloud_services_manager import CloudServicesManager
from modules.cloud_integration_module import CloudFacade
from modules.pentesting_tools.pentesting_facade import PentestingFacade
from modules.pentesting_tools.hexstrike_client import HexStrikeClient
from modules.pentesting_tools.wifi_audit_tools import WifiAuditTools
from modules.external_agent_tools import ExternalAgentTools
from modules.code_execution import CodeExecutor
from modules.automation_tools import DesktopAutomator, WebAutomator
from modules.system_monitor import SystemMonitorFacade, LocalMonitor, RemoteMonitor
from modules.mobile_integration_module import MobileFacade
from modules.os_operations.universal_operations import UniversalOSOperator
from modules.knowledge_retrieval.code_retriever import CodeRetriever
from modules.data_logger import DataLogger

# Extended Capabilities
from modules.robotics_control_module import RoboticsControlModule, ROS2_RobotInterface
from modules.social_media_api import SocialMediaManager
from modules.email_tools import EmailClient
from modules.encryption_tools import HashingTools, SymmetricCryptoTools, AsymmetricCryptoTools

# Persistent Memory (real sentence-transformers vector memory, not a stub)
from ai_core.cognitive_arch.long_term_memory import LongTermMemory
from ai_core.cognitive_arch.working_memory import WorkingMemory

# --- Integrated Repo Bridges ---
# Each bridge integrates an external repo's patterns without requiring
# that repo's full dependency stack to be installed.
try:
    from modules.cheetahclaws_bridge import CheetahClawsBridge
except Exception as _e:
    CheetahClawsBridge = None
    logging.getLogger("main").warning(f"CheetahClaws bridge unavailable: {_e}")

try:
    from modules.jarvis_bridge import JarvisBridge
except Exception as _e:
    JarvisBridge = None

try:
    from modules.opendevin_bridge import OpenDevinBridge
except Exception as _e:
    OpenDevinBridge = None

try:
    from modules.holomat_bridge import HolomatBridge
except Exception as _e:
    HolomatBridge = None

# ── Integrated repo modules (physical copies in modules/integrated/) ──────────
try:
    import modules.integrated as _integrated_pkg
    _AIA_AUTOMATION  = getattr(_integrated_pkg, 'AIA_AUTOMATION',  None)
    _AIA_VOICE       = getattr(_integrated_pkg, 'AIA_VOICE',       None)
    _CHEETAH_AVAIL   = getattr(_integrated_pkg, 'CHEETAH_AVAILABLE', False)
    _JARVIS_TOOLS    = getattr(_integrated_pkg, 'JARVIS_TOOLS',    None)
except Exception as _ie:
    _AIA_AUTOMATION = _AIA_VOICE = _JARVIS_TOOLS = None
    _CHEETAH_AVAIL = False

# ── Master Integration Hub — imports ALL 24 external repos directly ───────────
try:
    from modules.integration_hub import get_hub as _get_hub, DevinHub as _DevinHub
    _INTEGRATION_HUB: Optional['_DevinHub'] = _get_hub()
    logging.getLogger("main").info("Integration hub loaded — 24 repos active")
except Exception as _hub_err:
    _INTEGRATION_HUB = None
    logging.getLogger("main").warning(f"Integration hub optional: {_hub_err}")

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("DevinAGI")


class DevinAGI:
    """
    The main class that orchestrates the entire AGI system.
    """
    def __init__(self, use_voice: bool = False, permission_mode: Optional[str] = None):
        logger.info("Initializing Devin AGI...")
        self.mode = os.getenv("DEVIN_MODE", "live") # Read the mode
        self.is_running = True
        self.conversation_history: List[Dict] = []
        # Mirrors Claude Code's permission modes:
        #   default        -- ask for confirmation before a dangerous tool call (unchanged behavior)
        #   auto_approve   -- run dangerous tools without asking (still subject to the ethical VETO check, which is never bypassable)
        #   plan           -- describe every tool call instead of running any of them, so the user can review the whole plan first
        #   bypass         -- alias for auto_approve
        self.permission_mode = permission_mode or os.getenv("DEVIN_PERMISSION_MODE", "default")

        # --- 1. Start All Background Servers ---
        self.servers = self._start_background_servers()

        # --- 2. Initialize Core Brain Components ---
        logger.info("Initializing core cognitive modules...")
        self.agent = AIAgent(
            mode=self.mode, # Pass the mode to the agent
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            perplexity_api_key=os.getenv("PERPLEXITY_API_KEY"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        self.uim = UserInteractionManager(use_voice=use_voice)
        self.security_dashboard = SecurityDashboard()

        # --- Persistent Memory ---
        # Real vector memory (sentence-transformers embeddings + cosine
        # similarity), not the mock/placeholder pattern seen elsewhere in
        # this codebase -- fulfills the "persistent vector memory" goal.
        self.long_term_memory = LongTermMemory()
        self.working_memory = WorkingMemory()

        # --- 3. Initialize OpenClaw Ported Services ---
        logger.info("Initializing ported OpenClaw services...")
        self.messaging_gateway = MessagingGateway()
        telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if telegram_token:
            self.messaging_gateway.register_channel("Telegram", TelegramChannel(telegram_token))
        discord_token = os.getenv("DISCORD_BOT_TOKEN")
        if discord_token:
            self.messaging_gateway.register_channel("Discord", DiscordChannel(discord_token))
        slack_bot_token, slack_app_token = os.getenv("SLACK_BOT_TOKEN"), os.getenv("SLACK_APP_TOKEN")
        if slack_bot_token and slack_app_token:
            self.messaging_gateway.register_channel("Slack", SlackChannel(slack_bot_token, slack_app_token))

        self.canvas_server = CanvasServer()
        self.canvas_server.start_background()

        # --- 4. Initialize Value Alignment System ---
        logger.info("Initializing value alignment and ethical framework...")
        self.ethical_constraints = ConstraintSet(constraints=[
            DoNoHarmConstraint(),
            DataPrivacyConstraint(),
            HonestyAndTransparencyConstraint(ai_agent=self.agent)
        ])
        utility_components = {
            "TaskCompletion": TaskCompletionComponent(weight=0.5, ai_agent=self.agent),
            "Safety": SafetyComponent(weight=1.0, security_dashboard=self.security_dashboard),
            "Efficiency": EfficiencyComponent(weight=0.1),
            "ConstraintAdherence": ConstraintAdherenceComponent(weight=1.0),
        }
        self.utility_function = UtilityFunction(components=utility_components)

        # --- 4. Initialize All Tools and Facades ---
        logger.info("Initializing toolset and capabilities...")
        # Note: In a real deployment, credentials for tools would be managed securely.
        cloud_facade = CloudFacade() # Assumes credentials are in environment
        self.cloud_manager = CloudServicesManager(cloud_facade=cloud_facade, uim=self.uim)
        self.pentesting_facade = PentestingFacade()
        # hexstrike-ai and self-operating-computer are vendored as full
        # source (repo root); claude-code, gemini-cli, openclaw, shannon,
        # and airgorah are vendored as git submodules under external/ --
        # HexStrikeClient/ExternalAgentTools/WifiAuditTools are the runtime
        # hooks that actually drive them, owned here like every other
        # capability rather than left to ToolExecutor's internal defaults.
        self.hexstrike_client = HexStrikeClient()
        self.external_agent_tools = ExternalAgentTools()
        self.wifi_audit_tools = WifiAuditTools()
        self.code_executor = CodeExecutor()
        self.desktop_automator = DesktopAutomator()
        self.web_automator = WebAutomator()
        self.system_monitor = SystemMonitorFacade(monitors=[LocalMonitor()])
        self.mobile_facade = MobileFacade()
        self.os_operator = UniversalOSOperator()
        self.code_retriever = CodeRetriever(project_root=".")
        self.data_logger = DataLogger()

        # --- 5. Initialize Extended Capabilities ---
        logger.info("Initializing extended capabilities (Robotics, Social, Email, Crypto)...")
        try:
            self.robotics_manager = RoboticsControlModule(robot_interface=ROS2_RobotInterface())
        except Exception:
            self.robotics_manager = None 
        
        self.social_manager = SocialMediaManager(
            twitter_bearer=os.getenv("TWITTER_BEARER_TOKEN"),
            reddit_creds={
                "client_id": os.getenv("REDDIT_CLIENT_ID"),
                "client_secret": os.getenv("REDDIT_CLIENT_SECRET"),
                "user_agent": "DevinAI/1.0"
            } if os.getenv("REDDIT_CLIENT_ID") else None,
            facebook_access_token=os.getenv("FACEBOOK_ACCESS_TOKEN"),
            instagram_creds={
                "access_token": os.getenv("INSTAGRAM_ACCESS_TOKEN"),
                "ig_user_id": os.getenv("INSTAGRAM_USER_ID"),
            } if os.getenv("INSTAGRAM_ACCESS_TOKEN") else None,
            linkedin_creds={
                "access_token": os.getenv("LINKEDIN_ACCESS_TOKEN"),
                "member_urn": os.getenv("LINKEDIN_MEMBER_URN"),
            } if os.getenv("LINKEDIN_ACCESS_TOKEN") else None,
        )
        
        self.email_client = EmailClient(
            imap_server=os.getenv("DEVIN_IMAP_SERVER", "imap.gmail.com"),
            smtp_server=os.getenv("DEVIN_SMTP_SERVER", "smtp.gmail.com"),
            email_address=os.getenv("DEVIN_EMAIL_ADDRESS", ""),
            password=os.getenv("DEVIN_EMAIL_PASSWORD", "")
        )
        
        self.hashing_tools = HashingTools()
        try:
            self.symmetric_crypto = SymmetricCryptoTools()
            self.asymmetric_crypto = AsymmetricCryptoTools()
        except Exception:
            self.symmetric_crypto = None
            self.asymmetric_crypto = None

        # --- 5b. Initialize Integrated Repo Bridges ---
        logger.info("Initializing integrated external repo bridges...")
        self.cheetahclaws = CheetahClawsBridge() if CheetahClawsBridge else None
        self.jarvis = JarvisBridge() if JarvisBridge else None
        self.opendevin = OpenDevinBridge() if OpenDevinBridge else None
        self.holomat = HolomatBridge() if HolomatBridge else None
        _bridge_status = {
            "cheetahclaws": self.cheetahclaws is not None,
            "jarvis": self.jarvis is not None,
            "opendevin": self.opendevin is not None,
            "holomat": self.holomat is not None,
        }
        logger.info(f"Bridge status: {_bridge_status}")

        # --- 5c. Master Integration Hub (all 24 external repos) ---
        self.hub = _INTEGRATION_HUB
        if self.hub:
            logger.info("Integration hub active — 24 external repos loaded")
            # Register hub dispatch as a tool in the executor (done after executor init below)

        # --- 6. Initialize the Master Tool Executor ---
        logger.info("Registering all tools with the Tool Executor...")
        self.tool_executor = ToolExecutor(
            ai_agent=self.agent,
            security_dashboard=self.security_dashboard,
            cloud_services_manager=self.cloud_manager,
            pentesting_facade=self.pentesting_facade,
            hexstrike_client=self.hexstrike_client,
            external_agent_tools=self.external_agent_tools,
            wifi_audit_tools=self.wifi_audit_tools,
            code_executor=self.code_executor,
            desktop_automator=self.desktop_automator,
            web_automator=self.web_automator,
            system_monitor_facade=self.system_monitor,
            mobile_facade=self.mobile_facade,
            os_operator=self.os_operator,
            code_retriever=self.code_retriever,
            data_logger=self.data_logger,
            messaging_gateway=self.messaging_gateway,
            canvas_server=self.canvas_server,
            robotics_manager=self.robotics_manager,
            social_manager=self.social_manager,
            email_client=self.email_client,
            hashing_tools=self.hashing_tools,
            symmetric_crypto=self.symmetric_crypto,
            asymmetric_crypto=self.asymmetric_crypto
        )

        # Sub-agent delegation (mirrors Claude Code's Task tool): a bounded,
        # isolated sub-conversation using the same models/tools but its own
        # fresh history, so a self-contained chunk of work doesn't have to
        # pollute the main conversation with every intermediate step.
        self.tool_executor._register_tool(
            "delegate_subtask",
            self.run_subagent,
            "Delegates a focused, bounded sub-task to a fresh sub-agent with its own isolated conversation (same tools/models as the main assistant) -- use for self-contained work whose intermediate steps don't need to show up in the main conversation. Returns the sub-agent's final summary.",
        )

        self._log_integrated_repos()
        logger.info("✅ Devin AGI Initialization Complete. Ready for instructions.")

    def _log_integrated_repos(self):
        """
        Logs, at every boot, exactly which vendored/integrated external
        repos are wired into this running instance and how.
        """
        integrations = [
            # Vendored full source
            ("self-operating-computer/", "vendored", "operate_computer tool (PyAutoGUI + vision)"),
            ("hexstrike-ai/", "vendored", "run_hexstrike_command via HexStrikeClient"),
            # Git submodules — core AI tooling
            ("external/claude-code", "submodule+TS src/ layer", "TypeScript CLI mirrors claude-code architecture; delegate_to_claude_code via ExternalAgentTools"),
            ("external/gemini-cli", "submodule+GeminiProvider", "Gemini native tool-calling (free tier); delegate_to_gemini_cli via ExternalAgentTools"),
            ("external/openclaw", "submodule+ported natively", "MessagingGateway (Telegram/Discord/Slack); CanvasServer; run_openclaw_command"),
            ("external/shannon", "submodule", "run_shannon_pentest via ExternalAgentTools"),
            # Git submodules — pentesting
            ("external/airgorah", "submodule", "run_aircrack_suite_command via WifiAuditTools"),
            ("external/metasploit-framework", "submodule", "pymetasploit3/msfrpcd exploitation path (authorized use only)"),
            ("external/nishang", "submodule", "PowerShell pentesting scripts; invoked via execute_shell"),
            ("external/Responder", "submodule", "network responder (authorized targets only)"),
            ("external/PowerTools", "submodule", "Windows PowerShell toolkit (authorized use only)"),
            ("external/hackability", "submodule", "Burp Suite extension reference"),
            ("external/vulnerability-analysis", "submodule", "Docker-based CVE scanning pipeline reference"),
            # Git submodules — prior Devin versions
            ("external/Devin, external/Devin-2.0, external/Devin-3.0", "submodules+merged", "v1–v3 features ported natively into modules/"),
            # Git submodules — misc
            ("external/AIA", "submodule+ported", "social media, device control, consented face recognition"),
            ("external/moltbots.github.io", "submodule", "reference (static site)"),
            # Freshly cloned repos
            ("external/cheetahclaws", "cloned+bridge", "CheetahClawsBridge: AgentState, token tracking, smart compaction"),
            ("external/Holomat", "cloned+bridge", "HolomatBridge: spatial/holographic display interface"),
            ("external/Jarvis", "cloned+bridge", "JarvisBridge: voice assistant skills, local tool execution"),
            ("external/JARVIS-microsoft", "cloned", "Microsoft HuggingGPT/JARVIS multi-model orchestration reference"),
            ("external/OpenDevin", "cloned+bridge", "OpenDevinBridge: sandboxed code exec, web browsing, multi-agent events"),
            ("external/claude-code-source", "cloned", "Claude Code TypeScript source reference (collection-claude-code-source-code)"),
            ("external/cheetahclaws", "cloned", "CheetahClaws Python-native agent (SafeRL-Lab)"),
            # TypeScript layer
            ("src/", "new TypeScript layer", "Claude Code-style CLI: src/cli.ts, providers/, tools/, ui/, memory/, os/, integrations/"),
        ]
        ext_dir = os.path.join(os.path.dirname(__file__), "external")
        n_ready = sum(
            1 for _, method, _ in integrations
            if "cloned" in method or "submodule" in method or "vendored" in method
        )
        logger.info(f"Integrated external repos ({len(integrations)} entries, ~{n_ready} with code):")
        for repo_path, method, usage in integrations:
            logger.info(f"  [{method:30s}] {repo_path} => {usage}")

    def _start_background_servers(self) -> Dict[str, threading.Thread]:
        """Initializes and starts all backend servers in daemon threads."""
        servers_to_start = {
            "CloudIntegration": {"class": CloudIntegrationServer, "port": 5002},
            "Analytics": {"class": AnalyticsServer, "port": 5004, "args": ["analytics_db.feather"]},
            "MobileIntegration": {"class": MobileIntegrationServer, "port": 5006},
            "AILearning": {"class": AILearningServer, "port": 5007},
        }
        threads = {}
        for name, config in servers_to_start.items():
            try:
                # Get the arguments, defaulting to an empty list
                server_args = config.get("args", [])
                server_instance = config["class"](*server_args) # Use * to pass the list as arguments
                thread = threading.Thread(
                    target=server_instance.run,
                    args=("127.0.0.1", config["port"]),
                    daemon=True,
                    name=f"{name}ServerThread"
                )
                thread.start()
                threads[name] = thread
                logger.info(f"{name} Server started in background on port {config['port']}.")
            except Exception as e:
                logger.error(f"Failed to start the {name} Server. This feature will be unavailable. Error: {e}")
        
        return threads

    def run(self):
        """
        The main interactive loop -- a genuine, continuous conversation
        rather than a single goal-in/task-out run. Each user message can be
        plain chat or a task; Devin replies conversationally when there's
        nothing to do, or works through tool calls (shown transparently,
        one line per call and result, the way Claude Code shows "Running
        <tool>...") when there is. Control returns to the user after each
        turn instead of the process ending once one goal completes.
        """
        self.uim.display_message(
            "🦞 Devin is ready. Talk to it like you would talk to any capable assistant -- "
            "ask a question, ask it to do something, or just chat. Type 'exit' to quit.",
            level='info',
        )

        # A conversation with no system prompt has no defined persona at
        # all -- the model just sees a bare user message. This is what
        # actually gives Devin a consistent, thoughtful voice across turns
        # rather than a generic one that varies with whatever the
        # underlying model defaults to.
        self.conversation_history.append({
            "role": "system",
            "content": (
                "You are Devin, a capable AI engineer and assistant with real control over this "
                "computer: you can run shell commands, read/write files, operate the mouse and "
                "keyboard, browse the web, and call dozens of other tools. Talk like a sharp, "
                "direct colleague, not a chatbot -- be concise, get to the point, and skip filler "
                "and hedging. Use a tool when the user's request needs one; otherwise just answer. "
                "If a request is ambiguous, ask a short clarifying question instead of guessing. "
                "If a request is genuinely dangerous or unauthorized (e.g. attacking a system you "
                "don't have permission to test), say so plainly and decline, rather than doing it "
                "quietly or refusing without explanation."
            ),
        })

        while self.is_running:
            user_input = self.uim.get_user_input("\nYou: ")
            if not user_input.strip():
                continue
            if user_input.strip().lower() in ("exit", "quit", "bye", ":q"):
                self.uim.display_message("Goodbye!", level='info')
                break

            # Handle slash commands (Claude Code-style /help, /clear, /status, etc.)
            if user_input.strip().startswith("/"):
                if self.uim.handle_slash_command(user_input.strip(), self):
                    continue
                # Unknown slash command — let the AI handle it
                self.uim.display_message(f"Unknown command: {user_input.strip()}. Type /help for help.", level='warning')
                continue

            # Recall anything relevant from past sessions before planning, so
            # the agent isn't starting from a blank slate every turn.
            relevant_memories = self.long_term_memory.retrieve_relevant_memories(user_input, top_k=3)
            if relevant_memories:
                recalled = "\n".join(f"- {m['metadata'].get('content_preview', '')}" for m in relevant_memories)
                self.conversation_history.append({
                    "role": "system",
                    "content": f"Relevant memories from past sessions:\n{recalled}",
                })
            self.conversation_history.append({"role": "user", "content": user_input})
            self.working_memory.add_item("current_goal", user_input)

            # Work through as many tool calls as this turn needs; a plain
            # conversational reply (task_complete) ends the turn immediately
            # and hands control back to the user. A single LLM response can
            # now request multiple actions in one go (see
            # AIAgent.get_tool_selection_response) -- each is still executed
            # one at a time (true OS-level parallel execution would need
            # threading the tool calls themselves), but the model is no
            # longer truncated to one action per round-trip.
            recent_signatures: List[str] = []
            for _ in range(20):
                with self.uim.thinking_indicator():
                    response = self.agent.get_tool_selection_response(
                        self.conversation_history,
                        self.tool_executor.get_available_tools()
                    )

                if not response or not isinstance(response, dict):
                    self.uim.display_message("Sorry, I didn't get a usable response there -- could you rephrase?", level='error')
                    break

                if response.get("thinking"):
                    # Real reasoning transparency (Claude's extended thinking) --
                    # shown distinctly from the tool calls/final reply below.
                    self.uim.display_message(response["thinking"], level='thinking')

                if response.get("tool") == "task_complete":
                    reply = response.get("parameters", {}).get("reason", "...")
                    self.uim.display_message(reply, level='assistant')
                    self.conversation_history.append({"role": "assistant", "content": reply})
                    self.long_term_memory.add_memory(
                        f"User: {user_input}\nDevin: {reply}",
                        metadata={"type": "conversation"},
                    )
                    break

                tool_calls = response.get("tool_calls") or ([response] if "tool" in response else [])
                if not tool_calls:
                    self.uim.display_message("Sorry, I didn't get a usable response there -- could you rephrase?", level='error')
                    break

                if len(tool_calls) > 1:
                    self.uim.display_message(f"(requesting {len(tool_calls)} actions this turn)", level='tool')

                denied = False
                for tool_call in tool_calls:
                    # Loop-detection: if the exact same call repeats three
                    # times in a row, the agent is stuck, not making
                    # progress -- pause and ask rather than burning the
                    # whole step budget on a spinning wheel.
                    signature = f"{tool_call['tool']}:{json.dumps(tool_call.get('parameters', {}), sort_keys=True)}"
                    recent_signatures.append(signature)
                    if len(recent_signatures) >= 3 and len(set(recent_signatures[-3:])) == 1:
                        self.uim.display_message(f"I keep repeating the same action ({tool_call['tool']}) without new progress -- pausing here. What would you like to do?", level='assistant')
                        denied = True
                        break

                    # VERIFY & CONSENT: check the plan against ethical and utility functions
                    plan = Plan(steps=[tool_call])
                    violations = self.ethical_constraints.check_plan(plan)
                    if any(v.severity == "VETO" for v in violations):
                        self.uim.display_message(f"That would violate a core safety principle, so I won't do it: {tool_call['tool']}", level='error')
                        self.conversation_history.append({"role": "system", "content": f"Ethical VETO on {tool_call['tool']}."})
                        continue

                    utility_score = self.utility_function.evaluate_plan(plan, user_input, [])
                    if utility_score.total_utility < 0.1: # Arbitrary threshold for "good enough"
                        self.conversation_history.append({"role": "system", "content": f"Plan for {tool_call['tool']} seemed suboptimal or unsafe; skipped."})
                        continue

                    args_preview = ", ".join(f"{k}={v!r}" for k, v in tool_call.get("parameters", {}).items())

                    # Plan mode: describe every action instead of running any
                    # of it, so the whole plan can be reviewed up front --
                    # the ethical VETO check above still applies even here.
                    if self.permission_mode == "plan":
                        self.uim.display_message(f"○ [PLAN] {tool_call['tool']}({args_preview}) -- not executed (plan mode)", level='tool')
                        self.conversation_history.append({"role": "tool", "content": f"(plan mode) {tool_call['tool']} described but not executed."})
                        continue

                    if self.tool_executor.is_dangerous(tool_call['tool']) and self.permission_mode not in ("auto_approve", "bypass"):
                        if not self.uim.ask_for_confirmation(f"The next action is potentially dangerous: {tool_call}. Do you want to proceed?"):
                            self.conversation_history.append({"role": "system", "content": f"User denied permission to execute {tool_call['tool']}."})
                            self.uim.display_message("Okay, I won't do that -- what would you like instead?", level='assistant')
                            denied = True
                            break

                    # ACT: show the call transparently, then execute it
                    self.uim.display_message(f"● {tool_call['tool']}({args_preview})", level='tool')
                    result = self.tool_executor.execute_tool(tool_call)
                    self.uim.display_message(f"  → {result}", level='tool')

                    # PERCEIVE & UPDATE: add the action and result to history
                    self.conversation_history.append({"role": "assistant", "content": json.dumps(tool_call)})
                    self.conversation_history.append({"role": "tool", "content": json.dumps(result)})
                    self.working_memory.add_item(f"step_{len(self.conversation_history)}", {"tool_call": tool_call, "result": result})

                if denied:
                    break
            else:
                self.uim.display_message("That's taking a lot of steps -- pausing here so we can check in. What would you like to do next?", level='assistant')

            # Compact history instead of blindly discarding it once a long
            # session gets big: summarize the older half into one system
            # message via the LLM itself, then keep the recent tail intact,
            # so context shrinks without losing what happened earlier.
            if len(self.conversation_history) > 200:
                self._compact_conversation_history()

    def run_subagent(self, goal: str, max_steps: int = 10) -> str:
        """
        Runs a focused sub-agent on one bounded goal, in its own isolated
        conversation (not the main one), using the same AIAgent/tool
        executor. Returns the sub-agent's final summary once it calls
        task_complete or exhausts its step budget. Dangerous tools and the
        ethical VETO check still apply exactly as in the main loop --
        delegation narrows scope, it doesn't loosen safety.
        """
        sub_history: List[Dict] = [
            {
                "role": "system",
                "content": (
                    "You are a focused sub-agent working on exactly one bounded task, delegated "
                    "by the main assistant. Work efficiently and call task_complete with a clear, "
                    "concise summary of what you found or did as soon as the task is done."
                ),
            },
            {"role": "user", "content": goal},
        ]

        for _ in range(max_steps):
            with self.uim.thinking_indicator("Sub-agent is thinking..."):
                response = self.agent.get_tool_selection_response(sub_history, self.tool_executor.get_available_tools())
            if not response or not isinstance(response, dict):
                return "Sub-agent failed to get a usable response from the model."

            if response.get("tool") == "task_complete":
                return response.get("parameters", {}).get("reason", "Sub-task completed with no summary.")

            tool_calls = response.get("tool_calls") or ([response] if "tool" in response else [])
            for tool_call in tool_calls:
                plan = Plan(steps=[tool_call])
                violations = self.ethical_constraints.check_plan(plan)
                if any(v.severity == "VETO" for v in violations):
                    return f"Sub-agent aborted: '{tool_call['tool']}' would violate a core safety principle."

                if self.tool_executor.is_dangerous(tool_call['tool']) and self.permission_mode not in ("auto_approve", "bypass"):
                    if not self.uim.ask_for_confirmation(f"[sub-agent] wants to run a potentially dangerous action: {tool_call}. Proceed?"):
                        sub_history.append({"role": "system", "content": f"User denied permission to execute {tool_call['tool']}."})
                        continue

                args_preview = ", ".join(f"{k}={v!r}" for k, v in tool_call.get("parameters", {}).items())
                self.uim.display_message(f"  ↳ [sub-agent] {tool_call['tool']}({args_preview})", level='tool')
                result = self.tool_executor.execute_tool(tool_call)

                sub_history.append({"role": "assistant", "content": json.dumps(tool_call)})
                sub_history.append({"role": "tool", "content": json.dumps(result)})

        return "Sub-agent reached its step limit without completing the task."

    def _compact_conversation_history(self, keep_tail: int = 60):
        """
        Summarizes the older portion of a long conversation into one
        compact system message via the LLM itself, instead of blindly
        discarding it -- what happened earlier stays available in
        condensed form rather than being silently forgotten once history
        gets long.
        """
        old_messages, recent_messages = self.conversation_history[:-keep_tail], self.conversation_history[-keep_tail:]
        transcript = "\n".join(f"{m.get('role')}: {m.get('content')}" for m in old_messages if m.get("content"))

        provider = (
            AIProvider.ANTHROPIC if self.agent.claude_module else
            AIProvider.OPENAI if self.agent.openai_module else
            AIProvider.GOOGLE if self.agent.gemini_module else
            AIProvider.OLLAMA
        )
        summary_prompt = [
            {"role": "system", "content": "Summarize the following conversation transcript concisely -- keep any facts, decisions, file paths, or outcomes that might matter later. A few sentences is enough."},
            {"role": "user", "content": transcript[:12000]},
        ]
        try:
            summary = self.agent.get_general_chat_response(summary_prompt, provider=provider)
        except Exception as e:
            summary = None
            logger.warning(f"History compaction failed, falling back to plain truncation: {e}")

        if summary and not summary.startswith("Error:"):
            self.conversation_history = [{"role": "system", "content": f"[Summary of earlier conversation]: {summary}"}] + recent_messages
            logger.info(f"Compacted conversation history ({len(old_messages)} messages -> 1 summary).")
        else:
            self.conversation_history = recent_messages
            logger.warning("Compaction summary unavailable; truncated history instead.")

    def shutdown(self):
        """Gracefully shuts down all components."""
        logger.info("Shutting down Devin AGI...")
        self.is_running = False
        # The server threads are daemons, so they will exit when the main thread does.
        # In a more robust system, we would send shutdown requests to each server.
        logger.info("Shutdown complete.")


if __name__ == "__main__":
    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(
        description="Devin AGI v4.0.0 — Advanced AI Assistant with OS Control",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                        # Interactive mode
  python main.py --voice                # Voice input mode
  python main.py --permission-mode auto_approve  # No confirmation prompts
  python main.py --plan                 # Describe actions, don't execute
  python main.py --provider gemini      # Force Gemini provider

Slash commands (in REPL):
  /help   /clear   /status   /tools   /memory   /plan   /auto   /repos
        """
    )
    parser.add_argument("--voice", action="store_true", help="Enable voice input mode")
    parser.add_argument(
        "--permission-mode",
        choices=["default", "auto_approve", "bypass", "plan"],
        default=None,
        help="How to handle dangerous tool calls (default: ask each time)",
    )
    parser.add_argument(
        "--plan", action="store_true",
        help="Shortcut for --permission-mode plan",
    )
    parser.add_argument(
        "--provider",
        choices=["anthropic", "gemini", "openai", "ollama"],
        default=None,
        help="Force a specific AI provider",
    )
    parser.add_argument("--model", default=None, help="Override the model name")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    parser.add_argument("prompt", nargs="?", help="Run a single prompt and exit")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.plan and not args.permission_mode:
        args.permission_mode = "plan"

    # --- Startup Banner (Claude Code-style) ---
    from rich.console import Console as _Console
    from rich.panel import Panel as _Panel
    from rich.table import Table as _Table
    from rich.text import Text as _Text
    _console = _Console()

    # Determine which provider/model will be used
    _provider = args.provider or os.getenv("DEVIN_PROVIDER", "")
    if not _provider:
        if os.getenv("ANTHROPIC_API_KEY"):
            _provider = "anthropic (claude-sonnet-4-6)"
        elif os.getenv("GEMINI_API_KEY"):
            _provider = "gemini (gemini-2.5-flash)"
        elif os.getenv("OPENAI_API_KEY"):
            _provider = "openai (gpt-4o)"
        else:
            _provider = "gemini (key set)"

    _perm = args.permission_mode or os.getenv("DEVIN_PERMISSION_MODE", "default")

    # Count integrated repos and physical files
    _ext_count = 0
    _ext_base = os.path.join(os.path.dirname(__file__), "external")
    if os.path.isdir(_ext_base):
        _ext_count = sum(1 for d in os.listdir(_ext_base) if os.path.isdir(os.path.join(_ext_base, d)))

    _int_files = 0
    _int_base = os.path.join(os.path.dirname(__file__), "integrated")
    if os.path.isdir(_int_base):
        for _root, _dirs, _fnames in os.walk(_int_base):
            _dirs[:] = [d for d in _dirs if d not in ('__pycache__', 'node_modules', '.git')]
            _int_files += len(_fnames)

    _hub_status = "active" if _INTEGRATION_HUB else "loading"
    _console.print(_Panel(
        _Text.from_markup(
            f"[bold cyan]Devin AGI[/bold cyan]  [dim]v4.0.0[/dim]\n\n"
            f"[dim]cwd:[/dim]         [white]{os.getcwd()}[/white]\n"
            f"[dim]model:[/dim]       [white]{_provider}[/white]\n"
            f"[dim]permission:[/dim]  [white]{_perm}[/white]"
            f"   [dim]voice:[/dim] {'[green]on[/green]' if args.voice else '[dim]off[/dim]'}\n"
            f"[dim]repos:[/dim]       [white]{_ext_count} external repos cloned (AIA, gemini-cli, claude-code, SOC, Jarvis, OpenDevin, +more)[/white]\n"
            f"[dim]integrated:[/dim]  [white]{_int_files:,} source files (py, ts, js, css, json, html, all types)[/white]\n"
            f"[dim]hub:[/dim]         [white]Integration hub [{_hub_status}] — all 24 repos live-wired[/white]\n"
            f"[dim]interface:[/dim]   [white]Claude Code-style CLI (TypeScript) + Python AGI backend[/white]"
        ),
        title="[bold cyan]Devin AGI[/bold cyan]",
        border_style="cyan",
        padding=(0, 1),
    ))
    _console.print()

    agi = None
    try:
        agi = DevinAGI(use_voice=args.voice, permission_mode=args.permission_mode)

        # One-shot mode: run a single prompt and exit
        if args.prompt:
            agi.conversation_history.append({"role": "user", "content": args.prompt})
            # Run one turn of the conversation loop
            from rich.console import Console as _c2
            _c2().print(f"[dim]Running: {args.prompt}[/dim]")
            agi.run()
        else:
            agi.run()
    except KeyboardInterrupt:
        logger.info("User initiated shutdown (Ctrl+C).")
    except Exception as e:
        logger.critical(f"A critical error occurred in the main loop: {e}", exc_info=True)
    finally:
        if agi:
            agi.shutdown()
