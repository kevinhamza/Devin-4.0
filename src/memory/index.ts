// src/memory/index.ts — Lightweight in-process memory (SQLite-backed)
// Mirrors Devin's Python long-term memory but runs natively in TypeScript

import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { Memory } from '../types.js';

const MEMORY_DIR = path.join(os.homedir(), '.devin');
const MEMORY_FILE = path.join(MEMORY_DIR, 'memory.json');

interface StoredMemory {
  id: string;
  content: string;
  timestamp: number;
  tags: string[];
  metadata: Record<string, unknown>;
}

function loadMemories(): StoredMemory[] {
  try {
    if (fs.existsSync(MEMORY_FILE)) {
      return JSON.parse(fs.readFileSync(MEMORY_FILE, 'utf8'));
    }
  } catch { /* ignore */ }
  return [];
}

function saveMemories(memories: StoredMemory[]): void {
  fs.mkdirSync(MEMORY_DIR, { recursive: true });
  fs.writeFileSync(MEMORY_FILE, JSON.stringify(memories, null, 2));
}

function cosineSimilarity(a: number[], b: number[]): number {
  if (a.length !== b.length) return 0;
  let dot = 0, na = 0, nb = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    na += a[i] * a[i];
    nb += b[i] * b[i];
  }
  return dot / (Math.sqrt(na) * Math.sqrt(nb) || 1);
}

// Simple TF-based embedding (no external model needed)
function embed(text: string): number[] {
  const words = text.toLowerCase().split(/\W+/).filter(Boolean);
  const vocab = new Set(words);
  const vec: number[] = [];
  for (const word of vocab) {
    const count = words.filter(w => w === word).length;
    vec.push(count / words.length);
  }
  return vec;
}

export class LocalMemory {
  private memories: StoredMemory[];

  constructor() {
    this.memories = loadMemories();
  }

  add(content: string, tags: string[] = [], metadata: Record<string, unknown> = {}): string {
    const id = `mem_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
    this.memories.push({ id, content, timestamp: Date.now(), tags, metadata });
    if (this.memories.length > 1000) this.memories = this.memories.slice(-1000);
    saveMemories(this.memories);
    return id;
  }

  search(query: string, topK = 5): StoredMemory[] {
    if (this.memories.length === 0) return [];
    const qEmb = embed(query);
    return this.memories
      .map(m => ({ ...m, score: cosineSimilarity(qEmb, embed(m.content)) }))
      .sort((a, b) => b.score - a.score)
      .slice(0, topK)
      .filter(m => m.score > 0);
  }

  recent(n = 10): StoredMemory[] {
    return this.memories.slice(-n).reverse();
  }

  all(): StoredMemory[] {
    return [...this.memories];
  }
}
