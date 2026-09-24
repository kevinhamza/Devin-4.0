#!/usr/bin/env python3
"""
Devin AGI — Standalone Agentic Task Runner
==========================================
Self-contained. Zero dependencies beyond Python stdlib.
No imports from other Devin modules.

The AI (your choice of provider) reasons, plans, and calls tools
on its own until the task is complete.

Usage:
  python tests/run_task.py
  python tests/run_task.py "search today's news and tell me which are fake"
  python tests/run_task.py --provider claude "summarise the top AI news today"
  python tests/run_task.py --provider openai "what is the weather in Tokyo"
  python tests/run_task.py --provider gemini "who won the latest F1 race"

API keys (add to .env in project root, or export):
  GEMINI_API_KEY    → free: https://aistudio.google.com/app/apikey
  ANTHROPIC_API_KEY → https://console.anthropic.com/
  OPENAI_API_KEY    → https://platform.openai.com/api-keys
"""

import os, sys, json, time, re, subprocess, html as html_lib
import urllib.request, urllib.parse, urllib.error
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Any

# ── Load .env ────────────────────────────────────────────────────────────────
_root = Path(__file__).resolve().parent.parent
_env = _root / '.env'
if _env.exists():
    for _line in _env.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith('#') and '=' in _line:
            _k, _v = _line.split('=', 1)
            os.environ.setdefault(_k.strip(), _v.strip().strip('"\''))

GEMINI_KEY    = os.environ.get('GEMINI_API_KEY', '')
ANTHROPIC_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
OPENAI_KEY    = os.environ.get('OPENAI_API_KEY', '')

# ── Colour output ─────────────────────────────────────────────────────────────
_TTY = sys.stdout.isatty()
def _c(code, t): return f'\033[{code}m{t}\033[0m' if _TTY else t
cyan   = lambda t: _c('36;1', t)
green  = lambda t: _c('32;1', t)
yellow = lambda t: _c('33;1', t)
red    = lambda t: _c('31;1', t)
bold   = lambda t: _c('1',    t)
dim    = lambda t: _c('2',    t)
blue   = lambda t: _c('34;1', t)

# ═══════════════════════════════════════════════════════════════════════════════
# BUILT-IN TOOLS  (pure stdlib — no external imports required)
# ═══════════════════════════════════════════════════════════════════════════════

def _ua_get(url: str, timeout: int = 15) -> str:
    """HTTP GET with a browser User-Agent. Returns body text or ERROR:..."""
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/120.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            enc = r.headers.get_content_charset('utf-8')
            return raw.decode(enc, errors='replace')
    except Exception as e:
        return f'ERROR:{e}'


