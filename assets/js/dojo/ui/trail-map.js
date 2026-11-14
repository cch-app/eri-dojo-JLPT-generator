import { rng } from "../core/random.js";
import { SECTIONS, LEVELS } from "../content/levels.js";
import { HUTS, NODES, SUMMIT, TRAILS } from "../content/mountain.js";
import { keeperAt } from "../content/keepers.js";

const f1 = (n) => n.toFixed(1);

/** Catmull-Rom → cubic Bézier segment from p1 to p2. */
const bezier = (p0, p1, p2, p3) =>
  `C${f1(p1[0] + (p2[0] - p0[0]) / 6)} ${f1(p1[1] + (p2[1] - p0[1]) / 6)} ${f1(p2[0] - (p3[0] - p1[0]) / 6)} ${f1(p2[1] - (p3[1] - p1[1]) / 6)} ${f1(p2[0])} ${f1(p2[1])}`;

// contour rings around the summit, drifting downhill
function contours(r) {
  let out = "";
  for (let j = 1; j <= 17; j++) {
    const cx = 214, cy = 62 + j * 25, rx = 24 + j * 25, ry = 16 + j * 24, pts = [];
    for (let a = 0; a < 48; a++) {
      const th = (a / 48) * Math.PI * 2, n = 1 + 0.09 * Math.sin(th * 3 + j) + 0.06 * Math.sin(th * 5 + j * 1.7) + 0.04 * (r() - 0.5);
      pts.push([cx + Math.cos(th) * rx * n, cy + Math.sin(th) * ry * n]);
    }
    let d = `M${f1(pts[0][0])} ${f1(pts[0][1])}`;
    for (let i = 0; i < 48; i++) d += bezier(pts[(i + 47) % 48], pts[i], pts[(i + 1) % 48], pts[(i + 2) % 48]);
    const idx = j % 4 === 0;
    out += `<path d="${d}Z" fill="none" stroke="${idx ? "#8a6a44" : "#a88a62"}" stroke-width="${idx ? 1.1 : 0.6}" opacity="${idx ? 0.75 : 0.5}"/>`;
    if (idx) {
      const lp = pts[44];
      out += `<text x="${lp[0].toFixed(0)}" y="${lp[1].toFixed(0)}" class="m-alt">${3500 - j * 190}</text>`;
    }
  }
  return out;
}

// trail: one curve per leg so walked legs are solid and the rest dashed
function trail(cur) {
  let out = "";
  for (let i = 0; i < 20; i++) {
    const p0 = NODES[Math.max(0, i - 1)], p1 = NODES[i], p2 = NODES[i + 1], p3 = NODES[Math.min(20, i + 2)];
    out += `<path d="M${p1[0]} ${p1[1]}${bezier(p0, p1, p2, p3)}" class="${i < cur ? "m-walked" : "m-ahead"}"/>`;
  }
  return out;
}

// a stream and forests: hiking-map conventions
function forest(r) {
  let out = `<path d="M392 300C350 330 380 380 352 430C330 470 368 520 340 560C326 584 340 604 336 620" class="m-stream"/>`;
  for (let i = 0; i < 70; i++) {
    const x = 20 + r() * 360, y = 330 + r() * 270;
    if (NODES.some((n) => Math.hypot(n[0] - x, n[1] - y) < 26)) continue;
    out += `<path d="M${x.toFixed(0)} ${(y - 6).toFixed(0)}l4 7h-8z" class="m-tree"/>`;
  }
  return out;
}

function hutMarker(progress, locale, hi) {
  const [x, y] = NODES[hi * 4];
  const reached = progress.pos >= hi, col = hi === 0 ? "#efe6d2" : LEVELS[hi - 1].color, side = hi === 0 || hi === SUMMIT;
  const label = hi === SUMMIT ? "N1" : hi === 0 ? "" : LEVELS[hi - 1].id;
  const icon = hi === SUMMIT
    ? `<path d="M${x - 1} ${y - 24}v-16l13 5-13 5" fill="#b2452f" stroke="#2a1d14" stroke-width="1.2"/>`
    : `<path d="M${x - 6} ${y + 1}l6-6 6 6v6h-12z" fill="${hi <= 1 ? "#2a1d14" : "#efe6d2"}" opacity=".85"/>`;
  const name = `${HUTS[hi].ja}${label ? ` · ${label}` : ""}`, sub = `${locale.tx(HUTS[hi].g)} · ${HUTS[hi].alt}m`;
  const text = side
    ? `<g transform="translate(${x + 18} ${y - 1})"><text class="m-name m-halo" lang="ja">${name}</text><text class="m-sub m-halo" y="12">${sub}</text></g>`
    : `<g text-anchor="middle"><text class="m-name m-halo" x="${x}" y="${y - 18}" lang="ja">${name}</text><text class="m-sub m-halo" x="${x}" y="${y + 25}">${sub}</text></g>`;
  return `<g class="m-hut ${reached ? "" : "m-dim"}">
    <circle cx="${x}" cy="${y}" r="13" fill="#efe6d2" stroke="#2a1d14" stroke-width="2"/>
    <circle cx="${x}" cy="${y}" r="9" fill="${col}" stroke="#2a1d14" stroke-width="${hi === 0 ? 0 : 1}"/>
    ${icon}${text}</g>`;
}

