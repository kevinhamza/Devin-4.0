# Devin/modules/user_interaction_module.py
# Purpose: The central module for handling all text and voice-based interaction
#          between the AGI and the human operator.
#
# Rendering uses `rich` (already a transitive dependency, now made explicit
# in requirements.txt) instead of hand-rolled ANSI escape codes, so the
# terminal experience -- markdown-rendered replies, a styled prompt, a
# spinner while the model is thinking, dim/understated tool-call lines --
# reads closer to Claude Code's CLI rather than a wall of [INFO]/[SUCCESS]
# log-style lines.

import contextlib
import logging
import sys
import os
from typing import Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

# Try to import speech recognition
try:
    from modules.multimedia_tools.speech_recognition import LiveSpeechRecognizer
    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False

# Configure basic logging
logger = logging.getLogger("UserInteractionManager")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)
logger.propagate = False

console = Console()

# --- ANSI Color Codes for Formatted Output ---
# Kept for any code that still references Colors directly; display_message
# itself now renders through `console` below.
class Colors:
    """Container for ANSI color codes."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class UserInteractionManager:
    """
    Manages all console I/O, providing a clear and secure interface
    for the user to interact with the AGI.
    """
    def __init__(self, use_voice: bool = False):
        self.use_voice = use_voice
        self.recognizer: Optional[LiveSpeechRecognizer] = None
        if self.use_voice:
            if SPEECH_AVAILABLE:
                try:
                    self.recognizer = LiveSpeechRecognizer()
                    logger.info("Voice input enabled.")
                except Exception as e:
                    logger.error(f"Failed to initialize voice recognizer: {e}")
                    self.use_voice = False
            else:
                logger.warning("Speech recognition dependencies not found. Falling back to text.")
                self.use_voice = False

    def get_user_input(self, prompt: str) -> str:
        """
        Prompts the user for general input (text or voice).
        """
        if self.use_voice and self.recognizer:
            console.print(f"[bold cyan]🎙  {prompt.strip()}[/bold cyan]")
            console.print("[dim]Listening... (Press Ctrl+C to switch to text)[/dim]")
            try:
                text = self.recognizer.listen_and_transcribe(engine='google')
                if text:
                    console.print(f"[green]You said:[/green] {text}")
                    return text.strip()
                else:
                    console.print("[yellow]No speech detected. Falling back to text input.[/yellow]")
            except KeyboardInterrupt:
                console.print("\n[yellow]Voice input interrupted. Switching to text for this prompt.[/yellow]")
            except Exception as e:
                logger.error(f"Error during voice input: {e}")

        try:
            # A bare "❯" prompt, the same understated style Claude Code's
            # own input line uses. Uses console.print + input() rather than
            # rich's Prompt.ask, which always appends its own ": " suffix --
            # main.py's callers already pass a trailing "label: " string
            # (a leftover from the old [PROMPT] style), so Prompt.ask would
            # double it up into "label: :".
            label = prompt.strip()
            console.print(f"[bold cyan]❯[/bold cyan] {label}" if label else "[bold cyan]❯[/bold cyan]", end=" ")
            return input().strip()
        except KeyboardInterrupt:
            logger.warning("\nUser interrupted input. Returning empty string.")
            return ""
        except EOFError:
            return "exit"

    def ask_for_confirmation(self, prompt: str, is_dangerous: bool = False) -> bool:
        """
        Asks the user a yes/no question and returns a boolean.
        """
        try:
            if is_dangerous:
                console.print(Panel(
                    prompt,
                    title="[bold red]⚠ Dangerous action requires confirmation[/bold red]",
                    border_style="red",
                ))
                response = Prompt.ask("[bold red]Are you absolutely sure you want to proceed?[/bold red] (yes/no)").lower().strip()
            else:
                response = Prompt.ask(f"[yellow]{prompt}[/yellow] (y/n)").lower().strip()
            return response in ("y", "yes")
        except KeyboardInterrupt:
            logger.warning("\nUser interrupted confirmation. Defaulting to NO.")
            return False
        except EOFError:
            return False

    def display_message(self, message: str, level: str = 'info'):
        """Displays a formatted message to the user."""
        if level == 'info':
            console.print(f"[blue]{message}[/blue]")
        elif level == 'success':
            console.print(f"[green]✓ {message}[/green]")
        elif level == 'warning':
            console.print(f"[yellow]⚠ {message}[/yellow]")
        elif level == 'error':
            console.print(f"[red]✗ {message}[/red]")
        elif level == 'tool':
            # Dim, understated styling for a tool call/result shown
            # transparently as it happens -- the same visual role Claude
            # Code's own tool-call lines play: seen, but not shouting for
            # attention the way the final reply should.
            console.print(f"[dim cyan]{message}[/dim cyan]")
        elif level == 'thinking':
            console.print(f"[dim italic]∴ {message}[/dim italic]")
        elif level == 'assistant':
            # Render as markdown -- bold, code spans, lists in a reply
            # actually render instead of showing literal ** and backticks,
            # the same as Claude Code rendering its own responses.
            # Markdown(None) raises TypeError -- caught live when a
            # failed provider call propagated a None reply all the way
            # here, so guard against it rather than crashing the session.
            console.print("[bold]Devin:[/bold]", end=" ")
            console.print(Markdown(message) if message else "[dim](no response)[/dim]")
        else:
            console.print(message)

    @contextlib.contextmanager
    def thinking_indicator(self, message: str = "Devin is thinking..."):
        """
        A spinner shown while waiting on a model response, the same role
        Claude Code's own transient status line plays. Usage:
            with self.uim.thinking_indicator():
                response = self.agent.get_tool_selection_response(...)
        """
        with console.status(f"[cyan]{message}[/cyan]", spinner="dots"):
            yield

    def handle_slash_command(self, command: str, agi_instance) -> bool:
        """
        Handle Claude Code-style slash commands (/help, /clear, /status, etc.)
        Returns True if the command was handled, False otherwise.
        """
        parts = command.strip().split(None, 1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if cmd == "/help":
            help_text = """