def tool_web_search(query: str, num_results: int = 8) -> str:
    """
    Search the web using DuckDuckGo (no API key required).
    Returns JSON list of {title, url, snippet}.
    """
    params = urllib.parse.urlencode({'q': query})
    url = f'https://html.duckduckgo.com/html/?{params}'
    raw = _ua_get(url)
    if raw.startswith('ERROR:'):
        return json.dumps([{"error": raw}])

    # Parse results from DuckDuckGo HTML (no beautifulsoup needed)
    results: List[Dict[str, str]] = []
    # Title+URL
    for m in re.finditer(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
                          raw, re.S)[:num_results + 5]:
        href, title_html = m.group(1), m.group(2)
        title = re.sub(r'<[^>]+>', '', title_html).strip()
        # Unwrap DDG redirect
        uu = re.search(r'uddg=([^&]+)', href)
        actual = urllib.parse.unquote(uu.group(1)) if uu else href
        if actual and title:
            results.append({'title': title, 'url': actual, 'snippet': ''})

    # Snippets (fill in)
    snips = [re.sub(r'<[^>]+>', '', s).strip()
             for s in re.findall(r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>', raw, re.S)]
    for i, s in enumerate(snips[:len(results)]):
        results[i]['snippet'] = html_lib.unescape(s)

    return json.dumps(results[:num_results], ensure_ascii=False, indent=2)


def tool_web_fetch(url: str) -> str:
    """
    Fetch a webpage and return its cleaned text content (up to 8000 chars).
    Strips all HTML tags, scripts, and navigation elements.
    """
    raw = _ua_get(url, timeout=20)
    if raw.startswith('ERROR:'):
        return raw
    # Remove scripts, styles, nav, footer
    raw = re.sub(r'<(script|style|nav|footer|header)[^>]*>.*?</\1>', ' ', raw,
                 flags=re.S | re.I)
    # Strip remaining tags
    text = re.sub(r'<[^>]+>', ' ', raw)
    # Decode HTML entities
    text = html_lib.unescape(text)
    # Collapse whitespace
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    return text[:8000] + (f'\n\n[…truncated, total {len(text)} chars]' if len(text) > 8000 else '')


def tool_execute_shell(command: str) -> str:
    """
    Execute a shell command and return its stdout+stderr output.
    Runs with a 30-second timeout. Use for: date, curl -s, ls, whoami, uname, etc.
    """
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=30
        )
        out = (result.stdout + result.stderr).strip()
        return out[:4000] if out else f'(exit code {result.returncode}, no output)'
    except subprocess.TimeoutExpired:
        return 'ERROR: command timed out after 30s'
    except Exception as e:
        return f'ERROR: {e}'


def tool_think(thought: str) -> str:
    """
    Record a reasoning step without taking any external action.
    Use this to plan, reason through options, or explain your thinking.
    The thought is returned as-is so it appears in your context.
    """
    return f"[Reasoning recorded] {thought}"


def tool_task_complete(result: str) -> str:
    """Signal that the task is done. Provide the full final answer/report."""
    return result


# ── Tool registry (name → callable) ──────────────────────────────────────────
TOOL_REGISTRY = {
    'web_search':     tool_web_search,
    'web_fetch':      tool_web_fetch,
    'execute_shell':  tool_execute_shell,
    'think':          tool_think,
    'task_complete':  tool_task_complete,
}

# ── Tool schemas for AI providers ─────────────────────────────────────────────
TOOL_DEFINITIONS = [
    {
        "name": "think",
        "description": (
            "Record a reasoning step without any external action. "
            "Use to plan the approach, reason through options, or explain your logic. "
            "Always think before acting on a complex task."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "thought": {"type": "string", "description": "Your reasoning / plan"},
            },
            "required": ["thought"],
        },
    },
    {
        "name": "web_search",
        "description": (
            "Search the web using DuckDuckGo (no API key required). "
            "Returns JSON list of {title, url, snippet}. "
            "Use for: finding news, looking up facts, discovering URLs."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query":       {"type": "string",  "description": "Search query string"},
                "num_results": {"type": "integer", "description": "Results to return (default 8, max 15)"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "web_fetch",
        "description": (
            "Fetch the full text content of any URL. "
            "Returns cleaned page text, stripping HTML tags. "
            "Use to read articles, verify claims, check source credibility."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Full URL to fetch (http:// or https://)"},
            },
            "required": ["url"],
        },
    },
    {
        "name": "execute_shell",
        "description": (
            "Run a shell command. "
            "Useful for: `date` (current date/time), `curl -s URL` (HTTP), "
            "`uname -a` (OS info), `ls`, `cat file`, `python3 -c ...`."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to execute"},
            },
            "required": ["command"],
        },
    },
    {
        "name": "task_complete",
        "description": (
            "Call ONLY when the ENTIRE task is finished and verified. "
            "Provide the complete, well-formatted final answer in 'result'. "
            "Do NOT call this prematurely — finish all research first."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "result": {"type": "string", "description": "Full final answer / report for the user"},
            },
            "required": ["result"],
        },
    },
]

SYSTEM_PROMPT = """\
You are Devin, an advanced AI agent with access to web search, web browsing, and shell execution.

HOW TO REASON AND ACT:
1. Think first — use the `think` tool to plan your approach before taking any action.
2. Search — use `web_search` to find relevant information.
3. Read — use `web_fetch` to read articles and verify claims from the source.
4. Verify — cross-check claims with multiple sources where possible.
5. Complete — call `task_complete` ONLY when the full task is done and verified.

RULES:
- Never fabricate results. Only report what tools actually return.
- Never stop halfway. Keep going until the task is fully done.
- If a fetch fails, try an alternative URL. If search is empty, try a different query.
- Be thorough and specific in your final report. Give evidence, not just verdicts.
- The `think` tool costs nothing — use it freely to reason through complex steps.
"""

# ═══════════════════════════════════════════════════════════════════════════════
# Provider wrappers — unified call() → (texts, tool_calls)
# ═══════════════════════════════════════════════════════════════════════════════

def _http_post(url: str, headers: dict, body: dict) -> dict:
    data = json.dumps(body).encode('utf-8')
    req  = urllib.request.Request(url, data=data, headers=headers, method='POST')
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            err = e.read().decode('utf-8', errors='replace')
            if e.code == 429:
                wait = 25 * (attempt + 1)
                print(yellow(f"\n  [rate-limited — waiting {wait}s]"), end='', flush=True)
                time.sleep(wait); continue
            raise RuntimeError(f'HTTP {e.code}: {err[:300]}')
    raise RuntimeError('Max retries exceeded')


