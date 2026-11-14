import { $ } from "../core/dom.js";
import { Climb } from "../art/climb.js";
import { crossLand } from "../art/crossroads.js";
import { crossCfg, doorCfg } from "../art/scene-configs.js";
import { Sky } from "../art/sky.js";
import {
  GATE_CHOICES,
  backToCrossLine,
  climbLine,
  crossLines,
  doorLines,
  enterLine,
  knockLines,
  pickPathLine,
} from "../content/dialogue.js";
import { DOJOS, dojoForSide } from "../content/dojos.js";
import { Dialogue } from "../ui/dialogue.js";

const GATEKEEPER = { ja: "門番", g: ["Gatekeeper", "守門人"] };

function signHTML() {
  return `<div class="signpost">
    <div class="sp-post"></div><div class="sp-cap"></div><div class="sp-rope"></div>
    <button class="sp-board left" id="sp-left"><span class="plank"><span class="sp-ja" lang="ja">${DOJOS.read.ja}</span><span class="sp-gl" id="sp-left-gl"></span></span></button>
    <button class="sp-board right" id="sp-right"><span class="plank"><span class="sp-ja" lang="ja">${DOJOS.listen.ja}</span><span class="sp-gl" id="sp-right-gl"></span></span></button>
  </div>`;
}

function doorHTML(dojo) {
  return `<button class="dojo-door ${dojo.open ? "" : "locked"}" id="door">
    <div class="building">
      <div class="roof" aria-hidden="true"></div>
      <div class="frame" lang="ja">
        <div class="sign">${dojo.ja}</div>
        <div class="leaves"><span class="leaf l"></span><span class="leaf r"></span><div class="noren">${dojo.kanji}</div></div>
        ${dojo.open ? "" : `<span class="tag">修繕中</span>`}
      </div>
      <div class="torii" aria-hidden="true" lang="ja">
        <span class="pillar"></span><span class="pillar r"></span>
        <span class="nuki"></span><span class="shimaki"></span><span class="kasagi"></span>
        <span class="gaku">${dojo.ja.slice(0, 2)}</span>
      </div>
    </div>
  </button>`;
}

/**
 * RPG entrance: the gatekeeper at the crossroads, a first-person climb up the
 * stone steps, and the dojo door. Entering the open dojo leads to the hut.
 */
export class GateView {
  constructor(ctx) {
    this.ctx = ctx;
    this.stage = "cross";
    this.dojo = null;
  }

  mount(root) {
    this.root = root;
    root.innerHTML = `
    <div class="gate enter">
      <div class="gate-title" id="gateTitle"></div>
      <div class="scene" id="scene"></div>
      <div id="gateTalk"></div>
    </div>`;
    this.scene = $("#scene", root);
    this.dialogue = new Dialogue({
      who: GATEKEEPER,
      locale: this.ctx.locale,
      keys: this.ctx.keys,
      typeMs: 32,
      extraKeys: (e, d) => {
        if (this.stage === "cross" && d.choosing && (e.key === "ArrowLeft" || e.key === "ArrowRight")) {
          e.preventDefault();
          this.choose(e.key === "ArrowLeft" ? "left" : "right");
          return true;
        }
        return false;
      },
    }).attach($("#gateTalk", root));
    this.showCross(false);
  }

  unmount() {
    Sky.stop();
    Climb.stop();
    this.dialogue.destroy();
  }

  refresh() {
    this.labels();
    this.dialogue.refresh();
  }

  say(lines) {
    this.dialogue.say(lines, (act) => this.choose(act));
  }

  showCross(arrive) {
    this.stage = "cross";
    this.dojo = null;
    this.dialogue.setBusy(false);
    const sc = this.scene;
    sc.classList.toggle("arrive", !!arrive);
    sc.innerHTML = `<canvas class="sky"></canvas>${crossLand()}${signHTML()}<canvas class="mist"></canvas>`;
    $("#sp-left", sc).onclick = (e) => {
      e.stopPropagation();
      this.choose("left");
    };
    $("#sp-right", sc).onclick = (e) => {
      e.stopPropagation();
      this.choose("right");
    };
    this.labels();
    Sky.mount(sc, crossCfg);
    this.say(crossLines(this.ctx.progress));
  }

  showDoor(dojo) {
    this.stage = "door";
    this.dojo = dojo;
    this.dialogue.setBusy(false);
    const sc = this.scene;
    sc.classList.add("arrive");
    sc.innerHTML = `<canvas class="sky"></canvas><canvas class="ground"></canvas><canvas class="willow"></canvas><div class="stage">${doorHTML(dojo)}</div><canvas class="bamboo"></canvas><canvas class="mist"></canvas>`;
    $("#door", sc).onclick = (e) => {
      e.stopPropagation();
      this.choose(dojo.open ? "enter" : "knock");
    };
    this.labels();
    Sky.mount(sc, doorCfg);
    this.say(doorLines(dojo));
  }

  climb(dojo, dir) {
    this.dialogue.setBusy(true);
    Sky.stop();
    const sc = this.scene;
    sc.classList.remove("arrive");
    sc.innerHTML = `<canvas class="climb"></canvas>`;
    this.say([climbLine(dir)]);
    Climb.run($(".climb", sc), dir, () => (dir > 0 ? this.showDoor(dojo) : this.showCross(true)));
  }

  choose(act) {
    if (this.dialogue.busy) return;
    if ((act === "left" || act === "right") && this.stage === "cross") {
      const dojo = dojoForSide(act);
      this.dialogue.setBusy(true);
      $(act === "left" ? "#sp-left" : "#sp-right", this.scene).classList.add("picked");
      this.say([pickPathLine(act, () => this.climb(dojo, 1))]);
    } else if (act === "repeat") {
      this.say(crossLines(this.ctx.progress));
    } else if (act === "enter" && this.stage === "door") {
      this.dialogue.setBusy(true);
      $("#door", this.scene).classList.add("open");
      this.say([enterLine(this.ctx.progress, () => this.ctx.go("hut"))]);
    } else if (act === "knock" && this.stage === "door") {
      const d = $("#door", this.scene);
      d.classList.remove("shake");
      void d.offsetWidth; // restart the animation
      d.classList.add("shake");
      this.say(knockLines());
    } else if (act === "back" && this.stage === "door") {
      const dojo = this.dojo;
      this.dialogue.setBusy(true);
      this.say([backToCrossLine(() => this.climb(dojo, -1))]);
    }
  }

  labels() {
    const { locale } = this.ctx;
    const title = $("#gateTitle", this.root);
    if (this.stage === "door" && this.dojo) {
      const dojo = this.dojo;
      title.innerHTML = `<span lang="ja">${dojo.ja}</span> · ${locale.t(dojo.labelKey)}`;
      const d = $("#door", this.scene);
      if (d) d.setAttribute("aria-label", dojo.open ? locale.tx(GATE_CHOICES.read[0].g) : `${locale.t(dojo.labelKey)} · ${locale.t("underRepair")}`);
    } else if (this.stage === "cross") {
      title.innerHTML = `<span lang="ja">言の葉の里</span> · ${locale.t("village")} · ${locale.t("crossroads")}`;
      const l = $("#sp-left-gl", this.scene), r = $("#sp-right-gl", this.scene);
      if (l) {
        l.textContent = `← ${locale.t("reading")}`;
        r.textContent = `${locale.t("listening")} →`;
        $("#sp-left", this.scene).setAttribute("aria-label", locale.tx(GATE_CHOICES.cross[0].g));
        $("#sp-right", this.scene).setAttribute("aria-label", locale.tx(GATE_CHOICES.cross[1].g));
      }
    }
  }
}
