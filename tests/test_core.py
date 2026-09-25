"""
tests/test_core.py — Core agent test suite for Devin-4.0

Covers:
  - Syntax / import integrity
  - Tool registry completeness
  - Tool execution (non-GUI, non-network)
  - Provider selection logic
  - Memory / SQLite persistence
  - Agentic loop helpers (_is_task_mode, context management)
  - REPL command parsing
  - Cross-platform detection

Run:
  pytest tests/test_core.py -v
  python tests/test_core.py        (standalone, no pytest required)
"""

import os, sys, re, json, time, tempfile, importlib
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

PASS = 0
FAIL = 0
SKIP = 0
_results = []

def test(name: str, fn, skip_reason: str = ''):
    global PASS, FAIL, SKIP
    if skip_reason:
        SKIP += 1
        _results.append(('SKIP', name, skip_reason))
        print(f"  ⊘  SKIP  {name} — {skip_reason}")
        return
    try:
        fn()
        PASS += 1
        _results.append(('PASS', name, ''))
        print(f"  ✓  PASS  {name}")
    except Exception as e:
        FAIL += 1
        _results.append(('FAIL', name, str(e)))
        print(f"  ✗  FAIL  {name}: {e}")

# ─── 1. Syntax check ──────────────────────────────────────────────────────────

def t_syntax():
    import py_compile
    py_compile.compile(str(ROOT / 'agent.py'), doraise=True)

# ─── 2. Import agent module (suppress GUI / heavy deps) ───────────────────────

_agent = None