class GeminiProvider:
    name  = 'Gemini'
    model = 'gemini-2.5-flash'

    def __init__(self, key: str):
        self.key  = key
        self.url  = f'https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent'
        self.hist: List[dict] = []

    def _schemas(self):
        out = []
        for t in TOOL_DEFINITIONS:
            props = {k: {**v, 'type': v['type'].upper()}
                     for k, v in t['parameters']['properties'].items()}
            out.append({'name': t['name'], 'description': t['description'],
                        'parameters': {'type': 'OBJECT', 'properties': props,
                                       'required': t['parameters'].get('required', [])}})
        return [{'functionDeclarations': out}]

    def call(self, user_msg=None, tool_results=None):
        if user_msg:
            self.hist.append({'role': 'user', 'parts': [{'text': user_msg}]})
        if tool_results:
            self.hist.append({'role': 'user', 'parts': [
                {'functionResponse': {'name': r['name'], 'response': {'result': r['output']}}}
                for r in tool_results]})

        resp  = _http_post(self.url,
                           {'Content-Type': 'application/json',
                            'x-goog-api-key': self.key,
                            'x-goog-api-client': 'google-genai-sdk/2.19.0 gl-node/24'},
                           {'contents': self.hist, 'tools': self._schemas(),
                            'systemInstruction': {'parts': [{'text': SYSTEM_PROMPT}]},
                            'generationConfig': {'maxOutputTokens': 8192, 'temperature': 0.1}})

        parts = resp.get('candidates', [{}])[0].get('content', {}).get('parts', [])
        self.hist.append({'role': 'model', 'parts': parts})

        texts = [p['text'].strip() for p in parts if p.get('text', '').strip()]
        calls = [{'name': p['functionCall']['name'],
                  'args': p['functionCall'].get('args', {}),
                  'id':   f"g{int(time.time()*1000)}"}
                 for p in parts if 'functionCall' in p]
        return texts, calls


class ClaudeProvider:
    name  = 'Claude'
    model = 'claude-sonnet-4-6'
    url   = 'https://api.anthropic.com/v1/messages'

    def __init__(self, key: str):
        self.key  = key
        self.hist: List[dict] = []

    def _schemas(self):
        return [{'name': t['name'], 'description': t['description'],
                 'input_schema': t['parameters']} for t in TOOL_DEFINITIONS]

    def call(self, user_msg=None, tool_results=None):
        if user_msg:
            self.hist.append({'role': 'user', 'content': user_msg})
        if tool_results:
            self.hist.append({'role': 'user', 'content': [
                {'type': 'tool_result', 'tool_use_id': r['id'], 'content': r['output']}
                for r in tool_results]})

        resp    = _http_post(self.url,
                             {'Content-Type': 'application/json',
                              'x-api-key': self.key,
                              'anthropic-version': '2023-06-01'},
                             {'model': self.model, 'max_tokens': 8192,
                              'system': SYSTEM_PROMPT, 'tools': self._schemas(),
                              'messages': self.hist})
        content = resp.get('content', [])
        self.hist.append({'role': 'assistant', 'content': content})

        texts = [b['text'] for b in content if b.get('type') == 'text' and b.get('text')]
        calls = [{'name': b['name'], 'args': b.get('input', {}), 'id': b.get('id', '')}
                 for b in content if b.get('type') == 'tool_use']
        return texts, calls


class OpenAIProvider:
    name  = 'GPT'
    model = 'gpt-4o-mini'
    url   = 'https://api.openai.com/v1/chat/completions'

    def __init__(self, key: str):
        self.key  = key
        self.hist: List[dict] = [{'role': 'system', 'content': SYSTEM_PROMPT}]

    def _schemas(self):
        return [{'type': 'function', 'function': {
            'name': t['name'], 'description': t['description'],
            'parameters': t['parameters']}} for t in TOOL_DEFINITIONS]

    def call(self, user_msg=None, tool_results=None):
        if user_msg:
            self.hist.append({'role': 'user', 'content': user_msg})
        if tool_results:
            for r in tool_results:
                self.hist.append({'role': 'tool', 'tool_call_id': r['id'], 'content': r['output']})

        resp = _http_post(self.url,
                          {'Content-Type': 'application/json',
                           'Authorization': f'Bearer {self.key}'},
                          {'model': self.model, 'max_tokens': 8192,
                           'tools': self._schemas(), 'messages': self.hist})
        msg  = resp['choices'][0]['message']
        self.hist.append(msg)

        texts = [msg['content']] if msg.get('content') else []
        calls = []
        for tc in (msg.get('tool_calls') or []):
            try:   args = json.loads(tc['function']['arguments'])
            except: args = {}
            calls.append({'name': tc['function']['name'], 'args': args, 'id': tc['id']})
        return texts, calls

# ═══════════════════════════════════════════════════════════════════════════════
# Agentic loop
# ═══════════════════════════════════════════════════════════════════════════════

