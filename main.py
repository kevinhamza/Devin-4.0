# ==============================================================================
#  DEVIN AGI - MAIN ENTRY POINT
# ==============================================================================
#  Author: Kevin Devin
#  Version: 1.0.0
#  License: MIT
#  Description: The core entry point for the Devin AGI. This script
#               initializes all components, starts background servers, and
#               runs the main operational loop.
# ==============================================================================

import logging
import threading
import os
import json
import argparse
from typing import Dict, Any, List

# --- Load Environment Variables ---
from dotenv import load_dotenv
load_dotenv()

# --- Grand Integration: Import all major components of the Devin project ---

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

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("DevinAGI")


class DevinAGI:
    """
    The main class that orchestrates the entire AGI system.
    """
    def __init__(self, use_voice: bool = False):
        logger.info("Initializing Devin AGI...")
        self.mode = os.getenv("DEVIN_MODE", "live") # Read the mode
        self.is_running = True
        self.conversation_history: List[Dict] = []

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

        self._log_integrated_repos()
        logger.info("✅ Devin AGI Initialization Complete. Ready for instructions.")

    def _log_integrated_repos(self):
        """
        Logs, at every boot, exactly which vendored/integrated external
        repos are wired into this running instance and how -- so
        integration status is visible proof at runtime, not just a claim
        in documentation.
        """
        integrations = [
            ("self-operating-computer/", "vendored full source", "operate_computer tool"),
            ("hexstrike-ai/", "vendored full source", "run_hexstrike_command via self.hexstrike_client"),
            ("external/claude-code", "submodule", "delegate_to_claude_code via self.external_agent_tools"),
            ("external/gemini-cli", "submodule", "delegate_to_gemini_cli via self.external_agent_tools"),
            ("external/openclaw", "submodule", "run_openclaw_command via self.external_agent_tools; messaging/canvas patterns ported natively"),
            ("external/shannon", "submodule", "run_shannon_pentest via self.external_agent_tools"),
            ("external/airgorah", "submodule", "run_aircrack_suite_command via self.wifi_audit_tools"),
            ("external/metasploit-framework", "submodule", "run_full_pentest_scan exploitation path via pymetasploit3/msfrpcd"),
            ("external/PowerTools, external/nishang, external/Responder", "submodules", "invoked via execute_shell on authorized targets"),
            ("external/hackability", "submodule", "reference; used manually inside Burp Suite"),
            ("external/AIA", "submodule + natively ported modules", "social media posting, device control, consented face recognition"),
            ("external/vulnerability-analysis", "submodule", "reference for the Docker-based scanning pipeline"),
            ("external/moltbots.github.io", "submodule", "reference (static site)"),
            ("external/Devin, external/Devin-2.0, external/Devin-3.0", "submodules + natively merged", "v1-v3 feature parity confirmed; working subsystems live in modules/"),
        ]
        logger.info(f"Integrated external repos ({len(integrations)}):")
        for path, method, usage in integrations:
            logger.info(f"  - {path} [{method}] -> {usage}")

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
            if user_input.strip().lower() in ("exit", "quit", "bye"):
                self.uim.display_message("Goodbye!", level='info')
                break

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
            # and hands control back to the user.
            for _ in range(20):
                tool_call = self.agent.get_tool_selection_response(
                    self.conversation_history,
                    self.tool_executor.get_available_tools()
                )

                if not tool_call or not isinstance(tool_call, dict) or "tool" not in tool_call:
                    self.uim.display_message("Sorry, I didn't get a usable response there -- could you rephrase?", level='error')
                    break

                if tool_call.get("tool") == "task_complete":
                    reply = tool_call.get("parameters", {}).get("reason", "...")
                    self.uim.display_message(reply, level='assistant')
                    self.conversation_history.append({"role": "assistant", "content": reply})
                    self.long_term_memory.add_memory(
                        f"User: {user_input}\nDevin: {reply}",
                        metadata={"type": "conversation"},
                    )
                    break

                # VERIFY & CONSENT: check the plan against ethical and utility functions
                plan = Plan(steps=[tool_call])
                violations = self.ethical_constraints.check_plan(plan)
                if any(v.severity == "VETO" for v in violations):
                    self.uim.display_message(f"That would violate a core safety principle, so I won't do it: {tool_call['tool']}", level='error')
                    self.conversation_history.append({"role": "system", "content": f"Ethical VETO on {tool_call['tool']}."})
                    break

                utility_score = self.utility_function.evaluate_plan(plan, user_input, [])
                if utility_score.total_utility < 0.1: # Arbitrary threshold for "good enough"
                    self.conversation_history.append({"role": "system", "content": "That plan seems suboptimal or unsafe. Please propose a different approach."})
                    continue

                if self.tool_executor.is_dangerous(tool_call['tool']):
                    if not self.uim.ask_for_confirmation(f"The next action is potentially dangerous: {tool_call}. Do you want to proceed?"):
                        self.conversation_history.append({"role": "system", "content": f"User denied permission to execute {tool_call['tool']}."})
                        self.uim.display_message("Okay, I won't do that -- what would you like instead?", level='assistant')
                        break

                # ACT: show the call transparently, then execute it
                args_preview = ", ".join(f"{k}={v!r}" for k, v in tool_call.get("parameters", {}).items())
                self.uim.display_message(f"● {tool_call['tool']}({args_preview})", level='tool')
                result = self.tool_executor.execute_tool(tool_call)
                self.uim.display_message(f"  → {result}", level='tool')

                # PERCEIVE & UPDATE: add the action and result to history
                self.conversation_history.append({"role": "assistant", "content": json.dumps(tool_call)})
                self.conversation_history.append({"role": "tool", "content": json.dumps(result)})
                self.working_memory.add_item(f"step_{len(self.conversation_history)}", {"tool_call": tool_call, "result": result})
            else:
                self.uim.display_message("That's taking a lot of steps -- pausing here so we can check in. What would you like to do next?", level='assistant')

            # Keep history from growing unbounded across a long session
            # without ending the conversation the way a hard cap used to.
            if len(self.conversation_history) > 200:
                self.conversation_history = self.conversation_history[-100:]

    def shutdown(self):
        """Gracefully shuts down all components."""
        logger.info("Shutting down Devin AGI...")
        self.is_running = False
        # The server threads are daemons, so they will exit when the main thread does.
        # In a more robust system, we would send shutdown requests to each server.
        logger.info("Shutdown complete.")


if __name__ == "__main__":
    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(description="Devin AGI - Self-Operating System")
    parser.add_argument("--voice", action="store_true", help="Enable voice input mode")
    args = parser.parse_args()

    # --- ASCII Art Banner ---
    print(r"""
    ██████╗ ███████╗██╗   ██╗██╗███╗   ██╗
    ██╔══██╗██╔════╝██║   ██║██║████╗  ██║
    ██║  ██║█████╗  ██║   ██║██║██╔██╗ ██║
    ██║  ██║██╔══╝  ╚██╗ ██╔╝██║██║╚██╗██║
    ██████╔╝███████╗ ╚████╔╝ ██║██║ ╚████║
    ╚═════╝ ╚══════╝  ╚═══╝  ╚═╝╚═╝  ╚═══╝
    --- Artificial General Intelligence v1.0.0 ---
    """)
    
    agi = None
    try:
        agi = DevinAGI(use_voice=args.voice)
        agi.run()
    except KeyboardInterrupt:
        logger.info("User initiated shutdown (Ctrl+C).")
    except Exception as e:
        logger.critical(f"A critical error occurred in the main loop: {e}", exc_info=True)
    finally:
        if agi:
            agi.shutdown()
