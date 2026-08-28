// src/tools/definitions.ts — All tool definitions for Devin AGI
// Covers: file I/O, shell, web, OS automation (mouse/keyboard/windows/apps),
// memory, voice, pentesting, cloud, agents.

import { ToolDefinition } from '../types.js';

export const CORE_TOOLS: ToolDefinition[] = [
  // ── File System ──────────────────────────────────────────────────────────
  {
    name: 'read_file',
    description: 'Read file contents at a path. Returns numbered lines.',
    input_schema: {
      type: 'object',
      properties: {
        path: { type: 'string', description: 'Absolute or relative path to the file' },
        offset: { type: 'number', description: 'Starting line number (1-indexed)' },
        limit: { type: 'number', description: 'Max lines to read' },
      },
      required: ['path'],
    },
  },
  {
    name: 'write_file',
    description: 'Write content to a file, creating it if needed.',
    input_schema: {
      type: 'object',
      properties: {
        path: { type: 'string', description: 'Path to write' },
        content: { type: 'string', description: 'Content to write' },
      },
      required: ['path', 'content'],
    },
  },
  {
    name: 'edit_file',
    description: 'Replace a specific string in a file with new content.',
    input_schema: {
      type: 'object',
      properties: {
        path: { type: 'string', description: 'File path' },
        old_string: { type: 'string', description: 'Exact text to replace' },
        new_string: { type: 'string', description: 'Replacement text' },
        replace_all: { type: 'string', description: '"true" to replace all occurrences' },
      },
      required: ['path', 'old_string', 'new_string'],
    },
  },
  {
    name: 'list_files',
    description: 'List files and directories at a path.',
    input_schema: {
      type: 'object',
      properties: {
        path: { type: 'string', description: 'Directory to list' },
        recursive: { type: 'string', description: '"true" to list recursively' },
        pattern: { type: 'string', description: 'Glob filter (e.g. "*.py")' },
      },
      required: ['path'],
    },
  },
  {
    name: 'delete_file',
    description: 'Delete a file or empty directory.',
    input_schema: {
      type: 'object',
      properties: { path: { type: 'string', description: 'Path to delete' } },
      required: ['path'],
    },
  },
  {
    name: 'create_directory',
    description: 'Create a directory and all parents.',
    input_schema: {
      type: 'object',
      properties: { path: { type: 'string', description: 'Directory to create' } },
      required: ['path'],
    },
  },
  {
    name: 'search_files',
    description: 'Search for a pattern in files (grep-style).',
    input_schema: {
      type: 'object',
      properties: {
        pattern: { type: 'string', description: 'Regex or text pattern' },
        path: { type: 'string', description: 'Directory to search in' },
        file_pattern: { type: 'string', description: 'File glob (e.g. "*.py")' },
        case_sensitive: { type: 'string', description: '"false" for case-insensitive' },
      },
      required: ['pattern'],
    },
  },

  // ── Shell / Process ──────────────────────────────────────────────────────
  {
    name: 'execute_shell',
    description: 'Run a shell command. Returns stdout + stderr.',
    input_schema: {
      type: 'object',
      properties: {
        command: { type: 'string', description: 'Shell command' },
        cwd: { type: 'string', description: 'Working directory' },
        timeout: { type: 'number', description: 'Timeout ms (default 30000)' },
        background: { type: 'string', description: '"true" to run in background' },
      },
      required: ['command'],
    },
  },
  {
    name: 'execute_python',
    description: 'Execute Python code and return output.',
    input_schema: {
      type: 'object',
      properties: {
        code: { type: 'string', description: 'Python code' },
        cwd: { type: 'string', description: 'Working directory' },
      },
      required: ['code'],
    },
  },
  {
    name: 'kill_process',
    description: 'Kill a running process by PID.',
    input_schema: {
      type: 'object',
      properties: {
        pid: { type: 'number', description: 'Process ID' },
        signal: { type: 'string', description: 'Signal name (SIGTERM, SIGKILL)' },
      },
      required: ['pid'],
    },
  },

  // ── Web / Network ─────────────────────────────────────────────────────────
  {
    name: 'web_fetch',
    description: 'Fetch content from a URL.',
    input_schema: {
      type: 'object',
      properties: {
        url: { type: 'string', description: 'URL to fetch' },
        method: { type: 'string', description: 'HTTP method (GET/POST/PUT/DELETE)' },
        headers: { type: 'string', description: 'JSON string of headers' },
        body: { type: 'string', description: 'Request body' },
      },
      required: ['url'],
    },
  },
  {
    name: 'web_search',
    description: 'Search the web for information. Returns titles, URLs, and snippets.',
    input_schema: {
      type: 'object',
      properties: {
        query: { type: 'string', description: 'Search query' },
        num_results: { type: 'number', description: 'Number of results (default 10)' },
      },
      required: ['query'],
    },
  },
  {
    name: 'open_browser',
    description: 'Open a URL in the default browser.',
    input_schema: {
      type: 'object',
      properties: { url: { type: 'string', description: 'URL to open' } },
      required: ['url'],
    },
  },

  // ── Screenshot ────────────────────────────────────────────────────────────
  {
    name: 'take_screenshot',
    description: 'Capture the screen. Returns path to saved PNG image.',
    input_schema: {
      type: 'object',
      properties: {
        path: { type: 'string', description: 'Save path (auto-generated if omitted)' },
        region: { type: 'string', description: 'Region as "x,y,width,height"' },
      },
      required: [],
    },
  },

  // ── Real Mouse Control ────────────────────────────────────────────────────
  {
    name: 'mouse_click',
    description: 'Move mouse to (x,y) and click — like a real user. Supports left/right/middle and double-click.',
    input_schema: {
      type: 'object',
      properties: {
        x: { type: 'number', description: 'X screen coordinate' },
        y: { type: 'number', description: 'Y screen coordinate' },
        button: { type: 'string', description: 'left / right / middle (default: left)' },
        double_click: { type: 'string', description: '"true" for double-click' },
      },
      required: ['x', 'y'],
    },
  },
  {
    name: 'mouse_right_click',
    description: 'Right-click at (x,y) to open context menus.',
    input_schema: {
      type: 'object',
      properties: {
        x: { type: 'number', description: 'X coordinate' },
        y: { type: 'number', description: 'Y coordinate' },
      },
      required: ['x', 'y'],
    },
  },
  {
    name: 'mouse_move',
    description: 'Move the mouse to a position without clicking.',
    input_schema: {
      type: 'object',
      properties: {
        x: { type: 'number', description: 'X coordinate' },
        y: { type: 'number', description: 'Y coordinate' },
      },
      required: ['x', 'y'],
    },
  },
  {
    name: 'mouse_drag',
    description: 'Click and drag from one point to another — for selecting text, resizing windows, drag-and-drop.',
    input_schema: {
      type: 'object',
      properties: {
        x1: { type: 'number', description: 'Start X' },
        y1: { type: 'number', description: 'Start Y' },
        x2: { type: 'number', description: 'End X' },
        y2: { type: 'number', description: 'End Y' },
        duration: { type: 'number', description: 'Drag duration in seconds (default 0.5)' },
      },
      required: ['x1', 'y1', 'x2', 'y2'],
    },
  },
  {
    name: 'mouse_scroll',
    description: 'Scroll the mouse wheel at a position.',
    input_schema: {
      type: 'object',
      properties: {
        x: { type: 'number', description: 'X coordinate' },
        y: { type: 'number', description: 'Y coordinate' },
        direction: { type: 'string', description: '"up" or "down" (default: down)' },
        amount: { type: 'number', description: 'Scroll amount (default: 3)' },
      },
      required: ['x', 'y'],
    },
  },
  {
    name: 'get_mouse_position',
    description: 'Return current mouse cursor (x, y) position.',
    input_schema: { type: 'object', properties: {}, required: [] },
  },

  // ── Real Keyboard Control ─────────────────────────────────────────────────
  {
    name: 'keyboard_type',
    description: 'Type text using the keyboard, with human-like keystroke timing.',
    input_schema: {
      type: 'object',
      properties: {
        text: { type: 'string', description: 'Text to type' },
        human_like: { type: 'string', description: '"true" for human-like timing (default: true)' },
      },
      required: ['text'],
    },
  },
  {
    name: 'keyboard_hotkey',
    description: 'Press a keyboard shortcut like Ctrl+C, Alt+F4, Super+D.',
    input_schema: {
      type: 'object',
      properties: {
        keys: { type: 'string', description: 'Keys comma-separated (e.g. "ctrl,c" or "alt,F4")' },
      },
      required: ['keys'],
    },
  },
  {
    name: 'keyboard_press',
    description: 'Press a single key (e.g. Return, Escape, F5, Tab, space).',
    input_schema: {
      type: 'object',
      properties: {
        key: { type: 'string', description: 'Key name (Return, Escape, space, Tab, F1-F12, etc.)' },
      },
      required: ['key'],
    },
  },

  // ── Application Control ───────────────────────────────────────────────────
  {
    name: 'open_application',
    description: 'Open an application by name, just like clicking its icon.',
    input_schema: {
      type: 'object',
      properties: {
        name: { type: 'string', description: 'Application name or command (e.g. "firefox", "gedit", "nautilus")' },
        args: { type: 'string', description: 'Optional arguments to pass' },
      },
      required: ['name'],
    },
  },
  {
    name: 'close_application',
    description: 'Close an application by name.',
    input_schema: {
      type: 'object',
      properties: {
        name: { type: 'string', description: 'Application name to close' },
      },
      required: ['name'],
    },
  },
  {
    name: 'open_terminal',
    description: 'Open a terminal emulator window.',
    input_schema: { type: 'object', properties: {}, required: [] },
  },
  {
    name: 'run_command_in_terminal',
    description: 'Open a terminal and type a command, exactly like a user would.',
    input_schema: {
      type: 'object',
      properties: {
        command: { type: 'string', description: 'Command to run in terminal' },
      },
      required: ['command'],
    },
  },
  {
    name: 'search_and_open_app',
    description: 'Use the desktop app launcher (Super key) to search and open an application.',
    input_schema: {
      type: 'object',
      properties: {
        name: { type: 'string', description: 'App name to search for' },
      },
      required: ['name'],
    },
  },
  {
    name: 'open_file_manager',
    description: 'Open the file manager, optionally navigating to a path.',
    input_schema: {
      type: 'object',
      properties: {
        path: { type: 'string', description: 'Directory to open (optional)' },
      },
      required: [],
    },
  },

  // ── Window Management ─────────────────────────────────────────────────────
  {
    name: 'list_windows',
    description: 'List all open windows and their IDs.',
    input_schema: { type: 'object', properties: {}, required: [] },
  },
  {
    name: 'focus_window',
    description: 'Focus (bring to front) a window by its name.',
    input_schema: {
      type: 'object',
      properties: {
        name: { type: 'string', description: 'Window title or partial match' },
      },
      required: ['name'],
    },
  },
  {
    name: 'get_active_window',
    description: 'Get the title of the currently active window.',
    input_schema: { type: 'object', properties: {}, required: [] },
  },
  {
    name: 'maximize_window',
    description: 'Maximize the current or named window.',
    input_schema: {
      type: 'object',
      properties: {
        name: { type: 'string', description: 'Window name (optional, maximizes active if omitted)' },
      },
      required: [],
    },
  },
  {
    name: 'minimize_window',
    description: 'Minimize the active window.',
    input_schema: { type: 'object', properties: {}, required: [] },
  },
  {
    name: 'alt_tab',
    description: 'Switch between open windows using Alt+Tab.',
    input_schema: {
      type: 'object',
      properties: {
        times: { type: 'number', description: 'How many times to Tab (default: 1)' },
      },
      required: [],
    },
  },
  {
    name: 'close_current_window',
    description: 'Close the currently active window (Alt+F4).',
    input_schema: { type: 'object', properties: {}, required: [] },
  },
  {
    name: 'get_screen_size',
    description: 'Get the screen resolution (e.g. "1920x1080").',
    input_schema: { type: 'object', properties: {}, required: [] },
  },
  {
    name: 'show_desktop',
    description: 'Hide all windows and show the desktop.',
    input_schema: { type: 'object', properties: {}, required: [] },
  },

  // ── Smart Click & Type ────────────────────────────────────────────────────
  {
    name: 'click_and_type',
    description: 'Click on a field at (x,y) and type text into it — like filling a form.',
    input_schema: {
      type: 'object',
      properties: {
        x: { type: 'number', description: 'X coordinate of the field' },
        y: { type: 'number', description: 'Y coordinate of the field' },
        text: { type: 'string', description: 'Text to type into the field' },
        clear_first: { type: 'string', description: '"true" to select all and clear before typing' },
      },
      required: ['x', 'y', 'text'],
    },
  },

  // ── Image Search on Screen ────────────────────────────────────────────────
  {
    name: 'find_on_screen',
    description: 'Find an image template on the screen. Returns (x,y) of match or null.',
    input_schema: {
      type: 'object',
      properties: {
        image: { type: 'string', description: 'Path to the image template to find' },
        confidence: { type: 'number', description: 'Match confidence 0-1 (default: 0.8)' },
      },
      required: ['image'],
    },
  },
  {
    name: 'click_image',
    description: 'Find an image on screen and click it.',
    input_schema: {
      type: 'object',
      properties: {
        image: { type: 'string', description: 'Path to image template' },
        confidence: { type: 'number', description: 'Match confidence (default: 0.8)' },
        double_click: { type: 'string', description: '"true" for double-click' },
      },
      required: ['image'],
    },
  },

  // ── Clipboard ─────────────────────────────────────────────────────────────
  {
    name: 'clipboard_read',
    description: 'Read the current clipboard contents.',
    input_schema: { type: 'object', properties: {}, required: [] },
  },
  {
    name: 'clipboard_write',
    description: 'Write text to the clipboard.',
    input_schema: {
      type: 'object',
      properties: {
        text: { type: 'string', description: 'Text to write' },
      },
      required: ['text'],
    },
  },

  // ── System Info ───────────────────────────────────────────────────────────
  {
    name: 'get_system_info',
    description: 'Get system information: CPU, memory, disk, OS, network.',
    input_schema: {
      type: 'object',
      properties: {
        include: { type: 'string', description: 'Metrics to include: cpu,memory,disk,network,os (default: all)' },
      },
      required: [],
    },
  },
  {
    name: 'list_processes',
    description: 'List running processes.',
    input_schema: {
      type: 'object',
      properties: {
        filter: { type: 'string', description: 'Filter by name' },
        sort_by: { type: 'string', description: 'Sort: cpu, memory, pid' },
      },
      required: [],
    },
  },

  // ── Memory ────────────────────────────────────────────────────────────────
  {
    name: 'remember',
    description: 'Store information in long-term memory.',
    input_schema: {
      type: 'object',
      properties: {
        content: { type: 'string', description: 'What to remember' },
        tags: { type: 'string', description: 'Comma-separated tags' },
      },
      required: ['content'],
    },
  },
  {
    name: 'recall',
    description: 'Search long-term memory.',
    input_schema: {
      type: 'object',
      properties: {
        query: { type: 'string', description: 'Search query' },
        top_k: { type: 'number', description: 'Max results (default 5)' },
      },
      required: ['query'],
    },
  },

  // ── Research agent ────────────────────────────────────────────────────────────
  {
    name: 'research',
    description: 'Deep multi-source web research. Returns a markdown brief with sources and synthesis.',
    input_schema: {
      type: 'object',
      properties: {
        topic: { type: 'string', description: 'Research topic or question' },
        limit: { type: 'number', description: 'Max sources (default 8)' },
        fetch_content: { type: 'string', description: '"true" to fetch full page content' },
      },
      required: ['topic'],
    },
  },

  // ── High-level computer operation ─────────────────────────────────────────
  {
    name: 'operate_computer',
    description: 'High-level computer control: describe a goal in natural language. Devin will screenshot, analyze, and interact with the UI automatically.',
    input_schema: {
      type: 'object',
      properties: {
        objective: { type: 'string', description: 'What to accomplish on screen' },
        model: { type: 'string', description: 'Vision model: gemini, gpt4v (default: gemini)' },
      },
      required: ['objective'],
    },
  },

  // ── Browser automation ────────────────────────────────────────────────────
  {
    name: 'browser_automate',
    description: 'Open a URL in a browser and perform a sequence of UI actions (click, type, scroll, screenshot).',
    input_schema: {
      type: 'object',
      properties: {
        url: { type: 'string', description: 'URL to open' },
        actions: { type: 'string', description: 'JSON array of actions: [{type:"click",x,y}, {type:"type",text}, {type:"hotkey",keys}, {type:"wait",seconds}, {type:"screenshot"}]' },
      },
      required: ['url'],
    },
  },

  // ── Voice ─────────────────────────────────────────────────────────────────
  {
    name: 'speak',
    description: 'Speak text aloud using pyttsx3 TTS. Use this to give verbal responses to the user.',
    input_schema: {
      type: 'object',
      properties: {
        text: { type: 'string', description: 'Text to speak' },
        rate: { type: 'number', description: 'Speech rate (default 180)' },
      },
      required: ['text'],
    },
  },
  {
    name: 'listen_voice',
    description: 'Listen for voice input from the microphone and return transcribed text.',
    input_schema: {
      type: 'object',
      properties: {
        timeout: { type: 'number', description: 'Seconds to wait for speech (default 8)' },
        language: { type: 'string', description: 'Language code (default en-US)' },
      },
      required: [],
    },
  },

  // ── Sub-agent delegation ──────────────────────────────────────────────────
  {
    name: 'delegate_subtask',
    description: 'Delegate a focused sub-task to a fresh sub-agent.',
    input_schema: {
      type: 'object',
      properties: {
        goal: { type: 'string', description: 'Sub-task goal' },
        max_steps: { type: 'number', description: 'Max tool calls (default 10)' },
      },
      required: ['goal'],
    },
  },

  // ── Volume / Media ────────────────────────────────────────────────────────
  {
    name: 'volume_control',
    description: 'Control system volume: up, down, or mute.',
    input_schema: {
      type: 'object',
      properties: {
        action: { type: 'string', description: '"up", "down", or "mute"' },
        steps: { type: 'number', description: 'How many steps (default 5)' },
      },
      required: ['action'],
    },
  },

  // ── Task complete ─────────────────────────────────────────────────────────
  {
    name: 'task_complete',
    description: 'Signal task is fully complete and give a final summary.',
    input_schema: {
      type: 'object',
      properties: {
        reason: { type: 'string', description: 'Summary of what was accomplished' },
      },
      required: ['reason'],
    },
  },
];

