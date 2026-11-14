import { esc } from "../core/dom.js";
import { keeperAt } from "../content/keepers.js";
import { TOTAL_STAMPS, TRAILS } from "../content/mountain.js";

/** 登山印帳: one row per trail, one cell per checkpoint keeper's seal. */
export function stampBookHTML(progress, locale) {
  const rows = TRAILS.map((tr, s) => {
    const cells = [0, 1, 2].map((k) => {
      const K = keeperAt(s, k), got = progress.hasStamp(s, k);
      return got
        ? `<span class="sb-cell got" title="${esc(`${K.ja} · ${locale.tx(K.role.slice(1))}`)}"><span class="seal-k" lang="ja">${K.seal}</span><span class="sb-name" lang="ja">${K.ja}</span></span>`
        : `<span class="sb-cell" title="?"><span class="sb-q">?</span></span>`;
    }).join("");
    return `<div class="sb-row"><span class="sb-trail" lang="ja">${tr.ja}</span>${cells}</div>`;
  }).join("");
  return `<div class="stampbook"><div class="sb-head"><span lang="ja">登山印帳</span>${locale.lang === "zh" ? "" : ` · ${locale.t("stampBook")}`} <b>${progress.stampCount}/${TOTAL_STAMPS}</b></div>
    <div class="sb-grid">${rows}</div></div>`;
}
