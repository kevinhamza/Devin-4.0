"""
modules/ollama_provider.py — Devin's brain: whatever model Ollama serves on localhost.

No API key and no SDK: plain HTTP to OLLAMA_BASE_URL (default http://localhost:11434).

    from modules import ollama_provider as llm
    llm.pick_model()                         # best installed model
    llm.supports_vision('qwen2.5vl:3b')      # can it look at screenshots?
    llm.chat([{'role': 'user', 'content': 'hi'}])['content']
    llm.chat_json(messages, schema)          # reply guaranteed to match a JSON schema
    llm.chat_text(messages, until=done)      # short free text, cut off as soon as it is complete
    llm.pick_agent_model()                   # the model that operates the computer (can see)
    for piece in llm.stream_chat(messages): ...

Environment:
    OLLAMA_BASE_URL   server address
    OLLAMA_MODEL      model to use (otherwise the most capable installed one)
    DEVIN_AGENT_MODEL model that operates the computer (otherwise a model that can see)
    DEVIN_NUM_CTX     context window to request (default 4096)
"""
from __future__ import annotations

import base64
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Generator, Iterable, List, Optional, Tuple


class OllamaError(RuntimeError):
    pass


def _base() -> str:
    return (os.environ.get('OLLAMA_BASE_URL') or 'http://localhost:11434').rstrip('/')


def _num_ctx() -> int:
    try:
        return max(2048, int(os.environ.get('DEVIN_NUM_CTX', '4096')))
    except ValueError:
        return 8192


def _request(path: str, body: Optional[dict] = None, timeout: float = 600):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(_base() + path, data=data,
                                 headers={'Content-Type': 'application/json'} if data else {})
    try:
        return urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.HTTPError as e:
        detail = e.read().decode('utf-8', 'replace')[:400]
        try:
            detail = json.loads(detail).get('error', detail)
        except Exception:
            pass
        raise OllamaError(f'Ollama: {detail}') from e
    except (urllib.error.URLError, OSError) as e:
        raise OllamaError(f'cannot reach Ollama at {_base()} ({getattr(e, "reason", e)}) — '
                          f'start it with: ollama serve') from e


# ── Models ────────────────────────────────────────────────────────────────────

_info_cache: Dict[str, Dict[str, Any]] = {}


def is_available() -> bool:
    """True when Ollama answers and has at least one model."""
    try:
        return bool(list_models())
    except Exception:
        return False


def _tags() -> List[Dict[str, Any]]:
    with _request('/api/tags', timeout=5) as r:
        return json.loads(r.read()).get('models', [])


def list_models() -> List[str]:
    try:
        return [m['name'] for m in _tags()]
    except OllamaError:
        return []


def _param_count(size: str) -> float:
    """'494.03M' → 0.494, '7.6B' → 7.6 (billions of parameters)."""
    m = re.match(r'([\d.]+)\s*([KMBT]?)', str(size).upper())
    if not m:
        return 0.0
    return float(m.group(1)) * {'K': 1e-6, 'M': 1e-3, 'B': 1.0, 'T': 1e3, '': 1e-9}[m.group(2)]


def model_info(model: str) -> Dict[str, Any]:
    """{'capabilities': [...], 'params_b': float, 'context': int, 'family': str}"""
    if model in _info_cache:
        return _info_cache[model]
    info: Dict[str, Any] = {'capabilities': [], 'params_b': 0.0, 'context': 0, 'family': '',
                            'has_system': True}
    try:
        with _request('/api/show', {'model': model}, timeout=10) as r:
            d = json.loads(r.read())
        details = d.get('details') or {}
        info['capabilities'] = list(d.get('capabilities') or [])
        info['params_b'] = _param_count(details.get('parameter_size', ''))
        info['family'] = details.get('family', '')
        # Some small models have a prompt template with no place for instructions at all.
        template = d.get('template') or ''
        if template and '.System' not in template and '.Messages' not in template:
            info['has_system'] = False
        for k, v in (d.get('model_info') or {}).items():
            if k.endswith('.context_length'):
                info['context'] = int(v)
    except Exception:
        pass
    _info_cache[model] = info
    return info


