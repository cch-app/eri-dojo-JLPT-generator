import { $, esc } from "../core/dom.js";
import { LEVELS, SECTIONS } from "../content/levels.js";
import { reviewHTML } from "../ui/review.js";

/** Practice results: score by section, the coach's AI feedback (with PDF), and the answer review. */
export class PracticeResultView {
  constructor(ctx, { run, results, count }) {
    Object.assign(this, { ctx, run, results, count });
    this.coach = { state: "writing" };
  }

  mount(root) {
    this.root = root;
    this.render();
    this.askCoach();
  }

  unmount() {
    this.cancelCoach && this.cancelCoach();
  }

  refresh() {
    this.render();
  }

  askCoach() {
    const { locale } = this.ctx;
    this.cancelCoach = this.ctx.coach.review(
      { level: LEVELS[this.run.levelIndex].id, section: this.ctx.dojo.section, results: this.results.res, uiLocale: locale.serverLocale },
      {
        onDone: ({ html, token }) => this.showCoach({ state: "done", html, token }),
        onError: ({ message, retryable }) => this.showCoach({ state: "failed", message, retryable }),
      },
    );
  }

  showCoach(coach) {
    this.coach = coach;
    const box = $(".coach", this.root);
    if (box) box.outerHTML = this.coachHTML();
    this.bindCoach();
  }

  bindCoach() {
    const retry = $("#coachRetry", this.root);
    if (retry) retry.onclick = () => {
      this.showCoach({ state: "writing" });
      this.askCoach();
    };
  }

  coachHTML() {
    const { locale, api } = this.ctx, c = this.coach;
    let body;
    if (c.state === "done")
      body = `<div class="coach-body">${c.html}</div>
        <form class="coach-actions" method="post" action="${esc(api.feedbackPdfUrl)}">
          <input type="hidden" name="token" value="${esc(c.token)}" />
          <button type="submit" class="btn ghost">${locale.t("downloadPdf")}</button>
        </form>`;
    else if (c.state === "failed")
      body = `<div class="sheet-error" role="alert">${esc(locale.t("coachFailed"))}${c.message ? `<br>${esc(c.message)}` : ""}</div>
        ${c.retryable ? `<div class="coach-actions"><button type="button" class="btn ghost" id="coachRetry">${locale.t("retry")}</button></div>` : ""}`;
    else
      body = `<div class="brewing" aria-hidden="true"><span></span><span></span><span></span></div><p class="brewing-note" role="status">${locale.t("coachWriting")}</p>`;
    return `<section class="coach" aria-live="polite">
      <div class="coach-head"><b>${locale.t("coach")}</b><span class="gl">${locale.t("coachGl")}</span></div>${body}</section>`;
  }

  render() {
    const { locale } = this.ctx, R = this.results, L = LEVELS[this.run.levelIndex];
    const perfect = R.correct === R.total;
    const bars = SECTIONS.map((s) => {
      const r = R.res.filter((x) => x.sectionId === s.id), c = r.filter((x) => x.ok).length;
      return `<div class="bar"><span>${locale.t("sect")[s.id]}</span><div class="track"><div class="fill" style="width:${r.length ? (c / r.length) * 100 : 0}%"></div></div><span class="num">${c}/${r.length}</span></div>`;
    }).join("");
    this.root.innerHTML = `
    <div class="sheet enter">
      <div class="sheet-top"><div class="t"><span lang="ja">${L.id} 稽古 · 結果</span></div><div class="meta">${locale.t("mins", R.mins)}</div></div>
      <div class="verdict">
        <div class="big-seal ${perfect ? "pass" : ""}" lang="ja">${perfect ? "皆伝" : "稽古"}</div>
        <div><h2>${locale.t("scoreLine", Math.round(R.score * 100), R.correct, R.total)}</h2><p>${locale.t("practiceCount", this.count)}</p></div>
      </div>
      <div class="bars">${bars}</div>
      ${reviewHTML(R.res, !perfect, locale)}
      ${this.coachHTML()}
      <div class="nav"><button class="btn ghost" id="again">${locale.t("practiceAgain")}</button><button class="btn primary" id="home">${locale.t("backHut")}</button></div>
    </div>`;
    $("#again", this.root).onclick = () => this.ctx.go("quiz", { mode: "practice" });
    $("#home", this.root).onclick = () => this.ctx.go("hut");
    this.bindCoach();
  }
}
