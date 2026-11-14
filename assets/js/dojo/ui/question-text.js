/**
 * Generated prompts arrive as one block of text. When it holds several
 * paragraphs, everything before the last is the reading passage (本文) and
 * the last paragraph is the question itself.
 */
export function splitPrompt(prompt) {
  const parts = String(prompt || "").trim().split(/\n\s*\n/);
  if (parts.length < 2) return { passage: "", question: parts[0] || "" };
  return { passage: parts.slice(0, -1).join("\n\n"), question: parts[parts.length - 1] };
}
