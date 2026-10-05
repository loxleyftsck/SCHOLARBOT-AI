import { cpSync, mkdirSync, writeFileSync, rmSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';
import { build, loadEnv } from 'vite';

const frontend = fileURLToPath(new URL('../', import.meta.url));
const root = resolve(frontend, '..');
const local = process.argv.includes('--local');
const api = local ? 'http://127.0.0.1:8000' : process.env.VITE_API_BASE_URL || loadEnv('production', frontend, '').VITE_API_BASE_URL;
if (!local && (!api || !/^https:\/\//.test(api))) {
  throw new Error('Set VITE_API_BASE_URL to the HTTPS URL of your backend before building the public demo.');
}
await build({ root: frontend, base: '/app/', define: { 'import.meta.env.VITE_API_BASE_URL': JSON.stringify(api) } });
const output = resolve(root, 'dist-demo');
rmSync(output, { recursive: true, force: true });
mkdirSync(output, { recursive: true });
cpSync(resolve(root, 'landing'), output, { recursive: true });
cpSync(resolve(frontend, 'dist'), resolve(output, 'app'), { recursive: true });
writeFileSync(resolve(output, '_redirects'), '/app /app/ 301\n/app/* /app/index.html 200\n');
console.log('Pages output ready: dist-demo (landing /, workspace /app/)');
