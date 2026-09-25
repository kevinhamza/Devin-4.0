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


# ─── Phase AE: Retry + verify + template + archives ──────────────────────────

def t_verify_output():
    assert 'PASS' in _agent.tool_verify_output('hello world', 'world', 'contains')
    assert 'FAIL' in _agent.tool_verify_output('hello world', 'missing', 'contains')
    assert 'PASS' in _agent.tool_verify_output('HELLO', 'hello', 'icontains')
    assert 'PASS' in _agent.tool_verify_output('ERROR: bad', '', 'is_error')
    assert 'FAIL' in _agent.tool_verify_output('OK result', '', 'is_error')
    assert 'PASS' in _agent.tool_verify_output('version 1.2.3', r'\d+\.\d+', 'regex')


def t_template_fill():
    result = _agent.tool_template_fill('Hello {name}!', '{"name": "Devin"}')
    assert result == 'Hello Devin!', f"got: {result}"
    # Unfilled placeholder warns
    r2 = _agent.tool_template_fill('{a} {b}', '{"a": "x"}')
    assert 'x' in r2 and ('b' in r2 or 'WARNING' in r2)


def t_retry_on_failure():
    # Should succeed on first attempt
    r = _agent.tool_retry_on_failure('execute_python', '{"code": "print(99)"}', max_retries=2)
    assert '99' in r and 'SUCCESS' in r
    # Should exhaust retries on unknown tool
    r2 = _agent.tool_retry_on_failure('nonexistent_tool_xyz', '{}', max_retries=2)
    assert 'failed' in r2.lower() or 'ERROR' in r2


def t_zip_unzip_roundtrip():
    import tempfile, os
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test file
        test_file = os.path.join(tmpdir, 'test.txt')
        open(test_file, 'w').write('zip test content')
        zip_path = os.path.join(tmpdir, 'out.zip')
        # Zip it
        zr = _agent.tool_zip_files(zip_path, json.dumps([test_file]))
        assert 'Created' in zr or 'bytes' in zr, f"zip failed: {zr}"
        # Unzip it
        dest = os.path.join(tmpdir, 'extracted')
        os.makedirs(dest)
        uzr = _agent.tool_unzip(zip_path, dest)
        assert 'Extracted' in uzr or 'file' in uzr.lower(), f"unzip failed: {uzr}"

# ─── Phase AF: Dev workflow tools ────────────────────────────────────────────

def t_af_tools_registered():
    for name in ('find_and_replace', 'run_tests', 'git_ops', 'create_project'):
        assert name in _agent.TOOLS, f"tool {name!r} missing"
        t = _agent.TOOLS[name]
        for k in ('fn', 'desc', 'params', 'required', 'category'):
            assert k in t, f"{name} missing key {k!r}"


def t_find_and_replace():
    import tempfile, os
    with tempfile.TemporaryDirectory() as tmpdir:
        p = os.path.join(tmpdir, 'sample.py')
        with open(p, 'w') as f:
            f.write('x = old_value\ny = old_value\n')
        r = _agent.tool_find_and_replace(tmpdir, 'old_value', 'new_value', '*.py')
        assert 'new_value' in r or '2' in r, f"got: {r}"
        assert open(p).read() == 'x = new_value\ny = new_value\n'


def t_find_and_replace_dry_run():
    import tempfile, os
    with tempfile.TemporaryDirectory() as tmpdir:
        p = os.path.join(tmpdir, 'f.py')
        with open(p, 'w') as f:
            f.write('foo = 1\n')
        r = _agent.tool_find_and_replace(tmpdir, 'foo', 'bar', '*.py', dry_run=True)
        assert 'DRY RUN' in r or 'dry' in r.lower(), f"got: {r}"
        assert open(p).read() == 'foo = 1\n', "dry run must not modify file"


def t_git_ops():
    r = _agent.tool_git_ops('status')
    assert 'On branch' in r or 'nothing to commit' in r or 'branch' in r.lower(), f"got: {r}"
    # Blocked ops
    r2 = _agent.tool_git_ops('reset', '--hard HEAD')
    assert 'not permitted' in r2.lower() or 'ERROR' in r2, f"should block: {r2}"


def t_create_project():
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        r = _agent.tool_create_project('myapp', 'python', tmpdir)
        assert 'myapp' in r and 'Created' in r
        from pathlib import Path
        assert (Path(tmpdir) / 'myapp' / 'main.py').exists()
        assert (Path(tmpdir) / 'myapp' / 'README.md').exists()
        # Duplicate should error
        r2 = _agent.tool_create_project('myapp', 'python', tmpdir)
        assert 'ERROR' in r2