def supports_vision(model: Optional[str] = None) -> bool:
    return 'vision' in model_info(model or pick_model())['capabilities']


def supports_tools(model: Optional[str] = None) -> bool:
    return 'tools' in model_info(model or pick_model())['capabilities']


def supports_thinking(model: Optional[str] = None) -> bool:
    return 'thinking' in model_info(model or pick_model())['capabilities']


def pick_model(need_vision: bool = False) -> str:
    """The model Devin should use: OLLAMA_MODEL when installed, else the most capable one."""
    installed = list_models()
    want = (os.environ.get('OLLAMA_MODEL') or '').strip()
    if want:
        for name in installed:
            if name == want or name.split(':')[0] == want or name == want + ':latest':
                if not need_vision or supports_vision(name):
                    return name
        if not installed:
            return want
    if not installed:
        return want or 'qwen2.5:0.5b'
    chat_models = [m for m in installed if 'completion' in (model_info(m)['capabilities'] or ['completion'])]
    pool = [m for m in chat_models if supports_vision(m)] if need_vision else chat_models
    if not pool:
        pool = chat_models or installed
    return max(pool, key=lambda m: (supports_vision(m), model_info(m)['params_b']))


def _best_model() -> str:  # old name, still imported elsewhere
    return pick_model()


def pick_agent_model() -> str:
    """The model that operates the computer.

    DEVIN_AGENT_MODEL when set. Otherwise the model from `pick_model()` — unless that one
    cannot see screenshots and an installed model can: looking at the screen is the job,
    so the seeing model does it and the other one is left for conversation.
    """
    installed = list_models()
    want = (os.environ.get('DEVIN_AGENT_MODEL') or '').strip()
    if want:
        for name in installed:
            if name == want or name.split(':')[0] == want or name == want + ':latest':
                return name
    chosen = pick_model()
    if not installed or supports_vision(chosen):
        return chosen
    seeing = [m for m in installed if supports_vision(m)
              and 'completion' in (model_info(m)['capabilities'] or ['completion'])]
    return max(seeing, key=lambda m: model_info(m)['params_b']) if seeing else chosen


def describe_model(model: Optional[str] = None) -> str:
    """Short human label: 'qwen2.5:0.5b · 0.5B · text-only'."""
    model = model or pick_model()
    info = model_info(model)
    size = f'{info["params_b"]:.1f}B' if info['params_b'] >= 1 else f'{info["params_b"] * 1000:.0f}M'
    eyes = 'vision' if 'vision' in info['capabilities'] else 'text-only'
    return f'{model} · {size} · {eyes}' if info['params_b'] else f'{model} · {eyes}'


def pull_model(model_name: str, on_progress=None) -> bool:
    """Download a model. `on_progress(status, completed, total)` is called as it goes."""
    try:
        with _request('/api/pull', {'model': model_name}, timeout=3600) as resp:
            for raw in resp:
                try:
                    d = json.loads(raw)
                except Exception:
                    continue
                if d.get('error'):
                    raise OllamaError(d['error'])
                if on_progress:
                    on_progress(d.get('status', ''), d.get('completed', 0), d.get('total', 0))
        _info_cache.pop(model_name, None)
        return True
    except OllamaError:
        return False


# ── Chat ──────────────────────────────────────────────────────────────────────

def encode_image(image: Any, max_side: int = 0, fmt: str = 'PNG') -> str:
    """PIL image, file path or raw bytes → base64 string for the `images` field."""
    if isinstance(image, str) and os.path.exists(image):
        with open(image, 'rb') as f:
            image = f.read()
    if isinstance(image, (bytes, bytearray)):
        return base64.b64encode(bytes(image)).decode()
    if isinstance(image, str):
        return image  # already base64
    img = image
    if max_side and max(img.size) > max_side:
        scale = max_side / max(img.size)
        img = img.resize((max(1, int(img.width * scale)), max(1, int(img.height * scale))))
    buf = io.BytesIO()
    img.save(buf, fmt)
    return base64.b64encode(buf.getvalue()).decode()


