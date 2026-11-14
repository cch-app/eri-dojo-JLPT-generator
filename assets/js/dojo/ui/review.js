import { esc, examText } from "../core/dom.js";
import { splitPrompt } from "./question-text.js";

const choiceText = (r) => (r.pick == null ? "—" : r.question.choices[r.pick]);

/** Collapsible answer review shown on every result screen. */
export function reviewHTML(results, open, locale) {
  const rows = results.map((r, i) => {
    const { question } = splitPrompt(r.question.prompt);
    const right = r.question.choices[r.question.answer_index];
    const answer = r.ok
      ? `<span class="ok">○ ${esc(choiceText(r))}</span>`
      : `<span class="ng">× ${esc(choiceText(r))}</span> → <span class="ok">${esc(right)}</span>`;
    return `<div class="rv">
      <div class="q" lang="ja">${i + 1}. ${examText(question)}</div>
      <div class="a" lang="ja">${answer}</div>
      <div class="exp">${esc(r.question.explanation)}</div></div>`;
  }).join("");
  return `<details ${open ? "open" : ""}><summary>${locale.t("review")}</summary><div class="review">${rows}</div></details>`;
}
