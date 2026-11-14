/** Mount Kotonoha: six huts joined by five trails, each trail guarded by three checkpoints. */
export const HUTS = [
  { ja: "登山口", g: ["Trailhead", "登山口"], alt: 400 },
  { ja: "白帯小屋", g: ["White Belt Hut", "白帶山屋"], alt: 900 },
  { ja: "黄帯小屋", g: ["Yellow Belt Hut", "黃帶山屋"], alt: 1500 },
  { ja: "緑帯小屋", g: ["Green Belt Hut", "綠帶山屋"], alt: 2100 },
  { ja: "茶帯小屋", g: ["Brown Belt Hut", "棕帶山屋"], alt: 2800 },
  { ja: "山頂", g: ["Summit", "山頂"], alt: 3500 },
];

export const TRAILS = [
  { ja: "麓の道", g: ["Foothill trail", "山腳之路"] },
  { ja: "杉の道", g: ["Cedar trail", "杉林之路"] },
  { ja: "岩の道", g: ["Rocky trail", "岩石之路"] },
  { ja: "雲の道", g: ["Cloud trail", "雲海之路"] },
  { ja: "頂の道", g: ["Summit trail", "山頂之路"] },
];

export const CHECKPOINTS_PER_TRAIL = 3;
export const SUMMIT = TRAILS.length; // hut index of the summit
export const TOTAL_STAMPS = TRAILS.length * CHECKPOINTS_PER_TRAIL;

// map node n = hut index*4 + checkpoint (0 = at the hut); 21 nodes from trailhead to summit
export const NODES = [[200,585],[112,566],[70,526],[126,500],[226,484],[318,458],[340,418],[272,398],[172,383],[88,354],[80,314],[148,292],
  [244,277],[320,252],[318,212],[252,193],[176,180],[118,150],[136,114],[182,94],[214,62]];

export const nodeIndex = (hut, k) => hut * 4 + k;

export function altAt(n) {
  const h = Math.floor(n / 4), k = n % 4;
  if (k === 0) return HUTS[h].alt;
  return Math.round((HUTS[h].alt + ((HUTS[h + 1].alt - HUTS[h].alt) * k) / 4) / 10) * 10;
}