def run(task: str, provider_name: str = 'auto') -> str:
    # ── Select provider ───────────────────────────────────────────────────────
    if provider_name == 'auto':
        if GEMINI_KEY:       provider_name = 'gemini'
        elif ANTHROPIC_KEY:  provider_name = 'claude'
        elif OPENAI_KEY:     provider_name = 'openai'
        else:
            print(red('\n  No API key found. Set one of:'))
            print('    GEMINI_API_KEY     (free) https://aistudio.google.com/app/apikey')
            print('    ANTHROPIC_API_KEY         https://console.anthropic.com/')
            print('    OPENAI_API_KEY            https://platform.openai.com/api-keys')
            print('\n  Add to .env in the project root.\n')
            sys.exit(1)

    if   provider_name in ('gemini',):      ai = GeminiProvider(GEMINI_KEY)
    elif provider_name in ('claude', 'anthropic'): ai = ClaudeProvider(ANTHROPIC_KEY)
    elif provider_name in ('openai', 'gpt'): ai = OpenAIProvider(OPENAI_KEY)
    else:
        print(red(f'Unknown provider: {provider_name}')); sys.exit(1)

    # ── Banner ────────────────────────────────────────────────────────────────
    bar = '─' * 68
    print(f'\n{bold("╭" + bar + "╮")}')
    print(bold('│') + cyan(f'  Devin AGI  v4.0.0  ·  {ai.name} / {ai.model}') +
          ' ' * (68 - 26 - len(ai.name) - len(ai.model)) + bold('│'))
    print(bold('│') + dim(f'  {datetime.now():%Y-%m-%d %H:%M:%S}') + ' ' * 50 + bold('│'))
    print(bold('╰' + bar + '╯'))
    print(f'\n{cyan("Task:")} {task}\n{bold(bar)}')

    # ── Loop ──────────────────────────────────────────────────────────────────
    MAX = 40
    um, tr = task, None

    for step in range(1, MAX + 1):
        print(f'\n{dim(f"[step {step}/{MAX}]")}', end='', flush=True)

        try:
            texts, calls = ai.call(user_msg=um, tool_results=tr)
        except RuntimeError as e:
            print(red(f'\n  Provider error: {e}'))
            break
        um, tr = None, None

        for t in texts:
            t = re.sub(r'^\s*\(acting\)\s*', '', t).strip()
            if t:
                print(f'\n{bold("Devin:")} {t}')

        if not calls:
            final = '\n'.join(texts).strip()
            print(f'\n{bold("═"*68)}\n{bold("  ANSWER")}\n{bold("═"*68)}\n{final}\n{bold("═"*68)}')
            return final

        results: List[dict] = []
        done = False

        for tc in calls:
            name, args, tc_id = tc['name'], tc.get('args', {}), tc.get('id', f't{step}')

            # Pretty print tool call
            arg_str = ', '.join(f'{k}={repr(str(v))[:60]}' for k, v in args.items())
            print(f'\n  {cyan("●")} {bold(name)}({arg_str})')

            if name == 'task_complete':
                final = args.get('result', 'Done.')
                print(f'\n{bold("═"*68)}\n{bold("  TASK COMPLETE")}\n{bold("═"*68)}')
                print(final)
                print(f'\n  {green("✓")} {step} steps · {ai.name} ({ai.model})')
                print(bold('═' * 68))
                return final

            # Execute and show result
            output = TOOL_REGISTRY.get(name, lambda **kw: f'No tool: {name}')(**args)
            disp = output if len(str(output)) <= 500 else str(output)[:500] + f'…({len(str(output))} chars)'
            print(f'     {dim("↳")} {disp}')
            results.append({'name': name, 'id': tc_id, 'output': str(output)[:6000]})

        tr = results

    print(red(f'\n  Reached {MAX}-step limit.'))
    return 'Max steps reached.'

# ── CLI ───────────────────────────────────────────────────────────────────────

DEFAULT_TASK = (
    "Search for today's top news headlines. "
    "For each headline: fetch the original article, verify the source is a credible outlet "
    "(Reuters, BBC, AP, CNN, Guardian, etc.), check whether the article text actually "
    "supports the headline claim, and decide: REAL or FAKE. "
    "Produce a formatted final report with each headline, its URL, your verdict, and evidence."
)

if __name__ == '__main__':
    argv = sys.argv[1:]
    provider = 'auto'
    task = DEFAULT_TASK

    if argv and argv[0] == '--provider' and len(argv) >= 2:
        provider = argv[1]
        task = ' '.join(argv[2:]) if len(argv) > 2 else DEFAULT_TASK
    elif argv:
        task = ' '.join(argv)

    run(task, provider)
