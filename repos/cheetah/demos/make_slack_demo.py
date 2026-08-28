#!/usr/bin/env python3
"""
Generate animated GIF demo of cheetahclaws Slack Bridge.
Shows: auto-start → status → incoming message → tool call →
       in-place reply update → /cost passthrough → /stop from Slack
"""
from PIL import Image, ImageDraw, ImageFont
import os

# ── Catppuccin Mocha palette ─────────────────────────────────────────────
BG      = (30,  30,  46)
SURFACE = (49,  50,  68)
TEXT    = (205, 214, 244)
SUBTEXT = (108, 112, 134)
CYAN    = (137, 220, 235)
GREEN   = (166, 227, 161)
YELLOW  = (249, 226, 175)
RED     = (243, 139, 168)
MAUVE   = (203, 166, 247)
BLUE    = (137, 180, 250)
SLACK_PURPLE = (74, 21, 75)     # Slack aubergine brand color
SLACK_ACCENT = (54, 197, 240)   # Slack highlight blue

W, H = 960, 720
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
FONT_SIZE = 14
LINE_H    = 20
PAD_X     = 18
PAD_Y     = 16

# Phone panel dimensions
PHONE_X  = 555
PHONE_W  = 390
PHONE_H  = 580
PHONE_Y  = 70
PHONE_R  = 8

def make_font(size=FONT_SIZE, bold=False):
    path = FONT_BOLD if bold else FONT_PATH
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

FONT    = make_font()
FONT_B  = make_font(bold=True)
FONT_SM = make_font(FONT_SIZE - 2)
FONT_XS = make_font(FONT_SIZE - 3)

def seg(t, c=TEXT, b=False):
    return (t, c, b)

def render_line(draw, y, segments, x_start=PAD_X):
    x = x_start
    for text, color, bold in segments:
        font = FONT_B if bold else FONT
        draw.text((x, y), text, font=font, fill=color)
        x += font.getlength(text)
    return y + LINE_H


# ── Slack UI panel ───────────────────────────────────────────────────────

def draw_slack(img, messages):
    """
    Draw a minimal Slack-style chat panel on the right.
    messages: list of (sender, text, is_bot, is_placeholder)
      sender = display name string
    """
    d = ImageDraw.Draw(img)

    px, py, pw, ph = PHONE_X, PHONE_Y, PHONE_W, PHONE_H

    # ── Sidebar ──
    sidebar_w = 64
    sidebar_bg = SLACK_PURPLE
    d.rectangle([px, py, px + sidebar_w, py + ph], fill=sidebar_bg)

    # Workspace initial circle
    ws_x, ws_y = px + 12, py + 12
    d.rounded_rectangle([ws_x, ws_y, ws_x + 40, ws_y + 40], radius=8,
                         fill=(255, 255, 255, 40))
    d.text((ws_x + 8, ws_y + 8), "CC", font=FONT_B, fill=(255, 255, 255))

    # Sidebar icons (channel, dm, etc.)
    icon_y = ws_y + 54
    for icon in ["#", "◎", "✉", "☰"]:
        d.text((px + 20, icon_y), icon, font=FONT_SM, fill=(180, 140, 180))
        icon_y += 28

    # ── Main panel ──
    main_x = px + sidebar_w
    main_w = pw - sidebar_w
    panel_bg = (248, 248, 248)
    d.rectangle([main_x, py, px + pw, py + ph], fill=panel_bg)

    # Header bar
    header_h = 44
    d.rectangle([main_x, py, px + pw, py + header_h], fill=(255, 255, 255))
    d.line([(main_x, py + header_h), (px + pw, py + header_h)],
           fill=(221, 221, 221), width=1)

    # Channel name
    d.text((main_x + 12, py + 8), "#", font=FONT_B, fill=(30, 30, 30))
    d.text((main_x + 24, py + 8), "cheetahclaws", font=FONT_B, fill=(30, 30, 30))
    d.text((main_x + 12, py + 26), "cheetahclaws bot channel", font=FONT_XS, fill=(100, 100, 100))

    # Messages area
    msg_y = py + header_h + 8
    max_msg_y = py + ph - 50

    for sender, text, is_bot, is_placeholder in messages:
        if msg_y >= max_msg_y:
            break

        # Avatar circle
        av_color = (74, 21, 75) if is_bot else (54, 197, 240)
        av_x, av_y = main_x + 10, msg_y
        d.ellipse([av_x, av_y, av_x + 28, av_y + 28], fill=av_color)
        initial = sender[0].upper() if sender else "?"
        d.text((av_x + 7, av_y + 6), initial, font=FONT_SM, fill=(255, 255, 255))

        # Name + time
        name_color = (30, 30, 30)
        d.text((main_x + 46, msg_y), sender, font=FONT_B, fill=name_color)
        d.text((main_x + 46 + int(FONT_B.getlength(sender)) + 8, msg_y + 2),
               "12:34 PM", font=FONT_XS, fill=(160, 160, 160))

        # Message text — word-wrap at ~36 chars
        text_color = (100, 100, 100) if is_placeholder else (30, 30, 30)
        words = text.split()
        lines_wrapped = []
        cur = ""
        for w in words:
            if len(cur) + len(w) + 1 > 36:
                if cur:
                    lines_wrapped.append(cur)
                cur = w
            else:
                cur = (cur + " " + w).strip()
        if cur:
            lines_wrapped.append(cur)

        text_y = msg_y + 18
        for ln in lines_wrapped:
            if text_y >= max_msg_y:
                break
            d.text((main_x + 46, text_y), ln, font=FONT_SM, fill=text_color)
            text_y += 16

        msg_y = text_y + 10

    # Input bar
    input_y = py + ph - 44
    d.line([(main_x, input_y - 1), (px + pw, input_y - 1)], fill=(221, 221, 221), width=1)
    d.rounded_rectangle([main_x + 10, input_y + 4, px + pw - 10, py + ph - 8],
                         radius=6, fill=(255, 255, 255), outline=(221, 221, 221))
    d.text((main_x + 20, input_y + 12), "Message #cheetahclaws", font=FONT_SM, fill=(180, 180, 180))

    # Divider between terminal and Slack panel
    d.line([(PHONE_X - 12, PHONE_Y), (PHONE_X - 12, PHONE_Y + PHONE_H)],
           fill=SURFACE, width=1)