export const PENTEST_TOOLS: ToolDefinition[] = [
  {
    name: 'run_nmap_scan',
    description: 'Run nmap network scan. REQUIRES explicit authorization.',
    input_schema: {
      type: 'object',
      properties: {
        target: { type: 'string', description: 'Target IP, hostname, or CIDR' },
        flags: { type: 'string', description: 'nmap flags (e.g. "-sV -sC -p 1-1000")' },
        authorized: { type: 'string', description: 'Must be "yes"' },
      },
      required: ['target', 'authorized'],
    },
  },
  {
    name: 'run_hexstrike',
    description: 'Run HexStrike AI pentesting command.',
    input_schema: {
      type: 'object',
      properties: {
        command: { type: 'string', description: 'HexStrike command' },
        target: { type: 'string', description: 'Target (authorized only)' },
      },
      required: ['command'],
    },
  },
  {
    name: 'vulnerability_scan',
    description: 'Scan a target for vulnerabilities. Requires authorization.',
    input_schema: {
      type: 'object',
      properties: {
        target: { type: 'string', description: 'Target to scan' },
        scan_type: { type: 'string', description: 'web, network, or service' },
        authorized: { type: 'string', description: 'Must be "yes"' },
      },
      required: ['target', 'authorized'],
    },
  },
  {
    name: 'run_metasploit',
    description: 'Run a Metasploit module. Requires authorization.',
    input_schema: {
      type: 'object',
      properties: {
        module: { type: 'string', description: 'Module path (e.g. exploit/multi/handler)' },
        options: { type: 'string', description: 'JSON options' },
        authorized: { type: 'string', description: 'Must be "yes"' },
      },
      required: ['module', 'authorized'],
    },
  },
];

