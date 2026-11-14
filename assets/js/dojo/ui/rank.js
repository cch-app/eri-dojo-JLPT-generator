import { ja } from "../core/dom.js";

/** "白帯 · White belt" in English; the gloss alone in 繁中 (it already reads as the belt name). */
export const rankLabel = (rank, locale) => (locale.lang === "zh" ? locale.tx(rank.g) : `${ja(rank.ja)} · ${locale.tx(rank.g)}`);