def t_run_tests():
    # Run a small inline test file to verify the runner works
    import tempfile, os
    with tempfile.NamedTemporaryFile(suffix='_test.py', mode='w', delete=False) as f:
        f.write('def test_always_pass():\n    assert 1 + 1 == 2\n')
        tmp = f.name
    try:
        r = _agent.tool_run_tests(tmp, '', 15)
        assert 'exit' in r.lower() or 'passed' in r.lower() or 'PASS' in r, f"got: {r}"
    finally:
        os.unlink(tmp)


# ─── Phase AG: Code analysis tools ───────────────────────────────────────────

def t_ag_tools_registered():
    for name in ('explain_code', 'lint_code', 'profile_code', 'generate_tests'):
        assert name in _agent.TOOLS, f"tool {name!r} missing"
        t = _agent.TOOLS[name]
        for k in ('fn', 'desc', 'params', 'required', 'category'):
            assert k in t, f"{name} missing key {k!r}"


def t_explain_code():
    code = "import os\nimport re\ndef hello(name):\n    return f'Hello {name}'\n"
    r = _agent.tool_explain_code(code)
    assert 'import' in r.lower() and 'hello' in r.lower(), f"got: {r}"
    assert 'Lines:' in r


def t_profile_code():
    r = _agent.tool_profile_code('1 + 1', 100)
    assert 'µs/call' in r or 'ops' in r.lower(), f"got: {r}"
    # Safety block
    r2 = _agent.tool_profile_code('import os')
    assert 'ERROR' in r2 or 'blocked' in r2.lower(), f"should block: {r2}"


def t_generate_tests():
    code = "def add(a, b):\n    return a + b\ndef _private():\n    pass\n"
    r = _agent.tool_generate_tests(code, 'math_utils')
    assert 'def test_add' in r, f"got: {r}"
    assert 'test__private' not in r, "private functions should be skipped"
    assert 'import pytest' in r


# ─── Phase AH: Data & network tools ──────────────────────────────────────────

def t_ah_tools_registered():
    for name in ('http_request', 'parse_html', 'validate_json', 'csv_query', 'format_table'):
        assert name in _agent.TOOLS, f"tool {name!r} missing"
        t = _agent.TOOLS[name]
        for k in ('fn', 'desc', 'params', 'required', 'category'):
            assert k in t, f"{name} missing key {k!r}"


def t_validate_json():
    r = _agent.tool_validate_json('{"name": "devin", "version": 4}')
    assert 'Valid JSON' in r and 'name' in r, f"got: {r}"
    r2 = _agent.tool_validate_json('{invalid}')
    assert 'INVALID' in r2, f"should fail: {r2}"
    # Schema check
    r3 = _agent.tool_validate_json('{"a": 1, "b": 2}', '{"a": null, "c": null}')
    assert 'Missing' in r3 and 'Extra' in r3, f"got: {r3}"


def t_parse_html():
    html = '<html><h1>Title</h1><p>Hello <b>world</b></p><a href="https://x.com">link</a></html>'
    r = _agent.tool_parse_html(html, 'text')
    assert 'Hello' in r and 'world' in r, f"got: {r}"
    r2 = _agent.tool_parse_html(html, 'links')
    assert 'https://x.com' in r2, f"got: {r2}"
    r3 = _agent.tool_parse_html(html, 'headings')
    assert 'Title' in r3, f"got: {r3}"


def t_csv_query():
    csv_data = "name,age,city\nAlice,30,NYC\nBob,25,LA\nCarol,35,NYC"
    r = _agent.tool_csv_query(csv_data, 'name,age')
    assert 'Alice' in r and 'age' in r, f"got: {r}"
    r2 = _agent.tool_csv_query(csv_data, '', 'city == "NYC"')
    assert 'Alice' in r2 and 'Carol' in r2 and 'Bob' not in r2, f"filter: {r2}"


def t_format_table():
    data = "name,score\nAlice,95\nBob,87"
    r = _agent.tool_format_table(data)
    assert '│' in r and 'Alice' in r and 'score' in r, f"got: {r}"
    assert '2 rows' in r, f"row count: {r}"


# ─── Phase AI: Text processing tools ─────────────────────────────────────────

