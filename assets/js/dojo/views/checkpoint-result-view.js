import { $, ja } from "../core/dom.js";
import { checkpointResultLines } from "../content/dialogue.js";
import { keeperAt } from "../content/keepers.js";
import { LEVELS } from "../content/levels.js";
import { checkpointCardHTML, keeperFace, keeperWho } from "../ui/checkpoint-card.js";
import { Dialogue } from "../ui/dialogue.js";
import { reviewHTML } from "../ui/review.js";

/** The keeper's verdict: a seal (or 戻, back down), the stamp, and where to go next. */
export class CheckpointResultView {
  constructor(ctx, { results, outcome }) {
    Object.assign(this, { ctx, results, outcome });
    this.keeper = keeperAt(outcome.seg, outcome.k);
  }

  mount(root) {
    this.root = root;
    const K = this.keeper, { progress, locale, keys } = this.ctx;
    this.dialogue = new Dialogue({ who: keeperWho(K), svg: keeperFace(K), locale, keys, compact: true });
    this.render();
    this.dialogue.say(checkpointResultLines(this.outcome, this.results.passed, progress.stampCount), (a) => this.act(a));
  }

  unmount() {
    this.dialogue.destroy();
  }

  refresh() {
    this.render();
  }

  render() {
    const { locale } = this.ctx, R = this.results, { seg, k, arrived } = this.outcome, K = this.keeper;
    const verdict = `
      <div class="cp-verdict ${R.passed ? "pass" : "fail"}">
        <span class="big-seal ${R.passed ? "pass" : ""}" lang="ja">${R.passed ? K.seal : "戻"}</span>
        <div><h2>${locale.t("scoreLine", Math.round(R.score * 100), R.correct, R.total)}</h2>
        ${arrived ? `<p class="promo-line">${ja("昇級")} · ${locale.t("promoted", locale.tx(LEVELS[seg].name))}</p>` : ""}</div>
      </div>
      <div id="cpTalk"></div>${reviewHTML(R.res, !R.passed, locale)}`;
    this.root.innerHTML = checkpointCardHTML({ keeper: K, seg, k, doneK: R.passed ? k + 1 : k, side: verdict, locale });
    this.dialogue.attach($("#cpTalk", this.root));
  }

  act(a) {
    const { ctx } = this;
    if (a === "next") ctx.go("checkpoint");
    else if (a === "retreat") {
      ctx.progress.retreat();
      ctx.go("hut");
    } else ctx.go("hut");
  }
}
