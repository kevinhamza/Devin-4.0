// src/integrations/telegram.ts — Full Telegram bot integration
// Allows controlling Devin remotely via Telegram messages
// From openclaw/openclaw.mjs patterns + AIA/modules/chatbot.py

import * as https from 'https';
import * as http from 'http';

interface TelegramUpdate {
  update_id: number;
  message?: {
    message_id: number;
    from?: { id: number; username?: string; first_name?: string };
    chat: { id: number; type: string };
    text?: string;
    date: number;
  };
}

interface TelegramSendResult {
  ok: boolean;
  result?: unknown;
  description?: string;
}

// ── Core API client ───────────────────────────────────────────────────────────

function telegramRequest(
  token: string,
  method: string,
  params: Record<string, unknown> = {}
): Promise<TelegramSendResult> {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify(params);
    const options: https.RequestOptions = {
      hostname: 'api.telegram.org',
      path: `/bot${token}/${method}`,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body),
      },
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', (chunk: Buffer) => { data += chunk.toString(); });
      res.on('end', () => {
        try { resolve(JSON.parse(data) as TelegramSendResult); }
        catch { resolve({ ok: false, description: 'Parse error: ' + data.slice(0, 100) }); }
      });
    });
    req.on('error', reject);
    req.write(body);
    req.end();
  });
}

// ── Telegram Bot class ────────────────────────────────────────────────────────

export class TelegramBot {
  private token: string;
  private allowedUsers: Set<number | string>;
  private lastUpdateId = 0;
  private running = false;
  private onMessage?: (text: string, chatId: number, from: string) => Promise<string>;

  constructor(token: string, allowedUsers: (number | string)[] = []) {
    this.token = token;
    this.allowedUsers = new Set(allowedUsers);
  }

  async sendMessage(chatId: number, text: string, markdown = true): Promise<TelegramSendResult> {
    // Split long messages
    const chunks = this.splitMessage(text, 4096);
    let result: TelegramSendResult = { ok: true };
    for (const chunk of chunks) {
      result = await telegramRequest(this.token, 'sendMessage', {
        chat_id: chatId,
        text: chunk,
        parse_mode: markdown ? 'Markdown' : undefined,
      });
    }
    return result;
  }

  async sendPhoto(chatId: number, photoPath: string, caption?: string): Promise<TelegramSendResult> {
    // For local files we'd use multipart, for simplicity send as document path info
    return this.sendMessage(chatId, `📸 Screenshot: \`${photoPath}\`\n${caption || ''}`);
  }

  async getUpdates(timeout = 30): Promise<TelegramUpdate[]> {
    const res = await telegramRequest(this.token, 'getUpdates', {
      offset: this.lastUpdateId + 1,
      timeout,
      allowed_updates: ['message'],
    });
    if (!res.ok) return [];
    const updates = (res.result as TelegramUpdate[]) || [];
    if (updates.length > 0) {
      this.lastUpdateId = updates[updates.length - 1].update_id;
    }
    return updates;
  }

  async getMe(): Promise<{ username?: string; first_name?: string }> {
    const res = await telegramRequest(this.token, 'getMe', {});
    return (res.result as { username?: string; first_name?: string }) || {};
  }

  private isAllowed(update: TelegramUpdate): boolean {
    if (this.allowedUsers.size === 0) return true; // no allowlist = open
    const from = update.message?.from;
    if (!from) return false;
    return this.allowedUsers.has(from.id) ||
      (from.username ? this.allowedUsers.has(from.username) : false);
  }

  private splitMessage(text: string, maxLen: number): string[] {
    if (text.length <= maxLen) return [text];
    const parts: string[] = [];
    let i = 0;
    while (i < text.length) {
      parts.push(text.slice(i, i + maxLen));
      i += maxLen;
    }
    return parts;
  }

  setMessageHandler(handler: (text: string, chatId: number, from: string) => Promise<string>): void {
    this.onMessage = handler;
  }

  async start(): Promise<void> {
    this.running = true;
    const me = await this.getMe();
    console.log(`[Telegram] Bot started: @${me.username || me.first_name}`);

    while (this.running) {
      try {
        const updates = await this.getUpdates(25);
        for (const update of updates) {
          if (!update.message?.text) continue;
          if (!this.isAllowed(update)) {
            await telegramRequest(this.token, 'sendMessage', {
              chat_id: update.message.chat.id,
              text: '⛔ Not authorized.',
            });
            continue;
          }

          const chatId = update.message.chat.id;
          const text = update.message.text;
          const from = update.message.from?.username ||
            update.message.from?.first_name || String(update.message.from?.id || 'unknown');

          if (this.onMessage) {
            try {
              // Send typing indicator
              await telegramRequest(this.token, 'sendChatAction', {
                chat_id: chatId, action: 'typing',
              });
              const reply = await this.onMessage(text, chatId, from);
              await this.sendMessage(chatId, reply || '✓ Done');
            } catch (e) {
              await this.sendMessage(chatId, `❌ Error: ${e}`);
            }
          } else {
            await this.sendMessage(chatId, `Received: ${text}\n(No handler configured)`);
          }
        }
      } catch (e) {
        // Network error — wait and retry
        await new Promise(r => setTimeout(r, 5000));
      }
    }
  }

  stop(): void {
    this.running = false;
  }
}

// ── Simple send function (no bot instance needed) ─────────────────────────────

export async function sendTelegramMessage(
  token: string,
  chatId: number | string,
  text: string
): Promise<boolean> {
  const chunks = text.match(/[\s\S]{1,4096}/g) || [text];
  for (const chunk of chunks) {
    const res = await telegramRequest(token, 'sendMessage', {
      chat_id: chatId,
      text: chunk,
      parse_mode: 'Markdown',
    });
    if (!res.ok) return false;
  }
  return true;
}

// ── Bot factory ───────────────────────────────────────────────────────────────

export function createTelegramBot(
  token?: string,
  allowedUsers: (number | string)[] = []
): TelegramBot | null {
  const t = token || process.env.TELEGRAM_BOT_TOKEN;
  if (!t) return null;
  return new TelegramBot(t, allowedUsers);
}
