[English](https://github.com/SafeRL-Lab/nano-claude-code/blob/main/README.md) | [中文](https://github.com/SafeRL-Lab/nano-claude-code/blob/main/docs/README.CN.MD) | 한국어 | [日本語](https://github.com/SafeRL-Lab/nano-claude-code/blob/main/docs/README.JP.MD) | [Deutsch](https://github.com/SafeRL-Lab/nano-claude-code/blob/main/docs/README.DE.MD) | [Português](https://github.com/SafeRL-Lab/nano-claude-code/blob/main/docs/README.ES.MD)



<div align="center">
  <a href="[https://github.com/SafeRL-Lab/Robust-Gymnasium](https://github.com/SafeRL-Lab/nano-claude-code)">
    <img src="https://github.com/SafeRL-Lab/nano-claude-code/blob/main/docs/logo-v1.png" alt="로고" width="280"> 
  </a>

<h1 align="center" style="font-size: 30px;"><strong><em>Nano Claude Code</em></strong>: 모든 모델을 지원하는 빠르고 사용하기 쉬운 Claude Code의 Python 재구현</h1>
<p align="center">
    <a href="https://github.com/chauncygu/collection-claude-code-source-code">최신 Claude Code 소스 모음</a>
    ·
    <a href="https://github.com/SafeRL-Lab/nano-claude-code/issues">이슈</a>
  ·
    <a href="https://deepwiki.com/SafeRL-Lab/nano-claude-code">간단한 소개</a>
  </p>
</div>

<div align=center>
 <img src="https://github.com/SafeRL-Lab/nano-claude-code/blob/main/docs/demo.gif" width="850"/> 
</div>

---

## 🔥🔥🔥 뉴스 (태평양 시간)
- 2026년 4월 3일 오후 6:00: **v3.03** — 작업 관리 시스템(`task/` 패키지): `TaskCreate` / `TaskUpdate` / `TaskGet` / `TaskList` 도구, 순차 ID, 의존성 엣지(blocks/blocked_by), 메타데이터, `.nano_claude/tasks.json` 영속화, 스레드 안전 저장소, `/tasks` REPL 명령, 37개 신규 테스트(**약 9500줄**의 Python).
- 2026년 4월 3일 오후 2:50: **v3.02** — 플러그인 시스템(`plugin/` 패키지): `/plugin` CLI를 통한 설치/제거/활성화/비활성화/업데이트, 추천 엔진(키워드+태그 매칭), 다중 스코프(사용자/프로젝트), Git 기반 마켓플레이스. `AskUserQuestion` 도구: 번호 선택지와 자유 입력을 지원하는 작업 중 사용자 질의 기능(**약 8500줄**의 Python).
- 2026년 4월 3일 오전 10:00: **v3.01** — MCP(Model Context Protocol) 지원: `mcp/` 패키지, stdio + SSE + HTTP 전송, 자동 도구 발견, `/mcp` 명령, 34개 신규 테스트(**약 7000줄**의 Python).
- 2026년 4월 2일 오후 12:20: **v3.0** — 멀티 에이전트 패키지(`multi_agent/`), 메모리 패키지(`memory/`), 스킬 패키지(`skill`)에 내장 스킬, 인자 치환, fork/inline 실행, AI 메모리 검색, git worktree 격리, 에이전트 타입 정의 추가(**약 5000줄**의 Python). [업데이트 보기](https://github.com/SafeRL-Lab/nano-claude-code/blob/main/docs/update_readme_v3.0.md)
- 2026년 4월 2일 오전 10:00: **v2.0** — 컨텍스트 압축, 메모리, 서브에이전트, 스킬, diff 보기, 도구 플러그인 시스템(**약 3400줄**의 Python).
- 2026년 4월 1일 오후 1:47: VLLM 추론 지원(**약 2000줄**의 Python).
- 2026년 4월 1일 오전 11:30: 더 많은 **폐쇄형 모델** 및 **오픈소스 모델** 지원: Claude, GPT, Gemini, Kimi, Qwen, Zhipu, DeepSeek, Ollama 또는 OpenAI 호환 엔드포인트를 통한 로컬 오픈소스 모델(**약 1700줄**의 Python).
- 2026년 4월 1일 오전 9:50: 더 많은 **폐쇄형 모델** 지원: Claude, GPT, Gemini(**약 1300줄**의 Python).
- 2026년 4월 1일 오전 8:23: Nano Claude Code 초기 버전 공개(**약 900줄**의 Python).

---

# Nano Claude Code

Nano Claude Code는 Claude, GPT, Gemini, Kimi, Qwen, Zhipu, DeepSeek 및 Ollama 또는 임의의 OpenAI 호환 엔드포인트를 통한 로컬 오픈소스 모델 등 **모든 모델을 지원하는**, **가볍고 사용하기 쉬운** Claude Code의 Python 재구현입니다.

---

## 목차
  * [왜 Nano Claude Code인가](#왜-nano-claude-code인가)
  * [기능](#기능)
  * [지원 모델](#지원-모델)
  * [설치](#설치)
  * [사용법: 폐쇄형 API 모델](#사용법-폐쇄형-api-모델)
  * [사용법: 오픈소스 모델(로컬)](#사용법-오픈소스-모델로컬)
  * [모델 이름 형식](#모델-이름-형식)
  * [CLI 레퍼런스](#cli-레퍼런스)
  * [슬래시 명령어(REPL)](#슬래시-명령어repl)
  * [API 키 설정](#api-키-설정)
  * [권한 시스템](#권한-시스템)
  * [내장 도구](#내장-도구)
  * [메모리](#메모리)
  * [스킬](#스킬)
  * [서브에이전트](#서브에이전트)
  * [MCP (Model Context Protocol)](#mcp-model-context-protocol)
  * [플러그인 시스템](#플러그인-시스템)
  * [AskUserQuestion 도구](#askuserquestion-도구)
  * [작업 관리](#작업-관리)
  * [컨텍스트 압축](#컨텍스트-압축)
  * [Diff 보기](#diff-보기)
  * [CLAUDE.md 지원](#claudemd-지원)
  * [세션 관리](#세션-관리)
  * [프로젝트 구조](#프로젝트-구조)
  * [FAQ](#faq)

## 왜 Nano Claude Code인가

Claude Code는 강력한 프로덕션급 AI 코딩 어시스턴트이지만, 소스 코드는 컴파일된 12MB TypeScript/Node.js 번들(약 1,300개 파일, 약 28.3만 줄)입니다. Anthropic API에 강하게 결합되어 있고 수정이 어렵고, 로컬 모델이나 다른 모델에 연결해 실행하는 것도 사실상 불가능합니다.

**Nano Claude Code**는 동일한 핵심 루프를 읽기 쉬운 Python 약 1만 줄로 재구현했습니다. 필요한 것은 남기고, 불필요한 것은 덜어냈습니다. 보다 자세한 비교 분석은 여기에서 볼 수 있습니다(Nano Claude Code v3.03): [영문판](https://github.com/SafeRL-Lab/nano-claude-code/blob/main/docs/comparison_claude_code_vs_nano_v3.03_en.md), [중문판](https://github.com/SafeRL-Lab/nano-claude-code/blob/main/docs/comparison_claude_code_vs_nano_v3.03_cn.md)

### 한눈에 보기

| 항목 | Claude Code (TypeScript) | Nano Claude Code (Python) |
|-----------|--------------------------|---------------------------|
| 언어 | TypeScript + React/Ink | Python 3.8+ |
| 소스 파일 수 | 약 1,332개 TS/TSX 파일 | 51개 Python 파일 |
| 코드 줄 수 | 약 283K | 약 10.2K |
| 내장 도구 | 44+ | 21 |
| 슬래시 명령어 | 88 | 17 |
| 모델 제공자 | Anthropic 전용 | 7+ (Anthropic · OpenAI · Gemini · Kimi · Qwen · DeepSeek · Ollama · …) |
| 로컬 모델 | 아니오 | 예 — Ollama, LM Studio, vLLM, 모든 OpenAI 호환 엔드포인트 |
| 빌드 단계 필요 | 예 (Bun + esbuild) | 아니오 — `python nano_claude.py`로 직접 실행 |
| 런타임 확장성 | 닫혀 있음(컴파일 시점) | 열려 있음 — 런타임 `register_tool()`, Markdown 스킬, git 플러그인 |
| 작업 의존성 그래프 | 아니오 | 예 — `task/` 패키지의 `blocks` / `blocked_by` 엣지 |

### Claude Code가 더 강한 부분

- **UI 품질** — 스트리밍 렌더링, 세밀한 diff 시각화, 대화상자 시스템을 갖춘 React/Ink 컴포넌트 트리
- **도구 폭** — `NotebookEdit`, `LSP Diagnostics`, `RemoteTrigger`, `EnterWorktree` 등을 포함한 44개 이상의 도구
- **엔터프라이즈 기능** — MDM 관리 설정, 팀 권한 동기화, OAuth, 키체인 저장, GrowthBook 기능 플래그
- **AI 기반 메모리 추출** — 명시적 도구 호출 없이 대화에서 지식을 선제적으로 추출하는 `extractMemories`
- **프로덕션 신뢰성** — 단일 배포 파일 `cli.js`, 포괄적인 테스트 커버리지, 버전 고정 릴리스

### Nano Claude Code가 더 강한 부분

- **멀티 프로바이더** — `--model` 또는 `/model`만으로 Claude, GPT-4o, Gemini 2.5 Pro, DeepSeek, Qwen, 로컬 Llama 간 전환 가능, 재컴파일 불필요
- **로컬 모델 지원** — Ollama, LM Studio, 또는 vLLM 기반 모델로 완전 오프라인 실행 가능
- **읽기 쉬운 소스** — 전체 에이전트 루프가 174줄(`agent.py`)이며 Python 개발자라면 금방 이해하고 포크/확장 가능
- **빌드 없음** — `pip install -r requirements.txt`만으로 바로 실행, 변경 사항도 즉시 반영
- **동적 확장성** — `register_tool(ToolDef(...))`로 런타임 도구 등록, git URL 기반 스킬 팩 설치, MCP 서버 연결 가능
- **작업 의존성 그래프** — `TaskCreate` / `TaskUpdate`가 구조화된 다단계 계획용 `blocks` / `blocked_by` 엣지를 지원
- **2단계 컨텍스트 압축** — 규칙 기반 snip + AI 요약, `preserve_last_n_turns`로 조정 가능

### 핵심 설계 차이

**에이전트 루프** — Nano는 타입이 지정된 이벤트(`TextChunk`, `ToolStart`, `ToolEnd`, `TurnDone`)를 `yield`하는 Python 제너레이터를 사용합니다. 전체 루프가 한 파일에 있어 훅, 커스텀 렌더러, 로깅을 추가하기 쉽습니다.

**도구 등록** — 모든 도구는 `ToolDef(name, schema, func, read_only, concurrent_safe)` 데이터클래스입니다. 어떤 모듈이든 import 시점에 `register_tool()`을 호출할 수 있으며, MCP 서버, 플러그인, 스킬도 같은 메커니즘을 사용합니다.

**컨텍스트 압축**

| | Claude Code | Nano Claude Code |
|-|-------------|-----------------|
| 트리거 | 정확한 토큰 수 | `len / 3.5` 추정, 70%에서 동작 |
| 레이어 1 | — | Snip: 오래된 도구 출력 잘라내기(API 비용 없음) |
| 레이어 2 | AI 요약 | 오래된 턴의 AI 요약 |
| 제어 | 시스템 관리 | `preserve_last_n_turns` 매개변수 |

**메모리** — Claude Code의 `extractMemories`는 모델이 사실을 선제적으로 드러내게 합니다. Nano의 `memory/` 패키지는 도구 기반이며, 모델이 `MemorySave`를 명시적으로 호출합니다. 더 예측 가능하고 감사하기 쉽습니다.

### 누가 Nano Claude Code를 사용하면 좋은가

- 코딩 어시스턴트로 **로컬 모델 또는 비-Anthropic 모델**을 쓰고 싶은 개발자
- **에이전트형 코딩 어시스턴트가 어떻게 동작하는지** 연구하는 연구자
- 사유 도구, 맞춤 권한 정책, 특수화 에이전트 타입을 넣기 위한 **해킹 가능한 베이스라인**이 필요한 팀
- **Node.js 빌드 체인 없이** Claude Code 스타일 생산성을 원한다면 누구나

---

## 기능

| 기능 | 상세 |
|---|---|
| 멀티 프로바이더 | Anthropic · OpenAI · Gemini · Kimi · Qwen · Zhipu · DeepSeek · Ollama · LM Studio · 커스텀 엔드포인트 |
| 대화형 REPL | readline 히스토리, Tab 자동완성 슬래시 명령어 |
| 에이전트 루프 | 스트리밍 API + 자동 도구 사용 루프 |
| 21개 내장 도구 | Read · Write · Edit · Bash · Glob · Grep · WebFetch · WebSearch · MemorySave · MemoryDelete · MemorySearch · MemoryList · Agent · SendMessage · CheckAgentResult · ListAgentTasks · ListAgentTypes · Skill · SkillList · AskUserQuestion · *(MCP + plugin 도구는 시작 시 자동 추가)* |
| MCP 통합 | 모든 MCP 서버 연결 가능(stdio/SSE/HTTP), 도구 자동 등록 및 Claude에서 호출 가능 |
| 플러그인 시스템 | git URL 또는 로컬 경로에서 플러그인 설치/제거/활성화/비활성화/업데이트, 다중 스코프(사용자/프로젝트), 추천 엔진 |
| AskUserQuestion | Claude가 작업 중간에 멈추고 번호 선택지를 포함한 확인 질문 가능 |
| 작업 관리 | TaskCreate/Update/Get/List 도구, 순차 ID, 의존성 엣지, 메타데이터, `.nano_claude/tasks.json`에 저장, `/tasks` REPL 명령 |
| Diff 보기 | Edit/Write 시 Git 스타일 빨강/초록 diff 표시 |
| 컨텍스트 압축 | 긴 대화를 모델 컨텍스트 한도 안에 유지하도록 자동 압축 |
| 영구 메모리 | 4개 타입을 갖는 이중 스코프 메모리(사용자 + 프로젝트), AI 검색, 오래됨 경고 |
| 멀티 에이전트 | 타입이 지정된 서브에이전트(coder/reviewer/researcher/…) 생성, git worktree 격리, 백그라운드 모드 |
| 스킬 | 내장 `/commit` · `/review` + 인자 치환 및 fork/inline 실행을 지원하는 커스텀 markdown 스킬 |
| 플러그인 도구 | `tool_registry.py`를 통한 커스텀 도구 등록 |
| 권한 시스템 | `auto` / `accept-all` / `manual` 모드 |
| 17개 슬래시 명령어 | `/model` · `/config` · `/save` · `/cost` · `/memory` · `/skills` · `/agents` · … |
| 컨텍스트 주입 | `CLAUDE.md`, git status, cwd, 영구 메모리를 자동 로드 |
| 세션 영속화 | 대화를 `~/.nano_claude/sessions/`에 저장/불러오기 |
| Extended Thinking | 켜기/끄기 전환(Claude 모델만) |
| 비용 추적 | 토큰 사용량 + 예상 USD 비용 |
| 비대화형 모드 | 스크립팅/CI용 `--print` 플래그 |

---

## 지원 모델

### 폐쇄형(API)

| 제공자 | 모델 | 컨텍스트 | 장점 | API 키 환경변수 |
|---|---|---|---|---|
| **Anthropic** | `claude-opus-4-6` | 200k | 가장 강력하며 복잡한 추론에 적합 | `ANTHROPIC_API_KEY` |
| **Anthropic** | `claude-sonnet-4-6` | 200k | 속도와 품질의 균형 | `ANTHROPIC_API_KEY` |
| **Anthropic** | `claude-haiku-4-5-20251001` | 200k | 빠르고 비용 효율적 | `ANTHROPIC_API_KEY` |
| **OpenAI** | `gpt-4o` | 128k | 강력한 멀티모달 및 코딩 | `OPENAI_API_KEY` |
| **OpenAI** | `gpt-4o-mini` | 128k | 빠르고 저렴함 | `OPENAI_API_KEY` |
| **OpenAI** | `o3-mini` | 200k | 강한 추론 | `OPENAI_API_KEY` |
| **OpenAI** | `o1` | 200k | 고급 추론 | `OPENAI_API_KEY` |
| **Google** | `gemini-2.5-pro-preview-03-25` | 1M | 긴 컨텍스트, 멀티모달 | `GEMINI_API_KEY` |
| **Google** | `gemini-2.0-flash` | 1M | 빠르고 큰 컨텍스트 | `GEMINI_API_KEY` |
| **Google** | `gemini-1.5-pro` | 2M | 가장 큰 컨텍스트 창 | `GEMINI_API_KEY` |
| **Moonshot (Kimi)** | `moonshot-v1-8k` | 8k | 중국어/영어 | `MOONSHOT_API_KEY` |
| **Moonshot (Kimi)** | `moonshot-v1-32k` | 32k | 중국어/영어 | `MOONSHOT_API_KEY` |
| **Moonshot (Kimi)** | `moonshot-v1-128k` | 128k | 긴 컨텍스트 | `MOONSHOT_API_KEY` |
| **Alibaba (Qwen)** | `qwen-max` | 32k | 최고 수준의 Qwen 품질 | `DASHSCOPE_API_KEY` |
| **Alibaba (Qwen)** | `qwen-plus` | 128k | 균형형 | `DASHSCOPE_API_KEY` |
| **Alibaba (Qwen)** | `qwen-turbo` | 1M | 빠르고 저렴함 | `DASHSCOPE_API_KEY` |
| **Alibaba (Qwen)** | `qwq-32b` | 32k | 강한 추론 | `DASHSCOPE_API_KEY` |
| **Zhipu (GLM)** | `glm-4-plus` | 128k | 최고 수준의 GLM 품질 | `ZHIPU_API_KEY` |
| **Zhipu (GLM)** | `glm-4` | 128k | 범용 | `ZHIPU_API_KEY` |
| **Zhipu (GLM)** | `glm-4-flash` | 128k | 무료 티어 제공 | `ZHIPU_API_KEY` |
| **DeepSeek** | `deepseek-chat` | 64k | 강력한 코딩 | `DEEPSEEK_API_KEY` |
| **DeepSeek** | `deepseek-reasoner` | 64k | chain-of-thought 추론 | `DEEPSEEK_API_KEY` |

### 오픈소스(로컬, Ollama 경유)

| 모델 | 크기 | 장점 | Pull 명령 |
|---|---|---|---|
| `llama3.3` | 70B | 범용, 강한 추론 | `ollama pull llama3.3` |
| `llama3.2` | 3B / 11B | 경량 | `ollama pull llama3.2` |
| `qwen2.5-coder` | 7B / 32B | **코딩 작업에 최적** | `ollama pull qwen2.5-coder` |
| `qwen2.5` | 7B / 72B | 중국어/영어 | `ollama pull qwen2.5` |
| `deepseek-r1` | 7B–70B | 추론, 수학 | `ollama pull deepseek-r1` |
| `deepseek-coder-v2` | 16B | 코딩 | `ollama pull deepseek-coder-v2` |
| `mistral` | 7B | 빠르고 효율적 | `ollama pull mistral` |
| `mixtral` | 8x7B | 강력한 MoE 모델 | `ollama pull mixtral` |
| `phi4` | 14B | Microsoft, 강한 추론 | `ollama pull phi4` |
| `gemma3` | 4B / 12B / 27B | Google 오픈 모델 | `ollama pull gemma3` |
| `codellama` | 7B / 34B | 코드 생성 | `ollama pull codellama` |

> **참고:** 도구 호출을 사용하려면 function calling을 지원하는 모델이 필요합니다. 권장 로컬 모델: `qwen2.5-coder`, `llama3.3`, `mistral`, `phi4`.

---

## 설치

```bash
git clone <repo-url>
cd nano_claude_code

pip install -r requirements.txt
# 또는 수동 설치:
pip install anthropic openai httpx rich
```

---

## 사용법: 폐쇄형 API 모델

### Anthropic Claude

API 키는 [console.anthropic.com](https://console.anthropic.com)에서 발급받으세요.

```bash
export ANTHROPIC_API_KEY=sk-ant-api03-...

# 기본 모델 (claude-opus-4-6)
python nano_claude.py

# 특정 모델 선택
python nano_claude.py --model claude-sonnet-4-6
python nano_claude.py --model claude-haiku-4-5-20251001

# Extended Thinking 활성화
python nano_claude.py --model claude-opus-4-6 --thinking --verbose
```

### OpenAI GPT

API 키는 [platform.openai.com](https://platform.openai.com)에서 발급받으세요.

```bash
export OPENAI_API_KEY=sk-...

python nano_claude.py --model gpt-4o
python nano_claude.py --model gpt-4o-mini
python nano_claude.py --model gpt-4.1-mini
python nano_claude.py --model o3-mini
```

### Google Gemini

API 키는 [aistudio.google.com](https://aistudio.google.com)에서 발급받으세요.

```bash
export GEMINI_API_KEY=AIza...

python nano_claude.py --model gemini/gemini-2.0-flash
python nano_claude.py --model gemini/gemini-1.5-pro
python nano_claude.py --model gemini/gemini-2.5-pro-preview-03-25
```

### Kimi (Moonshot AI)

API 키는 [platform.moonshot.cn](https://platform.moonshot.cn)에서 발급받으세요.

```bash
export MOONSHOT_API_KEY=sk-...

python nano_claude.py --model kimi/moonshot-v1-32k
python nano_claude.py --model kimi/moonshot-v1-128k
```

### Qwen (Alibaba DashScope)

API 키는 [dashscope.aliyun.com](https://dashscope.aliyun.com)에서 발급받으세요.

```bash
export DASHSCOPE_API_KEY=sk-...

python nano_claude.py --model qwen/Qwen3.5-Plus
python nano_claude.py --model qwen/Qwen3-MAX
python nano_claude.py --model qwen/Qwen3.5-Flash
```

### Zhipu GLM

API 키는 [open.bigmodel.cn](https://open.bigmodel.cn)에서 발급받으세요.

```bash
export ZHIPU_API_KEY=...

python nano_claude.py --model zhipu/glm-4-plus
python nano_claude.py --model zhipu/glm-4-flash   # 무료 티어
```

### DeepSeek

API 키는 [platform.deepseek.com](https://platform.deepseek.com)에서 발급받으세요.

```bash
export DEEPSEEK_API_KEY=sk-...

python nano_claude.py --model deepseek/deepseek-chat
python nano_claude.py --model deepseek/deepseek-reasoner
```

---

## 사용법: 오픈소스 모델(로컬)

### 옵션 A — Ollama (권장)

Ollama는 별도 설정 없이 로컬에서 모델을 실행합니다. API 키가 필요 없습니다.

**1단계: Ollama 설치**

```bash
# macOS / Linux
curl -fsSL https://ollama.com/install.sh | sh

# 또는 https://ollama.com/download 에서 다운로드
```

**2단계: 모델 가져오기**

```bash
# 코딩용(권장)
ollama pull qwen2.5-coder
ollama pull qwen2.5-coder:32b

# 범용
ollama pull llama3.3
ollama pull llama3.2

# 추론
ollama pull deepseek-r1
ollama pull deepseek-r1:32b

# 기타
ollama pull phi4
ollama pull mistral
```

**3단계: Ollama 서버 시작** (macOS에서는 자동 실행, Linux에서는 수동 실행)

```bash
ollama serve     # http://localhost:11434 에서 시작
```

**4단계: nano claude 실행**

```bash
python nano_claude.py --model ollama/qwen2.5-coder
python nano_claude.py --model ollama/llama3.3
python nano_claude.py --model ollama/deepseek-r1
```

**로컬에서 사용 가능한 모델 목록 보기:**

```bash
ollama list
```

그다음 목록의 아무 모델이나 다음과 같이 사용할 수 있습니다:

```bash
python nano_claude.py --model ollama/<model-name>
```

### 옵션 B — LM Studio

LM Studio는 모델을 다운로드하고 실행할 수 있는 GUI와, OpenAI 호환 서버를 내장한 도구입니다.

**1단계:** [LM Studio](https://lmstudio.ai)를 다운로드하여 설치합니다.

**2단계:** LM Studio 내부에서 모델(GGUF 형식)을 검색하여 다운로드합니다.

**3단계:** **Local Server** 탭으로 이동해 **Start Server**를 클릭합니다(기본 포트: 1234).

**4단계:**

```bash
python nano_claude.py --model lmstudio/<model-name>
# 예시:
python nano_claude.py --model lmstudio/phi-4-GGUF
python nano_claude.py --model lmstudio/qwen2.5-coder-7b
```

모델 이름은 LM Studio 서버 상태 바에 표시되는 이름과 일치해야 합니다.

### 옵션 C — vLLM / 자체 호스팅 OpenAI 호환 서버

vLLM, TGI, llama.cpp server 등 OpenAI 호환 API를 제공하는 자체 추론 서버에 연결할 수 있습니다.

옵션 C 빠른 시작:

1단계: vLLM 시작
 ```bash
CUDA_VISIBLE_DEVICES=7 python -m vllm.entrypoints.openai.api_server \
      --model Qwen/Qwen2.5-Coder-7B-Instruct \
      --host 0.0.0.0 \
      --port 8000 \
      --enable-auto-tool-choice \
      --tool-call-parser hermes
```

2단계: nano claude 시작
```bash
export CUSTOM_BASE_URL=http://localhost:8000/v1
export CUSTOM_API_KEY=none
python nano_claude.py --model custom/Qwen/Qwen2.5-Coder-7B-Instruct
```

```bash
# 예시: vLLM이 Qwen2.5-Coder-32B를 서비스하는 경우
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-Coder-32B-Instruct \
    --port 8000

# 그런 다음 nano claude를 서버에 연결
python nano_claude.py
```

REPL 내부에서:

```text
/config custom_base_url=http://localhost:8000/v1
/config custom_api_key=token-abc123    # 인증이 없으면 생략
/model custom/Qwen2.5-Coder-32B-Instruct
```

또는 환경변수로 설정:

```bash
export CUSTOM_BASE_URL=http://localhost:8000/v1
export CUSTOM_API_KEY=token-abc123

python nano_claude.py --model custom/Qwen2.5-Coder-32B-Instruct
```

원격 GPU 서버라면:

```text
/config custom_base_url=http://192.168.1.100:8000/v1
/model custom/your-model-name
```

---

## 모델 이름 형식

아래 세 가지 형식을 모두 지원합니다.

```bash
# 1. 접두사로 자동 감지 (널리 알려진 모델에 동작)
python nano_claude.py --model gpt-4o
python nano_claude.py --model gemini-2.0-flash
python nano_claude.py --model deepseek-chat

# 2. 슬래시가 있는 명시적 프로바이더 접두사
python nano_claude.py --model ollama/qwen2.5-coder
python nano_claude.py --model kimi/moonshot-v1-128k

# 3. 콜론이 있는 명시적 프로바이더 접두사 (이것도 가능)
python nano_claude.py --model kimi:moonshot-v1-32k
python nano_claude.py --model qwen:qwen-max
```

**자동 감지 규칙:**

| 모델 접두사 | 감지되는 제공자 |
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

## CLI 레퍼런스

```text
python nano_claude.py [OPTIONS] [PROMPT]

옵션:
  -p, --print          비대화형: 프롬프트를 실행하고 종료
  -m, --model MODEL    모델 재정의 (예: gpt-4o, ollama/llama3.3)
  --accept-all         모든 작업 자동 승인 (권한 프롬프트 없음)
  --verbose            thinking 블록과 턴별 토큰 수 표시
  --thinking           Extended Thinking 활성화 (Claude 전용)
  --version            버전 출력 후 종료
  -h, --help           도움말 표시
```

**예시:**

```bash
# 기본 모델로 대화형 REPL
python nano_claude.py

# 시작 시 모델 전환
python nano_claude.py --model gpt-4o
python nano_claude.py -m ollama/deepseek-r1:32b

# 비대화형 / 스크립팅
python nano_claude.py --print "Write a Python fibonacci function"
python nano_claude.py -p "Explain the Rust borrow checker in 3 sentences" -m gemini/gemini-2.0-flash

# CI / 자동화 (권한 프롬프트 없음)
python nano_claude.py --accept-all --print "Initialize a Python project with pyproject.toml"

# 디버그 모드 (토큰 + thinking 확인)
python nano_claude.py --thinking --verbose
```

---

## 슬래시 명령어(REPL)

`/`를 입력하고 **Tab**을 누르면 자동완성됩니다.

| 명령어 | 설명 |
|---|---|
| `/help` | 모든 명령어 표시 |
| `/clear` | 대화 기록 지우기 |
| `/model` | 현재 모델 표시 + 사용 가능한 전체 모델 목록 |
| `/model <name>` | 모델 전환(즉시 적용) |
| `/config` | 현재 설정값 전체 보기 |
| `/config key=value` | 설정값 지정(디스크에 영속 저장) |
| `/save` | 세션 저장(타임스탬프 기반 자동 이름) |
| `/save <filename>` | 지정 이름으로 세션 저장 |
| `/load` | 저장된 세션 목록 보기 |
| `/load <filename>` | 저장된 세션 불러오기 |
| `/history` | 전체 대화 기록 출력 |
| `/context` | 메시지 수와 토큰 추정치 표시 |
| `/cost` | 토큰 사용량 및 예상 USD 비용 표시 |
| `/verbose` | verbose 모드 토글(토큰 + thinking) |
| `/thinking` | Extended Thinking 토글(Claude 전용) |
| `/permissions` | 현재 권한 모드 표시 |
| `/permissions <mode>` | 권한 모드 설정: `auto` / `accept-all` / `manual` |
| `/cwd` | 현재 작업 디렉터리 표시 |
| `/cwd <path>` | 작업 디렉터리 변경 |
| `/memory` | 영구 메모리 전체 목록 |
| `/memory <query>` | 키워드로 메모리 검색 |
| `/skills` | 사용 가능한 스킬 목록 |
| `/agents` | 서브에이전트 작업 상태 표시 |
| `/mcp` | 설정된 MCP 서버와 도구 목록 |
| `/mcp reload` | 모든 MCP 서버 재연결 및 도구 목록 갱신 |
| `/mcp reload <name>` | 특정 MCP 서버 하나만 재연결 |
| `/mcp add <name> <cmd> [args]` | 사용자 설정에 stdio MCP 서버 추가 |
| `/mcp remove <name>` | 사용자 설정에서 서버 제거 |
| `/exit` / `/quit` | 종료 |

**세션 내부에서 모델 전환:**

```text
[myproject] ❯ /model
  Current model: claude-opus-4-6  (provider: anthropic)

  Available models by provider:
    anthropic     claude-opus-4-6, claude-sonnet-4-6, ...
    openai        gpt-4o, gpt-4o-mini, o3-mini, ...
    ollama        llama3.3, llama3.2, phi4, mistral, ...
    ...

[myproject] ❯ /model gpt-4o
  Model set to gpt-4o  (provider: openai)

[myproject] ❯ /model ollama/qwen2.5-coder
  Model set to ollama/qwen2.5-coder  (provider: ollama)
```

---

## API 키 설정

### 방법 1: 환경변수 사용(권장)

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export OPENAI_API_KEY=sk-...
export GEMINI_API_KEY=AIza...
export MOONSHOT_API_KEY=sk-...
export DASHSCOPE_API_KEY=sk-...
export ZHIPU_API_KEY=...
export DEEPSEEK_API_KEY=sk-...
```

### 방법 2: REPL 안에서 설정(영속 저장)

```text
/config anthropic_api_key=sk-ant-...
/config openai_api_key=sk-...
/config gemini_api_key=AIza...
/config kimi_api_key=sk-...
/config qwen_api_key=sk-...
/config zhipu_api_key=...
/config deepseek_api_key=sk-...
```

키는 `~/.nano_claude/config.json`에 저장되며 다음 실행 시 자동 로드됩니다.

### 방법 3: 설정 파일 직접 수정

```json
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

## 권한 시스템

| 모드 | 동작 |
|---|---|
| `auto` (기본값) | 읽기 전용 작업은 항상 허용. Bash 명령과 파일 쓰기 전 확인 프롬프트 |
| `accept-all` | 절대 묻지 않음. 모든 작업 자동 진행 |
| `manual` | 읽기를 포함한 모든 단일 작업 전에 확인 |

**프롬프트 예시:**

```text
  Allow: Run: git commit -am "fix bug"  [y/N/a(ccept-all)]
```

- `y` — 이번 작업만 승인
- `n` 또는 Enter — 거부
- `a` — 승인하고 이번 세션 동안 `accept-all`로 전환

**`auto` 모드에서 항상 자동 승인되는 명령:**
`ls`, `cat`, `head`, `tail`, `wc`, `pwd`, `echo`, `git status`, `git log`, `git diff`, `git show`, `find`, `grep`, `rg`, `python`, `node`, `pip show`, `npm list` 및 기타 읽기 전용 셸 명령

---

## 내장 도구

### 핵심 도구

| 도구 | 설명 | 주요 매개변수 |
|---|---|---|
| `Read` | 줄 번호와 함께 파일 읽기 | `file_path`, `limit`, `offset` |
| `Write` | 파일 생성 또는 덮어쓰기(diff 표시) | `file_path`, `content` |
| `Edit` | 정확한 문자열 치환(diff 표시) | `file_path`, `old_string`, `new_string`, `replace_all` |
| `Bash` | 셸 명령 실행 | `command`, `timeout` (기본 30초) |
| `Glob` | glob 패턴으로 파일 찾기 | `pattern`, `path` |
| `Grep` | 파일 내 정규식 검색 | `pattern`, `path`, `glob`, `output_mode` |
| `WebFetch` | URL에서 텍스트를 가져오고 추출 | `url`, `prompt` |
| `WebSearch` | DuckDuckGo를 통한 웹 검색 | `query` |

### 메모리 도구

| 도구 | 설명 | 주요 매개변수 |
|---|---|---|
| `MemorySave` | 영구 메모리 저장 또는 갱신 | `name`, `type`, `description`, `content`, `scope` |
| `MemoryDelete` | 이름으로 메모리 삭제 | `name`, `scope` |
| `MemorySearch` | 키워드(또는 AI 랭킹)로 메모리 검색 | `query`, `scope`, `use_ai`, `max_results` |
| `MemoryList` | 나이와 메타데이터를 포함한 메모리 목록 | `scope` |

### 서브에이전트 도구

| 도구 | 설명 | 주요 매개변수 |
|---|---|---|
| `Agent` | 작업을 위해 서브에이전트 생성 | `prompt`, `subagent_type`, `isolation`, `name`, `model`, `wait` |
| `SendMessage` | 이름이 있는 백그라운드 에이전트에 메시지 전송 | `name`, `message` |
| `CheckAgentResult` | 백그라운드 에이전트의 상태/결과 확인 | `task_id` |
| `ListAgentTasks` | 활성/완료된 에이전트 작업 목록 | — |
| `ListAgentTypes` | 사용 가능한 에이전트 타입 정의 목록 | — |

### 스킬 도구

| 도구 | 설명 | 주요 매개변수 |
|---|---|---|
| `Skill` | 대화 안에서 이름으로 스킬 호출 | `name`, `args` |
| `SkillList` | 트리거와 메타데이터를 포함한 전체 스킬 목록 | — |

### MCP 도구

MCP 도구는 설정된 서버에서 자동 발견되며 `mcp__<server>__<tool>` 이름으로 등록됩니다. Claude는 이를 내장 도구와 동일하게 사용할 수 있습니다.

| 예시 도구 이름 | 출처 |
|---|---|
| `mcp__git__git_status` | `git` 서버의 `git_status` 도구 |
| `mcp__filesystem__read_file` | `filesystem` 서버의 `read_file` 도구 |
| `mcp__myserver__my_action` | 사용자가 설정한 커스텀 서버 |

> **커스텀 도구 추가:** 직접 도구를 등록하는 방법은 [Architecture Guide](docs/architecture.md#tool-registry)를 참고하세요.

---

## 메모리

모델은 내장 메모리 시스템을 통해 대화 간에도 내용을 기억할 수 있습니다.

**작동 방식:** 메모리는 Markdown 파일로 저장됩니다. 스코프는 두 가지입니다.
- **사용자 스코프** (`~/.nano_claude/memory/`) — 모든 프로젝트에서 공통 사용
- **프로젝트 스코프** (`.nano_claude/memory/` in cwd) — 현재 저장소 전용

`MEMORY.md` 인덱스(최대 200줄 / 25KB)는 저장 또는 삭제 시마다 자동 재구성되며, 시스템 프롬프트에 주입되어 Claude가 항상 전체 개요를 알 수 있습니다.

**메모리 타입:**

| 타입 | 사용 용도 |
|---|---|
| `user` | 사용자 역할, 선호, 배경 |
| `feedback` | 모델이 어떻게 행동하길 원하는지 |
| `project` | 진행 중인 작업, 마감, 결정 사항 |
| `reference` | 외부 리소스 링크 |

**메모리 파일 형식** (`~/.nano_claude/memory/coding_style.md`):
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

**예시 상호작용:**

```text
You: Remember that I prefer 4-space indentation and type hints in all Python code.
AI: [calls MemorySave] Memory saved: coding_style [feedback/user]

You: /memory
  [feedback/user] coding_style (today): Python formatting preferences

You: /memory python
  [feedback/user] coding_style: Prefers 4-space indent and type hints in Python
```

**오래됨 경고:** 1일보다 오래된 메모리는 `/memory` 출력에서 freshness 메모가 추가되어 검토/업데이트 시점을 알 수 있습니다.

**AI 랭킹 검색:** `MemorySearch(query="...", use_ai=true)`는 단순 키워드 매칭 대신 모델이 관련성에 따라 결과를 정렬합니다.

---

## 스킬

스킬은 모델에 특화된 능력을 부여하는 재사용 가능한 프롬프트 템플릿입니다. 별도 설정 없이 바로 사용할 수 있는 내장 스킬 두 개가 포함되어 있습니다.

**내장 스킬:**

| 트리거 | 설명 |
|---|---|
| `/commit` | staged 변경을 검토하고 구조화된 git 커밋 생성 |
| `/review [PR]` | 코드 또는 PR diff를 구조화된 피드백으로 검토 |

**빠른 시작 — 커스텀 스킬:**

```bash
mkdir -p ~/.nano_claude/skills
```

`~/.nano_claude/skills/deploy.md` 생성:

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

이제 다음처럼 사용합니다:

```text
You: /deploy staging 2.1.0
AI: [deploys version 2.1.0 to staging]
```

**인자 치환:**
- `$ARGUMENTS` — 전체 원시 인자 문자열
- `$ARG_NAME` — 이름이 지정된 위치 인자 치환
- 누락된 인자는 빈 문자열이 됨

**실행 모드:**
- `context: inline` (기본값) — 현재 대화 히스토리 안에서 실행
- `context: fork` — 새 히스토리의 격리된 서브에이전트로 실행, `model` override 지원

**우선순위** (높을수록 우선): project-level > user-level > built-in

**스킬 목록 보기:** `/skills`

**스킬 검색 경로:**

```text
./.nano_claude/skills/
~/.nano_claude/skills/
```

---

## 서브에이전트

모델은 병렬로 작업을 처리하기 위해 독립적인 서브에이전트를 생성할 수 있습니다.

**내장 특화 에이전트 타입:**

| 타입 | 최적화 대상 |
|---|---|
| `general-purpose` | 조사, 탐색, 다단계 작업 |
| `coder` | 코드 작성, 읽기, 수정 |
| `reviewer` | 보안, 정확성, 코드 품질 분석 |
| `researcher` | 웹 검색, 문서 조사 |
| `tester` | 테스트 작성 및 실행 |

**기본 사용법:**
```text
You: Search this codebase for all TODO comments and summarize them.
AI: [calls Agent(prompt="...", subagent_type="researcher")]
    Sub-agent reads files, greps for TODOs...
    Result: Found 12 TODOs across 5 files...
```

**백그라운드 모드** — 기다리지 않고 생성한 뒤 나중에 결과 수집:
```text
AI: [calls Agent(prompt="run all tests", name="test-runner", wait=false)]
AI: [continues other work...]
AI: [calls CheckAgentResult / SendMessage to follow up]
```

**Git worktree 격리** — 충돌 없이 격리된 브랜치에서 작업:
```text
Agent(prompt="refactor auth module", isolation="worktree")
```

변경이 없으면 worktree는 자동 정리되고, 변경이 있으면 브랜치 이름이 보고됩니다.

**커스텀 에이전트 타입** — `~/.nano_claude/agents/myagent.md` 생성:
```markdown
---
name: myagent
description: Specialized for X
model: claude-haiku-4-5-20251001
tools: [Read, Grep, Bash]
---
Extra system prompt for this agent type.
```

**실행 중 에이전트 목록:** `/agents`

서브에이전트는 독립적인 대화 기록을 가지며, 파일 시스템은 공유하고, 중첩은 3단계까지 제한됩니다.

---

## MCP (Model Context Protocol)

MCP를 사용하면 로컬 서브프로세스나 원격 HTTP 기반의 외부 도구 서버를 연결할 수 있고, Claude는 그 도구를 자동으로 사용할 수 있습니다. 이는 Claude Code가 기능 확장에 사용하는 것과 동일한 프로토콜입니다.

### 지원 전송 방식

| 전송 방식 | 설정 `type` | 설명 |
|---|---|---|
| **stdio** | `"stdio"` | 로컬 서브프로세스 실행(가장 일반적) |
| **SSE** | `"sse"` | HTTP Server-Sent Events 스트림 |
| **HTTP** | `"http"` | 스트리밍 가능한 HTTP POST(신형 서버) |

### 설정

프로젝트 디렉터리에 `.mcp.json` 파일을 두거나, 사용자 전체 서버용으로 `~/.nano_claude/mcp.json`을 수정하세요.

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

설정 우선순위: 프로젝트의 `.mcp.json`이 사용자 `~/.nano_claude/mcp.json`보다 같은 서버 이름에 대해 우선합니다.

### 빠른 시작

```bash
pip install uv
uvx mcp-server-git --help

/mcp add git uvx mcp-server-git

# 또는 프로젝트 디렉터리에 .mcp.json 생성 후:
/mcp reload
```

### REPL 명령어

```text
/mcp
/mcp reload
/mcp reload git
/mcp add myserver uvx mcp-server-x
/mcp remove myserver
```

### Claude가 MCP 도구를 사용하는 방식

연결 후 Claude는 MCP 도구를 직접 호출할 수 있습니다:

```text
You: What files changed in the last git commit?
AI: [calls mcp__git__git_diff_staged()]
    → shows diff output from the git MCP server
```

도구 이름은 `mcp__<server_name>__<tool_name>` 형식을 따릅니다. 영숫자나 `_`가 아닌 문자는 자동으로 `_`로 치환됩니다.

### 인기 있는 MCP 서버

| 서버 | 설치 | 제공 기능 |
|---|---|---|
| `mcp-server-git` | `uvx mcp-server-git` | git 작업(status, diff, log, commit) |
| `mcp-server-filesystem` | `uvx mcp-server-filesystem <path>` | 파일 읽기/쓰기/목록 |
| `mcp-server-fetch` | `uvx mcp-server-fetch` | HTTP fetch |
| `mcp-server-postgres` | `uvx mcp-server-postgres <conn-str>` | PostgreSQL 질의 |
| `mcp-server-sqlite` | `uvx mcp-server-sqlite --db-path x.db` | SQLite 질의 |
| `mcp-server-brave-search` | `uvx mcp-server-brave-search` | Brave 웹 검색 |

> 전체 레지스트리: [modelcontextprotocol.io/servers](https://modelcontextprotocol.io/servers)

---

## 플러그인 시스템

`plugin/` 패키지를 사용하면 git 저장소나 로컬 디렉터리에서 추가 도구, 스킬, MCP 서버를 불러와 nano-claude-code를 확장할 수 있습니다.

### 플러그인 설치

```bash
/plugin install my-plugin@https://github.com/user/my-plugin
/plugin install local-plugin@/path/to/local/plugin
```

### 플러그인 관리

```bash
/plugin
/plugin enable my-plugin
/plugin disable my-plugin
/plugin disable-all
/plugin update my-plugin
/plugin uninstall my-plugin
/plugin info my-plugin
```

### 플러그인 추천 엔진

```bash
/plugin recommend
/plugin recommend "docker database"
```

추천 엔진은 태그와 키워드 점수를 사용해 curated marketplace(git-tools, python-linter, docker-tools, sql-tools, test-runner, diagram-tools, aws-tools, web-scraper)와 현재 컨텍스트를 매칭합니다.

### 플러그인 매니페스트 (`plugin.json`)

```json
{
  "name": "my-plugin",
  "version": "0.1.0",
  "description": "Does something useful",
  "author": "you",
  "tags": ["git", "python"],
  "tools": ["tools"],
  "skills": ["skills/my.md"],
  "mcp_servers": {},
  "dependencies": ["httpx"]
}
```

또는 `PLUGIN.md`에서 YAML frontmatter를 사용할 수 있습니다.

### 스코프

| 스코프 | 위치 | 설정 |
|-------|----------|--------|
| user (기본) | `~/.nano_claude/plugins/` | `~/.nano_claude/plugins.json` |
| project | `.nano_claude/plugins/` | `.nano_claude/plugins.json` |

프로젝트 스코프로 설치하려면 `--project` 플래그 사용: `/plugin install name@url --project`

---

## AskUserQuestion 도구

Claude는 작업 도중 멈추고, 다음 단계로 넘어가기 전에 사용자에게 대화형 질문을 할 수 있습니다.

**Claude의 호출 예시:**
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

**터미널에 보이는 형태:**
```text
❓ Question from assistant:
   Which database should I use?

  [1] SQLite — Simple, file-based
  [2] PostgreSQL — Full-featured, requires server
  [0] Type a custom answer

Your choice (number or text):
```

- 번호로 선택하거나 자유 텍스트를 직접 입력할 수 있습니다.
- Claude는 응답을 받은 뒤 작업을 계속합니다.
- 5분 타임아웃이 있으며, 응답이 없으면 `"(no answer — timeout)"`이 반환됩니다.

---

## 작업 관리

`task/` 패키지는 Claude와 사용자가 세션 내 다단계 작업을 구조화된 목록으로 추적할 수 있게 해줍니다.

### Claude가 사용할 수 있는 도구

| 도구 | 매개변수 | 설명 |
|------|-----------|--------------|
| `TaskCreate` | `subject`, `description`, `active_form?`, `metadata?` | 작업 생성; `#id created: subject` 반환 |
| `TaskUpdate` | `task_id`, `subject?`, `description?`, `status?`, `owner?`, `add_blocks?`, `add_blocked_by?`, `metadata?` | 모든 필드 갱신; `status='deleted'`이면 작업 제거 |
| `TaskGet` | `task_id` | 특정 작업의 전체 상세 반환 |
| `TaskList` | _(none)_ | 상태 아이콘과 blocker 정보를 포함한 전체 작업 목록 |

**유효한 상태:** `pending` → `in_progress` → `completed` / `cancelled` / `deleted`

### 의존성 엣지

```text
TaskUpdate(task_id="3", add_blocked_by=["1","2"])
# 작업 3은 작업 1과 2가 끝나야 진행 가능
# 역방향 엣지도 자동 설정되어 1과 2의 "blocks"에 3이 추가됨
```

완료된 작업은 해결된 것으로 간주되어, `TaskList`에서 후속 작업을 막지 않습니다.

### 영속화

작업은 변경될 때마다 현재 작업 디렉터리의 `.nano_claude/tasks.json`에 저장되며, 첫 접근 시 다시 로드됩니다.

### REPL 명령어

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

### 전형적인 Claude 작업 흐름

```text
User: implement the login feature

Claude:
  TaskCreate(subject="Design auth schema", description="JWT vs session")  → #1
  TaskCreate(subject="Write login endpoint", description="POST /auth/login") → #2
  TaskCreate(subject="Write tests", description="Unit + integration") → #3
  TaskUpdate(task_id="2", add_blocked_by=["1"])
  TaskUpdate(task_id="3", add_blocked_by=["2"])

  TaskUpdate(task_id="1", status="in_progress", active_form="Designing schema")
  ... (does the work) ...
  TaskUpdate(task_id="1", status="completed")
  TaskList()  → task 2 is now unblocked
  ...
```

---

## 컨텍스트 압축

긴 대화는 모델의 컨텍스트 창 안에 유지되도록 자동 압축됩니다.

**두 개의 레이어:**

1. **Snip** — 오래된 도구 출력(파일 읽기, bash 결과)을 몇 턴 뒤 잘라냅니다. 빠르고 API 비용이 없습니다.
2. **Auto-compact** — 토큰 사용량이 컨텍스트 제한의 70%를 넘으면, 오래된 메시지를 모델이 간결한 요약으로 압축합니다.

이 과정은 투명하게 일어나므로 사용자가 따로 할 일은 없습니다.

---

## Diff 보기

모델이 파일을 수정하거나 덮어쓸 때 Git 스타일 diff가 표시됩니다:

```diff
  Changes applied to config.py:

--- a/config.py
+++ b/config.py
@@ -12,7 +12,7 @@
     "model": "claude-opus-4-6",
-    "max_tokens": 8192,
+    "max_tokens": 16384,
     "permission_mode": "auto",
```

초록색 줄은 추가, 빨간 줄은 삭제를 의미합니다. 새 파일 생성 시에는 대신 요약이 표시됩니다.

---

## CLAUDE.md 지원

프로젝트에 `CLAUDE.md` 파일을 두면 코드베이스에 대한 지속적 컨텍스트를 모델에 제공할 수 있습니다. Nano Claude는 이를 자동으로 찾아 시스템 프롬프트에 주입합니다.

```text
~/.claude/CLAUDE.md
/your/project/CLAUDE.md
```

**예시 `CLAUDE.md`:**

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

## 세션 관리

```bash
/save
/save debug_auth_bug

/load
/load debug_auth_bug
/load session_20260401_143022.json
```

세션은 `~/.nano_claude/sessions/`에 JSON 형식으로 저장됩니다.

---

## 프로젝트 구조

```text
nano_claude_code/
├── nano_claude.py        # 진입점: REPL + 슬래시 명령 + diff 렌더링
├── agent.py              # 에이전트 루프: 스트리밍, 도구 디스패치, 압축
├── providers.py          # 멀티 프로바이더: Anthropic, OpenAI 호환 스트리밍
├── tools.py              # 핵심 도구(Read/Write/Edit/Bash/Glob/Grep/Web) + 레지스트리 연결
├── tool_registry.py      # 도구 플러그인 레지스트리: 등록, 조회, 실행
├── compaction.py         # 컨텍스트 압축: snip + auto-summarize
├── context.py            # 시스템 프롬프트 빌더: CLAUDE.md + git + memory
├── config.py             # 설정 로드/저장/기본값
│
├── multi_agent/          # 멀티 에이전트 패키지
├── subagent.py           # 하위 호환 shim → multi_agent/
├── memory/               # 메모리 패키지
├── memory.py             # 하위 호환 shim → memory/
├── skill/                # 스킬 패키지
├── skills.py             # 하위 호환 shim → skill/
├── mcp/                  # MCP 패키지
└── tests/                # 135개 단위 테스트
```

> **개발자 참고:** 각 기능 패키지(`multi_agent/`, `memory/`, `skill/`, `mcp/`)는 자체 포함형입니다. 커스텀 도구는 `tools.py`에서 import되는 모듈 내 어디에서든 `register_tool(ToolDef(...))`를 호출해 추가할 수 있습니다.

---

## FAQ

**Q: MCP 서버는 어떻게 추가하나요?**

방법 1 — REPL:
```text
/mcp add git uvx mcp-server-git
```

방법 2 — 프로젝트에 `.mcp.json` 생성:
```json
{
  "mcpServers": {
    "git": {"type": "stdio", "command": "uvx", "args": ["mcp-server-git"]}
  }
}
```

그 후 `/mcp reload`를 실행하거나 재시작하세요. 연결 상태는 `/mcp`로 확인합니다.

**Q: MCP 서버에 오류가 보입니다. 어떻게 디버깅하나요?**

```text
/mcp
/mcp reload git
```

stdio 서버라면 명령이 `$PATH`에 있는지 확인하세요:
```bash
which uvx
uvx mcp-server-git
```

**Q: 인증이 필요한 MCP 서버도 사용할 수 있나요?**

HTTP/SSE + Bearer token:
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

env 기반 인증을 쓰는 stdio 서버:
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

**Q: 로컬 Ollama 모델에서 tool call이 동작하지 않습니다.**

모든 모델이 function calling을 지원하는 것은 아닙니다. 권장 모델: `qwen2.5-coder`, `llama3.3`, `mistral`, `phi4`.

```bash
ollama pull qwen2.5-coder
python nano_claude.py --model ollama/qwen2.5-coder
```

**Q: vLLM이 돌아가는 원격 GPU 서버에는 어떻게 연결하나요?**

```text
/config custom_base_url=http://your-server-ip:8000/v1
/config custom_api_key=your-token
/model custom/your-model-name
```

**Q: API 비용은 어떻게 확인하나요?**

```text
/cost

  Input tokens:  3,421
  Output tokens:   892
  Est. cost:     $0.0648 USD
```

**Q: 한 세션에서 여러 API 키를 쓸 수 있나요?**

예. 필요한 키를 먼저 모두 설정해 두면(환경변수 또는 `/config`), 모델을 자유롭게 바꿔도 각 호출은 현재 활성 프로바이더의 키를 사용합니다.

**Q: 모든 프로젝트에서 기본으로 쓰려면 어떻게 하나요?**

키를 `~/.bashrc` 또는 `~/.zshrc`에 넣고, 기본 모델을 `~/.nano_claude/config.json`에 설정하세요:

```json
{ "model": "claude-sonnet-4-6" }
```

**Q: Qwen / Zhipu에서 깨진 텍스트가 나옵니다.**

`DASHSCOPE_API_KEY` / `ZHIPU_API_KEY`가 올바른지, 계정에 충분한 quota가 있는지 확인하세요. 두 제공자 모두 UTF-8을 사용하며 중국어 처리를 잘 지원합니다.

**Q: nano claude에 파이프로 입력할 수 있나요?**

```bash
echo "Explain this file" | python nano_claude.py --print --accept-all
cat error.log | python nano_claude.py -p "What is causing this error?"
```

**Q: 어디서든 CLI처럼 실행하려면 어떻게 하나요?**

```bash
alias nc='python /path/to/nano_claude_code/nano_claude.py'

# 또는 setup.py가 있으면
pip install -e .
```
