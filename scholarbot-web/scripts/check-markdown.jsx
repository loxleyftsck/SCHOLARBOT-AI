/**
 * Smoke check for the bot answer renderer (src/markdown.jsx).
 *
 * Renders one answer containing every construct the Groq model actually emits —
 * GFM table, block and inline LaTeX, citation markers, code — and asserts the
 * HTML comes out right. Run with: npm run check:markdown
 */

import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { AnswerBody } from '../src/markdown.jsx';

const ANSWER = [
  '**1. Definisi**',
  '',
  'Elastisitas permintaan adalah ukuran kepekaan jumlah barang. [3]',
  '',
  '| Harga | Kuantitas | Elastisitas |',
  '|---|---|---|',
  '| Rp10.000 | 1000 kg | – |',
  '| Rp11.000 | 950 kg | 0,5 (<1) |',
  '',
  'Rumusnya \\[ E_d = \\frac{\\%\\Delta Q_d}{\\%\\Delta P} \\] dan inline \\( x^2 \\) juga.',
  '',
  '- Barang mewah bersifat elastis. [2]',
  '- Beras bersifat inelastis. [1][9]',
  '',
  '```python',
  'arr[1] = 5',
  '```',
  '',
  'Sisa `kode[2]` inline.',
].join('\n');

const html = renderToStaticMarkup(
  React.createElement(AnswerBody, {
    content: ANSWER,
    sourceCount: 3,
    activeId: 1,
    onCite: () => {},
  })
);

const count = (re) => (html.match(re) || []).length;

const checks = [
  ['tabel GFM dirender', /<table/.test(html)],
  ['semua sel tabel ada', count(/<td /g) === 6],
  ['rumus blok jadi KaTeX display', /katex-display/.test(html)],
  ['dua rumus dirender KaTeX', count(/class="katex"/g) === 2],
  // KaTeX keeps the original TeX inside <annotation>, so only check the visible text
  ['tidak ada delimiter LaTeX mentah', !html.includes('\\[') && !html.includes('\\(')],
  ['tiga badge sitasi valid', count(/title="Lihat sumber/g) === 3],
  ['badge aktif ditandai', html.includes('bg-walnut text-surface-raised border-walnut')],
  ['penanda di luar rentang tetap teks', html.includes('[9]')],
  ['kode blok tidak disentuh', html.includes('arr[1]')],
  ['kode inline tidak disentuh', html.includes('kode[2]')],
];

let failed = 0;
for (const [label, ok] of checks) {
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${label}`);
  if (!ok) failed++;
}

if (process.argv.includes('--html')) console.log('\n' + html);

if (failed) {
  console.error(`\n${failed} pemeriksaan gagal.`);
  process.exit(1);
}
console.log(`\n${checks.length} pemeriksaan lulus.`);
