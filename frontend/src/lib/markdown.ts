/**
 * Markdown rendering for builder block content.
 *
 * Multi-text fields (RichText, Hero subheadline, feature bodies, FAQ answers)
 * are authored in Markdown. We render with `marked` and sanitize the output
 * with DOMPurify (isomorphic — runs the same on the SSR Node server and in the
 * browser) before it reaches `{@html}`, so admin-authored content can't inject
 * scripts into a public page.
 */

import { marked } from 'marked';
import DOMPurify from 'isomorphic-dompurify';

marked.setOptions({ gfm: true, breaks: true });

/** Block-level Markdown → sanitized HTML (paragraphs, lists, headings, …). */
export function renderMarkdown(md: string | null | undefined): string {
  if (!md) return '';
  const html = marked.parse(md, { async: false }) as string;
  return DOMPurify.sanitize(html);
}

/** Inline Markdown → sanitized HTML, no wrapping block (titles, subheadlines). */
export function renderMarkdownInline(md: string | null | undefined): string {
  if (!md) return '';
  const html = marked.parseInline(md, { async: false }) as string;
  return DOMPurify.sanitize(html);
}
