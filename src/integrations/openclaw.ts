// src/integrations/openclaw.ts — Integration with openclaw (multi-channel messaging)

import * as cp from 'child_process';
import * as path from 'path';
import * as fs from 'fs';
import { PROJECT_ROOT } from '../config.js';

const OPENCLAW_DIR = path.join(PROJECT_ROOT, 'external', 'openclaw');

export function isOpenclawAvailable(): boolean {
  return fs.existsSync(OPENCLAW_DIR) && fs.readdirSync(OPENCLAW_DIR).length > 0;
}

export function sendTelegramMessage(text: string, chatId?: string): { success: boolean; error?: string } {
  const token = process.env.TELEGRAM_BOT_TOKEN;
  const id = chatId || process.env.TELEGRAM_CHAT_ID;
  if (!token || !id) return { success: false, error: 'TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set' };

  const url = `https://api.telegram.org/bot${token}/sendMessage`;
  const body = JSON.stringify({ chat_id: id, text, parse_mode: 'Markdown' });

  try {
    const result = cp.spawnSync('curl', ['-s', '-X', 'POST', url, '-H', 'Content-Type: application/json', '-d', body], {
      encoding: 'utf8',
      timeout: 10000,
    });
    const response = JSON.parse(result.stdout || '{}');
    return { success: response.ok === true };
  } catch (e) {
    return { success: false, error: String(e) };
  }
}
