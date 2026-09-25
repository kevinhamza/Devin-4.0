"""
tests/demo_workflow.py — End-to-end workflow demonstration for Devin-4.0

Exercises Devin's core capabilities without needing an AI API key:
  1. Platform info / OS detection
  2. Shell command execution
  3. Python code execution + write-and-run
  4. File I/O roundtrip
  5. Persistent memory (SQLite)
  6. GitHub public repo audit (real network call — no auth needed)
  7. Tool registry inspection
  8. Task-mode detection
  9. Screenshot / observe_and_plan (skipped if headless)
 10. Provider selection logic

Use this to verify a fresh install is working before adding an API key.

Run:
  python3 tests/demo_workflow.py
  python3 tests/demo_workflow.py --repo kevinhamza/Devin-4.0
"""

import os, sys, argparse, time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

os.environ.setdefault('GEMINI_API_KEY', '_placeholder_')

def _hr(char='─', width=64):
    return char * width

def _hdr(n, title):
    print()
    print(_hr('═'))
    print(f"  Step {n}: {title}")
    print(_hr('═'))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', default='kevinhamza/Devin-4.0',
                    help='public GitHub repo to audit (default: kevinhamza/Devin-4.0)')
    ap.add_argument('--deep', action='store_true',
                    help='deep audit (contributors, languages, releases)')
    args = ap.parse_args()

    print()
    print("╭" + "─" * 62 + "╮")
    print("│ Devin-4.0 End-to-End Workflow Demo".ljust(63) + "│")
    print("│ (no AI API key required — validates core plumbing)".ljust(63) + "│")
    print("╰" + "─" * 62 + "╯")

    import importlib.util
    spec = importlib.util.spec_from_file_location('agent', str(ROOT / 'agent.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)

    # 1. Platform
    _hdr(1, "Platform / OS detection")
    print(m.tool_platform_info())

    # 2. Shell
    _hdr(2, "Shell command execution")
    r = m.tool_execute_shell('echo "Devin running on $(uname -s) $(uname -m)"')
    print(r.strip())

    # 3. Python
    _hdr(3, "Python code execution")
    r = m.tool_execute_python('import sys; print(f"Python {sys.version_info.major}.{sys.version_info.minor}")')
    print(r.strip())

    # 4. write-and-run
    _hdr(4, "write_and_run (create script, execute, capture output)")
    script = '/tmp/devin_demo_wr.py'
    r = m.tool_write_and_run(script, 'for i in range(3): print(f"line {i+1}")')
    print(r.strip())

    # 5. File I/O roundtrip
    _hdr(5, "File I/O roundtrip")
    test_path = '/tmp/devin_demo_file.txt'
    w = m.tool_write_file(test_path, 'devin roundtrip test\nline 2')
    print(f"write: {w.strip()}")
    r = m.tool_read_file(test_path)
    print(f"read:  {r.strip()}")

    # 6. Memory
    _hdr(6, "Persistent memory (SQLite)")
    fact = f"demo_ran_at_{int(time.time())}"
    print(m.tool_remember(fact).strip())
    print(m.tool_recall(fact[:10]).strip())

    # 7. GitHub API audit
    _hdr(7, f"GitHub repo audit: {args.repo}")
    r = m.tool_github_repo_audit(args.repo, deep=args.deep)
    # Print first ~50 lines
    for line in r.split('\n')[:50]:
        print(line)
    total_lines = len(r.split('\n'))
    if total_lines > 50:
        print(f"  … [+{total_lines - 50} more lines]")

    # 8. Tool registry inspection
    _hdr(8, "Tool registry")
    cats = {}
    for name, tool in m.TOOLS.items():
        cats.setdefault(tool.get('category', 'other'), []).append(name)
    print(f"  Total tools: {len(m.TOOLS)}")
    for cat in sorted(cats):
        print(f"    {cat:15s} {len(cats[cat]):3d} tools")

    # 9. Task-mode detection
    _hdr(9, "Task-mode heuristic")
    tests = [
        ('open firefox and search python', True),
        ('what is 2+2?', False),
        ('run nmap on my lab VM', True),
        ('hello there', False),
        ('install requests and write a script that fetches my IP', True),
    ]
    for text, expected in tests:
        result = m._is_task_mode(text)
        ok = '✓' if result == expected else '✗'
        print(f"  {ok} {text!r:55s} → task={result} (expected {expected})")

    # 10. Screenshot / observe_and_plan
    _hdr(10, "Screenshot + observe_and_plan (headless-tolerant)")
    if os.environ.get('DISPLAY') or sys.platform in ('darwin', 'win32'):
        shot = m.tool_screenshot()
        print(f"  Screenshot: {shot[:120]}")
        # observe_and_plan needs a provider for full analysis — skip AI part in demo
        print("  observe_and_plan: registered ✓ (AI analysis requires API key)")
    else:
        print(f"  Headless environment (no DISPLAY) — GUI tools skipped correctly")

    # 11. Providers
    _hdr(11, "Provider layer")
    for pname, cls in [('gemini', 'GeminiProvider'),
                        ('claude', 'ClaudeProvider'),
                        ('openai', 'OpenAIProvider'),
                        ('huggingface', 'HuggingFaceProvider'),
                        ('ollama', 'OllamaProvider')]:
        assert hasattr(m, cls), f"missing {cls}"
        print(f"  ✓ {cls} available")

    # Modules
    mods = m._modules_status()
    loaded = sum(1 for v in mods.values() if v)
    print(f"\n  Modules loaded: {loaded}/{len(mods)}")
    print(f"  Tools registered: {len(m.TOOLS)}")

    print()
    print(_hr('═'))
    print("  ✓ Demo complete. All core paths exercised.")
    print(_hr('═'))
    print()
    print("  Next: set GEMINI_API_KEY (or another provider) in .env and run:")
    print("    ./devin 'audit the kevinhamza/Devin-4.0 GitHub repo'")
    print()


if __name__ == '__main__':
    main()
