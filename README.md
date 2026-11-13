<div align="center">

<h1>Devin 4.0</h1>
<h3>An AI agent that operates your computer the way a person does:<br/>it looks at the screen, moves the mouse, clicks and types — driven by a model running on your own machine.</h3>

[![CI](https://github.com/kevinhamza/Devin-4.0/actions/workflows/devin-ci.yml/badge.svg)](https://github.com/kevinhamza/Devin-4.0/actions/workflows/devin-ci.yml)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)

</div>

---

## What it is

You type a task in the terminal. Devin takes a screenshot, works out what is on it, plans what to do, and then
carries the plan out with the **real pointer and the real keyboard** — in any application, with no
per-application code and no hard-coded coordinates. After every single action it takes a fresh screenshot
and checks that the screen did what the action was supposed to do.

The model that does the thinking is served by [Ollama](https://ollama.com) on `localhost:11434`. Nothing
leaves your machine.

```
  ❯ open the calculator

  ◆ Thought for 1m 2s
    I need to open the calculator app by clicking Activities, searching for it, and selecting the icon.
    1. click "Activities"
    2. type "calculator"
    3. click "Calculator"
    4. done: the calculator is now open
  › click "Activities"
    the app search is open now
  › type "calculator"
    the field now reads "calculator"
  › click "Calculator"
    now in front: "Calculator"
  › Checked the screen: the task is complete
    The screen shows the "Calculator" application window open with input fields and buttons visible.

  the calculator is now open

  Worked for 2m 5s
```

That is from a real run on a 2-core laptop with a 4B local model. Most of the two minutes is the model thinking;
the mouse and keyboard part takes about ten seconds.

## How it works

```
 LOOK    screenshot  +  what is on it: accessibility tree and OCR of the pixels
   │
 THINK   the model reasons about the task and writes the next actions as plain lines
   │       click "name"    type "text" ENTER    key escape    scroll down    done "…"
   │
 ACT     one action at a time: the pointer glides to the exact spot and clicks,
   │     text is typed key by key at a human pace
   │
 CHECK   wait until the screen is still, take a new screenshot, compare:
           did the window change?  is the typed text really in the field?  did anything happen at all?
   │
   ├── as planned ──────────────► next action
   ├── something unexpected ────► drop the rest of the plan, look again, THINK again
   └── model says "done" ───────► the claim is checked against the screen before it is accepted
```

A few things the loop does that matter in practice:

- **A new window means stop and look.** A plan cannot know what a window it has never seen will show
  (a profile chooser, a first-run dialog, a different layout). When one appears, the rest of the plan is
  thrown away and the model is shown the new screen.
- **"Done" is never taken on trust.** The claim is checked against the screenshot. If the check says no,
  the task continues — or ends honestly as *not finished*, with what was done and what the screen shows.
- **Clicks are found by name, on the live screen.** `click "Images"` is resolved against the current
  screenshot at the moment of clicking, tolerant of OCR slips and of names written with or without spaces.
- **Screenshot timing.** Before the model is asked anything, Devin watches the screen until it has stopped
  changing, so it never reasons over a half-drawn window.

## Requirements

| | |
|---|---|
| **OS** | Linux. Developed and tested on GNOME (Wayland). Backends for other Wayland desktops (`ydotool`), plain X11 (`xdotool`) and macOS/Windows (`pyautogui`) are in the code but have **not** been tested on a real desktop. |
| **Python** | 3.9 or newer for Devin itself. On GNOME the system Python (`/usr/bin/python3`) must have PyGObject — it does on most distributions. |
| **Model server** | [Ollama](https://ollama.com) running locally, with at least one model pulled. A model that can see images is preferred. |
| **System packages** | `sudo apt install -y tesseract-ocr xclip python3-gi gir1.2-atspi-2.0 gir1.2-gstreamer-1.0 gstreamer1.0-pipewire` — and `ydotool` on non-GNOME Wayland desktops. |

## Install

```bash
git clone https://github.com/kevinhamza/Devin-4.0
cd Devin-4.0
python3 -m venv venv && source venv/bin/activate
./devin --setup        # installs the Python packages and lists any system package still missing
./devin --doctor       # checks screen capture, input control, OCR, the model, and power
```

`--doctor` should end up looking like this:

```
  ✓ mouse and keyboard control  gnome · screen 1366x768
  ✓ screen capture  1366x768 in 0.04s
  ✓ on-screen text reading (OCR)  tesseract
  ✓ model that works the computer  bonsai-2:4b · 4.2B · vision
  ✓ power  plugged in (60%)
```

Pull a model if you have none yet, for example `ollama pull bonsai-2:4b`.

## Use

```bash
./devin                           # interactive terminal
./devin --do "open the calculator"    # one task with the mouse and keyboard, then exit
./devin --chat "what can you do?"     # one answer; the computer is not touched
./devin "search for mountain photos"  # Devin decides: answer, or act
```

In the interactive terminal, **Shift+Tab** switches between three modes:

| Mode | What a message does |
|---|---|
| `auto` | Devin decides whether to answer or to operate the computer |
| `agent` | every message is a task carried out on the computer |
| `chat` | conversation only; the computer is never touched |

Commands inside the terminal:

| | |
|---|---|
| `/do <task>` · `/chat <message>` | force one or the other for a single message |
| `/look` | describe what is on the screen right now |
| `/model [name]` · `/models` · `/pull <name>` | show, switch, list or download Ollama models |
| `/eyes auto\|always\|never` | when the screenshot itself is sent to the model (see below) |
| `/steps <n>` | most actions per task |
| `/shell on\|off` | let Devin also run commands directly instead of through a terminal window (off by default) |
| `/doctor` | run the checks |
| `!<command>` | run a shell command yourself |
| **Ctrl+C** | stop the current task |

## Safety

Devin drives the same desktop you are working on, so the loop refuses a number of things outright,
whatever the model asks for:

- **It never restarts, shuts down, locks or logs out of the computer** — not by clicking, not by a key
  combination, not by a typed command — unless the task itself asks for exactly that. If such a dialog
  appears anyway, it is cancelled at once.
- **It never types into, or closes, the terminal it is running in.**
- **It types only where a text field has the keyboard** (the field reports focus, or it was just clicked).
  Letters sent to a window without a focused field are commands in many programs.
- **The top bar, system menus and notification pop-ups are not click targets.**
- **Destructive shell commands** (`rm -rf /`, `mkfs`, `dd of=/dev/…`, …) need your confirmation.
- A small model that is told "not finished" gets a limited number of further tries, then the task ends
  as failed rather than letting it change things at random.

These rules exist because of real incidents during development, and each one has a test.
They reduce risk; they do not remove it. **Watch a task while it runs, and press Ctrl+C if it goes wrong.**
Do not leave Devin unattended with unsaved work open.

## Configuration

Set these in `.env` (never commit that file) or in the environment:

| Variable | Default | Meaning |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | the Ollama server — may be another machine on your network |
| `OLLAMA_MODEL` | most capable installed | model used for conversation |
| `DEVIN_AGENT_MODEL` | an installed model that can see | model that operates the computer |
| `DEVIN_INPUT_BACKEND` | automatic | `gnome`, `ydotool`, `xdotool` or `pyautogui` |
| `DEVIN_MAX_STEPS` | `40` | most actions per task |
| `DEVIN_MAX_THINKS` | `10` | most times the model is consulted per task |
| `DEVIN_EYES` | `auto` | `auto`, `always`, `never` — when the screenshot itself goes to the model |
| `DEVIN_PROFILE` | `auto` | `lean` (short prompts for slow models), `full`, or measured automatically |
| `DEVIN_TYPE_INTERVAL` | `0.045` | seconds per key when typing |
| `DEVIN_ALLOW_SHELL` | `0` | `1` lets Devin run commands directly; `0` means mouse and keyboard only |
| `DEVIN_PROTECT_TERMINAL` | `1` | `0` switches off the "never type into my own terminal" guard |
| `DEVIN_TRACE` | off | `1` writes every prompt, reply and outcome to `$XDG_RUNTIME_DIR/devin/trace.jsonl` |

If `OLLAMA_MODEL` names a model that cannot see images and another installed model can, the seeing model
operates the computer and the named one is kept for conversation.

## Speed, and choosing a model

How well Devin does depends almost entirely on the model, and how fast it is depends on your hardware.

Measured on the development machine — a laptop with a 2-core i5-6300U, 8 GB RAM, no usable GPU — with
`bonsai-2:4b`:

| | |
|---|---|
| reading a prompt | about 5–6 tokens per second |
| one "think" (a prompt of ~450 tokens plus the reply) | 1 to 2 minutes |
| acting and checking the screenshot | 1 to 5 seconds per action |
| "open the calculator", model planning alone | worked, 2 min 5 s |
| a web search in a browser, plan supplied | worked, 91 s including the final check |
| multi-screen tasks with the model planning alone (browser with a profile chooser, a pentest tool's start-up wizard) | **did not finish** — the model lost its way |

So, on a machine like that, expect short single-application tasks to work and long multi-screen tasks to
fail. Three design decisions follow directly from those numbers:

1. **The model writes a plan, not one action per call.** A slow model cannot be asked before every click,
   and a small one is much better at laying out steps than at picking one action from a list.
2. **Plain text, not JSON.** Schema-constrained output was several times slower on this model.
3. **Text read off the screenshot instead of the picture itself** (`DEVIN_EYES=auto`). A small model
   reads a shrunken screenshot badly — it described a full-screen calculator as "a blank workspace" —
   and pays about twenty seconds for it. A fast, strong model is sent the screenshot every time.

A stronger model on a faster machine changes the picture: point `OLLAMA_BASE_URL` at it. Running on
battery slows a laptop's CPU and therefore the model; `./devin --doctor` tells you.

## Known limits

- Only GNOME on Wayland has been tested on a real desktop.
- Web pages are read by OCR: Chrome does not expose page content through the accessibility tree here,
  so icons without text cannot be targeted by a text-only model.
- A weak model still makes weak decisions. The loop catches wrong actions and false "done" claims; it
  cannot supply reasoning the model does not have.
- On the `ydotool` backend typing assumes a US keyboard layout. Characters that are not on the keyboard are pasted through the clipboard.

## Tests

```bash
./devin --test
```

Runs the unit tests of the loop and of the input layer against a **fake desktop** — they never move the
real pointer. They cover the plan/act/check loop, the label matcher, the action parser, and every safety
rule above.

## Where things are

| File | What it does |
|---|---|
| `devin` | launcher script |
| `main.py` | entry point, argument parsing |
| `modules/devin_repl.py` | the terminal interface |
| `modules/screen_vision.py` | the look → think → act → check loop, the parser, the safety rules |
| `modules/os_automation.py` | pointer, keyboard, screen capture, accessibility tree (all backends) |
| `modules/ollama_provider.py` | talking to Ollama |
| `modules/os_agent.py` | object-style access to the same functions for other code |
| `tests/test_computer_agent.py`, `tests/test_os_agent.py` | the tests |

The repository also contains the earlier Devin runtime (`agent.py`, the other files under `modules/`, the
TypeScript CLI in `src/`) and third-party projects under `repos/` and `external/`. `./devin --load-all`,
`--status`, `--caps` and `DEVIN_USE_CLASSIC_REPL=1` still reach them. They are not part of the loop
described here and are not covered by the tests above.

## Authorized use only

Devin acts with your permissions on your machine. Use it on systems you own or are explicitly allowed to
operate, and never commit `.env` or API keys.

## License

MIT — see [LICENSE](LICENSE).