function checkpointMarker(progress, n) {
  const [x, y] = NODES[n], seg = Math.floor(n / 4), k = (n % 4) - 1;
  const got = progress.hasStamp(seg, k), lit = got || n <= progress.node;
  return `<g class="m-cp ${lit ? "" : "m-dim"}">
    <circle cx="${x}" cy="${y}" r="9.5" fill="${got ? "#b2452f" : "#efe6d2"}" stroke="${got ? "#7a2a1a" : "#2a1d14"}" stroke-width="1.6"/>
    <text x="${x}" y="${y + 3.6}" class="m-cpk ${got ? "m-got" : ""}" lang="ja">${got ? keeperAt(seg, k).seal : SECTIONS[k].kanji}</text></g>`;
}

function trailNames() {
  return TRAILS.map((tr, s) => {
    const a = NODES[s * 4 + 2], east = a[0] > 200;
    return `<text x="${a[0] + (east ? 16 : -16)}" y="${a[1] + 4}" class="m-trail" text-anchor="${east ? "start" : "end"}" lang="ja">${tr.ja}</text>`;
  }).join("");
}

function youAreHere(cur) {
  const [x, y] = NODES[cur];
  return `<g class="m-you" transform="translate(${x} ${y})"><circle r="16" class="m-pulse"/><path d="M0 -6C-7 -16 -10 -22 -10 -27A10 10 0 0 1 10 -27C10 -22 7 -16 0 -6Z" fill="#b2452f" stroke="#efe6d2" stroke-width="1.6"/><circle cy="-27" r="4" fill="#efe6d2"/></g>`;
}

/** The hiking map of Mount Kotonoha with your walked trail, stamps and position. */
export function trailMapSVG(progress, locale) {
  const r = rng(404), cur = progress.node;
  let marks = "";
  for (let n = 0; n <= 20; n++) marks += n % 4 === 0 ? hutMarker(progress, locale, n / 4) : checkpointMarker(progress, n);
  return `<svg viewBox="0 0 400 620" class="trailmap" role="img" aria-label="${locale.t("mapTitle")}">
    <defs><radialGradient id="m-paper" cx="50%" cy="45%" r="75%"><stop offset="0" stop-color="#f3ead6"/><stop offset=".75" stop-color="#e6d8ba"/><stop offset="1" stop-color="#c9b58e"/></radialGradient>
      <pattern id="m-fiber" width="7" height="7" patternUnits="userSpaceOnUse"><path d="M0 3.5h7" stroke="#b9a37c" stroke-width=".3" opacity=".35"/></pattern></defs>
    <rect width="400" height="620" fill="url(#m-paper)"/><rect width="400" height="620" fill="url(#m-fiber)"/>
    ${contours(r)}${forest(r)}
    <path d="M196 70L214 52L232 70" fill="none" stroke="#6a5030" stroke-width="1"/>
    ${trail(cur)}${marks}${trailNames()}${youAreHere(cur)}
    <g transform="translate(16 18)"><rect width="150" height="38" fill="#efe6d2" stroke="#2a1d14" stroke-width="1.2"/>
      <text x="10" y="17" class="m-title" lang="ja">言の葉山 登山地図</text><text x="10" y="31" class="m-sub">${locale.t("mapTitle")}</text></g>
    <g transform="translate(360 40)"><circle r="14" fill="#efe6d2" stroke="#2a1d14"/><path d="M0 -11L4 3H-4Z" fill="#b2452f"/><path d="M0 11L4 -3H-4Z" fill="#2a1d14"/><text y="-17" class="m-sub" text-anchor="middle">N</text></g>
    <g transform="translate(16 590)" class="m-sub"><path d="M0 0h60" stroke="#2a1d14" stroke-width="2"/><path d="M0 -3v6M30 -3v6M60 -3v6" stroke="#2a1d14"/><text x="66" y="4">1 km</text></g>
    <g transform="translate(22 72)" class="m-legend">
      <circle cx="6" cy="0" r="5" fill="#f3efe6" stroke="#2a1d14"/><text x="15" y="3.5">${locale.t("legendHut")}</text>
      <circle cx="6" cy="14" r="5" fill="#efe6d2" stroke="#2a1d14"/><text x="15" y="17.5">${locale.t("legendCp")}</text></g>
  </svg>`;
}
