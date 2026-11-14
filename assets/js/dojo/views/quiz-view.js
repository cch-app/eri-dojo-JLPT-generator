import { $, $$, esc, examText, ja, scrollTop } from "../core/dom.js";
import { LEVELS, SECTIONS, sectionById } from "../content/levels.js";
import { keeperAt } from "../content/keepers.js";
import { QuizRun } from "../domain/quiz-run.js";
import { splitPrompt } from "../ui/question-text.js";

/**
 * The washi exam sheet. Practice covers all three sections of the hut's level;
 * a checkpoint trial covers the one section its keeper guards. Questions are
 * generated while you answer, so slots not yet written show drying ink.
 */
export class QuizView {
  constructor(ctx, { mode }) {
    this.ctx = ctx;
    this.mode = mode;
  }

  /** The trail map can't be used to walk away from a test. */
  get locksNavigation() {
    return true;
  }

  mount(root) {
    this.root = root;
    this.start();
  }

  start() {
    const { progress, config } = this.ctx;
    this.run = this.mode === "practice"
      ? new QuizRun({
          mode: "practice",
          levelIndex: LEVELS.indexOf(progress.practiceLevel),
          plan: SECTIONS.map((s) => ({ sectionId: s.id, count: config.practicePerSection })),
        })
      : new QuizRun({
          mode: "test",
          levelIndex: progress.pos,
          seg: progress.pos,
          k: progress.k,
          plan: [{ sectionId: SECTIONS[progress.k].id, count: config.checkpointSize }],
        });
    this.loader = this.ctx.createLoader();
    this.render(true);
    this.loader.load(this.run, () => this.onSupply());
    scrollTop();
  }

  unmount() {
    this.loader.cancel();
  }

  refresh() {
    this.render(false);
  }

  /** A question arrived (or generation ended): only repaint what changed under the reader's eyes. */
  onSupply() {
    const showing = $(".question", this.root) ? "question" : "waiting";
    const now = this.run.current ? "question" : "waiting";
    if (showing === now && !this.loader.error) this.patchChrome();
    else this.render(false);
  }

  sectionAt(i) {
    if (this.run.items[i]) return this.run.items[i].sectionId;
    let n = this.run.items.length;
    for (const p of this.run.plan) {
      const done = this.run.items.filter((it) => it.sectionId === p.sectionId).length;
      n += p.count - done;
      if (i < n) return p.sectionId;
    }
    return this.run.plan[this.run.plan.length - 1].sectionId;
  }

  titleHTML() {
    const { locale } = this.ctx, run = this.run, L = LEVELS[run.levelIndex];
    if (run.isTest) return `${ja(`第${run.k + 1}関`)} · ${ja(keeperAt(run.seg, run.k).ja)} <span class="t-gl">${locale.t("needAll")}</span>`;
    return `<span lang="ja">${L.id} 稽古 · ${L.belt}</span> <span class="t-gl">${locale.t("practiceTitle", L.id)}</span>`;
  }

  pipsHTML() {
    const run = this.run;
    return Array.from({ length: run.planned }, (_, i) => {
      const cls = i === run.idx ? "now" : run.answers[i] != null ? "done" : i >= run.items.length ? "pending" : "";
      return `<span class="pip ${cls}"></span>`;
    }).join("");
  }

  metaHTML() {
    return `${ja("問")} ${this.run.idx + 1} / ${Math.max(1, this.run.planned)}`;
  }

