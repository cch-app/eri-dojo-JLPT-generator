/** The five belts, N5 (white) to N1 (black). Questions themselves are generated per run. */
export const LEVELS = [
  { id: "N5", belt: "白帯", name: ["White belt", "白帶"], color: "#f3efe6", desc: ["Hiragana, basic kanji, everyday sentences.", "平假名、基礎漢字與日常短句。"] },
  { id: "N4", belt: "黄帯", name: ["Yellow belt", "黃帶"], color: "#e3b83c", desc: ["Daily-life kanji, giving/receiving, notices.", "生活常用漢字、授受表現與告示。"] },
  { id: "N3", belt: "緑帯", name: ["Green belt", "綠帶"], color: "#5e8a4a", desc: ["Bridging level: conjunctive grammar, work emails.", "銜接程度：接續文法與職場郵件。"] },
  { id: "N2", belt: "茶帯", name: ["Brown belt", "棕帶"], color: "#7b4a2a", desc: ["Abstract vocabulary, formal grammar, opinion essays.", "抽象詞彙、正式文法與評論文章。"] },
  { id: "N1", belt: "黒帯", name: ["Black belt", "黑帶"], color: "#141210", desc: ["Literary kanji, rare grammar, argumentative prose.", "書面語漢字、高階文法與論說文。"] },
];

/**
 * Test sections in checkpoint order. `category` is the generator's category id
 * for the Reading dojo; `kanji` marks the checkpoint on the map and stamp steps.
 */
export const SECTIONS = [
  { id: "vocab", ja: "文字・語彙", kanji: "語", category: "vocabulary" },
  { id: "grammar", ja: "文法", kanji: "文", category: "grammar" },
  { id: "reading", ja: "読解", kanji: "読", category: "reading_comprehension" },
];

export const sectionById = (id) => SECTIONS.find((s) => s.id === id);