def t_ai_tools_registered():
    for name in ('encode_decode', 'regex_extract', 'text_stats', 'markdown_to_text', 'count_tokens'):
        assert name in _agent.TOOLS, f"tool {name!r} missing"
        t = _agent.TOOLS[name]
        for k in ('fn', 'desc', 'params', 'required', 'category'):
            assert k in t, f"{name} missing key {k!r}"


def t_encode_decode():
    b64 = _agent.tool_encode_decode('hello', 'base64_encode')
    assert b64 == 'aGVsbG8=', f"b64 encode: {b64}"
    dec = _agent.tool_encode_decode(b64, 'base64_decode')
    assert dec == 'hello', f"b64 decode: {dec}"
    h = _agent.tool_encode_decode('test', 'sha256')
    assert len(h) == 64, f"sha256 len: {len(h)}"
    url = _agent.tool_encode_decode('hello world', 'url_encode')
    assert 'hello%20world' == url or '+' in url or '%20' in url, f"url_encode: {url}"
    r = _agent.tool_encode_decode('x', 'unknown_op')
    assert 'ERROR' in r


def t_regex_extract():
    r = _agent.tool_regex_extract('foo123bar456', r'\d+')
    assert '123' in r and '456' in r, f"got: {r}"
    r2 = _agent.tool_regex_extract('no digits here', r'\d+')
    assert 'No matches' in r2, f"got: {r2}"


def t_text_stats():
    r = _agent.tool_text_stats('Hello world. This is a test sentence.')
    assert 'Words:' in r and 'Characters:' in r and 'Reading time:' in r, f"got: {r}"


def t_markdown_to_text():
    md = '# Heading\n\n**bold** and *italic* [link](http://x.com)\n\n```\ncode\n```'
    r = _agent.tool_markdown_to_text(md)
    assert 'Heading' in r and 'bold' in r and 'link' in r, f"got: {r}"
    assert '#' not in r and '**' not in r and '[' not in r, f"still has markdown: {r}"


def t_count_tokens():
    r = _agent.tool_count_tokens('hello world ' * 100, 'claude')
    assert 'tokens' in r.lower() and 'claude' in r.lower(), f"got: {r}"


# ─── Phase AJ: Task planning & navigation ────────────────────────────────────

def t_aj_tools_registered():
    for name in ('task_plan', 'file_tree', 'extract_todos', 'make_executable'):
        assert name in _agent.TOOLS, f"tool {name!r} missing"
        t = _agent.TOOLS[name]
        for k in ('fn', 'desc', 'params', 'required', 'category'):
            assert k in t, f"{name} missing key {k!r}"


def t_task_plan():
    r = _agent.tool_task_plan('build a REST API', 4)
    assert '1.' in r or '[ ] 1' in r, f"got: {r}"
    r2 = _agent.tool_task_plan('fix the login bug', format='checklist')
    assert '[ ]' in r2 and 'bug' not in r2.split('\n')[0].lower() or 'Goal:' in r2, f"got: {r2}"
    r3 = _agent.tool_task_plan('deploy to production', format='json')
    data = json.loads(r3)
    assert 'steps' in data and len(data['steps']) > 0


def t_file_tree():
    r = _agent.tool_file_tree('.', max_depth=1, file_limit=20)
    assert 'agent.py' in r or 'item(s)' in r, f"got: {r}"
    r2 = _agent.tool_file_tree('/nonexistent_path_xyz')
    assert 'ERROR' in r2


def t_extract_todos():
    import tempfile, os
    with tempfile.TemporaryDirectory() as tmpdir:
        p = os.path.join(tmpdir, 'test.py')
        with open(p, 'w') as f:
            f.write('# TODO: fix this\nx = 1  # FIXME: needs work\n')
        r = _agent.tool_extract_todos(tmpdir, '*.py')
        assert 'TODO' in r and 'FIXME' in r, f"got: {r}"


def t_make_executable():
    import tempfile, os, stat
    with tempfile.NamedTemporaryFile(suffix='.sh', delete=False) as f:
        f.write(b'#!/bin/bash\necho hi\n')
        tmp = f.name
    try:
        r = _agent.tool_make_executable(tmp)
        assert 'executable' in r.lower(), f"got: {r}"
        mode = os.stat(tmp).st_mode
        assert mode & stat.S_IXUSR, "file should be executable"
    finally:
        os.unlink(tmp)


# ─── Phase AK: System, config & memory tools ─────────────────────────────────

def t_ak_tools_registered():
    for name in ('system_snapshot', 'config_read', 'config_write', 'memory_search'):
        assert name in _agent.TOOLS, f"tool {name!r} missing"
        t = _agent.TOOLS[name]
        for k in ('fn', 'desc', 'params', 'required', 'category'):
            assert k in t, f"{name} missing key {k!r}"