[bold cyan]Devin AGI — Slash Commands[/bold cyan]

[bold]Conversation[/bold]
  /help           Show this help
  /clear          Clear conversation history
  /compact        Summarize old history to save context
  /history [n]    Show last n messages (default: 10)

[bold]Status & Config[/bold]
  /status         Show session and system status
  /tools          List all available tools
  /repos          List integrated external repositories
  /config         Show configuration
  /cost           Show token usage for this session

[bold]Modes[/bold]
  /plan           Describe actions without executing (safe review)
  /auto           Auto-approve all tools (no confirmation)
  /default        Back to default mode (confirm dangerous tools)
  /voice          Toggle voice input

[bold]Navigation[/bold]
  /cd <path>      Change working directory
  /screenshot     Take a screenshot

[bold]Memory[/bold]
  /memory [query] Show or search memories

[bold]Other[/bold]
  exit / quit     Exit Devin
"""
            console.print(help_text)
            return True

        elif cmd == "/clear":
            if hasattr(agi_instance, 'conversation_history'):
                agi_instance.conversation_history.clear()
            console.print("[green]✓ Conversation history cleared.[/green]")
            return True

        elif cmd == "/status":
            import psutil, platform
            cpu = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory()
            from rich.table import Table
            t = Table(show_header=False, box=None, padding=(0, 1))
            t.add_column(style="dim")
            t.add_column()
            t.add_row("OS", platform.platform())
            t.add_row("CPU", f"{cpu:.1f}%")
            t.add_row("Memory", f"{mem.percent:.1f}% ({mem.used // 1024**2}MB / {mem.total // 1024**2}MB)")
            t.add_row("Provider", str(getattr(agi_instance, 'agent', {.__class__.__name__ if hasattr(getattr(agi_instance, 'agent', None), '__class__') else 'N/A'})))
            if hasattr(agi_instance, 'conversation_history'):
                t.add_row("Messages", str(len(agi_instance.conversation_history)))
            t.add_row("Permission", str(getattr(agi_instance, 'permission_mode', 'default')))
            console.print(Panel(t, title="[bold cyan]Devin Status[/bold cyan]", border_style="cyan"))
            return True

        elif cmd == "/tools":
            if hasattr(agi_instance, 'tool_executor'):
                tools = agi_instance.tool_executor.get_available_tools()
                console.print(f"[bold]Available tools ({len(tools)}):[/bold]")
                for tool in tools:
                    name = tool.get('name', '')
                    desc = tool.get('description', '')[:60]
                    console.print(f"  [cyan]{name:<30}[/cyan] [dim]{desc}[/dim]")
            return True

        elif cmd == "/repos":
            import os as _os
            ext_dir = _os.path.join(_os.path.dirname(_os.path.dirname(__file__)), "external")
            if _os.path.isdir(ext_dir):
                repos = [d for d in _os.listdir(ext_dir) if _os.path.isdir(_os.path.join(ext_dir, d))]
                console.print(f"[bold]Integrated repos ({len(repos)}):[/bold]")
                for r in sorted(repos):
                    contents = _os.listdir(_os.path.join(ext_dir, r))
                    status = "[green]ready[/green]" if len(contents) > 1 else "[yellow]empty[/yellow]"
                    console.print(f"  [cyan]{r:<30}[/cyan] {status}")
            return True

        elif cmd == "/compact":
            if hasattr(agi_instance, '_compact_conversation_history'):
                agi_instance._compact_conversation_history(keep_tail=40)
                console.print("[green]✓ History compacted.[/green]")
            return True

        elif cmd == "/plan":
            if hasattr(agi_instance, 'permission_mode'):
                agi_instance.permission_mode = 'plan'
            console.print("[green]✓ Plan mode: actions will be described, not executed.[/green]")
            return True

        elif cmd == "/auto":
            if hasattr(agi_instance, 'permission_mode'):
                agi_instance.permission_mode = 'auto_approve'
            console.print("[yellow]⚠ Auto-approve mode: dangerous tools run without confirmation.[/yellow]")
            return True

        elif cmd == "/default":
            if hasattr(agi_instance, 'permission_mode'):
                agi_instance.permission_mode = 'default'
            console.print("[green]✓ Default mode restored.[/green]")
            return True

        elif cmd == "/memory":
            if hasattr(agi_instance, 'long_term_memory') and agi_instance.long_term_memory:
                ltm = agi_instance.long_term_memory
                if args.strip():
                    results = ltm.retrieve_relevant_memories(args.strip(), top_k=10)
                    console.print(f"[bold]Memory search results for '{args.strip()}':[/bold]")
                    for r in results:
                        preview = r.get('metadata', {}).get('content_preview', str(r))[:100]
                        console.print(f"  [dim]•[/dim] {preview}")
                else:
                    console.print("[bold]Recent memories:[/bold]")
                    recent = ltm.retrieve_relevant_memories("", top_k=10)
                    for r in (recent or []):
                        preview = r.get('metadata', {}).get('content_preview', str(r))[:100]
                        console.print(f"  [dim]•[/dim] {preview}")
            return True

        elif cmd == "/cd":
            try:
                import os as _os
                _os.chdir(args.strip() or _os.path.expanduser("~"))
                console.print(f"[green]✓ Changed to {_os.getcwd()}[/green]")
            except Exception as e:
                console.print(f"[red]✗ {e}[/red]")
            return True

        elif cmd == "/screenshot":
            import os as _os, tempfile
            outpath = _os.path.join(tempfile.gettempdir(), f"devin_ss_{int(__import__('time').time())}.png")
            import subprocess
            try:
                subprocess.run(["python3", "-c", f"import pyautogui; pyautogui.screenshot('{outpath}')"], timeout=10)
                console.print(f"[green]✓ Screenshot: {outpath}[/green]")
            except Exception as e:
                console.print(f"[red]✗ Screenshot failed: {e}[/red]")
            return True

        elif cmd == "/voice":
            self.use_voice = not self.use_voice
            console.print(f"[green]✓ Voice input {'enabled' if self.use_voice else 'disabled'}.[/green]")
            return True

        return False
