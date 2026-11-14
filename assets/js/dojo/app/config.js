import { SECTIONS } from "../content/levels.js";

/** Page configuration injected by the server, plus sheet sizes clamped to what it accepts per stream. */
export function readConfig(doc = document) {
  const raw = JSON.parse(doc.getElementById("dojo-config").textContent || "{}");
  const max = raw.maxQuestions || 10;
  const practicePerSection = Math.min(3, max);
  return {
    uiLocale: raw.uiLocale,
    endpoints: raw.endpoints,
    practicePerSection,
    practiceSize: practicePerSection * SECTIONS.length,
    checkpointSize: Math.min(3, max),
  };
}
