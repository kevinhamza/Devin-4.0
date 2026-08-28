[English](https://github.com/SafeRL-Lab/nano-claude-code/blob/main/README.md) | [中文](https://github.com/SafeRL-Lab/nano-claude-code/blob/main/docs/README.CN.MD)  |[한국어](https://github.com/SafeRL-Lab/nano-claude-code/blob/main/docs/README.KO.MD) | [日本語](https://github.com/SafeRL-Lab/nano-claude-code/blob/main/docs/README.JP.MD) | [Deutsch](https://github.com/SafeRL-Lab/nano-claude-code/blob/main/docs/README.DE.MD) | Português

<div align="center">
  <a href="[https://github.com/SafeRL-Lab/Robust-Gymnasium](https://github.com/SafeRL-Lab/nano-claude-code)">
    <img src="https://github.com/SafeRL-Lab/nano-claude-code/blob/main/docs/logo-v1.png" alt="Logo" width="280"> 
  </a>


<h1 align="center" style="font-size: 30px;"><strong><em>Nano Claude Code</em></strong>: Una reimplementación rápida y fácil de usar de Claude Code en Python, compatible con cualquier modelo</h1>
<p align="center">
    <a href="https://github.com/chauncygu/collection-claude-code-source-code">La fuente más reciente sobre Claude Code</a>
    ·
    <a href="https://github.com/SafeRL-Lab/nano-claude-code/issues">Issues</a>
  ·
    <a href="https://deepwiki.com/SafeRL-Lab/nano-claude-code">Introducción breve</a>

  </p>
</div>

 <div align=center>
 <img src="https://github.com/SafeRL-Lab/nano-claude-code/blob/main/docs/demo.gif" width="850"/> 
 </div>
<div align=center>
<center style="color:#000000;text-decoration:underline"> </center>
 </div>

---

## 🔥🔥🔥 Novedades (hora del Pacífico)
- 06:00 PM, 03 de abril de 2026: **v3.03** — Sistema de gestión de tareas (paquete `task/`): herramientas `TaskCreate` / `TaskUpdate` / `TaskGet` / `TaskList` con IDs secuenciales, aristas de dependencia (`blocks`/`blocked_by`), metadatos, persistencia en `.nano_claude/tasks.json`, almacenamiento seguro para hilos, comando REPL `/tasks`, 37 pruebas nuevas (**~9500** líneas de Python).
- 02:50 PM, 03 de abril de 2026: **v3.02** — Sistema de plugins (paquete `plugin/`): instalar/desinstalar/habilitar/deshabilitar/actualizar mediante CLI `/plugin`, motor de recomendación (coincidencia por palabras clave + etiquetas), múltiples ámbitos (usuario/proyecto), marketplace basado en git. Herramienta `AskUserQuestion`: preguntas interactivas al usuario en mitad de una tarea, con opciones numeradas y entrada libre (**~8500** líneas de Python).
- 10:00 AM, 03 de abril de 2026: **v3.01** — Soporte para MCP (Model Context Protocol): paquete `mcp/`, transportes stdio + SSE + HTTP, descubrimiento automático de herramientas, comando `/mcp`, 34 pruebas nuevas (**~7000** líneas de Python).
- 12:20 PM, 02 de abril de 2026: **v3.0** — Paquetes multiagente (`multi_agent/`), memoria (`memory/`), habilidades (`skill/`) con habilidades integradas, sustitución de argumentos, ejecución fork/inline, búsqueda de memoria con IA, aislamiento con git worktree, definiciones de tipos de agente (**~5000** líneas de Python), ver [actualización](https://github.com/SafeRL-Lab/nano-claude-code/blob/main/docs/update_readme_v3.0.md).
- 10:00 AM, 02 de abril de 2026: **v2.0** — Compresión de contexto, memoria, subagentes, habilidades, vista diff, sistema de plugins de herramientas (**~3400** líneas de Python).
- 01:47 PM, 01 de abril de 2026: Soporte para inferencia con VLLM (**~2000** líneas de Python).
- 11:30 AM, 01 de abril de 2026: Soporte para más modelos **cerrados** y **abiertos**: Claude, GPT, Gemini, Kimi, Qwen, Zhipu, DeepSeek, y modelos abiertos locales vía Ollama o cualquier endpoint compatible con OpenAI. (**~1700** líneas de Python).
- 09:50 AM, 01 de abril de 2026: Soporte para más modelos **cerrados**: Claude, GPT, Gemini. (**~1300** líneas de Python).
- 08:23 AM, 01 de abril de 2026: Lanzamiento de la versión inicial de Nano Claude Code (**~900 líneas** de Python).

---

# Nano Claude Code

Nano Claude Code: **una reimplementación ligera** y **fácil de usar** de Claude Code en Python, **compatible con cualquier modelo**, como Claude, GPT, Gemini, Kimi, Qwen, Zhipu, DeepSeek y modelos abiertos locales vía Ollama o cualquier endpoint compatible con OpenAI.

---

## Contenido
  * [¿Por qué Nano Claude Code?](#por-qué-nano-claude-code)
  * [Características](#características)
  * [Modelos compatibles](#modelos-compatibles)
  * [Instalación](#instalación)
  * [Uso: modelos API de código cerrado](#uso-modelos-api-de-código-cerrado)
  * [Uso: modelos de código abierto (local)](#uso-modelos-de-código-abierto-local)
  * [Formato del nombre del modelo](#formato-del-nombre-del-modelo)
  * [Referencia de la CLI](#referencia-de-la-cli)
  * [Comandos con barra (REPL)](#comandos-con-barra-repl)
  * [Configuración de claves API](#configuración-de-claves-api)
  * [Sistema de permisos](#sistema-de-permisos)
  * [Herramientas integradas](#herramientas-integradas)
  * [Memoria](#memoria)
  * [Habilidades](#habilidades)
  * [Subagentes](#subagentes)
  * [MCP (Model Context Protocol)](#mcp-model-context-protocol)
  * [Sistema de plugins](#sistema-de-plugins)
  * [Herramienta AskUserQuestion](#herramienta-askuserquestion)
  * [Gestión de tareas](#gestión-de-tareas)
  * [Compresión de contexto](#compresión-de-contexto)
  * [Vista diff](#vista-diff)
  * [Soporte para CLAUDE.md](#soporte-para-claudemd)
  * [Gestión de sesiones](#gestión-de-sesiones)
  * [Estructura del proyecto](#estructura-del-proyecto)
  * [Preguntas frecuentes](#preguntas-frecuentes)

## ¿Por qué Nano Claude Code?

Claude Code es un potente asistente de programación con IA de nivel de producción, pero su código fuente es un bundle compilado de TypeScript/Node.js de 12 MB (~1300 archivos, ~283K líneas). Está fuertemente acoplado a la API de Anthropic, es difícil de modificar e imposible de ejecutar con un modelo local o alternativo.

**Nano Claude Code** reimplementa el mismo bucle central en ~10K líneas de Python legibles, conservando todo lo que necesitas y eliminando lo que no. Aquí puedes ver un análisis más detallado (Nano Claude Code v3.03), [versión en inglés](https://github.com/SafeRL-Lab/nano-claude-code/blob/main/docs/comparison_claude_code_vs_nano_v3.03_en.md) y [versión en chino](https://github.com/SafeRL-Lab/nano-claude-code/blob/main/docs/comparison_claude_code_vs_nano_v3.03_cn.md)

### Vista rápida

| Dimensión | Claude Code (TypeScript) | Nano Claude Code (Python) |
|-----------|--------------------------|---------------------------|
| Lenguaje | TypeScript + React/Ink | Python 3.8+ |
| Archivos fuente | ~1,332 archivos TS/TSX | 51 archivos Python |
| Líneas de código | ~283K | ~10.2K |
| Herramientas integradas | 44+ | 21 |
| Comandos con barra | 88 | 17 |
| Proveedores de modelos | Solo Anthropic | 7+ (Anthropic · OpenAI · Gemini · Kimi · Qwen · DeepSeek · Ollama · …) |
| Modelos locales | No | Sí — Ollama, LM Studio, vLLM, cualquier endpoint compatible con OpenAI |
| Requiere compilación | Sí (Bun + esbuild) | No — se ejecuta directamente con `python nano_claude.py` |
| Extensibilidad en ejecución | Cerrada (en tiempo de compilación) | Abierta — `register_tool()` en tiempo de ejecución, habilidades Markdown, plugins git |
| Grafo de dependencias de tareas | No | Sí — aristas `blocks` / `blocked_by` en el paquete `task/` |

### Donde Claude Code gana

- **Calidad de interfaz** — árbol de componentes React/Ink con renderizado en streaming, visualización diff de grano fino y sistemas de diálogo.
- **Amplitud de herramientas** — 44 herramientas, incluyendo `NotebookEdit`, `LSP Diagnostics`, `RemoteTrigger`, `EnterWorktree` y más.
- **Funciones empresariales** — configuración gestionada por MDM, sincronización de permisos en equipo, OAuth, almacenamiento en keychain, flags de funciones con GrowthBook.
- **Extracción de memoria impulsada por IA** — el servicio `extractMemories` extrae conocimiento de las conversaciones de forma proactiva sin llamadas explícitas a herramientas.
- **Fiabilidad de producción** — un único `cli.js` distribuible, amplia cobertura de pruebas y lanzamientos con versiones fijadas.

### Donde Nano Claude Code gana

- **Multiproveedor** — cambia entre Claude, GPT-4o, Gemini 2.5 Pro, DeepSeek, Qwen o un Llama local con `--model` o `/model`, sin recompilar.
- **Soporte para modelos locales** — ejecución completamente offline con Ollama, LM Studio o cualquier modelo servido por vLLM.
- **Código legible** — el bucle completo del agente tiene 174 líneas (`agent.py`). Cualquier desarrollador Python puede leerlo, bifurcarlo y ampliarlo en minutos.
- **Cero compilación** — `pip install -r requirements.txt` y ya está funcionando. Los cambios surten efecto inmediatamente.
- **Extensibilidad dinámica** — registra nuevas herramientas en tiempo de ejecución con `register_tool(ToolDef(...))`, instala paquetes de habilidades desde URLs git o conecta cualquier servidor MCP.
- **Grafo de dependencias de tareas** — `TaskCreate` / `TaskUpdate` admiten aristas `blocks` / `blocked_by` para planificación estructurada de múltiples pasos (no disponible en Claude Code).
- **Compresión de contexto en dos capas** — recorte basado en reglas + resumen con IA, configurable mediante `preserve_last_n_turns`.

### Diferencias clave de diseño

**Bucle del agente** — Nano usa un generador de Python que hace `yield` de eventos tipados (`TextChunk`, `ToolStart`, `ToolEnd`, `TurnDone`). Todo el bucle es visible en un solo archivo, lo que facilita añadir hooks, renderizadores personalizados o logging.

**Registro de herramientas** — cada herramienta es un dataclass `ToolDef(name, schema, func, read_only, concurrent_safe)`. Cualquier módulo puede llamar a `register_tool()` durante la importación; los servidores MCP, plugins y habilidades usan el mismo mecanismo.

**Compresión de contexto**

| | Claude Code | Nano Claude Code |
|-|-------------|-----------------|
| Activación | Conteo exacto de tokens | Estimación `len / 3.5`, se activa al 70 % |
| Capa 1 | — | Snip: trunca salidas antiguas de herramientas (sin coste de API) |
| Capa 2 | Resumen con IA | Resumen con IA de turnos antiguos |
| Control | Gestionado por el sistema | Parámetro `preserve_last_n_turns` |

**Memoria** — el servicio `extractMemories` de Claude Code hace que el modelo saque hechos de forma proactiva. El paquete `memory/` de Nano está guiado por herramientas: el modelo llama explícitamente a `MemorySave`, lo que resulta más predecible y auditable.

### Quién debería usar Nano Claude Code

- Desarrolladores que quieran **usar un modelo local o que no sea de Anthropic** como asistente de programación.
- Investigadores que estudien **cómo funcionan los asistentes de programación agénticos** — todo el sistema cabe en una sola pantalla.
- Equipos que necesiten una **base hackeable** para añadir herramientas propietarias, políticas de permisos personalizadas o tipos de agente especializados.
- Quien quiera la productividad tipo Claude Code **sin una cadena de compilación Node.js**.

---

## Características

| Característica | Detalles |
|---|---|
| Multiproveedor | Anthropic · OpenAI · Gemini · Kimi · Qwen · Zhipu · DeepSeek · Ollama · LM Studio · Endpoint personalizado |
| REPL interactivo | Historial con readline, autocompletado con Tab para comandos con barra |
| Bucle del agente | API en streaming + bucle automático de uso de herramientas |
| 21 herramientas integradas | Read · Write · Edit · Bash · Glob · Grep · WebFetch · WebSearch · MemorySave · MemoryDelete · MemorySearch · MemoryList · Agent · SendMessage · CheckAgentResult · ListAgentTasks · ListAgentTypes · Skill · SkillList · AskUserQuestion · *(las herramientas MCP + plugins se añaden automáticamente al inicio)* |
| Integración MCP | Conecta cualquier servidor MCP (stdio/SSE/HTTP), las herramientas se registran automáticamente y Claude puede invocarlas |
| Sistema de plugins | Instalar/desinstalar/habilitar/deshabilitar/actualizar plugins desde URLs git o rutas locales; múltiples ámbitos (usuario/proyecto); motor de recomendaciones |
| AskUserQuestion | Claude puede pausarse y hacer una pregunta aclaratoria al usuario a mitad de tarea, con opciones numeradas opcionales |
| Gestión de tareas | Herramientas TaskCreate/Update/Get/List; IDs secuenciales; aristas de dependencia; metadatos; persistencia en `.nano_claude/tasks.json`; comando REPL `/tasks` |
| Vista diff | Visualización tipo git en rojo/verde para Edit y Write |
| Compresión de contexto | Compacta automáticamente conversaciones largas para mantenerse dentro de los límites del modelo |
| Memoria persistente | Memoria de doble ámbito (usuario + proyecto) con 4 tipos, búsqueda con IA, avisos de obsolescencia |
| Multiagente | Lanza subagentes tipados (coder/reviewer/researcher/…), aislamiento con git worktree, modo en segundo plano |
| Habilidades | `/commit` · `/review` integrados + habilidades Markdown personalizadas con sustitución de argumentos y ejecución fork/inline |
| Herramientas plugin | Registra herramientas personalizadas vía `tool_registry.py` |
| Sistema de permisos | Modos `auto` / `accept-all` / `manual` |
| 17 comandos con barra | `/model` · `/config` · `/save` · `/cost` · `/memory` · `/skills` · `/agents` · … |
| Inyección de contexto | Carga automáticamente `CLAUDE.md`, estado de git, cwd y memoria persistente |
| Persistencia de sesión | Guarda / carga conversaciones en `~/.nano_claude/sessions/` |
| Extended Thinking | Activar/desactivar (solo modelos Claude) |
| Seguimiento de costes | Uso de tokens + coste estimado en USD |
| Modo no interactivo | Flag `--print` para scripting / CI |

---

## Modelos compatibles

### Código cerrado (API)

| Proveedor | Modelo | Contexto | Ventajas | Variable de entorno de API key |
|---|---|---|---|---|
| **Anthropic** | `claude-opus-4-6` | 200k | El más capaz, ideal para razonamiento complejo | `ANTHROPIC_API_KEY` |
| **Anthropic** | `claude-sonnet-4-6` | 200k | Buen equilibrio entre velocidad y calidad | `ANTHROPIC_API_KEY` |
| **Anthropic** | `claude-haiku-4-5-20251001` | 200k | Rápido y rentable | `ANTHROPIC_API_KEY` |
| **OpenAI** | `gpt-4o` | 128k | Multimodalidad y programación sólidas | `OPENAI_API_KEY` |
| **OpenAI** | `gpt-4o-mini` | 128k | Rápido y barato | `OPENAI_API_KEY` |
| **OpenAI** | `o3-mini` | 200k | Buen razonamiento | `OPENAI_API_KEY` |
| **OpenAI** | `o1` | 200k | Razonamiento avanzado | `OPENAI_API_KEY` |
| **Google** | `gemini-2.5-pro-preview-03-25` | 1M | Contexto largo, multimodal | `GEMINI_API_KEY` |
| **Google** | `gemini-2.0-flash` | 1M | Rápido, gran contexto | `GEMINI_API_KEY` |
| **Google** | `gemini-1.5-pro` | 2M | Ventana de contexto más grande | `GEMINI_API_KEY` |
| **Moonshot (Kimi)** | `moonshot-v1-8k` | 8k | Chino e inglés | `MOONSHOT_API_KEY` |
| **Moonshot (Kimi)** | `moonshot-v1-32k` | 32k | Chino e inglés | `MOONSHOT_API_KEY` |
| **Moonshot (Kimi)** | `moonshot-v1-128k` | 128k | Contexto largo | `MOONSHOT_API_KEY` |
| **Alibaba (Qwen)** | `qwen-max` | 32k | Mejor calidad Qwen | `DASHSCOPE_API_KEY` |
| **Alibaba (Qwen)** | `qwen-plus` | 128k | Equilibrado | `DASHSCOPE_API_KEY` |
| **Alibaba (Qwen)** | `qwen-turbo` | 1M | Rápido y barato | `DASHSCOPE_API_KEY` |
| **Alibaba (Qwen)** | `qwq-32b` | 32k | Razonamiento fuerte | `DASHSCOPE_API_KEY` |
| **Zhipu (GLM)** | `glm-4-plus` | 128k | Mejor calidad GLM | `ZHIPU_API_KEY` |
| **Zhipu (GLM)** | `glm-4` | 128k | Propósito general | `ZHIPU_API_KEY` |
| **Zhipu (GLM)** | `glm-4-flash` | 128k | Nivel gratuito disponible | `ZHIPU_API_KEY` |
| **DeepSeek** | `deepseek-chat` | 64k | Programación sólida | `DEEPSEEK_API_KEY` |
| **DeepSeek** | `deepseek-reasoner` | 64k | Razonamiento chain-of-thought | `DEEPSEEK_API_KEY` |

### Código abierto (local vía Ollama)

| Modelo | Tamaño | Ventajas | Comando de descarga |
|---|---|---|---|
| `llama3.3` | 70B | Propósito general, razonamiento fuerte | `ollama pull llama3.3` |
| `llama3.2` | 3B / 11B | Ligero | `ollama pull llama3.2` |
| `qwen2.5-coder` | 7B / 32B | **Lo mejor para tareas de programación** | `ollama pull qwen2.5-coder` |
| `qwen2.5` | 7B / 72B | Chino e inglés | `ollama pull qwen2.5` |
| `deepseek-r1` | 7B–70B | Razonamiento, matemáticas | `ollama pull deepseek-r1` |
| `deepseek-coder-v2` | 16B | Programación | `ollama pull deepseek-coder-v2` |
| `mistral` | 7B | Rápido, eficiente | `ollama pull mistral` |
| `mixtral` | 8x7B | Modelo MoE sólido | `ollama pull mixtral` |
| `phi4` | 14B | Microsoft, razonamiento sólido | `ollama pull phi4` |
| `gemma3` | 4B / 12B / 27B | Modelo abierto de Google | `ollama pull gemma3` |
| `codellama` | 7B / 34B | Generación de código | `ollama pull codellama` |

> **Nota:** el uso de herramientas requiere un modelo compatible con function calling. Modelos locales recomendados: `qwen2.5-coder`, `llama3.3`, `mistral`, `phi4`.

---

## Instalación

```bash
git clone <repo-url>
cd nano_claude_code

pip install -r requirements.txt
# o manualmente:
pip install anthropic openai httpx rich
```

---

## Uso: modelos API de código cerrado

### Anthropic Claude

Obtén tu API key en [console.anthropic.com](https://console.anthropic.com).

```bash
export ANTHROPIC_API_KEY=sk-ant-api03-...

# Modelo por defecto (claude-opus-4-6)
python nano_claude.py

# Elegir un modelo específico
python nano_claude.py --model claude-sonnet-4-6
python nano_claude.py --model claude-haiku-4-5-20251001

# Activar Extended Thinking
python nano_claude.py --model claude-opus-4-6 --thinking --verbose
```

### OpenAI GPT

Obtén tu API key en [platform.openai.com](https://platform.openai.com).

```bash
export OPENAI_API_KEY=sk-...

python nano_claude.py --model gpt-4o
python nano_claude.py --model gpt-4o-mini
python nano_claude.py --model gpt-4.1-mini
python nano_claude.py --model o3-mini
```

### Google Gemini

Obtén tu API key en [aistudio.google.com](https://aistudio.google.com).

```bash
export GEMINI_API_KEY=AIza...

python nano_claude.py --model gemini/gemini-2.0-flash
python nano_claude.py --model gemini/gemini-1.5-pro
python nano_claude.py --model gemini/gemini-2.5-pro-preview-03-25
```

### Kimi (Moonshot AI)

Obtén tu API key en [platform.moonshot.cn](https://platform.moonshot.cn).

```bash
export MOONSHOT_API_KEY=sk-...

python nano_claude.py --model kimi/moonshot-v1-32k
python nano_claude.py --model kimi/moonshot-v1-128k
```

### Qwen (Alibaba DashScope)

Obtén tu API key en [dashscope.aliyun.com](https://dashscope.aliyun.com).

```bash
export DASHSCOPE_API_KEY=sk-...

python nano_claude.py --model qwen/Qwen3.5-Plus
python nano_claude.py --model qwen/Qwen3-MAX
python nano_claude.py --model qwen/Qwen3.5-Flash
```

### Zhipu GLM

Obtén tu API key en [open.bigmodel.cn](https://open.bigmodel.cn).

```bash
export ZHIPU_API_KEY=...

python nano_claude.py --model zhipu/glm-4-plus
python nano_claude.py --model zhipu/glm-4-flash   # nivel gratuito
```

### DeepSeek

Obtén tu API key en [platform.deepseek.com](https://platform.deepseek.com).

```bash
export DEEPSEEK_API_KEY=sk-...

python nano_claude.py --model deepseek/deepseek-chat
python nano_claude.py --model deepseek/deepseek-reasoner
```

---

## Uso: modelos de código abierto (local)

### Opción A — Ollama (recomendado)

Ollama ejecuta modelos localmente sin configuración complicada. No requiere API key.

**Paso 1: Instalar Ollama**

```bash
# macOS / Linux
curl -fsSL https://ollama.com/install.sh | sh

# O descárgalo desde https://ollama.com/download
```

**Paso 2: Descargar un modelo**

```bash
# Lo mejor para programación (recomendado)
ollama pull qwen2.5-coder          # 4.7 GB (7B)
ollama pull qwen2.5-coder:32b      # 19 GB (32B)

# Propósito general
ollama pull llama3.3               # 42 GB (70B)
ollama pull llama3.2               # 2.0 GB (3B)

# Razonamiento
ollama pull deepseek-r1            # 4.7 GB (7B)
ollama pull deepseek-r1:32b        # 19 GB (32B)

# Otros
ollama pull phi4                   # 9.1 GB (14B)
ollama pull mistral                # 4.1 GB (7B)
```

**Paso 3: Iniciar el servidor de Ollama** (en macOS se ejecuta automáticamente; en Linux ejecútalo manualmente)

```bash
ollama serve     # inicia en http://localhost:11434
```

**Paso 4: Ejecutar nano claude**

```bash
python nano_claude.py --model ollama/qwen2.5-coder
python nano_claude.py --model ollama/llama3.3
python nano_claude.py --model ollama/deepseek-r1
```

**Listar los modelos disponibles localmente:**

```bash
ollama list
```

Luego usa cualquiera de los modelos listados:

```bash
python nano_claude.py --model ollama/<model-name>
```

---

### Opción B — LM Studio

LM Studio ofrece una interfaz gráfica para descargar y ejecutar modelos, con un servidor integrado compatible con OpenAI.

**Paso 1:** Descarga [LM Studio](https://lmstudio.ai) e instálalo.

**Paso 2:** Busca y descarga un modelo dentro de LM Studio (formato GGUF).

**Paso 3:** Ve a la pestaña **Local Server** → haz clic en **Start Server** (puerto por defecto: 1234).

**Paso 4:**

```bash
python nano_claude.py --model lmstudio/<model-name>
# por ejemplo:
python nano_claude.py --model lmstudio/phi-4-GGUF
python nano_claude.py --model lmstudio/qwen2.5-coder-7b
```

El nombre del modelo debe coincidir con el que LM Studio muestra en la barra de estado del servidor.

---

### Opción C — vLLM / servidor autohospedado compatible con OpenAI

Para servidores de inferencia autohospedados (vLLM, TGI, servidor llama.cpp, etc.) que exponen una API compatible con OpenAI:

Inicio rápido para la opción C:
Paso 1: Iniciar vllm:
 ```
CUDA_VISIBLE_DEVICES=7 python -m vllm.entrypoints.openai.api_server \
      --model Qwen/Qwen2.5-Coder-7B-Instruct \
      --host 0.0.0.0 \
      --port 8000 \
      --enable-auto-tool-choice \
      --tool-call-parser hermes
```

Paso 2: Iniciar nano claude:
```
  export CUSTOM_BASE_URL=http://localhost:8000/v1
  export CUSTOM_API_KEY=none
  python nano_claude.py --model custom/Qwen/Qwen2.5-Coder-7B-Instruct
```

```bash
# Ejemplo: vLLM sirviendo Qwen2.5-Coder-32B
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-Coder-32B-Instruct \
    --port 8000

# Luego ejecuta nano claude apuntando a tu servidor:
python nano_claude.py
```

Dentro del REPL:

```
/config custom_base_url=http://localhost:8000/v1
/config custom_api_key=token-abc123    # omitir si no hay autenticación
/model custom/Qwen2.5-Coder-32B-Instruct
```

O configúralo con variables de entorno:

```bash
export CUSTOM_BASE_URL=http://localhost:8000/v1
export CUSTOM_API_KEY=token-abc123

python nano_claude.py --model custom/Qwen2.5-Coder-32B-Instruct
```

Para un servidor GPU remoto:

```bash
/config custom_base_url=http://192.168.1.100:8000/v1
/model custom/your-model-name
```

---

## Formato del nombre del modelo

Se admiten tres formatos equivalentes:

```bash
# 1. Detección automática por prefijo (funciona para modelos conocidos)
python nano_claude.py --model gpt-4o
python nano_claude.py --model gemini-2.0-flash
python nano_claude.py --model deepseek-chat

# 2. Prefijo explícito del proveedor con barra
python nano_claude.py --model ollama/qwen2.5-coder
python nano_claude.py --model kimi/moonshot-v1-128k

# 3. Prefijo explícito del proveedor con dos puntos (también funciona)
python nano_claude.py --model kimi:moonshot-v1-32k
python nano_claude.py --model qwen:qwen-max
```

**Reglas de detección automática:**

| Prefijo del modelo | Proveedor detectado |
|---|---|
| `claude-` | anthropic |
| `gpt-`, `o1`, `o3` | openai |
| `gemini-` | gemini |
| `moonshot-`, `kimi-` | kimi |
| `qwen`, `qwq-` | qwen |
| `glm-` | zhipu |
| `deepseek-` | deepseek |
| `llama`, `mistral`, `phi`, `gemma`, `mixtral`, `codellama` | ollama |

---

## Referencia de la CLI

```
python nano_claude.py [OPTIONS] [PROMPT]

Opciones:
  -p, --print          Modo no interactivo: ejecuta el prompt y sale
  -m, --model MODEL    Sobrescribe el modelo (p. ej., gpt-4o, ollama/llama3.3)
  --accept-all         Aprueba automáticamente todas las operaciones (sin solicitudes de permiso)
  --verbose            Muestra bloques de razonamiento y conteos de tokens por turno
  --thinking           Activa Extended Thinking (solo Claude)
  --version            Imprime la versión y sale
  -h, --help           Muestra la ayuda
```

**Ejemplos:**

```bash
# REPL interactivo con el modelo por defecto
python nano_claude.py

# Cambiar modelo al inicio
python nano_claude.py --model gpt-4o
python nano_claude.py -m ollama/deepseek-r1:32b

# No interactivo / scripting
python nano_claude.py --print "Write a Python fibonacci function"
python nano_claude.py -p "Explain the Rust borrow checker in 3 sentences" -m gemini/gemini-2.0-flash

# CI / automatización (sin solicitudes de permiso)
python nano_claude.py --accept-all --print "Initialize a Python project with pyproject.toml"

# Modo depuración (ver tokens + thinking)
python nano_claude.py --thinking --verbose
```

---

## Comandos con barra (REPL)

Escribe `/` y pulsa **Tab** para autocompletar.

| Comando | Descripción |
|---|---|
| `/help` | Muestra todos los comandos |
| `/clear` | Borra el historial de conversación |
| `/model` | Muestra el modelo actual + lista todos los modelos disponibles |
| `/model <name>` | Cambia de modelo (surte efecto inmediatamente) |
| `/config` | Muestra todos los valores de configuración actuales |
| `/config key=value` | Establece un valor de configuración (se guarda en disco) |
| `/save` | Guarda la sesión (nombre automático por timestamp) |
| `/save <filename>` | Guarda la sesión con un nombre específico |
| `/load` | Lista todas las sesiones guardadas |
| `/load <filename>` | Carga una sesión guardada |
| `/history` | Imprime el historial completo de la conversación |
| `/context` | Muestra el número de mensajes y una estimación de tokens |
| `/cost` | Muestra el uso de tokens y el coste estimado en USD |
| `/verbose` | Activa/desactiva el modo verbose (tokens + thinking) |
| `/thinking` | Activa/desactiva Extended Thinking (solo Claude) |
| `/permissions` | Muestra el modo de permisos actual |
| `/permissions <mode>` | Establece el modo de permisos: `auto` / `accept-all` / `manual` |
| `/cwd` | Muestra el directorio de trabajo actual |
| `/cwd <path>` | Cambia el directorio de trabajo |
| `/memory` | Lista todas las memorias persistentes |
| `/memory <query>` | Busca memorias por palabra clave |
| `/skills` | Lista las habilidades disponibles |
| `/agents` | Muestra el estado de las tareas de subagentes |
| `/mcp` | Lista los servidores MCP configurados y sus herramientas |
| `/mcp reload` | Reconecta todos los servidores MCP y actualiza las herramientas |
| `/mcp reload <name>` | Reconecta un único servidor MCP |
| `/mcp add <name> <cmd> [args]` | Añade un servidor MCP stdio a la configuración del usuario |
| `/mcp remove <name>` | Elimina un servidor de la configuración del usuario |
| `/exit` / `/quit` | Sale |

**Cambio de modelo dentro de una sesión:**

```
[myproject] ❯ /model
  Modelo actual: claude-opus-4-6  (proveedor: anthropic)

  Modelos disponibles por proveedor:
    anthropic     claude-opus-4-6, claude-sonnet-4-6, ...
    openai        gpt-4o, gpt-4o-mini, o3-mini, ...
    ollama        llama3.3, llama3.2, phi4, mistral, ...
    ...

[myproject] ❯ /model gpt-4o
  Modelo configurado en gpt-4o  (proveedor: openai)

[myproject] ❯ /model ollama/qwen2.5-coder
  Modelo configurado en ollama/qwen2.5-coder  (proveedor: ollama)
```

---

## Configuración de claves API

### Método 1: Variables de entorno (recomendado)

```bash
# Añade esto a ~/.bashrc o ~/.zshrc
export ANTHROPIC_API_KEY=sk-ant-...
export OPENAI_API_KEY=sk-...
export GEMINI_API_KEY=AIza...
export MOONSHOT_API_KEY=sk-...       # Kimi
export DASHSCOPE_API_KEY=sk-...      # Qwen
export ZHIPU_API_KEY=...             # Zhipu GLM
export DEEPSEEK_API_KEY=sk-...       # DeepSeek
```

### Método 2: Configurar dentro del REPL (persistente)

```
/config anthropic_api_key=sk-ant-...
/config openai_api_key=sk-...
/config gemini_api_key=AIza...
/config kimi_api_key=sk-...
/config qwen_api_key=sk-...
/config zhipu_api_key=...
/config deepseek_api_key=sk-...
```

Las claves se guardan en `~/.nano_claude/config.json` y se cargan automáticamente en el siguiente inicio.

### Método 3: Editar directamente el archivo de configuración

```json
// ~/.nano_claude/config.json
{
  "model": "qwen/qwen-max",
  "max_tokens": 8192,
  "permission_mode": "auto",
  "verbose": false,
  "thinking": false,
  "qwen_api_key": "sk-...",
  "kimi_api_key": "sk-...",
  "deepseek_api_key": "sk-..."
}
```

---

## Sistema de permisos

| Modo | Comportamiento |
|---|---|
| `auto` (por defecto) | Las operaciones de solo lectura siempre están permitidas. Pide confirmación antes de ejecutar comandos Bash y escribir archivos. |
| `accept-all` | Nunca pide confirmación. Todas las operaciones continúan automáticamente. |
| `manual` | Pide confirmación antes de cada operación, incluidas las lecturas. |

**Cuando se solicita permiso:**

```
  Permitir: Ejecutar: git commit -am "fix bug"  [y/N/a(ccept-all)]
```

- `y` — aprobar esta acción
- `n` o Enter — denegar
- `a` — aprobar y cambiar a `accept-all` durante el resto de la sesión

**Comandos siempre aprobados automáticamente en modo `auto`:**
`ls`, `cat`, `head`, `tail`, `wc`, `pwd`, `echo`, `git status`, `git log`, `git diff`, `git show`, `find`, `grep`, `rg`, `python`, `node`, `pip show`, `npm list` y otros comandos shell de solo lectura.

---

## Herramientas integradas

### Herramientas centrales

| Herramienta | Descripción | Parámetros clave |
|---|---|---|
| `Read` | Lee un archivo con números de línea | `file_path`, `limit`, `offset` |
| `Write` | Crea o sobrescribe un archivo (muestra diff) | `file_path`, `content` |
| `Edit` | Reemplazo exacto de cadenas (muestra diff) | `file_path`, `old_string`, `new_string`, `replace_all` |
| `Bash` | Ejecuta un comando shell | `command`, `timeout` (30s por defecto) |
| `Glob` | Encuentra archivos por patrón glob | `pattern` (p. ej., `**/*.py`), `path` |
| `Grep` | Búsqueda regex en archivos (usa ripgrep si está disponible) | `pattern`, `path`, `glob`, `output_mode` |
| `WebFetch` | Recupera y extrae texto de una URL | `url`, `prompt` |
| `WebSearch` | Busca en la web mediante DuckDuckGo | `query` |

### Herramientas de memoria

| Herramienta | Descripción | Parámetros clave |
|---|---|---|
| `MemorySave` | Guarda o actualiza una memoria persistente | `name`, `type`, `description`, `content`, `scope` |
| `MemoryDelete` | Elimina una memoria por nombre | `name`, `scope` |
| `MemorySearch` | Busca memorias por palabra clave (o ranking con IA) | `query`, `scope`, `use_ai`, `max_results` |
| `MemoryList` | Lista todas las memorias con antigüedad y metadatos | `scope` |

### Herramientas de subagentes

| Herramienta | Descripción | Parámetros clave |
|---|---|---|
| `Agent` | Lanza un subagente para una tarea | `prompt`, `subagent_type`, `isolation`, `name`, `model`, `wait` |
| `SendMessage` | Envía un mensaje a un agente en segundo plano con nombre | `name`, `message` |
| `CheckAgentResult` | Comprueba el estado/resultado de un agente en segundo plano | `task_id` |
| `ListAgentTasks` | Lista todas las tareas de agentes activas y finalizadas | — |
| `ListAgentTypes` | Lista todas las definiciones disponibles de tipos de agente | — |

### Herramientas de habilidades

| Herramienta | Descripción | Parámetros clave |
|---|---|---|
| `Skill` | Invoca una habilidad por nombre dentro de la conversación | `name`, `args` |
| `SkillList` | Lista todas las habilidades disponibles con triggers y metadatos | — |

### Herramientas MCP

Las herramientas MCP se descubren automáticamente desde los servidores configurados y se registran con el nombre `mcp__<server>__<tool>`. Claude puede usarlas exactamente igual que las herramientas integradas.

| Nombre de herramienta de ejemplo | Procedencia |
|---|---|
| `mcp__git__git_status` | servidor `git`, herramienta `git_status` |
| `mcp__filesystem__read_file` | servidor `filesystem`, herramienta `read_file` |
| `mcp__myserver__my_action` | servidor personalizado configurado por ti |

> **Añadir herramientas personalizadas:** consulta la [Guía de Arquitectura](docs/architecture.md#tool-registry) para registrar tus propias herramientas.

---

## Memoria

El modelo puede recordar cosas entre conversaciones mediante el sistema de memoria integrado.

**Cómo funciona:** las memorias se almacenan como archivos Markdown. Hay dos ámbitos:
- **Ámbito de usuario** (`~/.nano_claude/memory/`) — te acompaña en todos los proyectos
- **Ámbito de proyecto** (`.nano_claude/memory/` en el cwd) — específico del repositorio actual

Un índice `MEMORY.md` (≤ 200 líneas / 25 KB) se reconstruye automáticamente en cada guardado o borrado y se inyecta en el prompt del sistema para que Claude tenga siempre una visión general.

**Tipos de memoria:**

| Tipo | Uso |
|---|---|
| `user` | Tu rol, preferencias, contexto |
| `feedback` | Cómo quieres que se comporte el modelo |
| `project` | Trabajo en curso, plazos, decisiones |
| `reference` | Enlaces a recursos externos |

**Formato del archivo de memoria** (`~/.nano_claude/memory/coding_style.md`):
```markdown
---
name: coding style
description: Python formatting preferences
type: feedback
created: 2026-04-02
---
Prefer 4-space indentation and full type hints in all Python code.
**Why:** user explicitly stated this preference.
**How to apply:** apply to every Python file written or edited.
```

**Ejemplo de interacción:**

```
Tú: Remember that I prefer 4-space indentation and type hints in all Python code.
IA: [llama a MemorySave] Memoria guardada: coding_style [feedback/user]

Tú: /memory
  [feedback/user] coding_style (today): Preferencias de formato de Python

Tú: /memory python
  [feedback/user] coding_style: Prefiere indentación de 4 espacios y type hints en Python
```

**Avisos de obsolescencia:** las memorias con más de 1 día reciben una nota de frescura en la salida de `/memory`, para que sepas cuándo revisarlas o actualizarlas.

**Búsqueda con ranking de IA:** `MemorySearch(query="...", use_ai=true)` usa el modelo para ordenar los resultados por relevancia en lugar de basarse solo en coincidencias de palabras clave.

---

## Habilidades

Las habilidades son plantillas de prompt reutilizables que dan al modelo capacidades especializadas. Se incluyen dos habilidades integradas de serie, sin necesidad de configuración.

**Habilidades integradas:**

| Trigger | Descripción |
|---|---|
| `/commit` | Revisa los cambios staged y crea un commit git bien estructurado |
| `/review [PR]` | Revisa código o un diff de PR con feedback estructurado |

**Inicio rápido — habilidad personalizada:**

```bash
mkdir -p ~/.nano_claude/skills
```

Crea `~/.nano_claude/skills/deploy.md`:

```markdown
---
name: deploy
description: Deploy to an environment
triggers: [/deploy]
allowed-tools: [Bash, Read]
when_to_use: Use when the user wants to deploy a version to an environment.
argument-hint: [env] [version]
arguments: [env, version]
context: inline
---

Deploy $VERSION to the $ENV environment.
Full args: $ARGUMENTS
```

Ahora úsala:

```
Tú: /deploy staging 2.1.0
IA: [despliega la versión 2.1.0 en staging]
```

**Sustitución de argumentos:**
- `$ARGUMENTS` — cadena completa de argumentos sin procesar
- `$ARG_NAME` — sustitución posicional por nombre de argumento (primera palabra → primer nombre)
- Los argumentos faltantes se convierten en cadenas vacías

**Modos de ejecución:**
- `context: inline` (por defecto) — se ejecuta dentro del historial actual de conversación
- `context: fork` — se ejecuta como un subagente aislado con historial nuevo; admite sobrescribir `model`

**Prioridad** (gana la mayor): nivel de proyecto > nivel de usuario > integrada

**Listar habilidades:** `/skills` — muestra triggers, pista de argumentos, origen y `when_to_use`

**Rutas de búsqueda de habilidades:**

```
./.nano_claude/skills/     # nivel de proyecto (sobrescribe el nivel de usuario)
~/.nano_claude/skills/     # nivel de usuario
```

---

## Subagentes

El modelo puede lanzar subagentes independientes para gestionar tareas en paralelo.

**Tipos de agente especializados** — integrados:

| Tipo | Optimizado para |
|---|---|
| `general-purpose` | Investigación, exploración, tareas de varios pasos |
| `coder` | Escribir, leer y modificar código |
| `reviewer` | Análisis de seguridad, corrección y calidad de código |
| `researcher` | Búsqueda web y consulta de documentación |
| `tester` | Escribir y ejecutar pruebas |

**Uso básico:**
```
Tú: Search this codebase for all TODO comments and summarize them.
IA: [llama a Agent(prompt="...", subagent_type="researcher")]
    El subagente lee archivos, busca TODOs...
    Resultado: Encontró 12 TODOs en 5 archivos...
```

**Modo en segundo plano** — lanzar sin esperar y recoger el resultado más tarde:
```
IA: [llama a Agent(prompt="run all tests", name="test-runner", wait=false)]
IA: [continúa con otro trabajo...]
IA: [llama a CheckAgentResult / SendMessage para hacer seguimiento]
```

**Aislamiento con git worktree** — los agentes trabajan en una rama aislada sin conflictos:
```
Agent(prompt="refactor auth module", isolation="worktree")
```
El worktree se limpia automáticamente si no hubo cambios; de lo contrario se informa del nombre de la rama.

**Tipos de agente personalizados** — crea `~/.nano_claude/agents/myagent.md`:
```markdown
---
name: myagent
description: Specialized for X
model: claude-haiku-4-5-20251001
tools: [Read, Grep, Bash]
---
Extra system prompt for this agent type.
```

**Listar agentes en ejecución:** `/agents`

Los subagentes tienen historial de conversación independiente, comparten el sistema de archivos y están limitados a 3 niveles de anidamiento.

---

## MCP (Model Context Protocol)

MCP te permite conectar cualquier servidor de herramientas externo — subproceso local o HTTP remoto — y Claude puede usar sus herramientas automáticamente. Es el mismo protocolo que Claude Code usa para ampliar sus capacidades.

### Transportes compatibles

| Transporte | `type` en config | Descripción |
|---|---|---|
| **stdio** | `"stdio"` | Lanza un subproceso local (el más común) |
| **SSE** | `"sse"` | Flujo HTTP Server-Sent Events |
| **HTTP** | `"http"` | HTTP POST con streaming (servidores más nuevos) |

### Configuración

Coloca un archivo `.mcp.json` en el directorio del proyecto **o** edita `~/.nano_claude/mcp.json` para servidores globales de usuario.

```json
{
  "mcpServers": {
    "git": {
      "type": "stdio",
      "command": "uvx",
      "args": ["mcp-server-git"]
    },
    "filesystem": {
      "type": "stdio",
      "command": "uvx",
      "args": ["mcp-server-filesystem", "/tmp"]
    },
    "my-remote": {
      "type": "sse",
      "url": "http://localhost:8080/sse",
      "headers": {"Authorization": "Bearer my-token"}
    }
  }
}
```

Prioridad de configuración: `.mcp.json` (proyecto) sobrescribe `~/.nano_claude/mcp.json` (usuario) por nombre de servidor.

### Inicio rápido

```bash
# Instala un servidor MCP popular
pip install uv        # uv incluye uvx
uvx mcp-server-git --help   # verifica que funciona

# Añádelo a la configuración del usuario vía REPL
/mcp add git uvx mcp-server-git

# O crea .mcp.json en tu directorio de proyecto y luego:
/mcp reload
```

### Comandos REPL

```
/mcp                          # lista servidores + sus herramientas + estado de conexión
/mcp reload                   # reconecta todos los servidores, actualiza la lista de herramientas
/mcp reload git               # reconecta un único servidor
/mcp add myserver uvx mcp-server-x   # añade un servidor stdio
/mcp remove myserver          # lo elimina de la configuración del usuario
```

### Cómo usa Claude las herramientas MCP

Una vez conectado, Claude puede invocar herramientas MCP directamente:

```
Tú: What files changed in the last git commit?
IA: [llama a mcp__git__git_diff_staged()]
    → muestra la salida diff del servidor MCP de git
```

Los nombres de herramienta siguen el patrón `mcp__<server_name>__<tool_name>`. Todos los caracteres
que no sean alfanuméricos o `_` se reemplazan automáticamente por `_`.

### Servidores MCP populares

| Servidor | Instalación | Proporciona |
|---|---|---|
| `mcp-server-git` | `uvx mcp-server-git` | operaciones git (status, diff, log, commit) |
| `mcp-server-filesystem` | `uvx mcp-server-filesystem <path>` | lectura/escritura/listado de archivos |
| `mcp-server-fetch` | `uvx mcp-server-fetch` | herramienta de fetch HTTP |
| `mcp-server-postgres` | `uvx mcp-server-postgres <conn-str>` | consultas PostgreSQL |
| `mcp-server-sqlite` | `uvx mcp-server-sqlite --db-path x.db` | consultas SQLite |
| `mcp-server-brave-search` | `uvx mcp-server-brave-search` | búsqueda web con Brave |

> Explora el registro completo en [modelcontextprotocol.io/servers](https://modelcontextprotocol.io/servers)

---

## Sistema de plugins

El paquete `plugin/` te permite ampliar nano-claude-code con herramientas, habilidades y servidores MCP adicionales desde repositorios git o directorios locales.

### Instalar un plugin

```bash
/plugin install my-plugin@https://github.com/user/my-plugin
/plugin install local-plugin@/path/to/local/plugin
```

### Gestionar plugins

```bash
/plugin                   # lista los plugins instalados
/plugin enable my-plugin  # habilita un plugin deshabilitado
/plugin disable my-plugin # deshabilita sin desinstalar
/plugin disable-all       # deshabilita todos los plugins
/plugin update my-plugin  # obtiene la última versión desde git
/plugin uninstall my-plugin
/plugin info my-plugin    # muestra detalles del manifest
```

### Motor de recomendación de plugins

```bash
/plugin recommend                    # autodetecta a partir de los archivos del proyecto
/plugin recommend "docker database"  # recomienda según palabras clave del contexto
```

El motor compara tu contexto con un marketplace curado (git-tools, python-linter, docker-tools, sql-tools, test-runner, diagram-tools, aws-tools, web-scraper) usando puntuación por etiquetas y palabras clave.

### Manifest del plugin (plugin.json)

```json
{
  "name": "my-plugin",
  "version": "0.1.0",
  "description": "Does something useful",
  "author": "you",
  "tags": ["git", "python"],
  "tools": ["tools"],        // módulo(s) Python que exportan TOOL_DEFS
  "skills": ["skills/my.md"],
  "mcp_servers": {},
  "dependencies": ["httpx"]  // paquetes pip
}
```

También puedes usar YAML frontmatter en `PLUGIN.md`.

### Ámbitos

| Ámbito | Ubicación | Configuración |
|-------|----------|--------|
| usuario (por defecto) | `~/.nano_claude/plugins/` | `~/.nano_claude/plugins.json` |
| proyecto | `.nano_claude/plugins/` | `.nano_claude/plugins.json` |

Usa la flag `--project`: `/plugin install name@url --project`

---

## Herramienta AskUserQuestion

Claude puede pausarse a mitad de una tarea e interactuar contigo antes de continuar.

**Ejemplo de invocación por Claude:**
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

**Lo que ves en la terminal:**
```
❓ Pregunta del asistente:
   Which database should I use?

  [1] SQLite — Simple, file-based
  [2] PostgreSQL — Full-featured, requires server
  [0] Escribir una respuesta personalizada

Tu elección (número o texto):
```

- Selecciona por número o escribe texto libre directamente
- Claude recibe tu respuesta y continúa la tarea
- Tiempo de espera de 5 minutos (devuelve `"(no answer — timeout)"` si no respondes)

---

## Gestión de tareas

El paquete `task/` proporciona a Claude (y a ti) una lista estructurada de tareas para seguir trabajo de varios pasos dentro de una sesión.

### Herramientas disponibles para Claude

| Herramienta | Parámetros | Qué hace |
|------|-----------|--------------|
| `TaskCreate` | `subject`, `description`, `active_form?`, `metadata?` | Crea una tarea; devuelve `#id created: subject` |
| `TaskUpdate` | `task_id`, `subject?`, `description?`, `status?`, `owner?`, `add_blocks?`, `add_blocked_by?`, `metadata?` | Actualiza cualquier campo; `status='deleted'` elimina la tarea |
| `TaskGet` | `task_id` | Devuelve los detalles completos de una tarea |
| `TaskList` | _(ninguno)_ | Lista todas las tareas con iconos de estado y bloqueadores pendientes |

**Estados válidos:** `pending` → `in_progress` → `completed` / `cancelled` / `deleted`

### Aristas de dependencia

```
TaskUpdate(task_id="3", add_blocked_by=["1","2"])
# La tarea 3 ahora está bloqueada por las tareas 1 y 2.
# Las aristas inversas se establecen automáticamente: las tareas 1 y 2 reciben la tarea 3 en su lista "blocks".
```

Las tareas completadas se consideran resueltas — `TaskList` oculta su efecto bloqueante sobre las dependientes.

### Persistencia

Las tareas se guardan en `.nano_claude/tasks.json` en el directorio de trabajo actual tras cada mutación y se vuelven a cargar en el primer acceso.

### Comandos REPL

```
/tasks                    lista todas las tareas
/tasks create <subject>   crea rápidamente una tarea
/tasks start <id>         marca como in_progress
/tasks done <id>          marca como completed
/tasks cancel <id>        marca como cancelled
/tasks delete <id>        elimina una tarea
/tasks get <id>           muestra todos los detalles
/tasks clear              elimina todas las tareas
```

### Flujo típico de Claude

```
Usuario: implement the login feature

Claude:
  TaskCreate(subject="Design auth schema", description="JWT vs session")  → #1
  TaskCreate(subject="Write login endpoint", description="POST /auth/login") → #2
  TaskCreate(subject="Write tests", description="Unit + integration") → #3
  TaskUpdate(task_id="2", add_blocked_by=["1"])
  TaskUpdate(task_id="3", add_blocked_by=["2"])

  TaskUpdate(task_id="1", status="in_progress", active_form="Designing schema")
  ... (hace el trabajo) ...
  TaskUpdate(task_id="1", status="completed")
  TaskList()  → la tarea 2 ya no está bloqueada
  ...
```

---

## Compresión de contexto

Las conversaciones largas se comprimen automáticamente para mantenerse dentro de la ventana de contexto del modelo.

**Dos capas:**

1. **Snip** — las salidas antiguas de herramientas (lecturas de archivos, resultados de bash) se truncan tras unos pocos turnos. Rápido, sin coste de API.
2. **Auto-compact** — cuando el uso de tokens supera el 70 % del límite de contexto, los mensajes antiguos se resumen con el modelo en una recapitulación concisa.

Esto ocurre de forma transparente. No necesitas hacer nada.

---

## Vista diff

Cuando el modelo edita o sobrescribe un archivo, ves un diff estilo git:

```diff
  Cambios aplicados a config.py:

--- a/config.py
+++ b/config.py
@@ -12,7 +12,7 @@
     "model": "claude-opus-4-6",
-    "max_tokens": 8192,
+    "max_tokens": 16384,
     "permission_mode": "auto",
```

Líneas verdes = añadidas, líneas rojas = eliminadas. Las nuevas creaciones de archivos muestran un resumen en su lugar.

---

## Soporte para CLAUDE.md

Coloca un archivo `CLAUDE.md` en tu proyecto para darle al modelo contexto persistente sobre tu base de código. Nano Claude lo encuentra e inyecta automáticamente en el prompt del sistema.

```
~/.claude/CLAUDE.md          # Global — se aplica a todos los proyectos
/your/project/CLAUDE.md      # Nivel de proyecto — se encuentra ascendiendo desde cwd
```

**Ejemplo de `CLAUDE.md`:**

```markdown
# Project: FastAPI Backend

## Stack
- Python 3.12, FastAPI, PostgreSQL, SQLAlchemy 2.0, Alembic
- Tests: pytest, coverage target 90%

## Conventions
- Format with black, lint with ruff
- Full type annotations required
- New endpoints must have corresponding tests

## Important Notes
- Never hard-code credentials — use environment variables
- Do not modify existing Alembic migration files
- The `staging` branch deploys automatically to staging on push
```

---

## Gestión de sesiones

```bash
# Dentro del REPL:
/save                          # nombre automático: session_20260401_143022.json
/save debug_auth_bug           # guardado con nombre

/load                          # lista todas las sesiones guardadas
/load debug_auth_bug           # reanuda una sesión
/load session_20260401_143022.json
```

Las sesiones se almacenan como JSON en `~/.nano_claude/sessions/`.

---

## Estructura del proyecto

```
nano_claude_code/
├── nano_claude.py        # Punto de entrada: REPL + comandos con barra + renderizado diff
├── agent.py              # Bucle del agente: streaming, despacho de herramientas, compactación
├── providers.py          # Multiproveedor: Anthropic, streaming OpenAI-compatible
├── tools.py              # Herramientas centrales (Read/Write/Edit/Bash/Glob/Grep/Web) + conexión con el registro
├── tool_registry.py      # Registro de plugins de herramientas: registrar, buscar, ejecutar
├── compaction.py         # Compresión de contexto: snip + auto-resumen
├── context.py            # Constructor del prompt del sistema: CLAUDE.md + git + memoria
├── config.py             # Carga/guardado/configuración por defecto
│
├── multi_agent/          # Paquete multiagente
│   ├── __init__.py       # Reexportaciones
│   ├── subagent.py       # AgentDefinition, SubAgentManager, helpers de worktree
│   └── tools.py          # Agent, SendMessage, CheckAgentResult, ListAgentTasks, ListAgentTypes
├── subagent.py           # Shim de compatibilidad → multi_agent/
│
├── memory/               # Paquete de memoria
│   ├── __init__.py       # Reexportaciones
│   ├── types.py          # MEMORY_TYPES y guía de formato
│   ├── store.py          # guardar/cargar/eliminar/buscar, reconstrucción del índice MEMORY.md
│   ├── scan.py           # MemoryHeader, helpers de antigüedad/frescura
│   ├── context.py        # get_memory_context(), truncamiento, búsqueda con IA
│   └── tools.py          # MemorySave, MemoryDelete, MemorySearch, MemoryList
├── memory.py             # Shim de compatibilidad → memory/
│
├── skill/                # Paquete de habilidades
│   ├── __init__.py       # Reexportaciones; importa builtin para registrar las integradas
│   ├── loader.py         # SkillDef, parse, load_skills, find_skill, substitute_arguments
│   ├── builtin.py        # Habilidades integradas: /commit, /review
│   ├── executor.py       # execute_skill(): inline o subagente forkeado
│   └── tools.py          # Skill, SkillList
├── skills.py             # Shim de compatibilidad → skill/
│
├── mcp/                  # Paquete MCP (Model Context Protocol)
│   ├── __init__.py       # Reexportaciones
│   ├── types.py          # MCPServerConfig, MCPTool, MCPServerState, helpers JSON-RPC
│   ├── client.py         # StdioTransport, HttpTransport, MCPClient, MCPManager
│   ├── config.py         # Carga .mcp.json (proyecto) + ~/.nano_claude/mcp.json (usuario)
│   └── tools.py          # Descubrir automáticamente + registrar herramientas MCP en tool_registry
│
└── tests/                # 135 pruebas unitarias
    ├── test_mcp.py
    ├── test_memory.py
    ├── test_skills.py
    ├── test_subagent.py
    ├── test_tool_registry.py
    ├── test_compaction.py
    └── test_diff_view.py
```

> **Para desarrolladores:** cada paquete de funcionalidad (`multi_agent/`, `memory/`, `skill/`, `mcp/`) es autocontenido. Añade herramientas personalizadas llamando a `register_tool(ToolDef(...))` desde cualquier módulo importado por `tools.py`.

---

## Preguntas frecuentes

**P: ¿Cómo añado un servidor MCP?**

Opción 1 — vía REPL (servidor stdio):
```
/mcp add git uvx mcp-server-git
```

Opción 2 — crea `.mcp.json` en tu proyecto:
```json
{
  "mcpServers": {
    "git": {"type": "stdio", "command": "uvx", "args": ["mcp-server-git"]}
  }
}
```

Después ejecuta `/mcp reload` o reinicia. Usa `/mcp` para comprobar el estado de la conexión.

**P: Un servidor MCP muestra un error. ¿Cómo lo depuro?**

```
/mcp                    # muestra el mensaje de error por servidor
/mcp reload git         # intenta reconectar
```

Si el servidor usa stdio, asegúrate de que el comando esté en tu `$PATH`:
```bash
which uvx               # debería imprimir una ruta
uvx mcp-server-git      # ejecútalo manualmente para ver errores
```

**P: ¿Puedo usar servidores MCP que requieran autenticación?**

Para servidores HTTP/SSE con token Bearer:
```json
{
  "mcpServers": {
    "my-api": {
      "type": "sse",
      "url": "https://myserver.example.com/sse",
      "headers": {"Authorization": "Bearer sk-my-token"}
    }
  }
}
```

Para servidores stdio con autenticación por variables de entorno:
```json
{
  "mcpServers": {
    "brave": {
      "type": "stdio",
      "command": "uvx",
      "args": ["mcp-server-brave-search"],
      "env": {"BRAVE_API_KEY": "your-key"}
    }
  }
}
```

**P: Las llamadas a herramientas no funcionan con mi modelo local de Ollama.**

No todos los modelos admiten function calling. Usa uno de los modelos recomendados para herramientas: `qwen2.5-coder`, `llama3.3`, `mistral` o `phi4`.

```bash
ollama pull qwen2.5-coder
python nano_claude.py --model ollama/qwen2.5-coder
```

**P: ¿Cómo me conecto a un servidor GPU remoto que ejecuta vLLM?**

```
/config custom_base_url=http://your-server-ip:8000/v1
/config custom_api_key=your-token
/model custom/your-model-name
```

**P: ¿Cómo compruebo mi coste de API?**

```
/cost

  Tokens de entrada:  3,421
  Tokens de salida:     892
  Coste estimado:    $0.0648 USD
```

**P: ¿Puedo usar varias API keys en la misma sesión?**

Sí. Configura todas las claves que necesites por adelantado (mediante variables de entorno o `/config`). Luego cambia de modelo libremente: cada llamada usa la clave del proveedor activo.

**P: ¿Cómo hago que un modelo esté disponible en todos los proyectos?**

Añade las claves a `~/.bashrc` o `~/.zshrc`. Configura el modelo por defecto en `~/.nano_claude/config.json`:

```json
{ "model": "claude-sonnet-4-6" }
```

**P: Qwen / Zhipu devuelve texto corrupto.**

Asegúrate de que tu `DASHSCOPE_API_KEY` / `ZHIPU_API_KEY` sea correcta y que la cuenta tenga cuota suficiente. Ambos proveedores usan UTF-8 y manejan bien el chino.

**P: ¿Puedo canalizar entrada a nano claude?**

```bash
echo "Explain this file" | python nano_claude.py --print --accept-all
cat error.log | python nano_claude.py -p "What is causing this error?"
```

**P: ¿Cómo lo ejecuto como una herramienta CLI desde cualquier lugar?**

```bash
# Añade un alias a ~/.bashrc o ~/.zshrc
alias nc='python /path/to/nano_claude_code/nano_claude.py'

# O instálalo como script
pip install -e .   # si existe setup.py
```