export const CLOUD_TOOLS: ToolDefinition[] = [
  {
    name: 'list_aws_resources',
    description: 'List AWS resources.',
    input_schema: {
      type: 'object',
      properties: {
        resource_type: { type: 'string', description: 'ec2, s3, lambda, rds' },
        region: { type: 'string', description: 'AWS region (default: us-east-1)' },
      },
      required: ['resource_type'],
    },
  },
  {
    name: 'run_cloud_command',
    description: 'Run a cloud provider CLI command.',
    input_schema: {
      type: 'object',
      properties: {
        provider: { type: 'string', description: 'aws, gcloud, or az' },
        command: { type: 'string', description: 'CLI arguments' },
      },
      required: ['provider', 'command'],
    },
  },
];

// ── Extended tool set from all integrated repos ────────────────────────────────

const EXTENDED_TOOLS: ToolDefinition[] = [
  // File tools (claude-code-source GlobTool/GrepTool)
  {
    name: 'read_file_lines',
    description: 'Read specific lines from a file.',
    input_schema: {
      type: 'object',
      properties: {
        path: { type: 'string', description: 'File path' },
        start_line: { type: 'number', description: 'Start line (1-based)' },
        end_line: { type: 'number', description: 'End line (inclusive)' },
      },
      required: ['path'],
    },
  },
  {
    name: 'glob_search',
    description: 'Find files by glob pattern (e.g. **/*.ts, src/**/*.py).',
    input_schema: {
      type: 'object',
      properties: {
        pattern: { type: 'string', description: 'Glob pattern' },
        directory: { type: 'string', description: 'Search directory (optional)' },
        max_results: { type: 'number', description: 'Max files to return (default 100)' },
      },
      required: ['pattern'],
    },
  },
  {
    name: 'grep_search',
    description: 'Search file contents with regex (ripgrep).',
    input_schema: {
      type: 'object',
      properties: {
        pattern: { type: 'string', description: 'Regex pattern to search' },
        path: { type: 'string', description: 'File or directory path' },
        glob: { type: 'string', description: 'Glob filter (e.g. *.ts)' },
        case_insensitive: { type: 'boolean', description: 'Case insensitive search' },
        max_results: { type: 'number', description: 'Max matches to return' },
      },
      required: ['pattern'],
    },
  },
  {
    name: 'find_files',
    description: 'Find files by name or extension in a directory.',
    input_schema: {
      type: 'object',
      properties: {
        directory: { type: 'string', description: 'Directory to search' },
        name: { type: 'string', description: 'Filename pattern (e.g. *.log)' },
        extension: { type: 'string', description: 'File extension (e.g. py)' },
        max_depth: { type: 'number', description: 'Max directory depth' },
      },
      required: ['directory'],
    },
  },
  {
    name: 'stat_file',
    description: 'Get file metadata: size, type, permissions, timestamps.',
    input_schema: {
      type: 'object',
      properties: {
        path: { type: 'string', description: 'File path' },
      },
      required: ['path'],
    },
  },
  {
    name: 'list_directory',
    description: 'List directory contents.',
    input_schema: {
      type: 'object',
      properties: {
        path: { type: 'string', description: 'Directory path' },
        recursive: { type: 'boolean', description: 'List recursively' },
      },
      required: ['path'],
    },
  },
  // CVE / Security
  {
    name: 'lookup_cve',
    description: 'Look up a CVE by ID (e.g. CVE-2023-1234). Returns severity, description, CVSS score.',
    input_schema: {
      type: 'object',
      properties: {
        cve_id: { type: 'string', description: 'CVE ID (e.g. CVE-2023-1234)' },
      },
      required: ['cve_id'],
    },
  },
  {
    name: 'search_cves',
    description: 'Search CVEs by keyword (product name, vulnerability type).',
    input_schema: {
      type: 'object',
      properties: {
        keyword: { type: 'string', description: 'Search keyword' },
        max_results: { type: 'number', description: 'Max results (default 10)' },
      },
      required: ['keyword'],
    },
  },
  {
    name: 'scan_web_security',
    description: 'Scan a web app for security issues: missing headers, SQLi, XSS, etc. Authorization required.',
    input_schema: {
      type: 'object',
      properties: {
        url: { type: 'string', description: 'Target URL' },
        authorized: { type: 'string', description: 'Set to "yes" for systems you own or have permission to test' },
      },
      required: ['url', 'authorized'],
    },
  },
  {
    name: 'scan_paths',
    description: 'Discover accessible paths on a web server (admin panels, config files). Authorization required.',
    input_schema: {
      type: 'object',
      properties: {
        url: { type: 'string', description: 'Target base URL' },
        authorized: { type: 'string', description: 'Must be "yes"' },
        custom_paths: { type: 'string', description: 'Comma-separated custom paths to test' },
      },
      required: ['url', 'authorized'],
    },
  },
  {
    name: 'test_xss',
    description: 'Test a URL parameter for XSS vulnerability. Authorization required.',
    input_schema: {
      type: 'object',
      properties: {
        url: { type: 'string', description: 'Target URL' },
        param: { type: 'string', description: 'Parameter name to test' },
        authorized: { type: 'string', description: 'Must be "yes"' },
      },
      required: ['url', 'param', 'authorized'],
    },
  },
  {
    name: 'test_sqli',
    description: 'Test a URL parameter for SQL injection. Authorization required.',
    input_schema: {
      type: 'object',
      properties: {
        url: { type: 'string', description: 'Target URL' },
        param: { type: 'string', description: 'Parameter name to test' },
        authorized: { type: 'string', description: 'Must be "yes"' },
      },
      required: ['url', 'param', 'authorized'],
    },
  },
  {
    name: 'check_ssl',
    description: 'Check SSL/TLS certificate validity, expiry, and configuration.',
    input_schema: {
      type: 'object',
      properties: {
        host: { type: 'string', description: 'Hostname to check' },
        port: { type: 'number', description: 'Port (default 443)' },
      },
      required: ['host'],
    },
  },
  {
    name: 'scan_wifi',
    description: 'Scan for nearby WiFi networks. Authorization required.',
    input_schema: {
      type: 'object',
      properties: {
        authorized: { type: 'string', description: 'Must be "yes"' },
      },
      required: ['authorized'],
    },
  },
  // Threat intelligence (Shannon)
  {
    name: 'check_ip_reputation',
    description: 'Check if an IP address is malicious (AbuseIPDB, TOR check, reverse DNS).',
    input_schema: {
      type: 'object',
      properties: {
        ip: { type: 'string', description: 'IP address to check' },
      },
      required: ['ip'],
    },
  },
  {
    name: 'analyze_domain',
    description: 'Analyze a domain for phishing indicators, WHOIS info, DNS records.',
    input_schema: {
      type: 'object',
      properties: {
        domain: { type: 'string', description: 'Domain to analyze' },
      },
      required: ['domain'],
    },
  },
  {
    name: 'check_file_hash',
    description: 'Check if a file hash (MD5/SHA1/SHA256) is malicious (VirusTotal).',
    input_schema: {
      type: 'object',
      properties: {
        hash: { type: 'string', description: 'File hash' },
        type: { type: 'string', description: 'Hash type: md5, sha1, sha256' },
      },
      required: ['hash'],
    },
  },
  {
    name: 'osint_gather',
    description: 'Gather OSINT on a target (person, company, domain, username).',
    input_schema: {
      type: 'object',
      properties: {
        target: { type: 'string', description: 'Target to investigate' },
        type: { type: 'string', description: 'person | company | domain | username' },
      },
      required: ['target', 'type'],
    },
  },
  // System tools (AIA)
  {
    name: 'system_metrics',
    description: 'Get CPU, memory, and disk usage.',
    input_schema: { type: 'object', properties: {}, required: [] },
  },
  {
    name: 'get_weather',
    description: 'Get current weather for a city.',
    input_schema: {
      type: 'object',
      properties: {
        city: { type: 'string', description: 'City name' },
      },
      required: ['city'],
    },
  },
  {
    name: 'schedule_task_runner',
    description: 'Schedule a shell command to run after N minutes.',
    input_schema: {
      type: 'object',
      properties: {
        name: { type: 'string', description: 'Task name' },
        delay_minutes: { type: 'number', description: 'Minutes from now to run' },
        command: { type: 'string', description: 'Shell command to execute' },
      },
      required: ['name', 'delay_minutes', 'command'],
    },
  },
  {
    name: 'list_scheduled_tasks',
    description: 'List all scheduled tasks.',
    input_schema: { type: 'object', properties: {}, required: [] },
  },
  // AI Vision (Gemini)
  {
    name: 'analyze_image_gemini',
    description: 'Use Gemini Vision to analyze an image file.',
    input_schema: {
      type: 'object',
      properties: {
        image_path: { type: 'string', description: 'Path to image file' },
        prompt: { type: 'string', description: 'What to analyze in the image' },
      },
      required: ['image_path'],
    },
  },
  {
    name: 'analyze_screenshot_gemini',
    description: 'Take a screenshot and analyze it with Gemini Vision.',
    input_schema: {
      type: 'object',
      properties: {
        prompt: { type: 'string', description: 'What to look for on screen' },
      },
      required: [],
    },
  },
  {
    name: 'generate_code_gemini',
    description: 'Generate code using Gemini AI.',
    input_schema: {
      type: 'object',
      properties: {
        description: { type: 'string', description: 'What code to generate' },
        language: { type: 'string', description: 'Programming language' },
        context: { type: 'string', description: 'Additional context' },
      },
      required: ['description', 'language'],
    },
  },
  // Jarvis voice
  {
    name: 'jarvis_speak_text',
    description: 'Speak text aloud using Jarvis TTS (pyttsx3).',
    input_schema: {
      type: 'object',
      properties: {
        text: { type: 'string', description: 'Text to speak' },
      },
      required: ['text'],
    },
  },
  {
    name: 'jarvis_command',
    description: 'Parse and execute a Jarvis voice command (weather, time, music, open app, etc.).',
    input_schema: {
      type: 'object',
      properties: {
        command: { type: 'string', description: 'Voice command to execute' },
      },
      required: ['command'],
    },
  },
];

