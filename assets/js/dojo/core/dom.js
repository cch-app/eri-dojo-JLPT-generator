export const $ = (selector, root = document) => root.querySelector(selector);
export const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

const ESCAPES = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" };
export const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ESCAPES[c]);

/** Wrap Japanese text so it is always set in Japanese faces. */
export const ja = (s) => `<span lang="ja">${s}</span>`;

/**
 * Escape untrusted (AI-generated) text, then re-allow the one bit of markup
 * the exam style uses: <u>…</u> to mark the target word.
 */
export function examText(s) {
  return esc(s).replace(/&lt;u&gt;([\s\S]*?)&lt;\/u&gt;/g, "<u>$1</u>");
}

export function scrollTop() {
  window.scrollTo(0, 0);
}
