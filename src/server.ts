// src/server.ts — Web API server for Devin-4.0 web UI
// Serves the web interface and proxies API requests to the conversation engine

import * as http from 'http';
import * as fs from 'fs';
import * as path from 'path';
import * as url from 'url';

const DEVIN_ROOT = path.join(__dirname, '..');
const WEB_DIR = path.join(DEVIN_ROOT, 'web');
const PORT = parseInt(process.env.PORT || '3000', 10);

const MIME_TYPES: Record<string, string> = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css',
  '.js': 'application/javascript',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.woff2': 'font/woff2',
};

// ── Request handler ───────────────────────────────────────────────────────────

type ConversationHandler = (message: string) => Promise<{
  response: string;
  toolCalls?: Array<{ name: string; result: string }>;
}>;

let conversationHandler: ConversationHandler | null = null;

export function setConversationHandler(handler: ConversationHandler): void {
  conversationHandler = handler;
}

async function handleRequest(
  req: http.IncomingMessage,
  res: http.ServerResponse
): Promise<void> {
  const parsedUrl = url.parse(req.url || '/', true);
  const pathname = parsedUrl.pathname || '/';

  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  // API routes
  if (pathname === '/api/chat' && req.method === 'POST') {
    let body = '';
    req.on('data', (chunk: Buffer) => { body += chunk.toString(); });
    req.on('end', async () => {
      try {
        const { message } = JSON.parse(body);
        if (!message) {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: 'message required' }));
          return;
        }
        if (conversationHandler) {
          const result = await conversationHandler(message);
          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify(result));
        } else {
          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({
            response: `Devin received: "${message}"\n\nStart Devin CLI (devin) for full AI conversation support.`,
            toolCalls: [],
          }));
        }
      } catch (e) {
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: String(e) }));
      }
    });
    return;
  }

  if (pathname === '/api/status' && req.method === 'GET') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      status: 'online',
      version: '4.0',
      handler: !!conversationHandler,
      timestamp: new Date().toISOString(),
    }));
    return;
  }

  // Static files
  let filePath = path.join(WEB_DIR, pathname === '/' ? 'index.html' : pathname);
  if (!filePath.startsWith(WEB_DIR)) {
    res.writeHead(403);
    res.end('Forbidden');
    return;
  }

  if (!fs.existsSync(filePath)) {
    filePath = path.join(WEB_DIR, 'index.html');
  }

  const ext = path.extname(filePath);
  const mimeType = MIME_TYPES[ext] || 'application/octet-stream';

  try {
    const content = fs.readFileSync(filePath);
    res.writeHead(200, { 'Content-Type': mimeType });
    res.end(content);
  } catch {
    res.writeHead(404);
    res.end('Not found');
  }
}

// ── Server factory ────────────────────────────────────────────────────────────

export function createWebServer(): http.Server {
  const server = http.createServer((req, res) => {
    handleRequest(req, res).catch(e => {
      res.writeHead(500);
      res.end(String(e));
    });
  });
  return server;
}

export function startWebServer(port = PORT): Promise<void> {
  return new Promise((resolve) => {
    const server = createWebServer();
    server.listen(port, () => {
      console.log(`[Web] Devin UI: http://localhost:${port}`);
      resolve();
    });
  });
}

// ── CLI entry ────────────────────────────────────────────────────────────────

if (require.main === module) {
  startWebServer().then(() => {
    console.log('[Web] Server running. Open browser at http://localhost:3000');
  });
}