def t_system_snapshot():
    r = _agent.tool_system_snapshot()
    assert 'System Snapshot' in r or 'CPU' in r or 'Memory' in r, f"got: {r[:200]}"
    assert 'OS:' in r or 'Python:' in r, f"no OS/Python info: {r[:200]}"


def t_config_read_write():
    import tempfile, os
    with tempfile.NamedTemporaryFile(suffix='.cfg', delete=False, mode='w') as f:
        f.write('[database]\nhost = localhost\nport = 5432\n')
        tmp = f.name
    try:
        r = _agent.tool_config_read(tmp, 'database')
        assert 'localhost' in r and 'port' in r, f"read: {r}"
        # Write a new key
        rw = _agent.tool_config_write(tmp, 'database', 'name', 'mydb')
        assert 'Written' in rw, f"write: {rw}"
        # Verify written
        r2 = _agent.tool_config_read(tmp, 'database')
        assert 'mydb' in r2, f"after write: {r2}"
        # Non-existent section
        r3 = _agent.tool_config_read(tmp, 'missing_section')
        assert 'not found' in r3.lower() or 'ERROR' in r3, f"got: {r3}"
    finally:
        os.unlink(tmp)


def t_memory_search():
    # memory_search gracefully handles missing db
    r = _agent.tool_memory_search('test query')
    # Either results or "No memory database" or "No memories found"
    assert isinstance(r, str) and len(r) > 0, f"got: {r}"


# ─── Phase AL: Code review, watch, convert, internet ─────────────────────────

def t_al_tools_registered():
    for name in ('code_review', 'watch_file', 'convert_units', 'internet_check'):
        assert name in _agent.TOOLS, f"tool {name!r} missing"
        t = _agent.TOOLS[name]
        for k in ('fn', 'desc', 'params', 'required', 'category'):
            assert k in t, f"{name} missing key {k!r}"


def t_code_review():
    import tempfile, os
    code = ('def func():\n'
            '    try:\n'
            '        pass\n'
            '    except:\n'
            '        pass\n'
            'password = "supersecret123"\n')
    with tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False) as f:
        f.write(code)
        tmp = f.name
    try:
        r = _agent.tool_code_review(tmp)
        assert 'broad exception' in r.lower() or 'credential' in r.lower(), f"got: {r}"
    finally:
        os.unlink(tmp)


def t_convert_units():
    r = _agent.tool_convert_units(1.0, 'km', 'm')
    assert '1000' in r, f"got: {r}"
    r2 = _agent.tool_convert_units(100, 'c', 'f')
    assert '212' in r2, f"got: {r2}"
    r3 = _agent.tool_convert_units(1, 'gb', 'mb')
    assert '1024' in r3, f"got: {r3}"
    r4 = _agent.tool_convert_units(1, 'kg', 'lb')
    assert '2.2' in r4 or 'lb' in r4, f"got: {r4}"


def t_internet_check():
    r = _agent.tool_internet_check()
    # Either connected or not — both are valid results
    assert 'latency' in r.lower() or 'connect' in r.lower() or 'down' in r.lower(), f"got: {r}"


# ─── Phase AM: Calculate, list_tools, diff_json, parse_args ──────────────────

def t_am_tools_registered():
    for name in ('calculate', 'list_tools', 'diff_json', 'parse_args'):
        assert name in _agent.TOOLS, f"tool {name!r} missing"
        t = _agent.TOOLS[name]
        for k in ('fn', 'desc', 'params', 'required', 'category'):
            assert k in t, f"{name} missing key {k!r}"


def t_calculate():
    r = _agent.tool_calculate('2 + 2 * 3')
    assert '8' in r, f"got: {r}"
    r2 = _agent.tool_calculate('sqrt(16)')
    assert '4' in r2, f"got: {r2}"
    r3 = _agent.tool_calculate('pi * 2')
    assert '6.28' in r3, f"got: {r3}"
    r4 = _agent.tool_calculate('import os')
    assert 'ERROR' in r4, f"should block: {r4}"


def t_list_tools():
    r = _agent.tool_list_tools()
    assert 'Tools' in r and 'calculate' in r, f"got: {r[:200]}"
    r2 = _agent.tool_list_tools(category='code')
    assert 'code' in r2.lower(), f"got: {r2[:200]}"
    r3 = _agent.tool_list_tools(search='git')
    assert 'git_ops' in r3, f"got: {r3}"