def t_import():
    global _agent
    # Provide dummy env vars so providers don't fail at import
    os.environ.setdefault('GEMINI_API_KEY', '_test_')
    os.environ.setdefault('ANTHROPIC_API_KEY', '_test_')
    # Load agent module
    spec = importlib.util.spec_from_file_location('agent', str(ROOT / 'agent.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _agent = mod

# ─── 3. TOOLS dict ────────────────────────────────────────────────────────────

def t_tools_dict_exists():
    assert hasattr(_agent, 'TOOLS'), "TOOLS dict missing from agent"
    assert isinstance(_agent.TOOLS, dict), "TOOLS is not a dict"

def t_tools_count():
    n = len(_agent.TOOLS)
    assert n >= 100, f"Expected >= 100 tools, got {n}"

def t_tools_schema():
    required_fields = {'fn', 'desc', 'params', 'required', 'category'}
    for name, spec in _agent.TOOLS.items():
        missing = required_fields - set(spec.keys())
        assert not missing, f"Tool '{name}' missing fields: {missing}"
        assert callable(spec['fn']), f"Tool '{name}' fn is not callable"
        assert isinstance(spec['desc'], str) and spec['desc'], f"Tool '{name}' has empty desc"
        assert isinstance(spec['params'], dict), f"Tool '{name}' params not a dict"

def t_tools_categories():
    cats = {t.get('category') for t in _agent.TOOLS.values()}
    expected = {'os', 'vision', 'browser', 'shell', 'filesystem', 'control', 'memory', 'voice'}
    present = expected & cats
    assert len(present) >= 5, f"Expected core categories, found: {cats}"

# ─── 4. Tool execution (safe, non-GUI) ────────────────────────────────────────

def t_tool_platform_info():
    result = _agent.TOOLS['platform_info']['fn']()
    assert 'platform' in result.lower() or 'os' in result.lower() or '{' in result

def t_tool_execute_python():
    result = _agent.TOOLS['execute_python']['fn']('print(2+2)')
    assert '4' in str(result), f"Expected '4' in result, got: {result!r}"

def t_tool_execute_shell():
    result = _agent.TOOLS['execute_shell']['fn']('echo hello_devin')
    assert 'hello_devin' in str(result), f"Expected echo output, got: {result!r}"

def t_tool_write_and_read_file():
    with tempfile.TemporaryDirectory() as d:
        path = str(Path(d) / 'test.txt')
        w = _agent.TOOLS['write_file']['fn'](path, 'devin test content')
        assert 'error' not in w.lower(), f"Write failed: {w}"
        r = _agent.TOOLS['read_file']['fn'](path)
        assert 'devin test content' in r, f"Read returned: {r!r}"

def t_tool_list_files():
    result = _agent.TOOLS['list_files']['fn'](str(ROOT))
    assert 'agent.py' in result, f"agent.py not in list: {result[:200]}"

def t_tool_get_system_info():
    result = _agent.TOOLS['get_system_info']['fn']()
    assert isinstance(result, str) and len(result) > 10

def t_tool_think_and_plan():
    result = _agent.TOOLS['think_and_plan']['fn']('open firefox and search google')
    assert 'TASK' in result or 'PLAN' in result or 'OBSERVE' in result

def t_tool_task_complete():
    result = _agent.TOOLS['task_complete']['fn']('test done')
    assert 'TASK_COMPLETE' in result or 'test done' in result

def t_tool_ask_user():
    result = _agent.TOOLS['ask_user']['fn']('test question?')
    assert isinstance(result, str)

def t_tool_sleep():
    start = time.time()
    _agent.TOOLS['sleep']['fn'](0.1)
    elapsed = time.time() - start
    assert elapsed >= 0.05, f"sleep(0.1) only took {elapsed:.3f}s"

def t_tool_web_search():
    # Non-network: just verify it's callable with a reasonable signature
    fn = _agent.TOOLS['web_search']['fn']
    assert callable(fn)

def t_tool_remember_and_recall():
    fact = f"test_fact_{int(time.time())}"
    r1 = _agent.TOOLS['remember']['fn'](fact)
    assert 'error' not in r1.lower(), f"remember failed: {r1}"
    r2 = _agent.TOOLS['recall']['fn'](fact[:10])
    assert fact in r2, f"recall didn't return fact. Got: {r2[:200]}"

def t_tool_screenshot_callable():
    fn = _agent.TOOLS['screenshot']['fn']
    assert callable(fn)

def t_tool_observe_and_plan():
    assert 'observe_and_plan' in _agent.TOOLS, "observe_and_plan not registered"
    fn = _agent.TOOLS['observe_and_plan']['fn']
    assert callable(fn)

# ─── 5. _is_task_mode ─────────────────────────────────────────────────────────

def t_task_mode_detection():
    assert _agent._is_task_mode('open firefox and search for python'), "task not detected"
    assert _agent._is_task_mode('install requests library and write a test script'), "install task not detected"
    assert _agent._is_task_mode('run nmap on localhost'), "run task not detected"
    assert not _agent._is_task_mode('what is 2+2?'), "question incorrectly flagged as task"
    assert not _agent._is_task_mode('who are you?'), "question incorrectly flagged as task"

# ─── 6. Provider classes ──────────────────────────────────────────────────────

def t_provider_classes_exist():
    for cls in ['GeminiProvider', 'ClaudeProvider', 'OpenAIProvider',
                'HuggingFaceProvider', 'OllamaProvider']:
        assert hasattr(_agent, cls), f"Provider class '{cls}' missing"

def t_hf_provider_models():
    hf = _agent.HuggingFaceProvider('_test_key_')
    assert hf.model == _agent.HuggingFaceProvider.MODELS[0], "Default HF model wrong"
    assert len(_agent.HuggingFaceProvider.MODELS) >= 5, "Need at least 5 HF models"
    assert len(_agent.HuggingFaceProvider.TOOL_CALL_MODELS) >= 3, "Need at least 3 native tool models"

def t_pick_provider_hf():
    os.environ['HF_TOKEN'] = '_test_hf_key_'
    try:
        p = _agent._pick_provider('huggingface')
        assert isinstance(p, _agent.HuggingFaceProvider)
        assert p.api_key == '_test_hf_key_'
    finally:
        os.environ.pop('HF_TOKEN', None)

def t_pick_provider_ollama():
    p = _agent._pick_provider('ollama')
    assert isinstance(p, _agent.OllamaProvider)

# ─── 7. Context management ────────────────────────────────────────────────────

def t_estimate_chars():
    msgs = [{"role": "user", "content": "hello"}, {"role": "assistant", "content": "world"}]
    n = _agent._estimate_chars(msgs)
    assert n >= 10, f"estimate_chars too low: {n}"

def t_compact_messages():
    msgs = [{"role": "user", "content": f"msg {i}"} for i in range(20)]
    compacted = _agent._compact_messages(list(msgs))
    assert len(compacted) < len(msgs), "compact_messages should reduce message count"

# ─── 8. Module loading ────────────────────────────────────────────────────────

def t_modules_status():
    mods = _agent._modules_status()
    assert isinstance(mods, dict), "_modules_status() not a dict"
    assert len(mods) >= 10, f"Expected >= 10 tracked modules, got {len(mods)}"
    loaded = sum(1 for v in mods.values() if v)
    print(f"        ({loaded}/{len(mods)} modules loaded)", end='')

# ─── 9. System prompt ─────────────────────────────────────────────────────────

def t_system_prompt():
    sp = _agent.SYSTEM_PROMPT
    assert isinstance(sp, str) and len(sp) > 500, "SYSTEM_PROMPT too short"
    for keyword in ['OBSERVE', 'PLAN', 'ACT', 'VERIFY', 'task_complete']:
        assert keyword in sp, f"SYSTEM_PROMPT missing keyword: {keyword}"

# ─── 10. Memory / SQLite ──────────────────────────────────────────────────────

def t_memory_db():
    db = _agent._DB
    count = db.execute('SELECT count(*) FROM memories').fetchone()[0]
    assert count >= 0, "memories table not readable"

# ─── 11. REPL helpers ────────────────────────────────────────────────────────

def t_make_help():
    h = _agent._make_help()
    assert '/help' in h and '/tools' in h and '/status' in h
    assert 'GEMINI_API_KEY' in h or 'gemini' in h.lower()

def t_render_markdown():
    result = _agent._render_markdown('**bold** and _italic_ and `code`')
    assert isinstance(result, str) and len(result) > 0

def t_box():
    result = _agent._box('test message')
    assert 'test message' in result

# ─── 12. Cross-platform flags ────────────────────────────────────────────────

def t_platform_flags():
    is_linux = getattr(_agent, '_IS_LINUX', None)
    is_mac   = getattr(_agent, '_IS_MAC', None)
    is_win   = getattr(_agent, '_IS_WIN', None)
    platform = getattr(_agent, '_PLATFORM', None)
    assert platform is not None, "_PLATFORM not set"
    assert isinstance(platform, str) and len(platform) > 0
    # At most one of the flags should be True
    flags = [is_linux, is_mac, is_win]
    true_count = sum(1 for f in flags if f)
    assert true_count <= 1, f"Multiple platform flags set: linux={is_linux} mac={is_mac} win={is_win}"

# ─── 13. Tool dispatch ───────────────────────────────────────────────────────

def t_dispatch_tool_execute_python():
    result = _agent._dispatch_tool('execute_python', {'code': 'print(1+1)'})
    assert '2' in str(result) or 'error' in str(result).lower()

def t_dispatch_unknown_tool():
    result = _agent._dispatch_tool('nonexistent_tool_xyz', {})
    assert 'ERROR' in str(result) or 'unknown' in str(result).lower()

# ─── 14. Write-and-run ───────────────────────────────────────────────────────

def t_write_and_run():
    result = _agent.TOOLS['write_and_run']['fn'](
        '/tmp/devin_test_wr.py',
        'print("devin_write_and_run_ok")'
    )
    assert 'devin_write_and_run_ok' in result, f"write_and_run failed: {result[:200]}"

# ─── 15. Tool: observe_and_plan (no display) ────────────────────────────────

def t_observe_and_plan_headless():
    result = _agent.TOOLS['observe_and_plan']['fn']('test goal in headless env')
    assert 'GOAL' in result or 'OBSERVE' in result or 'PLAN' in result

def t_github_repo_audit_registered():
    assert 'github_repo_audit' in _agent.TOOLS, "github_repo_audit not registered"
    spec = _agent.TOOLS['github_repo_audit']
    assert spec['category'] == 'git'
    assert 'repo' in spec['params']

def t_github_repo_audit_normalization():
    # Bad input should return ERROR, not raise
    r = _agent.tool_github_repo_audit('not-a-repo')
    assert 'ERROR' in r


# ─── Phase AA: Workflow / checkpoint tools ───────────────────────────────────

def t_multi_step_workflow():
    steps = json.dumps([
        {"tool": "execute_python", "args": {"code": "print('wf_step_1')"}, "label": "step1"},
        {"tool": "execute_shell",  "args": {"command": "echo wf_step_2"},   "label": "step2"},
    ])
    result = _agent.tool_multi_step_workflow(steps)
    assert 'wf_step_1' in result, f"step1 not in result: {result[:300]}"
    assert 'wf_step_2' in result, f"step2 not in result: {result[:300]}"
    assert 'SUMMARY: 2/2' in result


def t_multi_step_workflow_stop_on_error():
    steps = json.dumps([
        {"tool": "execute_python", "args": {"code": "raise ValueError('intentional')"}, "label": "bad"},
        {"tool": "execute_python", "args": {"code": "print('should_not_run')"},         "label": "skipped"},
    ])
    result = _agent.tool_multi_step_workflow(steps, stop_on_error=True)
    assert 'should_not_run' not in result, "step 2 ran despite stop_on_error"
    assert 'ERROR' in result or 'Stopped' in result


def t_wait_for_condition_true():
    r = _agent.tool_wait_for_condition('True', timeout=5)
    assert 'met' in r.lower() or 'attempt' in r.lower()


def t_wait_for_condition_timeout():
    r = _agent.tool_wait_for_condition('False', timeout=2, interval=0.5)
    assert 'TIMEOUT' in r or 'timeout' in r.lower()


def t_checkpoint_roundtrip():
    import time as _time
    cp_name = f'test_cp_{int(_time.time())}'
    save_r = _agent.tool_checkpoint_save(cp_name, 'test_data_roundtrip')
    assert 'saved' in save_r.lower(), f"save failed: {save_r}"
    load_r = _agent.tool_checkpoint_load(cp_name)
    assert load_r == 'test_data_roundtrip', f"load returned: {load_r}"
    list_r = _agent.tool_checkpoint_list()
    assert cp_name in list_r, f"checkpoint not in list: {list_r[:200]}"


def t_workflow_tools_registered():
    for name in ('multi_step_workflow', 'wait_for_condition',
                 'checkpoint_save', 'checkpoint_load', 'checkpoint_list',
                 'run_workflow_file', 'batch_execute', 'decompose_task'):
        assert name in _agent.TOOLS, f"tool '{name}' not registered"
        spec = _agent.TOOLS[name]
        for key in ('fn', 'desc', 'params', 'required', 'category'):
            assert key in spec, f"tool '{name}' missing key '{key}'"
        assert spec['category'] == 'workflow'


def t_batch_execute_parallel():
    items = json.dumps([
        {"tool": "execute_python", "args": {"code": "print('bA')"}, "id": "A"},
        {"tool": "execute_python", "args": {"code": "print('bB')"}, "id": "B"},
        {"tool": "execute_shell",  "args": {"command": "echo bC"},   "id": "C"},
    ])
    r = _agent.tool_batch_execute(items)
    assert 'bA' in r, f"A not in result: {r[:200]}"
    assert 'bB' in r, f"B not in result: {r[:200]}"
    assert 'bC' in r, f"C not in result: {r[:200]}"
    assert '3/3' in r


def t_decompose_task():
    r = _agent.tool_decompose_task("install nginx")
    assert 'GOAL' in r
    assert 'SUB-TASK' in r or 'install' in r.lower()
    # Should contain a tool suggestion
    assert 'execute_shell' in r or 'write_file' in r


# ─── Phase AC: File analysis tools ───────────────────────────────────────────

def t_summarize_file():
    import tempfile, os
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("# test file\ndef hello():\n    return 42\nclass Foo:\n    pass\n")
        fpath = f.name
    try:
        r = _agent.tool_summarize_file(fpath)
        assert 'FILE:' in r
        assert 'Lines:' in r
        assert 'hello' in r or 'CONTENT' in r
    finally:
        os.unlink(fpath)


def t_diff_files():
    import tempfile, os
    f1 = tempfile.mktemp(suffix='.txt')
    f2 = tempfile.mktemp(suffix='.txt')
    try:
        open(f1, 'w').write("alpha\nbeta\ngamma\n")
        open(f2, 'w').write("alpha\nbeta_changed\ngamma\n")
        r = _agent.tool_diff_files(f1, f2)
        assert '-beta' in r or '+beta_changed' in r, f"diff not in result: {r}"
    finally:
        for f in (f1, f2):
            try: os.unlink(f)
            except: pass


def t_search_in_files():
    r = _agent.tool_search_in_files('def tool_', directory='.', file_glob='agent.py', max_results=5)
    assert 'def tool_' in r or 'matches' in r.lower()


# ─── Phase AD: Process monitoring + env + JSON tools ─────────────────────────

def t_tail_file():
    import tempfile, os
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        f.write("line1\nline2\nline3\nline4\nline5\n")
        fpath = f.name
    try:
        r = _agent.tool_tail_file(fpath, lines=3)
        assert 'line3' in r or 'line4' in r or 'line5' in r, f"tail didn't show last lines: {r}"
        assert 'line1' not in r.split('last 3 lines')[1] if 'last 3 lines' in r else True
    finally:
        os.unlink(fpath)


def t_json_query():
    data = '{"name": "Devin", "version": 4, "tools": [{"id": 1}, {"id": 2}]}'
    assert _agent.tool_json_query(data, 'name') == 'Devin'
    assert _agent.tool_json_query(data, 'version') == '4'
    assert _agent.tool_json_query(data, 'tools[0].id') == '1'
    # Bad key returns ERROR
    r = _agent.tool_json_query(data, 'missing_key')
    assert 'ERROR' in r or 'not found' in r


def t_get_env():
    # Should return PATH (almost always set)
    r = _agent.tool_get_env('PATH')
    assert 'PATH=' in r
    # Secret keys should be redacted
    import os as _os
    _os.environ['TEST_SECRET_KEY_FOR_DEVIN'] = 'should_be_hidden'
    r2 = _agent.tool_get_env('TEST_SECRET_KEY_FOR_DEVIN')
    assert 'REDACTED' in r2, f"secret not redacted: {r2}"
    del _os.environ['TEST_SECRET_KEY_FOR_DEVIN']


def t_ad_tools_registered():
    for name in ('monitor_process', 'tail_file', 'get_env', 'set_env', 'json_query'):
        assert name in _agent.TOOLS, f"'{name}' not registered"
        spec = _agent.TOOLS[name]
        for key in ('fn', 'desc', 'params', 'required', 'category'):
            assert key in spec, f"'{name}' missing key '{key}'"

# ─── Runner ──────────────────────────────────────────────────────────────────

def main():
    print()
    print("═" * 60)
    print("  Devin-4.0 Core Test Suite")
    print("═" * 60)

    has_display = bool(os.environ.get('DISPLAY') or sys.platform == 'darwin' or sys.platform == 'win32')

    # Phase 1: Syntax (before import)
    print("\n── Phase 1: Syntax ──")
    test("agent.py syntax", t_syntax)

    # Phase 2: Import (heavy — loads all modules)
    print("\n── Phase 2: Import ──")
    test("import agent module", t_import)

    if _agent is None:
        print("\n  Cannot continue — agent import failed.")
        return

    # Phase 3: Tools
    print("\n── Phase 3: Tool Registry ──")
    test("TOOLS dict exists", t_tools_dict_exists)
    test("TOOLS count >= 100", t_tools_count)
    test("TOOLS schema valid", t_tools_schema)
    test("TOOLS categories present", t_tools_categories)

    # Phase 4: Tool execution
    print("\n── Phase 4: Tool Execution (non-GUI) ──")
    test("platform_info()", t_tool_platform_info)
    test("execute_python('print(2+2)')", t_tool_execute_python)
    test("execute_shell('echo hello')", t_tool_execute_shell)
    test("write_file + read_file roundtrip", t_tool_write_and_read_file)
    test("list_files(root)", t_tool_list_files)
    test("get_system_info()", t_tool_get_system_info)
    test("think_and_plan()", t_tool_think_and_plan)
    test("task_complete()", t_tool_task_complete)
    test("ask_user()", t_tool_ask_user)
    test("sleep(0.1)", t_tool_sleep)
    test("web_search callable", t_tool_web_search)
    test("remember + recall memory", t_tool_remember_and_recall)
    test("screenshot callable", t_tool_screenshot_callable)
    test("observe_and_plan registered", t_tool_observe_and_plan)
    test("write_and_run", t_write_and_run)
    test("observe_and_plan headless", t_observe_and_plan_headless)
    test("github_repo_audit registered", t_github_repo_audit_registered)
    test("github_repo_audit normalization", t_github_repo_audit_normalization)

    # Phase 5: Intelligence
    print("\n── Phase 5: Agentic Intelligence ──")
    test("_is_task_mode() detection", t_task_mode_detection)
    test("system_prompt content", t_system_prompt)
    test("_estimate_chars()", t_estimate_chars)
    test("_compact_messages()", t_compact_messages)

    # Phase 6: Providers
    print("\n── Phase 6: Provider Layer ──")
    test("provider classes exist", t_provider_classes_exist)
    test("HF provider models list", t_hf_provider_models)
    test("pick_provider('huggingface')", t_pick_provider_hf)
    test("pick_provider('ollama')", t_pick_provider_ollama)

    # Phase 7: Core helpers
    print("\n── Phase 7: Core Helpers ──")
    test("_modules_status()", t_modules_status)
    test("_make_help()", t_make_help)
    test("_render_markdown()", t_render_markdown)
    test("_box()", t_box)
    test("_PLATFORM flags", t_platform_flags)
    test("memory/SQLite table", t_memory_db)

    # Phase 8: Dispatch
    print("\n── Phase 8: Tool Dispatch ──")
    test("_dispatch_tool execute_python", t_dispatch_tool_execute_python)
    test("_dispatch_tool unknown graceful", t_dispatch_unknown_tool)

    # Phase 9: Workflow + checkpoint tools (Phase AA)
    print("\n── Phase 9: Workflow & Checkpoint Tools ──")
    test("workflow tools registered", t_workflow_tools_registered)
    test("multi_step_workflow 2-step", t_multi_step_workflow)
    test("multi_step_workflow stop_on_error", t_multi_step_workflow_stop_on_error)
    test("wait_for_condition true", t_wait_for_condition_true)
    test("wait_for_condition timeout", t_wait_for_condition_timeout)
    test("checkpoint save/load/list roundtrip", t_checkpoint_roundtrip)
    test("batch_execute parallel 3 tools", t_batch_execute_parallel)
    test("decompose_task structure", t_decompose_task)

    # Phase 10: File analysis tools (Phase AC)
    print("\n── Phase 10: File Analysis Tools ──")
    test("summarize_file", t_summarize_file)
    test("diff_files", t_diff_files)
    test("search_in_files", t_search_in_files)

    # Phase 11: Process monitoring + env + JSON tools (Phase AD)
    print("\n── Phase 11: System Monitoring & Data Tools ──")
    test("Phase AD tools registered", t_ad_tools_registered)
    test("tail_file last N lines", t_tail_file)
    test("json_query dot-path", t_json_query)
    test("get_env + secret redaction", t_get_env)

    # Summary
    total = PASS + FAIL + SKIP
    print()
    print("═" * 60)
    print(f"  Results: {PASS} passed  {FAIL} failed  {SKIP} skipped  (/{total} total)")
    print("═" * 60)

    if FAIL > 0:
        print("\n  FAILED tests:")
        for status, name, reason in _results:
            if status == 'FAIL':
                print(f"    ✗ {name}: {reason}")
        sys.exit(1)
    else:
        print("\n  All tests passed.")
        sys.exit(0)


if __name__ == '__main__':
    main()