def _prepare(messages: Iterable[Dict[str, Any]], system: Optional[str],
             fold_system: bool = False) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if system and fold_system:
        # The model would never see a system message: put the instructions in the user turn.
        messages = list(messages)
        for i, m in enumerate(messages):
            if m.get('role', 'user') == 'user':
                messages[i] = dict(m, content=system + '\n\n' + (m.get('content') or ''))
                break
        system = None
    if system:
        out.append({'role': 'system', 'content': system})
    for m in messages:
        role = m.get('role', 'user')
        if role == 'system' and system:
            continue
        msg: Dict[str, Any] = {'role': role, 'content': m.get('content') or ''}
        if m.get('images'):
            msg['images'] = [encode_image(i) for i in m['images']]
        for key in ('tool_calls', 'tool_name'):
            if m.get(key):
                msg[key] = m[key]
        out.append(msg)
    return out


def _body(messages, system, model, schema, tools, temperature, max_tokens, think, stream, num_ctx=None) -> dict:
    model = model or pick_model()
    body: Dict[str, Any] = {
        'model': model,
        'messages': _prepare(messages, system, fold_system=not model_info(model)['has_system']),
        'stream': stream,
        'keep_alive': os.environ.get('OLLAMA_KEEP_ALIVE', '30m'),
        'options': {'temperature': temperature, 'num_predict': max_tokens, 'num_ctx': num_ctx or _num_ctx()},
    }
    if schema is not None:
        body['format'] = schema
    if tools:
        body['tools'] = tools
    if think is not None and supports_thinking(model):
        body['think'] = think
    return body


def chat(messages: List[Dict[str, Any]], system: Optional[str] = None, model: Optional[str] = None,
         schema: Optional[dict] = None, tools: Optional[list] = None, temperature: float = 0.2,
         max_tokens: int = 1024, think: Optional[bool] = None, timeout: float = 600,
         num_ctx: Optional[int] = None) -> Dict[str, Any]:
    """One complete reply. Messages may carry `images` (PIL images, paths or bytes).

    Returns {'content', 'thinking', 'tool_calls', 'model', 'tokens_in', 'tokens_out', 'seconds'}.
    """
    body = _body(messages, system, model, schema, tools, temperature, max_tokens, think, False, num_ctx)
    with _request('/api/chat', body, timeout=timeout) as r:
        d = json.loads(r.read())
    if d.get('error'):
        raise OllamaError(d['error'])
    msg = d.get('message') or {}
    calls = [{'name': (c.get('function') or {}).get('name', ''),
              'arguments': (c.get('function') or {}).get('arguments') or {}}
             for c in (msg.get('tool_calls') or [])]
    return {
        'content': msg.get('content') or '',
        'thinking': msg.get('thinking') or '',
        'tool_calls': calls,
        'model': body['model'],
        'tokens_in': d.get('prompt_eval_count', 0),
        'tokens_out': d.get('eval_count', 0),
        'seconds': (d.get('total_duration') or 0) / 1e9,
        # how fast this machine reads a prompt with this model (0 when the prompt was cached)
        'prompt_tps': (d.get('prompt_eval_count', 0) / (d['prompt_eval_duration'] / 1e9)
                       if d.get('prompt_eval_duration') and d.get('prompt_eval_count', 0) >= 40 else 0.0),
    }