def t_diff_json():
    a = '{"name": "Alice", "age": 30}'
    b = '{"name": "Bob", "age": 30, "city": "NYC"}'
    r = _agent.tool_diff_json(a, b)
    assert 'CHANGED' in r and 'Alice' in r and 'ADDED' in r and 'city' in r, f"got: {r}"
    r2 = _agent.tool_diff_json(a, a)
    assert 'identical' in r2.lower(), f"got: {r2}"


def t_parse_args():
    r = _agent.tool_parse_args('--name Alice --age 30 positional_val')
    data = json.loads(r.split('\n\n')[0])
    assert data.get('name') == 'Alice', f"got: {r}"
    assert data.get('age') == '30', f"got: {r}"
    assert 'positional_val' in data.get('_positional', []), f"got: {r}"


# ─── Phase AT tests ──────────────────────────────────────────────────────────

def t_at_tools_registered():
    for name in ('goal_plan', 'self_reflect', 'generate_report'):
        assert name in _agent.TOOLS, f"missing: {name}"

def t_goal_plan():
    r = _agent.tool_goal_plan('implement a REST API endpoint for user signup')
    assert 'GOAL PLAN' in r, f"got: {r}"
    assert 'STEPS' in r, f"got: {r}"
    assert 'task_complete' in r, f"got: {r}"

def t_self_reflect():
    r_err = _agent.tool_self_reflect('ERROR: file not found: /tmp/missing.py')
    assert 'ERROR' in r_err, f"got: {r_err}"
    r_ok = _agent.tool_self_reflect('✓ All 5 tests passed.', goal='Run test suite')
    assert 'SUCCESS' in r_ok or '✅' in r_ok, f"got: {r_ok}"

def t_generate_report():
    import json
    secs = json.dumps([
        {"heading": "Summary", "content": "Everything went well."},
        {"heading": "Details", "content": "123 files processed."},
    ])
    r = _agent.tool_generate_report('Test Report', secs, 'markdown')
    assert '# Test Report' in r, f"got: {r}"
    assert '## Summary' in r, f"got: {r}"
    r_html = _agent.tool_generate_report('HTML Report', secs, 'html')
    assert '<h1>' in r_html, f"got: {r_html}"


# ─── Phase AS tests ──────────────────────────────────────────────────────────

def t_as_tools_registered():
    for name in ('symbol_search', 'find_dead_code', 'count_lines', 'ast_parse'):
        assert name in _agent.TOOLS, f"missing: {name}"

def t_symbol_search():
    import tempfile, pathlib
    with tempfile.TemporaryDirectory() as td:
        pathlib.Path(td, 'mod.py').write_text('def my_func(): pass\nmy_func()')
        r = _agent.tool_symbol_search(td, 'my_func')
        assert 'my_func' in r, f"got: {r}"
        assert '1' in r or '2' in r, f"got: {r}"

def t_count_lines():
    import tempfile, pathlib
    with tempfile.TemporaryDirectory() as td:
        pathlib.Path(td, 'a.py').write_text('x = 1\n# comment\n\ny = 2\n')
        r = _agent.tool_count_lines(td)
        assert 'TOTAL' in r, f"got: {r}"
        assert 'Code' in r or 'CODE' in r or 'code' in r.lower(), f"got: {r}"

def t_ast_parse_tool():
    code = "import os\ndef foo(a, b): pass\nclass Bar: pass"
    r = _agent.tool_ast_parse(code)
    assert 'foo' in r, f"got: {r}"
    assert 'Bar' in r, f"got: {r}"
    assert 'os' in r, f"got: {r}"


# ─── Phase AR tests ──────────────────────────────────────────────────────────

def t_ar_tools_registered():
    for name in ('list_processes', 'kill_process', 'spawn_process', 'process_info'):
        assert name in _agent.TOOLS, f"missing: {name}"

def t_list_processes():
    r = _agent.tool_list_processes('python3', limit=5)
    # Should either find processes or say "No processes found"
    assert isinstance(r, str) and len(r) > 0, f"got: {r}"

def t_spawn_process():
    r = _agent.tool_spawn_process('echo spawn_ok', detach=False)
    assert 'spawn_ok' in r or 'Exit code' in r, f"got: {r}"

def t_process_info_self():
    import os
    r = _agent.tool_process_info(os.getpid())
    assert isinstance(r, str) and len(r) > 0, f"got: {r}"
    # Should mention the pid somewhere
    assert str(os.getpid()) in r, f"got: {r}"


