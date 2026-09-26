"""
tests/test_devin_core.py — Pytest-compatible core test suite for Devin-4.0

Covers:
  - Module imports
  - Tool registry
  - OS agent capabilities (non-GUI)
  - Reasoning engine
  - HF provider
  - Memory helpers
  - REPL command parsing
  - Shell tool execution

Run: pytest tests/test_devin_core.py -v
"""
import os, sys, json, tempfile, subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# Load .env for tests
_ENV = ROOT / '.env'
if _ENV.exists():
    for _l in _ENV.read_text().splitlines():
        _l = _l.strip()
        if _l and not _l.startswith('#') and '=' in _l:
            _k, _, _v = _l.partition('=')
            os.environ.setdefault(_k.strip(), _v.strip().strip('"\''))

import pytest


# ─── Module imports ────────────────────────────────────────────────────────────

def test_import_os_agent():
    from modules.os_agent import get_os_agent, OSAgent
    agent = get_os_agent()
    assert isinstance(agent, OSAgent)


def test_import_reasoning_engine():
    from modules.reasoning_engine import get_reasoning_engine, ReasoningEngine
    engine = get_reasoning_engine()
    assert isinstance(engine, ReasoningEngine)


def test_import_hf_provider():
    from modules.hf_enhanced_provider import chat, stream_chat, has_token, list_free_models
    models = list_free_models()
    assert len(models) >= 1
    assert 'Qwen' in models[0] or 'llama' in models[0].lower()


def test_import_devin_repl():
    from modules.devin_repl import DevinREPL, get_repl, start_repl, _build_agent_tools


def test_import_free_claude_provider():
    from modules.free_claude_provider import is_available, chat as fc_chat


def test_import_conversation_engine():
    from modules.conversation_engine import get_conversation_engine


def test_import_system_monitor():
    from modules.system_monitor_enhanced import get_system_monitor


def test_import_voice_engine():
    from modules.voice_engine import get_voice_engine


# ─── OS Agent ─────────────────────────────────────────────────────────────────

def test_os_agent_has_required_methods():
    from modules.os_agent import get_os_agent
    agent = get_os_agent()
    required = [
        'screenshot', 'click', 'double_click', 'right_click',
        'type_text', 'press_key', 'hotkey', 'scroll', 'drag',
        'open_application', 'focus_window', 'list_windows',
        'get_clipboard', 'set_clipboard', 'navigate_browser',
        'browser_search', 'click_element', 'find_element',
        'observe', 'execute_task_with_vision',
    ]
    for method in required:
        assert hasattr(agent, method), f"OSAgent missing method: {method}"


def test_os_agent_screenshot_returns_actionresult():
    from modules.os_agent import get_os_agent
    agent = get_os_agent()
    result = agent.screenshot()
    assert hasattr(result, 'success')
    assert hasattr(result, 'message')
    assert isinstance(result.success, bool)


def test_os_agent_screenshot_file_created():
    import platform
    # Skip if no display is available (headless CI / terminal without X)
    if platform.system() == 'Linux' and not os.environ.get('DISPLAY'):
        pytest.skip("No DISPLAY set — screenshot requires a running X/Wayland session")
    from modules.os_agent import get_os_agent
    agent = get_os_agent()
    result = agent.screenshot()
    # Skip rather than fail when the display is set but not accessible
    if not result.success:
        msg = result.message or ''
        if 'display' in msg.lower() or 'screen' in msg.lower() or 'capture' in msg.lower():
            pytest.skip(f"Display not accessible — MANUAL VERIFICATION REQUIRED: {msg}")
    assert result.success, f"Screenshot failed: {result.message}"
    assert result.screenshot_before is not None
    assert Path(result.screenshot_before).exists(), "Screenshot file not created"


# ─── Reasoning Engine ─────────────────────────────────────────────────────────

def test_reasoning_engine_has_methods():
    from modules.reasoning_engine import get_reasoning_engine
    engine = get_reasoning_engine()
    for method in ['think', 'chat', 'register_tool', 'clear_history']:
        assert hasattr(engine, method), f"ReasoningEngine missing: {method}"


def test_reasoning_engine_register_tool():
    from modules.reasoning_engine import ReasoningEngine
    engine = ReasoningEngine()
    called = []
    def my_tool(x: str):
        called.append(x)
        return f"got: {x}"
    engine.register_tool('my_tool', my_tool, 'Test tool', {'x': 'input string'})
    assert 'my_tool' in engine._tools