// ── Hub Tools — access all 24 integrated repos ────────────────────────────────
const HUB_TOOLS: ToolDefinition[] = [
  {
    name: 'hub_status',
    description: 'Show integration status of all 24 cloned repos (AIA, SOC, Jarvis, Metasploit, etc.).',
    input_schema: { type: 'object', properties: {}, required: [] },
  },
  {
    name: 'hub_dispatch',
    description: 'Dispatch a command to any integrated repo module. tool: osint_ip|osint_domain|port_scan|wifi_scan|system_metrics|gemini_generate|aia_speak|jarvis_exec|soc_click|vuln_url|msf_command|telegram_send|cheetah_tools.',
    input_schema: {
      type: 'object',
      properties: {
        tool: { type: 'string', description: 'Hub tool name' },
        args: { type: 'object', description: 'Tool arguments as key-value object' },
      },
      required: ['tool'],
    },
  },
  {
    name: 'system_metrics_hub',
    description: 'Get real-time CPU, RAM, disk, network, and top process metrics via psutil.',
    input_schema: { type: 'object', properties: {}, required: [] },
  },
  {
    name: 'soc_click',
    description: 'AI-guided UI interaction: describe a button/element and Devin finds and clicks it using vision.',
    input_schema: {
      type: 'object',
      properties: {
        description: { type: 'string', description: 'Natural language description of the UI element to click' },
      },
      required: ['description'],
    },
  },
  {
    name: 'ai_operate',
    description: 'Run the self-operating-computer pipeline: give an objective, Devin autonomously screenshots and interacts with the OS to accomplish it.',
    input_schema: {
      type: 'object',
      properties: {
        objective: { type: 'string', description: 'What to accomplish on the computer' },
        model: { type: 'string', description: 'Vision model to use (default: gemini)' },
      },
      required: ['objective'],
    },
  },
];

export const ALL_TOOLS: ToolDefinition[] = [
  ...CORE_TOOLS,
  ...PENTEST_TOOLS,
  ...CLOUD_TOOLS,
  ...EXTENDED_TOOLS,
  ...HUB_TOOLS,
];
