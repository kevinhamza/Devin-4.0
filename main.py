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
from modules.messaging_gateway import MessagingGateway, TelegramChannel
from modules.canvas_server import CanvasServer

# Tool-Providing Facades and Managers
# from modules.cloud_integration_services import CloudServicesManager
from modules.cloud_services_manager import CloudServicesManager
from modules.cloud_integration_module import CloudFacade
from modules.pentesting_tools.pentesting_facade import PentestingFacade
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
            } if os.getenv("REDDIT_CLIENT_ID") else None
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

        logger.info("✅ Devin AGI Initialization Complete. Ready for instructions.")

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
        """The main operational loop of the AGI."""
        goal = self.uim.get_user_input("\nPlease state your high-level goal: ")
        self.conversation_history.append({"role": "user", "content": f"My goal is: {goal}"})

        # Recall anything relevant from past sessions before planning, so the
        # agent isn't starting from a blank slate every run.
        relevant_memories = self.long_term_memory.retrieve_relevant_memories(goal, top_k=3)
        if relevant_memories:
            recalled = "\n".join(f"- {m['metadata'].get('content_preview', '')}" for m in relevant_memories)
            self.conversation_history.append({
                "role": "system",
                "content": f"Relevant memories from past sessions:\n{recalled}",
            })
        self.working_memory.add_item("current_goal", goal)

        while self.is_running:
            # 1. THINK: Agent decides the next step
            tool_call = self.agent.get_tool_selection_response(
                self.conversation_history,
                self.tool_executor.get_available_tools()
            )

            if not tool_call or not isinstance(tool_call, dict) or "tool" not in tool_call:
                logger.info("Agent decided no further action is needed or failed to select a tool. Concluding task.")
                break
            if tool_call.get("tool") == "task_complete":
                reason = tool_call.get("parameters", {}).get("reason", "No specific reason provided.")
                self.uim.display_message(f"Agent has concluded the task. Reason: {reason}", level='success')
                self.long_term_memory.add_memory(
                    f"Goal: {goal}\nOutcome: completed. {reason}",
                    metadata={"type": "task_history", "outcome": "completed"},
                )
                break

            # 2. VERIFY & CONSENT: Check the plan against ethical and utility functions
            plan = Plan(steps=[tool_call])
            violations = self.ethical_constraints.check_plan(plan)
            if any(v.severity == "VETO" for v in violations):
                logger.error(f"Ethical VETO: Plan '{tool_call}' violates a core principle. Aborting.")
                break
                
            utility_score = self.utility_function.evaluate_plan(plan, goal, [])
            if utility_score.total_utility < 0.1: # Arbitrary threshold for "good enough"
                 logger.warning(f"Plan '{tool_call}' has low utility ({utility_score.total_utility:.2f}). Asking AI to reconsider.")
                 self.conversation_history.append({"role": "system", "content": "That plan seems suboptimal or unsafe. Please propose a different approach."})
                 continue
            
            if self.tool_executor.is_dangerous(tool_call['tool']):
                if not self.uim.ask_for_confirmation(f"The next action is potentially dangerous: {tool_call}. Do you want to proceed?"):
                    logger.warning("Action aborted by user consent.")
                    self.conversation_history.append({"role": "system", "content": f"User denied permission to execute {tool_call['tool']}."})
                    continue

            # 3. ACT: Execute the approved plan
            result = self.tool_executor.execute_tool(tool_call)
            
            # 4. PERCEIVE & UPDATE: Add the action and result to history
            self.conversation_history.append({"role": "assistant", "content": json.dumps(tool_call)})
            self.conversation_history.append({"role": "tool", "content": json.dumps(result)})
            self.working_memory.add_item(f"step_{len(self.conversation_history)}", {"tool_call": tool_call, "result": result})

            # Check for completion (simplified)
            if "complete" in str(result).lower() or "finished" in str(result).lower():
                 logger.info("Agent reported task completion.")
                 self.long_term_memory.add_memory(
                     f"Goal: {goal}\nOutcome: completed via tool '{tool_call['tool']}'.",
                     metadata={"type": "task_history", "outcome": "completed"},
                 )
                 break

            if len(self.conversation_history) > 20: # Safety break
                logger.warning("Conversation limit reached. Ending session.")
                self.long_term_memory.add_memory(
                    f"Goal: {goal}\nOutcome: did not complete within the conversation limit.",
                    metadata={"type": "task_history", "outcome": "incomplete"},
                )
                break

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