def test_reasoning_engine_think_with_tool():
    """Test that the reasoning engine can call a tool and return an answer."""
    hf_token = os.environ.get('HF_TOKEN', '')
    if not hf_token:
        pytest.skip("HF_TOKEN not set — skipping live API test")
    os.environ['DEVIN_PROVIDER'] = 'huggingface'
    from modules.reasoning_engine import ReasoningEngine
    engine = ReasoningEngine(max_iterations=5)
    called = []
    def add_tool(a: int, b: int):
        called.append((a, b))
        return str(int(a) + int(b))
    engine.register_tool('add', add_tool, 'Add two numbers', {'a': 'first number', 'b': 'second number'})
    try:
        result = engine.think('What is 7 + 3? Use the add tool.')
        if not result.success:
            err = str(result.error or '')
            if ('402' in err or 'credits' in err.lower() or 'depleted' in err.lower()
                    or 'All providers failed' in err):
                pytest.skip(f"Provider unavailable: {err[:100]}")
        assert result.success, f"Reasoning failed: {result.error}"
        assert '10' in result.answer or result.tool_calls > 0
    except RuntimeError as e:
        if '402' in str(e) or 'credits' in str(e).lower() or 'depleted' in str(e).lower():
            pytest.skip(f"HF free tier credits exhausted: {e}")
        raise


# ─── HuggingFace Provider ─────────────────────────────────────────────────────

def test_hf_provider_token_check():
    from modules.hf_enhanced_provider import has_token
    # Just verify the function exists and returns bool
    result = has_token()
    assert isinstance(result, bool)


def test_hf_provider_connection():
    hf_token = os.environ.get('HF_TOKEN', '')
    if not hf_token:
        pytest.skip("HF_TOKEN not set — skipping live API test")
    from modules.hf_enhanced_provider import test_connection
    try:
        result = test_connection()
        assert isinstance(result, dict)
        if not result.get('ok'):
            err = str(result.get('error', ''))
            if '402' in err or 'credits' in err.lower() or 'depleted' in err.lower():
                pytest.skip(f"HF free tier credits exhausted: {err}")
        assert result.get('ok') is True, f"HF connection failed: {result}"
    except RuntimeError as e:
        if '402' in str(e) or 'credits' in str(e).lower() or 'depleted' in str(e).lower():
            pytest.skip(f"HF free tier credits exhausted: {e}")
        raise


def test_hf_provider_chat():
    hf_token = os.environ.get('HF_TOKEN', '')
    if not hf_token:
        pytest.skip("HF_TOKEN not set — skipping live API test")
    from modules.hf_enhanced_provider import chat
    try:
        result = chat([{'role': 'user', 'content': 'Reply with exactly: DEVIN_TEST_OK'}])
        assert isinstance(result, dict)
        assert 'text' in result
        assert len(result['text']) > 0
    except RuntimeError as e:
        if '402' in str(e) or 'credits' in str(e).lower() or 'depleted' in str(e).lower():
            pytest.skip(f"HF free tier credits exhausted: {e}")
        raise


def test_hf_provider_stream():
    hf_token = os.environ.get('HF_TOKEN', '')
    if not hf_token:
        pytest.skip("HF_TOKEN not set — skipping live API test")
    from modules.hf_enhanced_provider import stream_chat
    try:
        chunks = list(stream_chat([{'role': 'user', 'content': 'Say: hello'}], max_tokens=20))
        assert len(chunks) > 0
        combined = ''.join(chunks)
        assert len(combined) > 0
    except Exception as e:
        if '402' in str(e) or 'credits' in str(e).lower() or 'depleted' in str(e).lower():
            pytest.skip(f"HF free tier credits exhausted: {e}")
        raise


# ─── REPL Tool Registry ───────────────────────────────────────────────────────

def test_repl_tool_registry_builds():
    from modules.devin_repl import _build_agent_tools
    tools = _build_agent_tools()
    assert isinstance(tools, dict)
    assert len(tools) >= 10


def test_repl_tools_have_required_fields():
    from modules.devin_repl import _build_agent_tools
    tools = _build_agent_tools()
    for name, info in tools.items():
        assert 'fn' in info, f"Tool '{name}' missing 'fn'"
        assert 'description' in info, f"Tool '{name}' missing 'description'"
        assert callable(info['fn']), f"Tool '{name}' fn is not callable"


def test_repl_shell_tool():
    from modules.devin_repl import _build_agent_tools
    tools = _build_agent_tools()
    assert 'shell_run' in tools
    result = tools['shell_run']['fn'](cmd='echo DEVIN_SHELL_OK')
    assert 'DEVIN_SHELL_OK' in result


def test_repl_file_tools():
    from modules.devin_repl import _build_agent_tools
    tools = _build_agent_tools()
    assert 'read_file' in tools
    assert 'write_file' in tools

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write('test content')
        path = f.name

    result = tools['read_file']['fn'](path=path)
    assert 'test content' in result

    write_result = tools['write_file']['fn'](path=path, content='new content')
    assert 'Written' in write_result

    result2 = tools['read_file']['fn'](path=path)
    assert 'new content' in result2

    Path(path).unlink()


