import { ja } from "../core/dom.js";
import { buildCharacter } from "../art/portraits.js";
import { SECTIONS } from "../content/levels.js";
import { TRAILS, altAt, nodeIndex } from "../content/mountain.js";

/**
 * The checkpoint encounter frame: keeper portrait on one side, the three
 * trial steps above whatever `side` content the view supplies (dialogue, verdict).
 * `doneK` = steps already cleared (defaults to k).
 */
export function checkpointCardHTML({ keeper: K, seg, k, doneK = k, side, locale }) {
  const steps = SECTIONS.map((s, i) => {
    const cls = i < doneK ? "done" : i === k && i >= doneK ? "now" : "";
    return `<span class="${cls}"><b lang="ja">${s.kanji}</b>${locale.t("sect")[s.id]}</span>`;
  }).join("");
  return `<section class="cp enter">
    <div class="cp-head"><span class="eyebrow">${ja(TRAILS[seg].ja)} · ${locale.tx(TRAILS[seg].g)} · ${locale.t("checkpointN", k + 1)}</span>
      <span class="cp-alt">${locale.t("alt", altAt(nodeIndex(seg, k + 1)))}</span></div>
    <div class="cp-body">
      <div class="cp-portrait">${buildCharacter({ ...K.look, id: "kp" })}<div class="cp-name"><b lang="ja">${K.ja}</b><span>${locale.tx(K.role.slice(1))} · ${locale.lang === "zh" ? K.zh : K.en}</span></div></div>
      <div class="cp-side">
        <div class="cp-steps">${steps}</div>
        ${side}
      </div>
    </div></section>`;
}

/** The keeper's small talking portrait for the dialogue box. */
export const keeperFace = (K) => buildCharacter({ ...K.look, id: "kt" });
export const keeperWho = (K) => ({ ja: K.ja, g: [K.role[1], K.role[2]] });