# ─── Phase AQ tests ──────────────────────────────────────────────────────────

def t_aq_tools_registered():
    for name in ('ping', 'port_scan', 'dns_lookup', 'http_headers', 'whois_ip'):
        assert name in _agent.TOOLS, f"missing: {name}"

def t_port_scan():
    # localhost port 22 might be open or closed, but the function must return structured output
    r = _agent.tool_port_scan('127.0.0.1', '22,65432', timeout=0.3)
    assert 'Port scan' in r, f"got: {r}"
    assert '/tcp' in r, f"got: {r}"

def t_dns_lookup():
    # Only test that the function returns without crashing; network may be restricted
    r = _agent.tool_dns_lookup('localhost', 'A')
    # Either returns an IP or an error — just not a Python exception
    assert isinstance(r, str), f"got: {r}"

def t_http_headers_tool():
    # Test against a known endpoint that's likely accessible
    r = _agent.tool_http_headers('http://ip-api.com/json/8.8.8.8?fields=status', timeout=5)
    # Should return HTTP status line or an error string — must be a string
    assert isinstance(r, str) and len(r) > 0, f"got: {r}"


# ─── Phase AP tests ──────────────────────────────────────────────────────────

def t_ap_tools_registered():
    for name in ('bulk_rename', 'folder_sync', 'archive_info', 'checksum'):
        assert name in _agent.TOOLS, f"missing: {name}"

def t_bulk_rename():
    import tempfile, os, pathlib
    with tempfile.TemporaryDirectory() as td:
        # Create test files
        for name in ('report_2024.txt', 'report_2023.txt', 'other.txt'):
            pathlib.Path(td, name).write_text('x')
        # Dry run
        r = _agent.tool_bulk_rename(td, r'report_(\d+)', r'summary_\1', '*.txt', True)
        assert 'WOULD' in r, f"got: {r}"
        # Actual rename
        r2 = _agent.tool_bulk_rename(td, r'report_(\d+)', r'summary_\1', '*.txt', False)
        assert 'RENAME' in r2, f"got: {r2}"
        names = [f.name for f in pathlib.Path(td).iterdir()]
        assert 'summary_2024.txt' in names, f"files: {names}"

def t_folder_sync():
    import tempfile, pathlib
    with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as dst:
        pathlib.Path(src, 'a.txt').write_text('hello')
        pathlib.Path(src, 'b.txt').write_text('world')
        r = _agent.tool_folder_sync(src, dst, dry_run=False)
        assert 'COPY' in r or 'sync' in r.lower(), f"got: {r}"
        assert pathlib.Path(dst, 'a.txt').exists(), "a.txt not copied"

def t_archive_info():
    import tempfile, zipfile, pathlib
    with tempfile.TemporaryDirectory() as td:
        zpath = str(pathlib.Path(td, 'test.zip'))
        with zipfile.ZipFile(zpath, 'w') as z:
            z.writestr('file1.txt', 'hello')
            z.writestr('file2.txt', 'world')
        r = _agent.tool_archive_info(zpath)
        assert 'ZIP' in r, f"got: {r}"
        assert 'file1.txt' in r, f"got: {r}"

def t_checksum():
    import tempfile, pathlib, hashlib
    with tempfile.TemporaryDirectory() as td:
        fpath = str(pathlib.Path(td, 'f.txt'))
        pathlib.Path(fpath).write_text('hello')
        r = _agent.tool_checksum(fpath, 'sha256')
        assert 'SHA256' in r, f"got: {r}"
        expected = hashlib.sha256(b'hello').hexdigest()
        assert expected in r, f"hash mismatch: {r}"


# ─── Phase AO tests ──────────────────────────────────────────────────────────

def t_ao_tools_registered():
    for name in ('pipe', 'string_ops', 'sleep', 'generate_uuid', 'random_value', 'timestamp'):
        assert name in _agent.TOOLS, f"missing: {name}"

def t_pipe():
    # write a file then read it back via pipe
    import tempfile, os
    steps = json.dumps([
        {"tool": "execute_python", "args": {"code": "print('pipe_test')"}},
        {"tool": "string_ops", "args": {"operation": "upper"}},
    ])
    r = _agent.tool_pipe(steps)
    assert 'PIPE_TEST' in r, f"got: {r}"

def t_string_ops():
    assert _agent.tool_string_ops('Hello World', 'upper') == 'HELLO WORLD'
    assert _agent.tool_string_ops('Hello World', 'lower') == 'hello world'
    assert _agent.tool_string_ops('abc', 'repeat', '3') == 'abcabcabc'
    r = _agent.tool_string_ops('hello world python', 'split')
    data = json.loads(r)
    assert 'python' in data, f"got: {r}"
    assert _agent.tool_string_ops('my file name', 'slugify') == 'my-file-name'