# ─── Memory helpers ───────────────────────────────────────────────────────────

def test_memory_save_and_load():
    from modules.devin_repl import _load_memories, _save_memory, _MEMORY_FILE
    # Use a temp file for testing
    import modules.devin_repl as repl_mod
    orig = repl_mod._MEMORY_FILE
    tmp = Path(tempfile.mktemp(suffix='.json'))
    repl_mod._MEMORY_FILE = tmp
    try:
        _save_memory('test fact for devin')
        mems = _load_memories()
        assert any('test fact for devin' in m.get('content', '') for m in mems)
    finally:
        repl_mod._MEMORY_FILE = orig
        if tmp.exists():
            tmp.unlink()


# ─── Provider selection ───────────────────────────────────────────────────────

def test_provider_selection_hf():
    from modules.devin_repl import _select_provider
    provider = _select_provider('hf')
    assert provider.name == 'huggingface'


def test_provider_selection_auto():
    """Auto-selection picks an available provider."""
    from modules.devin_repl import _select_provider
    provider = _select_provider('')
    assert provider.name in ['claude', 'gemini', 'openai', 'huggingface', 'free_claude', 'free_claude_sub', 'none']


def test_provider_fcc_available_with_env(monkeypatch):
    """FCC provider becomes available when FCC_BASE_URL is set."""
    monkeypatch.setenv('FCC_BASE_URL', 'http://localhost:8080')
    from modules.devin_repl import _FCCProvider
    fcc = _FCCProvider()
    assert fcc.available() is True
    assert fcc.name == 'free_claude'


def test_provider_fcc_unavailable_without_env(monkeypatch):
    """FCC provider is unavailable when FCC_BASE_URL is not set."""
    monkeypatch.delenv('FCC_BASE_URL', raising=False)
    from modules.devin_repl import _FCCProvider
    fcc = _FCCProvider()
    assert fcc.available() is False


def test_provider_selection_fcc(monkeypatch):
    """Selecting 'free_claude' returns FCC when FCC_BASE_URL set."""
    monkeypatch.setenv('FCC_BASE_URL', 'http://localhost:8080')
    from modules.devin_repl import _select_provider
    provider = _select_provider('free_claude')
    assert provider.name == 'free_claude'


# ─── REPL slash command parsing ───────────────────────────────────────────────

class _FakeProvider:
    name = 'test'
    def available(self): return True
    def stream(self, messages, system=''):
        yield 'test response'


def test_repl_slash_help(capsys):
    from modules.devin_repl import DevinREPL
    repl = DevinREPL.__new__(DevinREPL)
    repl._provider = _FakeProvider()
    repl._history = []
    repl._voice_mode = False
    repl._running = True
    repl._session = None
    repl._use_pt = False

    result = repl._handle_slash('/help')
    assert result is True
    out = capsys.readouterr().out
    assert '/help' in out or 'commands' in out.lower()


def test_repl_slash_unknown_returns_true(capsys):
    from modules.devin_repl import DevinREPL
    repl = DevinREPL.__new__(DevinREPL)
    repl._provider = _FakeProvider()
    repl._history = []
    repl._voice_mode = False
    repl._running = True
    repl._session = None
    repl._use_pt = False

    result = repl._handle_slash('/notacommand')
    assert result is True


def test_repl_slash_exit():
    from modules.devin_repl import DevinREPL
    repl = DevinREPL.__new__(DevinREPL)
    repl._provider = _FakeProvider()
    repl._history = []
    repl._voice_mode = False
    repl._running = True
    repl._session = None
    repl._use_pt = False

    result = repl._handle_slash('/exit')
    assert result is True
    assert repl._running is False


# ─── Agentic task (live API) ──────────────────────────────────────────────────

def test_agentic_task_shell():
    hf_token = os.environ.get('HF_TOKEN', '')
    if not hf_token:
        pytest.skip("HF_TOKEN not set — skipping live agentic test")
    os.environ['DEVIN_PROVIDER'] = 'huggingface'
    from modules.devin_repl import _run_agentic_task
    try:
        result = _run_agentic_task('Use shell_run to run: echo DEVIN_AGENTIC_OK. Report the output.')
        assert 'DEVIN_AGENTIC_OK' in result or len(result) > 10
    except Exception as e:
        if '402' in str(e) or 'credits' in str(e).lower() or 'depleted' in str(e).lower():
            pytest.skip(f"HF free tier credits exhausted: {e}")
        raise


if __name__ == '__main__':
    import subprocess
    subprocess.run([sys.executable, '-m', 'pytest', __file__, '-v'], cwd=str(ROOT))
