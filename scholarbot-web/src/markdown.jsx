/**
 * Markdown rendering for bot answers: GFM tables, KaTeX math, and the inline
 * [n] citation badges of the v4.0 citation system.
 *
 * Split out of App.jsx so it can be rendered and checked in isolation.
 */

import { useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import { visit } from 'unist-util-visit';
import 'katex/dist/katex.min.css';

export const CITATION_REGEX = /\[(\d{1,2})\]/g;

/** Collect citation ids actually used in an answer, ignoring out-of-range markers. */
export function parseCitationIds(text, sourceCount) {
  if (!text || !sourceCount) return [];
  const found = new Set();
  for (const raw of text.match(CITATION_REGEX) || []) {
    const id = parseInt(raw.slice(1, -1), 10);
    if (id >= 1 && id <= sourceCount) found.add(id);
  }
  return [...found].sort((a, b) => a - b);
}

/**
 * Normalize the LaTeX delimiters the model actually emits.
 *
 * remark-math only understands $...$ and $$...$$, while Groq models routinely
 * answer with \( ... \) and \[ ... \]. Without this the formula shows up as
 * raw backslashes in the bubble.
 */
export function normalizeMathDelimiters(text) {
  if (!text) return text;
  return text
    .replace(/\\\[([\s\S]+?)\\\]/g, (_, body) => `\n\n$$\n${body.trim()}\n$$\n\n`)
    .replace(/\\\(([\s\S]+?)\\\)/g, (_, body) => `$${body.trim()}$`);
}

/**
 * Rehype plugin: split text nodes on [n] markers into <citation> elements.
 *
 * react-markdown has no hook for text nodes, so the supported way to inject a
 * custom inline element is to rewrite the tree and map the new tag through the
 * `components` prop. Markers above `maxId` are left as plain text, and code
 * blocks are skipped so snippets like arr[1] stay untouched.
 */
export function rehypeCitations({ maxId = 0 } = {}) {
  return (tree) => {
    visit(tree, 'text', (node, index, parent) => {
      if (!parent || index === null || maxId < 1) return;
      if (parent.tagName === 'code' || parent.tagName === 'pre') return;
      if (!/\[\d{1,2}\]/.test(node.value)) return;

      const parts = [];
      let lastIndex = 0;
      let match;
      const re = /\[(\d{1,2})\]/g;

      while ((match = re.exec(node.value)) !== null) {
        const id = parseInt(match[1], 10);
        if (id < 1 || id > maxId) continue; // unknown source → leave as text

        if (match.index > lastIndex) {
          parts.push({ type: 'text', value: node.value.slice(lastIndex, match.index) });
        }
        parts.push({
          type: 'element',
          tagName: 'citation',
          properties: {},
          children: [{ type: 'text', value: String(id) }],
        });
        lastIndex = match.index + match[0].length;
      }

      if (!parts.length) return;
      if (lastIndex < node.value.length) {
        parts.push({ type: 'text', value: node.value.slice(lastIndex) });
      }
      parent.children.splice(index, 1, ...parts);
      return index + parts.length;
    });
  };
}

/** Clickable [n] badge rendered in place of a citation marker. */
function CitationBadge({ id, isActive, onCite }) {
  return (
    <button
      type="button"
      onClick={() => onCite?.(id)}
      title={`Lihat sumber ${id}`}
      className={`inline-flex items-center justify-center align-super mx-0.5 min-w-[15px] h-[15px] px-1 rounded-full
        text-[8px] font-bold leading-none transition-colors cursor-pointer border
        ${isActive
          ? 'bg-walnut text-surface-raised border-walnut'
          : 'bg-walnut/10 text-walnut border-walnut/20 hover:bg-walnut hover:text-surface-raised'}`}
    >
      {id}
    </button>
  );
}

/** Element overrides that keep markdown output inside the editorial theme. */
function buildMarkdownComponents({ activeId, onCite }) {
  return {
    citation: ({ children }) => {
      const id = parseInt(String(children), 10);
      return <CitationBadge id={id} isActive={activeId === id} onCite={onCite} />;
    },
    p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
    strong: ({ children }) => <strong className="font-bold text-text-primary">{children}</strong>,
    em: ({ children }) => <em className="italic">{children}</em>,
    h1: ({ children }) => <h4 className="font-bold text-sm text-text-primary font-serif mt-2 mb-1">{children}</h4>,
    h2: ({ children }) => <h4 className="font-bold text-sm text-text-primary font-serif mt-2 mb-1">{children}</h4>,
    h3: ({ children }) => <h4 className="font-bold text-sm text-text-primary font-serif mt-2 mb-1">{children}</h4>,
    h4: ({ children }) => <h5 className="font-bold text-xs text-text-primary font-serif mt-2 mb-1">{children}</h5>,
    ul: ({ children }) => <ul className="list-disc pl-5 flex flex-col gap-1 mb-2">{children}</ul>,
    ol: ({ children }) => <ol className="list-decimal pl-5 flex flex-col gap-1 mb-2">{children}</ol>,
    li: ({ children }) => <li className="leading-relaxed">{children}</li>,
    blockquote: ({ children }) => (
      <blockquote className="pl-3 border-l-2 border-border text-text-muted italic mb-2">{children}</blockquote>
    ),
    a: ({ href, children }) => (
      <a href={href} target="_blank" rel="noopener noreferrer" className="text-walnut underline underline-offset-2">
        {children}
      </a>
    ),
    // react-markdown v9+ dropped the `inline` prop: a fenced block either carries
    // a language class or spans multiple lines.
    code: ({ className, children }) => {
      const isBlock = /language-/.test(className || '') || String(children).includes('\n');
      return isBlock
        ? <code className="block font-mono text-[10px] leading-relaxed">{children}</code>
        : <code className="px-1 py-0.5 rounded bg-background/70 border border-border/60 font-mono text-[10px]">{children}</code>;
    },
    pre: ({ children }) => (
      <pre className="p-2.5 mb-2 rounded-lg bg-background/70 border border-border/60 overflow-x-auto scrollbar-thin">
        {children}
      </pre>
    ),
    hr: () => <hr className="my-3 border-divider" />,
    table: ({ children }) => (
      <div className="mb-2 overflow-x-auto scrollbar-thin rounded-lg border border-border">
        <table className="w-full border-collapse text-[10px]">{children}</table>
      </div>
    ),
    thead: ({ children }) => <thead className="bg-surface-raised">{children}</thead>,
    th: ({ children }) => (
      <th className="px-2 py-1.5 text-left font-bold text-text-primary border-b border-border">{children}</th>
    ),
    td: ({ children }) => <td className="px-2 py-1.5 border-b border-divider align-top">{children}</td>,
  };
}

/** Bot answer body: markdown + math + clickable citations. */
export function AnswerBody({ content, sourceCount = 0, activeId = null, onCite }) {
  const normalized = useMemo(() => normalizeMathDelimiters(content), [content]);
  const components = useMemo(() => buildMarkdownComponents({ activeId, onCite }), [activeId, onCite]);

  return (
    <div className="markdown-body">
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex, [rehypeCitations, { maxId: sourceCount }]]}
        components={components}
      >
        {normalized}
      </ReactMarkdown>
    </div>
  );
}
