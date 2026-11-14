import { $, scrollTop } from "../core/dom.js";
import { REDUCED } from "../core/motion.js";
import { hutLines } from "../content/dialogue.js";
import { HUTS, TOTAL_STAMPS, TRAILS, altAt } from "../content/mountain.js";
import { Dialogue } from "../ui/dialogue.js";
import { locationTitle } from "../ui/map-modal.js";
import { rankLabel } from "../ui/rank.js";
import { stampBookHTML } from "../ui/stamp-book.js";
import { trailMapSVG } from "../ui/trail-map.js";

const GATEKEEPER = { ja: "門番", g: ["Gatekeeper", "守門人"] };

/** The hut you're resting at (or the trail you're on): map, location, what to do next, stamp book. */
export class HutView {
  constructor(ctx) {
    this.ctx = ctx;
    this.confirmReset = false;
    this.dialogue = null;
  }

  mount(root) {
    this.root = root;
    this.render();
  }

  unmount() {
    this.dialogue && this.dialogue.destroy();
  }

  refresh() {
    this.render();
  }

  /** Topbar map button while already on the map: bring the map into view instead of opening the overlay. */
  focusMap() {
    const c = $(".map-card", this.root);
    c.scrollIntoView({ behavior: REDUCED ? "auto" : "smooth", block: "start" });
    c.classList.remove("flash");
    void c.offsetWidth; // restart the animation
    c.classList.add("flash");
  }

  act(a) {
    const { ctx } = this;
    if (a === "practice") ctx.go("quiz", { mode: "practice" });
    else if (a === "setout" || a === "continue") ctx.go("checkpoint");
    else if (a === "retreat") {
      ctx.progress.retreat();
      this.restartTalk();
    }
  }

  restartTalk() {
    this.dialogue && this.dialogue.destroy();
    this.dialogue = null;
    this.render();
  }

  actionsHTML() {
    const { progress: pr, locale, config } = this.ctx;
    if (pr.onTrail)
      return `<button class="act primary" id="aCont">${locale.t("continueTo", pr.k + 1)}</button>
        <button class="act" id="aRetreat">${locale.t("retreat")}<small>${locale.t("retreatSub")}</small></button>`;
    const practice = `<button class="act" id="aPractice">${locale.t("practiceBtn", pr.practiceLevel.id, config.practiceSize)}<small>${locale.t("practiceSub")}</small></button>`;
    return pr.atSummit
      ? `${practice}<p class="summit-note">${locale.t("summitDone")}</p>`
      : `${practice}<button class="act primary" id="aSetOut">${locale.t("setOut", 1)}<small>${locale.t("setOutSub", pr.trailLevel.id)}</small></button>`;
  }

  footHTML() {
    const { locale } = this.ctx;
    const reset = this.confirmReset
      ? `<span class="confirm">${locale.t("eraseQ")} <button class="danger" id="yesReset">${locale.t("erase")}</button><button class="linkish" id="noReset">${locale.t("keep")}</button></span>`
      : `<button class="linkish" id="reset">${locale.t("reset")}</button>`;
    return `<div class="foot"><span>${locale.t("saved")}</span><span>${reset}</span></div>`;
  }

  render() {
    const { progress: pr, locale } = this.ctx;
    const p = pr.pos, r = pr.rank();
    this.root.innerHTML = `
    <button class="linkish backgate" id="toGate">${locale.t("backGate")}</button>
    <section class="trail enter">
      <div class="map-card">${trailMapSVG(pr, locale)}</div>
      <aside class="camp">
        <div class="loc">
          <div class="eyebrow">${pr.onTrail ? locale.t("onTrail") : locale.t("youAreHere")}</div>
          <h1>${locationTitle(pr)}</h1>
          <div class="loc-sub">${pr.onTrail ? locale.tx(TRAILS[p].g) : locale.tx(HUTS[p].g)} · ${locale.t("alt", altAt(pr.node))}</div>
          <div class="loc-row"><span class="mini-belt ${r.unranked ? "unranked" : ""}" style="background:${r.color}"></span><span>${locale.t("rank")}: <b>${rankLabel(r, locale)}</b></span></div>
          <div class="meter" aria-hidden="true"><span style="width:${Math.round((pr.stampCount / TOTAL_STAMPS) * 100)}%"></span></div>
          <div class="loc-prog">${locale.t("progress", pr.clearedCount)}</div>
        </div>
        <div id="mapTalk"></div>
        <div class="actions">${this.actionsHTML()}</div>
        ${stampBookHTML(pr, locale)}
        ${this.footHTML()}
      </aside>
    </section>`;
    this.bindTalk();
    this.bindButtons();
  }

  bindTalk() {
    const talkRoot = $("#mapTalk", this.root);
    if (this.dialogue) return this.dialogue.attach(talkRoot); // same conversation, shown instantly
    const { progress, locale, keys } = this.ctx;
    this.dialogue = new Dialogue({ who: GATEKEEPER, locale, keys, compact: true }).attach(talkRoot);
    this.dialogue.say(hutLines(progress, { arrived: progress.consumeArrival() }), (a) => this.act(a));
  }

  bindButtons() {
    const { ctx } = this;
    const on = (id, fn) => {
      const b = $(`#${id}`, this.root);
      if (b) b.onclick = fn;
    };
    on("toGate", () => {
      ctx.go("gate");
      scrollTop();
    });
    on("aPractice", () => this.act("practice"));
    on("aSetOut", () => this.act("setout"));
    on("aCont", () => this.act("continue"));
    on("aRetreat", () => this.act("retreat"));
    on("reset", () => {
      this.confirmReset = true;
      this.render();
    });
    on("noReset", () => {
      this.confirmReset = false;
      this.render();
    });
    on("yesReset", () => {
      ctx.progress.reset();
      this.confirmReset = false;
      this.restartTalk();
    });
  }
}
