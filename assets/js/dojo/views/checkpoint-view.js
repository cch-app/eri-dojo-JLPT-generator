import { $, scrollTop } from "../core/dom.js";
import { checkpointIntroLines } from "../content/dialogue.js";
import { keeperAt } from "../content/keepers.js";
import { checkpointCardHTML, keeperFace, keeperWho } from "../ui/checkpoint-card.js";
import { Dialogue } from "../ui/dialogue.js";

/** Meeting the keeper of the next checkpoint before taking the trial. */
export class CheckpointView {
  constructor(ctx) {
    this.ctx = ctx;
  }

  get keeper() {
    return keeperAt(this.ctx.progress.pos, this.ctx.progress.k);
  }

  mount(root) {
    this.root = root;
    const K = this.keeper;
    this.dialogue = new Dialogue({ who: keeperWho(K), svg: keeperFace(K), locale: this.ctx.locale, keys: this.ctx.keys, compact: true });
    this.render();
    this.dialogue.say(checkpointIntroLines(this.ctx.progress), (a) => this.act(a));
    scrollTop();
  }

  unmount() {
    this.dialogue.destroy();
  }

  refresh() {
    this.render();
  }

  render() {
    const { progress, locale } = this.ctx;
    this.root.innerHTML = checkpointCardHTML({ keeper: this.keeper, seg: progress.pos, k: progress.k, side: `<div id="cpTalk"></div>`, locale });
    this.dialogue.attach($("#cpTalk", this.root));
  }

  act(a) {
    if (a === "begin") this.ctx.go("quiz", { mode: "test" });
    else if (a === "back") {
      this.ctx.progress.retreat();
      this.ctx.go("hut");
    }
  }
}