# ── Terminal helpers ─────────────────────────────────────────────────────

def draw_frame(lines_segments, slack_messages=None):
    img = Image.new("RGB", (W, H), BG)
    d   = ImageDraw.Draw(img)
    y   = PAD_Y
    for item in lines_segments:
        if item is None:
            y += LINE_H
        elif isinstance(item, list):
            y = render_line(d, y, item)
        else:
            y = render_line(d, y, [item])
    if slack_messages is not None:
        draw_slack(img, slack_messages)
    return img


SL_COLOR = (100, 180, 230)  # terminal Slack accent

BANNER_SL = [
    [seg("╭─ CheetahClaws ─────────────────────────────────────────╮", SUBTEXT)],
    [seg("│  ", SUBTEXT), seg("Model: ", SUBTEXT), seg("claude-opus-4-6", CYAN, True)],
    [seg("│  ", SUBTEXT), seg("Permissions: ", SUBTEXT), seg("auto", YELLOW, True),
     seg("  flags: [", SUBTEXT), seg("slack", SL_COLOR, True), seg("]", SUBTEXT)],
    [seg("│  Type /help for commands, Ctrl+C to cancel                 │", SUBTEXT)],
    [seg("╰────────────────────────────────────────────────────────────╯", SUBTEXT)],
    None,
]

def prompt_line(text="", cursor=False):
    cur = "█" if cursor else ""
    return [seg("[cheetahclaws] ", SUBTEXT), seg("» ", CYAN, True), seg(text + cur, TEXT)]

def ok_line(t):
    return [seg("  ✓ ", GREEN, True), seg(t, TEXT)]

def info_line(t):
    return [seg("  ℹ ", CYAN), seg(t, SUBTEXT)]

def warn_line(t):
    return [seg("  ⚠ ", YELLOW), seg(t, SUBTEXT)]

def claude_header():
    return [seg("╭─ Claude ", SUBTEXT), seg("●", GREEN),
            seg(" ─────────────────────────────────────────────", SUBTEXT)]

def claude_sep():
    return [seg("╰──────────────────────────────────────────────────────────", SUBTEXT)]

def tool_line(icon, name, arg, color=CYAN):
    return [seg(f"  {icon}  ", SUBTEXT), seg(name, color),
            seg("(", SUBTEXT), seg(arg, TEXT), seg(")", SUBTEXT)]

def tool_ok(msg):
    return [seg("  ✓ ", GREEN), seg(msg, SUBTEXT)]