def stream(messages: List[Dict[str, Any]], system: Optional[str] = None, model: Optional[str] = None,
           temperature: float = 0.6, max_tokens: int = 2048, think: Optional[bool] = None,
           timeout: float = 600) -> Generator[Tuple[str, str], None, Dict[str, Any]]:
    """Yield ('thinking' | 'content', text) pieces as they arrive. Returns usage stats."""
    body = _body(messages, system, model, None, None, temperature, max_tokens, think, True)
    stats: Dict[str, Any] = {'model': body['model'], 'tokens_in': 0, 'tokens_out': 0}
    with _request('/api/chat', body, timeout=timeout) as resp:
        for raw in resp:
            raw = raw.strip()
            if not raw:
                continue
            try:
                d = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if d.get('error'):
                raise OllamaError(d['error'])
            msg = d.get('message') or {}
            if msg.get('thinking'):
                yield 'thinking', msg['thinking']
            if msg.get('content'):
                yield 'content', msg['content']
            if d.get('done'):
                stats['tokens_in'] = d.get('prompt_eval_count', 0)
                stats['tokens_out'] = d.get('eval_count', 0)
                break
    return stats


def chat_text(messages: List[Dict[str, Any]], system: Optional[str] = None, model: Optional[str] = None,
              temperature: float = 0.1, max_tokens: int = 80, think: Optional[bool] = False,
              timeout: float = 600, num_ctx: Optional[int] = None, stop: Optional[List[str]] = None,
              until: Any = None) -> Dict[str, Any]:
    """A short free-text reply, read as it is written and cut off the moment it is complete.

    `until(text)` is called after every piece; when it returns True the connection is
    closed, which makes Ollama stop generating. On a slow CPU every token that is not
    written saves real seconds, and unlike `chat_json` nothing constrains the sampler —
    grammar-constrained output is several times slower on small local models.

    Returns {'content', 'thinking', 'tokens_in', 'tokens_out', 'first_token', 'prompt_tps', 'model'}.
    """
    body = _body(messages, system, model, None, None, temperature, max_tokens, think, True, num_ctx)
    if stop:
        body['options']['stop'] = list(stop)
    started = time.monotonic()
    out: Dict[str, Any] = {'content': '', 'thinking': '', 'tokens_in': 0, 'tokens_out': 0,
                           'first_token': 0.0, 'prompt_tps': 0.0, 'model': body['model']}
    pieces = 0
    with _request('/api/chat', body, timeout=timeout) as resp:
        for raw in resp:
            raw = raw.strip()
            if not raw:
                continue
            try:
                d = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if d.get('error'):
                raise OllamaError(d['error'])
            msg = d.get('message') or {}
            if msg.get('thinking'):
                out['thinking'] += msg['thinking']
            if msg.get('content'):
                if not out['first_token']:
                    out['first_token'] = time.monotonic() - started
                out['content'] += msg['content']
                pieces += 1
            if d.get('done'):
                out['tokens_in'] = d.get('prompt_eval_count', 0)
                out['tokens_out'] = d.get('eval_count', 0)
                if d.get('prompt_eval_duration') and out['tokens_in'] >= 40:
                    out['prompt_tps'] = out['tokens_in'] / (d['prompt_eval_duration'] / 1e9)
                break
            if until is not None and msg.get('content') and until(out['content']):
                break
    if not out['tokens_in']:
        # Cut off early, so Ollama never sent its counts: estimate them (about 4 characters a token).
        chars = sum(len(m.get('content') or '') for m in body['messages'])
        images = sum(len(m.get('images') or []) for m in body['messages'])
        out['tokens_in'] = chars // 4 + images * 90
        out['tokens_out'] = pieces
        if out['first_token'] > 1.0 and out['tokens_in'] >= 40:
            out['prompt_tps'] = out['tokens_in'] / out['first_token']
    out['seconds'] = time.monotonic() - started
    return out


