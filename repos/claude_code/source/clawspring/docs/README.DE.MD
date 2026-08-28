[English](https://github.com/SafeRL-Lab/nano-claude-code/blob/main/README.md) | [中文](https://github.com/SafeRL-Lab/nano-claude-code/blob/main/docs/README.CN.MD)  |[한국어](https://github.com/SafeRL-Lab/nano-claude-code/blob/main/docs/README.KO.MD) | [日本語](https://github.com/SafeRL-Lab/nano-claude-code/blob/main/docs/README.JP.MD) | Deutsch | [Português](https://github.com/SafeRL-Lab/nano-claude-code/blob/main/docs/README.ES.MD)

<div align="center">
  <a href="[https://github.com/SafeRL-Lab/Robust-Gymnasium](https://github.com/SafeRL-Lab/nano-claude-code)">
    <img src="https://github.com/SafeRL-Lab/nano-claude-code/blob/main/docs/logo-v1.png" alt="Logo" width="280"> 
  </a>

<h1 align="center" style="font-size: 30px;"><strong><em>Nano Claude Code</em></strong>: Eine schnelle, leicht verständliche Python-Neuimplementierung von Claude Code mit Unterstützung für jedes Modell</h1>
<p align="center">
    <a href="https://github.com/chauncygu/collection-claude-code-source-code">Neueste Claude-Code-Quellen</a>
    ·
    <a href="https://github.com/SafeRL-Lab/nano-claude-code/issues">Issues</a>
  ·
    <a href="https://deepwiki.com/SafeRL-Lab/nano-claude-code">Kurze Einführung</a>
  </p>
</div>

<div align=center>
 <img src="https://github.com/SafeRL-Lab/nano-claude-code/blob/main/docs/demo.gif" width="850"/> 
</div>

---

## 🔥🔥🔥 Neuigkeiten (Pazifikzeit)
- 03. Apr 2026, 18:00: **v3.03** — Task-Management-System (`task/`): `TaskCreate` / `TaskUpdate` / `TaskGet` / `TaskList`, fortlaufende IDs, Abhängigkeitskanten (`blocks` / `blocked_by`), Metadaten, Persistenz in `.nano_claude/tasks.json`, thread-sicherer Store, `/tasks`-Befehl, 37 neue Tests (**~9500** Zeilen Python).
- 03. Apr 2026, 14:50: **v3.02** — Plugin-System (`plugin/`): Installieren/Deinstallieren/Aktivieren/Deaktivieren/Aktualisieren über `/plugin`, Empfehlungs-Engine (Keyword + Tags), mehrere Scopes (user/project), git-basierter Marketplace. `AskUserQuestion` erlaubt interaktive Rückfragen während einer Aufgabe (**~8500** Zeilen Python).
- 03. Apr 2026, 10:00: **v3.01** — MCP-Unterstützung: `mcp/`-Paket, stdio + SSE + HTTP, automatische Tool-Erkennung, `/mcp`, 34 neue Tests (**~7000** Zeilen Python).
- 02. Apr 2026, 12:20: **v3.0** — Multi-Agenten (`multi_agent/`), Speicher (`memory/`), Skills (`skill/`) mit eingebauten Skills, Argumentsubstitution, fork/inline-Ausführung, KI-Speichersuche, git-worktree-Isolation, Agententypen (**~5000** Zeilen Python).
- 02. Apr 2026, 10:00: **v2.0** — Kontextkompression, Speicher, Sub-Agenten, Skills, Diff-Ansicht, Tool-Plugin-System.
- 01. Apr 2026, 13:47: Unterstützung für VLLM-Inferenz.
- 01. Apr 2026, 11:30: Unterstützung für weitere Closed-Source- und Open-Source-Modelle: Claude, GPT, Gemini, Kimi, Qwen, Zhipu, DeepSeek sowie lokale Modelle via Ollama oder beliebige OpenAI-kompatible Endpunkte.
- 01. Apr 2026, 09:50: Unterstützung für weitere Closed-Source-Modelle: Claude, GPT, Gemini.
- 01. Apr 2026, 08:23: Erste Version von Nano Claude Code veröffentlicht.

---

# Nano Claude Code

Nano Claude Code ist eine **leichte** und **einfach zu nutzende** Python-Neuimplementierung von Claude Code, die **jedes Modell** unterstützt, darunter Claude, GPT, Gemini, Kimi, Qwen, Zhipu, DeepSeek sowie lokale Open-Source-Modelle über Ollama oder beliebige OpenAI-kompatible Endpunkte.

---

## Inhalt
- [Warum Nano Claude Code](#warum-nano-claude-code)
- [Funktionen](#funktionen)
- [Unterstützte Modelle](#unterstützte-modelle)
- [Installation](#installation)
- [Verwendung: Closed-Source-API-Modelle](#verwendung-closed-source-api-modelle)
- [Verwendung: Open-Source-Modelle (lokal)](#verwendung-open-source-modelle-lokal)
- [Format von Modellnamen](#format-von-modellnamen)
- [CLI-Referenz](#cli-referenz)
- [Slash-Befehle (REPL)](#slash-befehle-repl)
- [API-Keys konfigurieren](#api-keys-konfigurieren)
- [Berechtigungssystem](#berechtigungssystem)
- [Eingebaute Tools](#eingebaute-tools)
- [Memory](#memory)
- [Skills](#skills)
- [Sub-Agenten](#sub-agenten)
- [MCP](#mcp)
- [Plugin-System](#plugin-system)
- [AskUserQuestion-Tool](#askuserquestion-tool)
- [Task Management](#task-management)
- [Kontextkompression](#kontextkompression)
- [Diff-Ansicht](#diff-ansicht)
- [CLAUDE.md-Unterstützung](#claudemd-unterstützung)
- [Sitzungsverwaltung](#sitzungsverwaltung)
- [Projektstruktur](#projektstruktur)
- [FAQ](#faq)

## Warum Nano Claude Code

Claude Code ist ein leistungsstarker, produktionsreifer KI-Coding-Assistent – aber der Quellcode ist ein kompiliertes 12-MB-TypeScript/Node.js-Bundle (ca. 1300 Dateien, ca. 283K Zeilen). Er ist eng an die Anthropic-API gekoppelt, schwer anzupassen und praktisch nicht mit lokalen oder alternativen Modellen nutzbar.

**Nano Claude Code** implementiert dieselbe Kernschleife in etwa 10K Zeilen gut lesbarem Python neu. Alles Wichtige bleibt erhalten, Unnötiges wird weggelassen. Eine ausführlichere Analyse gibt es hier: [Englische Version](https://github.com/SafeRL-Lab/nano-claude-code/blob/main/docs/comparison_claude_code_vs_nano_v3.03_en.md) und [Chinesische Version](https://github.com/SafeRL-Lab/nano-claude-code/blob/main/docs/comparison_claude_code_vs_nano_v3.03_cn.md)

### Auf einen Blick

| Dimension | Claude Code (TypeScript) | Nano Claude Code (Python) |
|---|---|---|
| Sprache | TypeScript + React/Ink | Python 3.8+ |
| Quelldateien | ~1.332 TS/TSX-Dateien | 51 Python-Dateien |
| Codezeilen | ~283K | ~10.2K |
| Eingebaute Tools | 44+ | 21 |
| Slash-Befehle | 88 | 17 |
| Modellanbieter | nur Anthropic | 7+ (Anthropic · OpenAI · Gemini · Kimi · Qwen · DeepSeek · Ollama · …) |
| Lokale Modelle | Nein | Ja — Ollama, LM Studio, vLLM, OpenAI-kompatible Endpunkte |
| Build-Schritt nötig | Ja | Nein |
| Laufzeit-Erweiterbarkeit | Geschlossen | Offen |
| Task-Dependency-Graph | Nein | Ja |

### Wo Claude Code stärker ist

- **UI-Qualität** — React/Ink mit Streaming-Rendering, feingranularer Diff-Visualisierung und Dialogsystemen
- **Tool-Breite** — mehr als 44 Tools
- **Enterprise-Features** — MDM, Team-Permissions, OAuth, Keychain, Feature Flags
- **KI-gesteuerte Memory-Extraktion** — `extractMemories`
- **Produktionszuverlässigkeit** — ein verteilbares `cli.js`, umfangreiche Tests, versionierte Releases

### Wo Nano Claude Code stärker ist

- **Multi-Provider** — Wechsel zwischen Claude, GPT-4o, Gemini 2.5 Pro, DeepSeek, Qwen oder lokalen Llama-Modellen über `--model` oder `/model`
- **Lokale Modelle** — vollständig offline mit Ollama, LM Studio oder vLLM
- **Lesbarer Quellcode** — die gesamte Agent-Schleife umfasst 174 Zeilen in `agent.py`
- **Kein Build** — `pip install -r requirements.txt` und direkt loslegen
- **Dynamische Erweiterbarkeit** — Tools zur Laufzeit registrieren, Skill-Pakete installieren, MCP-Server anbinden
- **Task-Abhängigkeiten** — `TaskCreate` / `TaskUpdate` unterstützen strukturierte Abhängigkeiten
- **Zweistufige Kontextkompression** — Snip + KI-Zusammenfassung

### Zentrale Designunterschiede

**Agent Loop** — Nano nutzt einen Python-Generator, der typisierte Events (`TextChunk`, `ToolStart`, `ToolEnd`, `TurnDone`) per `yield` ausgibt.

**Tool Registration** — Jedes Tool ist ein `ToolDef(...)`-Dataclass. Module können bei Import `register_tool()` aufrufen. Das gleiche Muster wird für MCP, Plugins und Skills genutzt.

**Kontextkompression**

| | Claude Code | Nano Claude Code |
|---|---|---|
| Trigger | Exakte Tokenzahl | Schätzung `len / 3.5`, Auslösung bei 70 % |
| Ebene 1 | — | Snip alter Tool-Ausgaben |
| Ebene 2 | KI-Zusammenfassung | KI-Zusammenfassung älterer Turns |
| Kontrolle | Systemverwaltet | `preserve_last_n_turns` |

**Memory** — Claude Code extrahiert Wissen proaktiv. Nano verwendet ein explizites, tool-basiertes `MemorySave`, was vorhersehbarer und auditierbarer ist.

### Für wen eignet sich Nano Claude Code?

- Entwickler, die **lokale oder nicht-Anthropic-Modelle** als Coding-Assistenten verwenden möchten
- Forschende, die verstehen möchten, **wie agentische Coding-Assistenten funktionieren**
- Teams, die eine **gut hackbare Basis** für eigene Tools, Policies oder Agententypen brauchen
- Alle, die Claude-Code-ähnliche Produktivität **ohne Node.js-Buildkette** möchten

---

## Funktionen

| Funktion | Details |
|---|---|
| Multi-Provider | Anthropic · OpenAI · Gemini · Kimi · Qwen · Zhipu · DeepSeek · Ollama · LM Studio · Custom Endpoint |
| Interaktive REPL | readline-History, Tab-Vervollständigung |
| Agent Loop | Streaming API + automatische Tool-Nutzung |
| 21 eingebaute Tools | Read, Write, Edit, Bash, Glob, Grep, WebFetch, WebSearch, MemorySave, MemoryDelete, MemorySearch, MemoryList, Agent, SendMessage, CheckAgentResult, ListAgentTasks, ListAgentTypes, Skill, SkillList, AskUserQuestion |
| MCP-Integration | Beliebige MCP-Server (stdio/SSE/HTTP) anschließen |
| Plugin-System | Installieren/Deinstallieren/Aktivieren/Deaktivieren/Aktualisieren von Plugins |
| AskUserQuestion | Rückfragen mitten in der Aufgabe |
| Task Management | TaskCreate/Update/Get/List, IDs, Abhängigkeiten, Metadaten |
| Diff-Ansicht | Git-artige Diff-Anzeige |
| Kontextkompression | Automatische Verdichtung langer Gespräche |
| Persistenter Speicher | User- und Projekt-Scope |
| Multi-Agent | Typisierte Sub-Agenten, Worktree-Isolation |
| Skills | Eingebaute und eigene Markdown-Skills |
| Permission-System | `auto` / `accept-all` / `manual` |
| Session-Persistenz | Speichern/Laden von Sitzungen |
| Kosten-Tracking | Token-Verbrauch + geschätzte USD-Kosten |
| Nicht-interaktiver Modus | `--print` für Skripte / CI |

---

## Unterstützte Modelle

### Closed Source (API)

Die folgende Tabelle bleibt aus Genauigkeitsgründen nahe am Original:

| Provider | Model | Context | Strengths | API Key Env |
|---|---|---|---|---|
| **Anthropic** | `claude-opus-4-6` | 200k | Most capable, best for complex reasoning | `ANTHROPIC_API_KEY` |
| **Anthropic** | `claude-sonnet-4-6` | 200k | Balanced speed & quality | `ANTHROPIC_API_KEY` |
| **Anthropic** | `claude-haiku-4-5-20251001` | 200k | Fast, cost-efficient | `ANTHROPIC_API_KEY` |
| **OpenAI** | `gpt-4o` | 128k | Strong multimodal & coding | `OPENAI_API_KEY` |
| **OpenAI** | `gpt-4o-mini` | 128k | Fast, cheap | `OPENAI_API_KEY` |
| **OpenAI** | `o3-mini` | 200k | Strong reasoning | `OPENAI_API_KEY` |
| **OpenAI** | `o1` | 200k | Advanced reasoning | `OPENAI_API_KEY` |
| **Google** | `gemini-2.5-pro-preview-03-25` | 1M | Long context, multimodal | `GEMINI_API_KEY` |
| **Google** | `gemini-2.0-flash` | 1M | Fast, large context | `GEMINI_API_KEY` |
| **Google** | `gemini-1.5-pro` | 2M | Largest context window | `GEMINI_API_KEY` |
| **Moonshot (Kimi)** | `moonshot-v1-8k` | 8k | Chinese & English | `MOONSHOT_API_KEY` |
| **Moonshot (Kimi)** | `moonshot-v1-32k` | 32k | Chinese & English | `MOONSHOT_API_KEY` |
| **Moonshot (Kimi)** | `moonshot-v1-128k` | 128k | Long context | `MOONSHOT_API_KEY` |
| **Alibaba (Qwen)** | `qwen-max` | 32k | Best Qwen quality | `DASHSCOPE_API_KEY` |
| **Alibaba (Qwen)** | `qwen-plus` | 128k | Balanced | `DASHSCOPE_API_KEY` |
| **Alibaba (Qwen)** | `qwen-turbo` | 1M | Fast, cheap | `DASHSCOPE_API_KEY` |
| **Alibaba (Qwen)** | `qwq-32b` | 32k | Strong reasoning | `DASHSCOPE_API_KEY` |
| **Zhipu (GLM)** | `glm-4-plus` | 128k | Best GLM quality | `ZHIPU_API_KEY` |
| **Zhipu (GLM)** | `glm-4` | 128k | General purpose | `ZHIPU_API_KEY` |
| **Zhipu (GLM)** | `glm-4-flash` | 128k | Free tier available | `ZHIPU_API_KEY` |
| **DeepSeek** | `deepseek-chat` | 64k | Strong coding | `DEEPSEEK_API_KEY` |
| **DeepSeek** | `deepseek-reasoner` | 64k | Chain-of-thought reasoning | `DEEPSEEK_API_KEY` |

### Open Source (lokal via Ollama)

| Modell | Größe | Stärke | Pull-Befehl |
|---|---|---|---|
| `llama3.3` | 70B | Allgemein, starke Reasoning-Fähigkeiten | `ollama pull llama3.3` |
| `llama3.2` | 3B / 11B | Leichtgewichtig | `ollama pull llama3.2` |
| `qwen2.5-coder` | 7B / 32B | **Am besten für Coding** | `ollama pull qwen2.5-coder` |
| `qwen2.5` | 7B / 72B | Chinesisch & Englisch | `ollama pull qwen2.5` |
| `deepseek-r1` | 7B–70B | Reasoning, Mathematik | `ollama pull deepseek-r1` |
| `deepseek-coder-v2` | 16B | Coding | `ollama pull deepseek-coder-v2` |
| `mistral` | 7B | Schnell, effizient | `ollama pull mistral` |
| `mixtral` | 8x7B | Starkes MoE-Modell | `ollama pull mixtral` |
| `phi4` | 14B | Microsoft, starkes Reasoning | `ollama pull phi4` |
| `gemma3` | 4B / 12B / 27B | Offenes Google-Modell | `ollama pull gemma3` |
| `codellama` | 7B / 34B | Codegenerierung | `ollama pull codellama` |

> **Hinweis:** Tool Calling benötigt ein Modell mit Function Calling. Empfohlen: `qwen2.5-coder`, `llama3.3`, `mistral`, `phi4`.

---

## Installation

```bash
git clone <repo-url>
cd nano_claude_code

pip install -r requirements.txt
pip install anthropic openai httpx rich
```

---

## Verwendung: Closed-Source-API-Modelle

### Anthropic Claude

```bash
export ANTHROPIC_API_KEY=sk-ant-api03-...

python nano_claude.py
python nano_claude.py --model claude-sonnet-4-6
python nano_claude.py --model claude-haiku-4-5-20251001
python nano_claude.py --model claude-opus-4-6 --thinking --verbose
```

### OpenAI GPT

```bash
export OPENAI_API_KEY=sk-...

python nano_claude.py --model gpt-4o
python nano_claude.py --model gpt-4o-mini
python nano_claude.py --model gpt-4.1-mini
python nano_claude.py --model o3-mini
```

### Google Gemini

```bash
export GEMINI_API_KEY=AIza...

python nano_claude.py --model gemini/gemini-2.0-flash
python nano_claude.py --model gemini/gemini-1.5-pro
python nano_claude.py --model gemini/gemini-2.5-pro-preview-03-25
```

### Kimi, Qwen, Zhipu, DeepSeek

Die Nutzung entspricht dem Original-README und verwendet die jeweiligen Umgebungsvariablen:
`MOONSHOT_API_KEY`, `DASHSCOPE_API_KEY`, `ZHIPU_API_KEY`, `DEEPSEEK_API_KEY`.

---

## Verwendung: Open-Source-Modelle (lokal)

### Option A — Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5-coder
ollama pull llama3.3
ollama serve

python nano_claude.py --model ollama/qwen2.5-coder
python nano_claude.py --model ollama/llama3.3
```

### Option B — LM Studio

```bash
python nano_claude.py --model lmstudio/<model-name>
```

### Option C — vLLM / Self-Hosted OpenAI-Compatible Server

```bash
export CUSTOM_BASE_URL=http://localhost:8000/v1
export CUSTOM_API_KEY=none
python nano_claude.py --model custom/Qwen/Qwen2.5-Coder-7B-Instruct
```

---

## Format von Modellnamen

Unterstützte Formen:

```bash
python nano_claude.py --model gpt-4o
python nano_claude.py --model ollama/qwen2.5-coder
python nano_claude.py --model kimi:moonshot-v1-32k
```

Automatische Erkennung:
- `claude-` → anthropic
- `gpt-`, `o1`, `o3` → openai
- `gemini-` → gemini
- `moonshot-`, `kimi-` → kimi
- `qwen`, `qwq-` → qwen
- `glm-` → zhipu
- `deepseek-` → deepseek
- `llama`, `mistral`, `phi`, `gemma`, `mixtral`, `codellama` → ollama

---

## CLI-Referenz

```text
python nano_claude.py [OPTIONS] [PROMPT]

-p, --print
-m, --model MODEL
--accept-all
--verbose
--thinking
--version
-h, --help
```

Beispiele:
```bash
python nano_claude.py
python nano_claude.py --model gpt-4o
python nano_claude.py --accept-all --print "Initialize a Python project with pyproject.toml"
python nano_claude.py --thinking --verbose
```

---

## Slash-Befehle (REPL)

Wichtige Befehle:
`/help`, `/clear`, `/model`, `/config`, `/save`, `/load`, `/history`, `/context`, `/cost`, `/verbose`, `/thinking`, `/permissions`, `/cwd`, `/memory`, `/skills`, `/agents`, `/mcp`, `/exit`, `/quit`

---

## API-Keys konfigurieren

### Methode 1: Umgebungsvariablen

```bash
export ANTHROPIC_API_KEY=...
export OPENAI_API_KEY=...
export GEMINI_API_KEY=...
export MOONSHOT_API_KEY=...
export DASHSCOPE_API_KEY=...
export ZHIPU_API_KEY=...
export DEEPSEEK_API_KEY=...
```

### Methode 2: In der REPL

```text
/config anthropic_api_key=...
/config openai_api_key=...
```

### Methode 3: Direkt in `~/.nano_claude/config.json`

```json
{
  "model": "qwen/qwen-max",
  "max_tokens": 8192,
  "permission_mode": "auto"
}
```

---

## Berechtigungssystem

| Modus | Verhalten |
|---|---|
| `auto` | Leseoperationen immer erlaubt; Nachfrage bei Bash und Schreiboperationen |
| `accept-all` | Nie nachfragen |
| `manual` | Vor jeder Aktion nachfragen |

---

## Eingebaute Tools

### Kern-Tools
`Read`, `Write`, `Edit`, `Bash`, `Glob`, `Grep`, `WebFetch`, `WebSearch`

### Memory-Tools
`MemorySave`, `MemoryDelete`, `MemorySearch`, `MemoryList`

### Sub-Agent-Tools
`Agent`, `SendMessage`, `CheckAgentResult`, `ListAgentTasks`, `ListAgentTypes`

### Skill-Tools
`Skill`, `SkillList`

### MCP-Tools
Werden automatisch als `mcp__<server>__<tool>` registriert.

---

## Memory

Memory wird als Markdown gespeichert:
- User-Scope: `~/.nano_claude/memory/`
- Project-Scope: `.nano_claude/memory/`

Typen:
- `user`
- `feedback`
- `project`
- `reference`

`MEMORY.md` wird automatisch neu aufgebaut und in den System-Prompt injiziert.

---

## Skills

Eingebaute Skills:
- `/commit`
- `/review [PR]`

Eigene Skills können als Markdown-Dateien in `~/.nano_claude/skills/` oder `./.nano_claude/skills/` abgelegt werden.

---

## Sub-Agenten

Eingebaute Typen:
- `general-purpose`
- `coder`
- `reviewer`
- `researcher`
- `tester`

Unterstützt Hintergrundmodus, git-worktree-Isolation und benutzerdefinierte Agententypen.

---

## MCP

Beispiel-Konfiguration:

```json
{
  "mcpServers": {
    "git": {
      "type": "stdio",
      "command": "uvx",
      "args": ["mcp-server-git"]
    }
  }
}
```

Wichtige Befehle:
```text
/mcp
/mcp reload
/mcp add git uvx mcp-server-git
/mcp remove git
```

---

## Plugin-System

```bash
/plugin install my-plugin@https://github.com/user/my-plugin
/plugin enable my-plugin
/plugin disable my-plugin
/plugin update my-plugin
/plugin uninstall my-plugin
/plugin recommend
```

---

## AskUserQuestion-Tool

Claude kann eine Aufgabe pausieren und interaktiv eine Rückfrage stellen:

```json
{
  "tool": "AskUserQuestion",
  "question": "Which database should I use?",
  "options": [
    {"label": "SQLite", "description": "Simple, file-based"},
    {"label": "PostgreSQL", "description": "Full-featured, requires server"}
  ],
  "allow_freetext": true
}
```

---

## Task Management

Verfügbare Tools:
- `TaskCreate`
- `TaskUpdate`
- `TaskGet`
- `TaskList`

REPL:
```text
/tasks
/tasks create <subject>
/tasks start <id>
/tasks done <id>
/tasks cancel <id>
/tasks delete <id>
/tasks get <id>
/tasks clear
```

---

## Kontextkompression

Zwei Ebenen:
1. **Snip** — alte Tool-Ausgaben werden abgeschnitten
2. **Auto-compact** — bei mehr als 70 % des Kontextlimits werden ältere Turns zusammengefasst

---

## Diff-Ansicht

```diff
--- a/config.py
+++ b/config.py
@@ -12,7 +12,7 @@
     "model": "claude-opus-4-6",
-    "max_tokens": 8192,
+    "max_tokens": 16384,
```

---

## CLAUDE.md-Unterstützung

Unterstützte Orte:
```text
~/.claude/CLAUDE.md
/your/project/CLAUDE.md
```

---

## Sitzungsverwaltung

```bash
/save
/save debug_auth_bug
/load
/load debug_auth_bug
```

---

## Projektstruktur

```text
nano_claude_code/
├── nano_claude.py
├── agent.py
├── providers.py
├── tools.py
├── tool_registry.py
├── compaction.py
├── context.py
├── config.py
├── multi_agent/
├── memory/
├── skill/
├── mcp/
└── tests/
```

---

## FAQ

**Wie füge ich einen MCP-Server hinzu?**
```text
/mcp add git uvx mcp-server-git
```

**Wie debugge ich einen MCP-Server?**
```text
/mcp
/mcp reload git
which uvx
uvx mcp-server-git
```

**Kann ich MCP-Server mit Authentifizierung verwenden?**
Ja, über `headers` (HTTP/SSE) oder `env` (stdio).

**Warum funktionieren Tool Calls mit meinem lokalen Ollama-Modell nicht?**
Nutze Modelle mit Function Calling, z. B. `qwen2.5-coder`, `llama3.3`, `mistral`, `phi4`.

**Wie prüfe ich die API-Kosten?**
```text
/cost
```

**Kann ich mehrere API-Keys in derselben Sitzung verwenden?**
Ja.

**Wie kann ich das Tool global als CLI nutzen?**
```bash
alias nc='python /path/to/nano_claude_code/nano_claude.py'
pip install -e .
```