def text_line(t, indent=2):
    return [seg(" " * indent + t, TEXT)]

def sl_incoming(text):
    return [seg("  📩 Slack ", SL_COLOR, True), seg("[U04ABZ]: ", SUBTEXT), seg(text, TEXT)]

def sl_sent(preview):
    return [seg("  ✈  ", SL_COLOR), seg("Response sent → ", SUBTEXT), seg(preview, SUBTEXT)]

SPINNER = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]

BOT_NAME  = "cheetahclaws"
USER_NAME = "alex"


# ── Scene builder ─────────────────────────────────────────────────────────

def build_scenes():
    scenes = []

    def add(lines, ms=120, slack=None):
        scenes.append((lines, ms, slack))

    # ── 0: Banner — slack flag, auto-start ───────────────────────────────
    add(BANNER_SL + [
        ok_line("Slack bridge started."),
        info_line("Send a message in the configured Slack channel."),
        info_line("Stop with /slack stop or send /stop in Slack."),
        None,
        prompt_line(cursor=True),
    ], 1200, slack=[])

    # ── 1: /slack status ──────────────────────────────────────────────────
    base = BANNER_SL + [
        ok_line("Slack bridge started."),
        info_line("Send a message in the configured Slack channel."),
        info_line("Stop with /slack stop or send /stop in Slack."),
        None,
    ]
    cmd_status = "/slack status"
    for i in range(0, len(cmd_status) + 1, 3):
        add(base + [prompt_line(cmd_status[:i], cursor=(i < len(cmd_status)))], 60, slack=[])
    add(base + [prompt_line(cmd_status)], 300, slack=[])

    add(base + [
        prompt_line(cmd_status),
        None,
        ok_line("Slack bridge running  (channel: C0123456789)"),
        None,
        prompt_line(cursor=True),
    ], 1000, slack=[])

    # Bot posts online notification
    slack_init = [
        (BOT_NAME, "🟢 cheetahclaws is online. Send me a message and I'll process it.", True, False),
    ]
    add(base + [prompt_line(cursor=True)], 800, slack=slack_init)

    # ── 2: First message from user ────────────────────────────────────────
    slack_q1 = slack_init + [
        (USER_NAME, "What files are in this project?", False, False),
    ]

    add(base + [
        prompt_line(cursor=True),
        None,
        sl_incoming("What files are in this project?"),
    ], 900, slack=slack_q1)

    # ── 3: Thinking placeholder posted + model processes ─────────────────
    sl_base = base + [
        prompt_line(cursor=False),
        None,
        sl_incoming("What files are in this project?"),
        None,
    ]

    # Placeholder appears in Slack immediately
    slack_thinking = slack_q1 + [
        (BOT_NAME, "⏳ Thinking…", True, True),
    ]

    add(sl_base + [
        [seg("  ✓ ", GREEN), seg("placeholder posted to Slack", SUBTEXT)],
        None,
        claude_header(),
        tool_line("⚙", "Glob", "**/*", CYAN),
    ], 500, slack=slack_thinking)

    add(sl_base + [
        [seg("  ✓ ", GREEN), seg("placeholder posted to Slack", SUBTEXT)],
        None,
        claude_header(),
        tool_line("⚙", "Glob", "**/*", CYAN),
        tool_ok("12 files matched"),
    ], 600, slack=slack_thinking)

    resp1_lines = [
        "Here are the files in this project:",
        "",
        "  cheetahclaws.py   — Main REPL + slash commands",
        "  agent.py          — Core agent loop",
        "  tools.py          — Built-in tools (Read/Write/Edit/Bash…)",
        "  providers.py      — API provider abstraction",
        "  config.py         — Configuration management",
        "  context.py        — System prompt builder",
        "  memory/           — Persistent memory system",
    ]

    tool_done = sl_base + [
        [seg("  ✓ ", GREEN), seg("placeholder posted to Slack", SUBTEXT)],
        None,
        claude_header(),
        tool_line("⚙", "Glob", "**/*", CYAN),
        tool_ok("12 files matched"),
        None,
        [seg("│ ", SUBTEXT)],
    ]

    streamed = []
    for line in resp1_lines:
        streamed.append(text_line(line, 2) if line else None)
        add(tool_done + [x for x in streamed if x is not None], 55, slack=slack_thinking)

    add(tool_done + [text_line(l, 2) if l else None for l in resp1_lines] + [claude_sep()],
        500, slack=slack_thinking)

    # ── 4: Placeholder updated with real response ─────────────────────────
    slack_r1 = slack_q1 + [
        (BOT_NAME, "Here are the files: cheetahclaws.py, agent.py, tools.py, providers.py, config.py …", True, False),
    ]

    after_r1 = sl_base + [
        [seg("  ✓ ", GREEN), seg("placeholder posted to Slack", SUBTEXT)],
        None,
        claude_header(),
        tool_line("⚙", "Glob", "**/*", CYAN),
        tool_ok("12 files matched"),
        None,
        [seg("│ ", SUBTEXT)],
    ] + [text_line(l, 2) if l else None for l in resp1_lines] + [claude_sep(), None]

    add(after_r1 + [
        [seg("  ✓ ", GREEN), seg("Slack placeholder updated with response", SUBTEXT)],
    ], 900, slack=slack_r1)
    add(after_r1 + [
        sl_sent("Here are the files in this project: …"),
        None,
        prompt_line(cursor=True),
    ], 800, slack=slack_r1)

    # ── 5: /cost slash command from Slack ────────────────────────────────
    slack_q2 = slack_r1 + [
        (USER_NAME, "/cost", False, False),
    ]

    add(after_r1 + [
        prompt_line(cursor=False),
        None,
        sl_incoming("/cost"),
        [seg("                  ", SUBTEXT), seg("(slash command passthrough)", SUBTEXT)],
    ], 900, slack=slack_q2)

    cost_base = after_r1 + [
        prompt_line(cursor=False),
        None,
        sl_incoming("/cost"),
        [seg("                  ", SUBTEXT), seg("(slash command passthrough)", SUBTEXT)],
        None,
    ]

    cost_lines = [
        [seg("  Input tokens:  ", CYAN), seg("2,614", TEXT, True)],
        [seg("  Output tokens: ", CYAN), seg("389",   TEXT, True)],
        [seg("  Est. cost:     ", CYAN), seg("$0.0398 USD", GREEN, True)],
    ]

    add(cost_base + cost_lines, 700, slack=slack_q2)

    slack_cost = slack_q2 + [
        (BOT_NAME, "Input: 2,614 | Output: 389 | Cost: $0.0398", True, False),
    ]
    add(cost_base + cost_lines + [None, sl_sent("Input: 2,614 | Output: 389 | Cost: $0.0398")],
        900, slack=slack_cost)
    add(cost_base + cost_lines + [None, sl_sent("Input: 2,614 | Output: 389 | Cost: $0.0398"),
        None, prompt_line(cursor=True)], 800, slack=slack_cost)

    # ── 6: Second question ────────────────────────────────────────────────
    slack_q3 = slack_cost + [
        (USER_NAME, "How does /brainstorm work?", False, False),
    ]

    q3_base = after_r1 + [
        prompt_line(cursor=False),
        None,
        sl_incoming("How does /brainstorm work?"),
        None,
    ]

    slack_think3 = slack_q3 + [
        (BOT_NAME, "⏳ Thinking…", True, True),
    ]

    add(q3_base + [
        [seg("  ✓ ", GREEN), seg("placeholder posted to Slack", SUBTEXT)],
        None,
        claude_header(),
        tool_line("⚙", "Grep", "def cmd_brainstorm", MAUVE),
        tool_ok("Found in cheetahclaws.py:480"),
        None,
        tool_line("⚙", "Read", "cheetahclaws.py:480-550", CYAN),
        tool_ok("71 lines read"),
    ], 700, slack=slack_think3)

    resp3 = "/brainstorm starts a multi-persona AI debate, generates expert viewpoints, synthesizes a Master Plan, and auto-creates todo_list.txt."
    resp3_parts = []
    cur = ""
    for ch in resp3:
        cur += ch
        resp3_parts.append(cur)

    step = max(1, len(resp3_parts) // 20)
    for idx in range(0, len(resp3_parts), step):
        add(q3_base + [
            [seg("  ✓ ", GREEN), seg("placeholder posted to Slack", SUBTEXT)],
            None,
            claude_header(),
            tool_line("⚙", "Grep", "def cmd_brainstorm", MAUVE),
            tool_ok("Found in cheetahclaws.py:480"),
            None,
            tool_line("⚙", "Read", "cheetahclaws.py:480-550", CYAN),
            tool_ok("71 lines read"),
            None,
            [seg("│ ", SUBTEXT)],
            text_line(resp3_parts[idx], 2),
        ], 50, slack=slack_think3)

    slack_r3 = slack_q3 + [
        (BOT_NAME, "/brainstorm runs a multi-persona AI debate and synthesizes a Master Plan…", True, False),
    ]

    add(q3_base + [
        [seg("  ✓ ", GREEN), seg("placeholder posted to Slack", SUBTEXT)],
        None,
        claude_header(),
        tool_line("⚙", "Grep", "def cmd_brainstorm", MAUVE),
        tool_ok("Found in cheetahclaws.py:480"),
        None,
        tool_line("⚙", "Read", "cheetahclaws.py:480-550", CYAN),
        tool_ok("71 lines read"),
        None,
        [seg("│ ", SUBTEXT)],
        text_line(resp3, 2),
        claude_sep(),
        None,
        sl_sent("/brainstorm runs a multi-persona AI debate…"),
        None,
        prompt_line(cursor=True),
    ], 1000, slack=slack_r3)

    # ── 7: /stop from Slack ───────────────────────────────────────────────
    slack_stop    = slack_r3 + [(USER_NAME, "/stop", False, False)]
    slack_stopped = slack_stop + [(BOT_NAME, "🔴 cheetahclaws bridge stopped.", True, False)]

    stop_base = q3_base + [
        [seg("  ✓ ", GREEN), seg("placeholder posted to Slack", SUBTEXT)],
        None,
        claude_header(),
        tool_line("⚙", "Grep", "def cmd_brainstorm", MAUVE),
        tool_ok("Found in cheetahclaws.py:480"),
        None,
        tool_line("⚙", "Read", "cheetahclaws.py:480-550", CYAN),
        tool_ok("71 lines read"),
        None,
        [seg("│ ", SUBTEXT)],
        text_line(resp3, 2),
        claude_sep(),
        None,
        sl_sent("/brainstorm runs a multi-persona AI debate…"),
        None,
        prompt_line(cursor=False),
        None,
        sl_incoming("/stop"),
        None,
    ]

    add(stop_base + [
        warn_line("Slack bridge stopped by remote /stop command."),
        None,
        prompt_line(cursor=True),
    ], 2200, slack=slack_stopped)

    return scenes


# ── Render ─────────────────────────────────────────────────────────────────

def _build_palette():
    theme = [
        BG, SURFACE, TEXT, SUBTEXT,
        CYAN, GREEN, YELLOW, RED, MAUVE, BLUE,
        (74, 21, 75),       # Slack purple
        (54, 197, 240),     # Slack accent blue
        (100, 180, 230),    # terminal SL accent
        (248, 248, 248),    # panel bg
        (255, 255, 255), (0, 0, 0),
        (30, 30, 30),       # text dark
        (100, 100, 100),    # placeholder text
        (160, 160, 160),    # dim text
        (221, 221, 221),    # border
        (180, 140, 180),    # sidebar icons
    ]
    flat = []
    for c in theme:
        flat.extend(c)
    while len(flat) < 256 * 3:
        flat.extend((0, 0, 0))
    return flat


def render_gif(output_path="slack_demo.gif"):
    print("Building Slack demo scenes...")
    scenes = build_scenes()
    print(f"  {len(scenes)} frames")

    pal_ref = Image.new("P", (1, 1))
    pal_ref.putpalette(_build_palette())

    print("  Rendering frames...")
    rgb_frames, durations = [], []
    for i, (lines, ms, slack) in enumerate(scenes):
        img = draw_frame(lines, slack_messages=slack)
        rgb_frames.append(img)
        durations.append(ms)
        if i % 30 == 0:
            print(f"    {i}/{len(scenes)}...")

    print("  Quantizing palette...")
    p_frames = [f.quantize(palette=pal_ref, dither=0) for f in rgb_frames]

    print(f"Saving → {output_path} ...")
    p_frames[0].save(
        output_path,
        save_all=True,
        append_images=p_frames[1:],
        duration=durations,
        loop=0,
        optimize=False,
    )
    size_kb = os.path.getsize(output_path) // 1024
    print(f"Done! {size_kb} KB — {len(p_frames)} frames")


if __name__ == "__main__":
    docs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs")
    out = os.path.join(docs_dir, "slack_demo.gif")
    render_gif(out)
    print(f"\n→ {out}")