def chat_json(messages: List[Dict[str, Any]], schema: dict, system: Optional[str] = None,
              model: Optional[str] = None, temperature: float = 0.1, max_tokens: int = 700,
              think: Optional[bool] = None, timeout: float = 600,
              num_ctx: Optional[int] = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Reply constrained to `schema` (Ollama structured outputs). Returns (object, raw reply).

    The grammar constraint makes even very small models emit valid JSON; one retry
    covers a reply cut off by the token limit.
    """
    last: Dict[str, Any] = {}
    for attempt in range(2):
        last = chat(messages, system=system, model=model, schema=schema, temperature=temperature,
                    max_tokens=max_tokens * (attempt + 1), think=think, timeout=timeout, num_ctx=num_ctx)
        text = last['content'].strip()
        try:
            return json.loads(text), last
        except json.JSONDecodeError:
            m = re.search(r'\{.*\}', text, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group(0)), last
                except json.JSONDecodeError:
                    pass
    raise OllamaError(f'model did not return valid JSON: {last.get("content", "")[:200]!r}')


# ── Older call shapes still used around the codebase ──────────────────────────

def stream_chat(messages: List[Dict[str, str]], system_prompt: Optional[str] = None,
                model: Optional[str] = None, max_tokens: int = 4096,
                temperature: float = 0.7) -> Generator[str, None, None]:
    """Yield text chunks only (no thinking)."""
    try:
        for kind, text in stream(messages, system=system_prompt, model=model,
                                 temperature=temperature, max_tokens=max_tokens):
            if kind == 'content':
                yield text
    except OllamaError as e:
        yield f'[{e}]'


def complete(messages: List[Dict[str, str]], system_prompt: Optional[str] = None,
             model: Optional[str] = None, max_tokens: int = 4096) -> str:
    try:
        return chat(messages, system=system_prompt, model=model, max_tokens=max_tokens,
                    temperature=0.7)['content']
    except OllamaError as e:
        return f'[{e}]'


def _tools_to_ollama(tools: Any) -> list:
    """Accept Devin's {name: {desc, params}} registry, or a list of JSON-schema functions."""
    if isinstance(tools, list):
        out = []
        for t in tools:
            fn = t.get('function') or t
            out.append({'type': 'function', 'function': {
                'name': fn.get('name', ''), 'description': fn.get('description', ''),
                'parameters': fn.get('parameters') or {'type': 'object', 'properties': {}}}})
        return out
    out = []
    for name, info in (tools or {}).items():
        props = {p: {'type': 'string', 'description': str(d)}
                 for p, d in (info.get('params') or {}).items()}
        out.append({'type': 'function', 'function': {
            'name': name, 'description': info.get('desc') or info.get('description', ''),
            'parameters': {'type': 'object', 'properties': props, 'required': []}}})
    return out


def chat_with_tools(messages: List[Dict[str, str]], tools: Any, system_prompt: Optional[str] = None,
                    model: Optional[str] = None, max_tokens: int = 4096) -> Dict[str, Any]:
    """Native tool calling. Returns {'content', 'tool_calls': [{'name', 'arguments'}], 'done'}."""
    try:
        r = chat(messages, system=system_prompt, model=model, tools=_tools_to_ollama(tools),
                 max_tokens=max_tokens, temperature=0.2)
        return {'content': r['content'], 'tool_calls': r['tool_calls'], 'done': True}
    except OllamaError as e:
        return {'content': f'[{e}]', 'tool_calls': [], 'done': True}


class OllamaProvider:
    """Object form, for callers that expect a provider instance."""

    name = 'ollama'

    def __init__(self, model: Optional[str] = None):
        self._model = model

    @property
    def model(self) -> str:
        return self._model or pick_model()

    def is_available(self) -> bool:
        return is_available()

    available = is_available

    def stream(self, messages, system: str = ''):
        return stream_chat(messages, system_prompt=system or None, model=self.model)

    def complete(self, messages, system: str = '') -> str:
        return complete(messages, system_prompt=system or None, model=self.model)

    def chat_with_tools(self, messages, system: str = '', tools: Any = None) -> Tuple[str, List[Dict]]:
        r = chat_with_tools(messages, tools or [], system_prompt=system or None, model=self.model)
        return r['content'], [{'name': c['name'], 'input': c['arguments']} for c in r['tool_calls']]


# One module object no matter which name it was imported under (one desktop session).
for _alias in ('ollama_provider', 'modules.ollama_provider'):
    sys.modules.setdefault(_alias, sys.modules[__name__])