def t_sleep():
    import time
    start = time.time()
    r = _agent.tool_sleep(0.1)
    elapsed = time.time() - start
    assert 'Slept' in r, f"got: {r}"
    assert elapsed >= 0.05, f"sleep too short: {elapsed}"

def t_generate_uuid():
    r = _agent.tool_generate_uuid()
    assert len(r) == 36, f"got: {r}"
    parts = r.split('-')
    assert len(parts) == 5, f"got: {r}"
    r5 = _agent.tool_generate_uuid(5, 'dns', 'example.com')
    assert len(r5) == 36, f"got: {r5}"

def t_random_value():
    r = _agent.tool_random_value('int', 1, 10)
    assert 1 <= int(r) <= 10, f"got: {r}"
    rs = _agent.tool_random_value('string', length=12)
    assert len(rs) == 12, f"got: {rs}"
    rc = _agent.tool_random_value('choice', choices='["a","b","c"]')
    assert rc in ('a', 'b', 'c'), f"got: {rc}"

def t_timestamp():
    r = _agent.tool_timestamp('iso')
    assert 'T' in r or '-' in r, f"got: {r}"
    ru = _agent.tool_timestamp('unix')
    assert ru.isdigit(), f"got: {ru}"
    rd = _agent.tool_timestamp('date')
    assert len(rd) == 10 and rd[4] == '-', f"got: {rd}"


# ─── Phase AN tests ──────────────────────────────────────────────────────────

def t_an_tools_registered():
    for name in ('summarize_changes', 'task_complete', 'format_output'):
        assert name in _agent.TOOLS, f"missing: {name}"

def t_summarize_changes():
    before = "line one\nline two\nline three\n"
    after  = "line one\nline TWO\nline four\n"
    r = _agent.tool_summarize_changes(before, after, 'test')
    assert 'Lines added' in r, f"got: {r}"
    assert 'Lines removed' in r, f"got: {r}"
    r2 = _agent.tool_summarize_changes("same", "same")
    assert 'No changes' in r2, f"got: {r2}"

def t_task_complete():
    r = _agent.tool_task_complete('Finished the work', '["file_a.py","file_b.py"]')
    assert 'TASK COMPLETE' in r, f"got: {r}"
    assert 'Finished the work' in r, f"got: {r}"
    assert 'file_a.py' in r, f"got: {r}"

