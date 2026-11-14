import { shuffle } from "../core/random.js";

/**
 * One sitting at the exam sheet: a practice set at a hut, or a checkpoint trial.
 *
 * Questions arrive while the challenger is already answering (they are
 * generated on demand), so the run knows how many it *plans* to hold and
 * fills those slots as questions are supplied, section by section.
 */
export class QuizRun {
  /**
   * @param {object} o
   * @param {"practice"|"test"} o.mode
   * @param {number} o.levelIndex index into LEVELS
   * @param {{sectionId: string, count: number}[]} o.plan sections in sheet order
   * @param {number} [o.seg] trail index (tests only)
   * @param {number} [o.k] checkpoint index (tests only)
   */
  constructor({ mode, levelIndex, plan, seg = null, k = null }) {
    this.mode = mode;
    this.levelIndex = levelIndex;
    this.plan = plan.map((p) => ({ ...p }));
    this.seg = seg;
    this.k = k;
    this.items = [];
    this.answers = [];
    this.idx = 0;
    this.complete = false;
    this.hint = { used: false, removed: {} };
    this.start = Date.now();
  }

  get isTest() {
    return this.mode === "test";
  }

  /** Questions the sheet will hold once generation finishes. */
  get planned() {
    return this.complete ? this.items.length : this.plan.reduce((n, p) => n + p.count, 0);
  }

  get current() {
    return this.items[this.idx] || null;
  }

  get isLast() {
    return this.idx === this.planned - 1;
  }

  get answer() {
    return this.answers[this.idx] ?? null;
  }

  supply(sectionId, question) {
    this.items.push({ question, sectionId, order: shuffle(question.choices.map((_, i) => i)) });
    this.answers.push(null);
  }

  /** A section's generator stopped early: shrink its slot count to what arrived. */
  closeSection(sectionId) {
    const delivered = this.items.filter((it) => it.sectionId === sectionId).length;
    const p = this.plan.find((x) => x.sectionId === sectionId);
    if (p) p.count = delivered;
    this.keepIdxInPlan();
  }

  finishSupply() {
    this.complete = true;
    this.keepIdxInPlan();
  }

  /** If the slot being waited on will never arrive, step back to the last real question. */
  keepIdxInPlan() {
    this.idx = Math.min(this.idx, Math.max(0, this.planned - 1));
  }

  select(choiceIndex) {
    if (!this.current || this.isStruck(choiceIndex)) return;
    this.answers[this.idx] = choiceIndex;
  }

  isStruck(choiceIndex) {
    return this.isTest && this.hint.removed[this.idx] === choiceIndex;
  }

  get canAdvance() {
    return this.answer !== null && !this.isLast;
  }

  get canSubmit() {
    return this.answer !== null && this.isLast && this.complete;
  }

  next() {
    if (this.canAdvance) this.idx++;
  }

  back() {
    if (this.idx > 0) this.idx--;
  }

  /** Checkpoint aid: strike out one wrong option on the current question, once per trial. */
  useHint(random = Math.random) {
    const it = this.current;
    if (!this.isTest || this.hint.used || !it) return;
    const wrong = it.order.filter((i) => i !== it.question.answer_index && i !== this.answer);
    if (!wrong.length) return;
    this.hint.removed[this.idx] = wrong[Math.floor(random() * wrong.length)];
    this.hint.used = true;
  }

  results() {
    const res = this.items.map((it, i) => ({
      question: it.question,
      sectionId: it.sectionId,
      pick: this.answers[i],
      ok: this.answers[i] === it.question.answer_index,
    }));
    const correct = res.filter((r) => r.ok).length;
    return {
      res,
      correct,
      total: res.length,
      score: res.length ? correct / res.length : 0,
      passed: res.length > 0 && correct === res.length,
      mins: Math.max(1, Math.round((Date.now() - this.start) / 60000)),
    };
  }
}