  bodyHTML() {
    const { locale } = this.ctx, run = this.run, L = LEVELS[run.levelIndex];
    const it = run.current;
    const sectionId = this.sectionAt(run.idx);
    const mondai = `<div class="mondai">${ja(sectionById(sectionId).ja)} <span class="gl">· ${L.id} · ${locale.t("sect")[sectionId]}</span></div>`;
    const err = this.loader.error;
    if (err && !it)
      return `<div class="sheet-error" role="alert">${esc(locale.t("genFailed"))}${err.message ? `<br>${esc(err.message)}` : ""}</div>`;
    if (!it)
      return `${mondai}<div class="brewing" aria-hidden="true"><span></span><span></span><span></span></div>
        <p class="brewing-note" role="status">${locale.t(run.items.length ? "brewingNext" : "brewing")}</p>`;
    const { passage, question } = splitPrompt(it.question.prompt);
    const opts = it.order.map((choice, i) => {
      const sel = run.answer === choice, struck = run.isStruck(choice);
      return `<button class="opt ${sel ? "sel" : ""} ${struck ? "struck" : ""}" role="radio" aria-checked="${sel}" data-c="${choice}" ${struck ? "disabled" : ""}><span class="n">${i + 1}</span><span>${esc(it.question.choices[choice])}</span></button>`;
    }).join("");
    return `${mondai}
      ${passage ? `<div class="passage" lang="ja">${esc(passage)}</div>` : ""}
      <div class="question" lang="ja">${examText(question)}</div>
      <div class="opts" role="radiogroup" lang="ja">${opts}</div>`;
  }

  navHTML() {
    const { locale } = this.ctx, run = this.run;
    const failed = this.loader.error && !run.current;
    const canRetry = failed && this.loader.error.retryable;
    const hint = run.isTest && !failed
      ? `<button class="btn ghost hintb" id="hint" ${run.hint.used || !run.current ? "disabled" : ""}>${run.hint.used ? locale.t("hintUsed") : locale.t("hint")}</button>`
      : "";
    const main = failed
      ? canRetry ? `<button class="btn primary" id="retry">${locale.t("retry")}</button>` : ""
      : `<button class="btn ${run.isLast ? "shu" : "primary"}" id="next" ${(run.isLast ? run.canSubmit : run.canAdvance) ? "" : "disabled"}>${run.isLast ? locale.t("submit") : locale.t("next")}</button>`;
    return `<div class="grp">
        <button class="btn ghost" id="quit">${locale.t("leave")}</button>
        ${run.idx > 0 ? `<button class="btn ghost" id="back">${locale.t("back")}</button>` : ""}
        ${hint}
      </div>${main}`;
  }

  render(animate) {
    this.root.innerHTML = `
    <div class="sheet${animate ? " enter" : ""}">
      <div class="sheet-top">
        <div class="t">${this.titleHTML()}</div>
        <div class="meta">${this.metaHTML()}</div>
      </div>
      <div class="pips" aria-hidden="true">${this.pipsHTML()}</div>
      <div class="sheet-body">${this.bodyHTML()}</div>
      <div class="nav">${this.navHTML()}</div>
    </div>`;
    $$(".opt:not([disabled])", this.root).forEach((b) => (b.onclick = () => {
      this.run.select(+b.dataset.c);
      this.render(true);
    }));
    this.bindNav();
  }

  patchChrome() {
    $(".pips", this.root).innerHTML = this.pipsHTML();
    $(".meta", this.root).innerHTML = this.metaHTML();
    $(".nav", this.root).innerHTML = this.navHTML();
    this.bindNav();
  }

  bindNav() {
    const run = this.run, on = (id, fn) => {
      const b = $(`#${id}`, this.root);
      if (b) b.onclick = fn;
    };
    on("next", () => {
      if (run.isLast) return this.finish();
      run.next();
      this.render(true);
    });
    on("back", () => {
      run.back();
      this.render(true);
    });
    on("quit", () => this.ctx.go(run.isTest ? "checkpoint" : "hut"));
    on("hint", () => {
      run.useHint();
      this.render(false);
    });
    on("retry", () => {
      this.loader.cancel();
      this.start();
    });
  }

  finish() {
    const { progress } = this.ctx, run = this.run, results = run.results();
    if (run.isTest) {
      const outcome = progress.recordCheckpoint(results.passed);
      this.ctx.go("checkpointResult", { run, results, outcome });
    } else {
      const count = progress.recordPractice(LEVELS[run.levelIndex].id, results.score);
      this.ctx.go("practiceResult", { run, results, count });
    }
    scrollTop();
  }
}