def t_format_output():
    r = _agent.tool_format_output('hello world', 'box', 'Title')
    assert '┌' in r and '┘' in r, f"got: {r}"
    r2 = _agent.tool_format_output('alpha\nbeta\ngamma', 'list')
    assert '•' in r2 or '*' in r2 or '-' in r2, f"got: {r2}"
    r3 = _agent.tool_format_output('one\ntwo', 'numbered')
    assert '1.' in r3 or '1)' in r3, f"got: {r3}"


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

    # Phase 12: Retry + verify + template + archives (Phase AE)
    print("\n── Phase 12: Retry, Verify & Archive Tools ──")
    test("verify_output modes", t_verify_output)
    test("template_fill", t_template_fill)
    test("retry_on_failure", t_retry_on_failure)
    test("zip/unzip roundtrip", t_zip_unzip_roundtrip)

    # Phase 13: Dev workflow tools (Phase AF)
    print("\n── Phase 13: Dev Workflow Tools ──")
    test("Phase AF tools registered", t_af_tools_registered)
    test("find_and_replace", t_find_and_replace)
    test("find_and_replace dry_run", t_find_and_replace_dry_run)
    test("git_ops status + blocked ops", t_git_ops)
    test("create_project scaffold", t_create_project)
    test("run_tests", t_run_tests)

    # Phase 14: Code analysis tools (Phase AG)
    print("\n── Phase 14: Code Analysis Tools ──")
    test("Phase AG tools registered", t_ag_tools_registered)
    test("explain_code", t_explain_code)
    test("profile_code", t_profile_code)
    test("generate_tests stubs", t_generate_tests)

    # Phase 15: Data & network tools (Phase AH)
    print("\n── Phase 15: Data & Network Tools ──")
    test("Phase AH tools registered", t_ah_tools_registered)
    test("validate_json", t_validate_json)
    test("parse_html", t_parse_html)
    test("csv_query", t_csv_query)
    test("format_table", t_format_table)

    # Phase 16: Text processing tools (Phase AI)
    print("\n── Phase 16: Text Processing Tools ──")
    test("Phase AI tools registered", t_ai_tools_registered)
    test("encode_decode (base64/sha256/url)", t_encode_decode)
    test("regex_extract", t_regex_extract)
    test("text_stats", t_text_stats)
    test("markdown_to_text", t_markdown_to_text)
    test("count_tokens", t_count_tokens)

    # Phase 17: Task planning & navigation (Phase AJ)
    print("\n── Phase 17: Task Planning & Navigation ──")
    test("Phase AJ tools registered", t_aj_tools_registered)
    test("task_plan (numbered/checklist/json)", t_task_plan)
    test("file_tree", t_file_tree)
    test("extract_todos", t_extract_todos)
    test("make_executable", t_make_executable)

    # Phase 18: System, config & memory (Phase AK)
    print("\n── Phase 18: System, Config & Memory ──")
    test("Phase AK tools registered", t_ak_tools_registered)
    test("system_snapshot", t_system_snapshot)
    test("config_read + config_write", t_config_read_write)
    test("memory_search", t_memory_search)

    # Phase 19: Code review, watch, convert, internet (Phase AL)
    print("\n── Phase 19: Code Review, Units & Connectivity ──")
    test("Phase AL tools registered", t_al_tools_registered)
    test("code_review", t_code_review)
    test("convert_units", t_convert_units)
    test("internet_check", t_internet_check)

    # Phase 20: Calculate, list_tools, diff_json, parse_args (Phase AM)
    print("\n── Phase 20: Calculate, List Tools, Diff JSON ──")
    test("Phase AM tools registered", t_am_tools_registered)
    test("calculate (math eval)", t_calculate)
    test("list_tools filter", t_list_tools)
    test("diff_json", t_diff_json)
    test("parse_args", t_parse_args)

    # Phase 21: Summarize changes, task complete, format output (Phase AN)
    print("\n── Phase 21: Change Summary, Task Done, Output Format ──")
    test("Phase AN tools registered", t_an_tools_registered)
    test("summarize_changes", t_summarize_changes)
    test("task_complete", t_task_complete)
    test("format_output", t_format_output)

    # Phase 22: Final intelligence — goal_plan, self_reflect, generate_report (Phase AT)
    print("\n── Phase 22: Final Intelligence Tools ──")
    test("Phase AT tools registered", t_at_tools_registered)
    test("goal_plan", t_goal_plan)
    test("self_reflect", t_self_reflect)
    test("generate_report", t_generate_report)

    # Phase 23: Code intelligence — symbol search, dead code, count lines, AST (Phase AS)
    print("\n── Phase 23: Code Intelligence Tools ──")
    test("Phase AS tools registered", t_as_tools_registered)
    test("symbol_search", t_symbol_search)
    test("count_lines", t_count_lines)
    test("ast_parse", t_ast_parse_tool)

    # Phase 24: Process control — list, spawn, info (Phase AR)
    print("\n── Phase 24: Process Control Tools ──")
    test("Phase AR tools registered", t_ar_tools_registered)
    test("list_processes", t_list_processes)
    test("spawn_process", t_spawn_process)
    test("process_info (self)", t_process_info_self)

    # Phase 25: Network tools — ping, port_scan, dns_lookup, http_headers (Phase AQ)
    print("\n── Phase 25: Network Tools ──")
    test("Phase AQ tools registered", t_aq_tools_registered)
    test("port_scan", t_port_scan)
    test("dns_lookup", t_dns_lookup)
    test("http_headers", t_http_headers_tool)

    # Phase 26: Bulk rename, folder sync, archive info, checksum (Phase AP)
    print("\n── Phase 26: File Management Tools ──")
    test("Phase AP tools registered", t_ap_tools_registered)
    test("bulk_rename", t_bulk_rename)
    test("folder_sync", t_folder_sync)
    test("archive_info", t_archive_info)
    test("checksum", t_checksum)

    # Phase 27: Pipe, string ops, sleep, uuid, random, timestamp (Phase AO)
    print("\n── Phase 27: Pipe, String Ops, Utilities ──")
    test("Phase AO tools registered", t_ao_tools_registered)
    test("pipe tool chain", t_pipe)
    test("string_ops", t_string_ops)
    test("sleep", t_sleep)
    test("generate_uuid", t_generate_uuid)
    test("random_value", t_random_value)
    test("timestamp", t_timestamp)

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
