import { $, $$, esc } from "../core/dom.js";
import { REDUCED } from "../core/motion.js";
import { NpcFace } from "./npc.js";

/**
 * RPG dialog box: a talking portrait types out Japanese lines, shows the
 * gloss in the interface language, and offers choices (mouse or arrows+Enter).
 *
 * Lines are produced by content/dialogue.js; when a choice is picked the
 * dialogue calls `onAct(act)`. The owning view decides what that means.
 */
export class Dialogue {
  /**
   * @param {object} o
   * @param {{ja: string, g: string[]}} o.who speaker name
   * @param {string} [o.svg] portrait markup (defaults to the gatekeeper)
   * @param {import("../i18n/locale.js").Locale} o.locale
   * @param {import("./keyboard.js").KeyScopes} o.keys
   * @param {boolean} [o.compact] smaller box used beside maps and portraits
   * @param {number} [o.typeMs] typing speed per character
   * @param {(e: KeyboardEvent, d: Dialogue) => boolean} [o.extraKeys] return true if handled
   */
  constructor({ who, svg, locale, keys, compact = false, typeMs = 30, extraKeys = null }) {
    Object.assign(this, { who, svg, locale, keys, compact, typeMs, extraKeys });
    this.face = new NpcFace();
    this.lines = [];
    this.i = 0;
    this.choiceIdx = 0;
    this.typing = false;
    this.busy = false;
    this.onAct = () => {};
    this.unbindKeys = keys.bind((e) => this.onKey(e));
  }

  get line() {
    return this.lines[this.i];
  }

  get choosing() {
    return !!(this.line && this.line.choice && !this.typing && !this.busy);
  }

  /** Render into `root`; with lines already loaded, show the current one instantly (language switch, re-render). */
  attach(root) {
    clearInterval(this.timer);
    this.typing = false;
    this.root = root;
    root.innerHTML = `<div class="dialog${this.compact ? " talk" : ""}" aria-live="polite">
      <div class="portrait"><div class="face" aria-hidden="true"></div><div class="who"><span lang="ja">${esc(this.who.ja)}</span> <br><span class="whoGl"></span></div></div>
      <div class="say"><div class="ja" lang="ja"></div><div class="gloss"></div><div class="choices"></div></div>
      <span class="more" aria-hidden="true" hidden>▼</span></div>`;
    this.el = (q) => $(q, root);
    this.el(".dialog").onclick = () => this.advance();
    this.face.mount(this.el(".face"), this.svg);
    this.el(".whoGl").textContent = this.locale.tx(this.who.g);
    if (this.line) this.showDone(this.line);
    return this;
  }

  say(lines, onAct) {
    clearInterval(this.timer);
    this.typing = false;
    this.face.talk(false);
    this.lines = lines;
    this.i = 0;
    this.choiceIdx = 0;
    if (onAct) this.onAct = onAct;
    this.showLine();
  }

  /** While busy (walking, doors opening) clicks and keys are ignored. */
  setBusy(on) {
    this.busy = on;
  }

  showLine() {
    const L = this.line;
    this.el(".gloss").textContent = "";
    this.el(".choices").innerHTML = "";
    this.el(".more").hidden = true;
    clearInterval(this.timer);
    this.finishTyping = () => {
      clearInterval(this.timer);
      this.typing = false;
      this.face.talk(false);
      this.showDone(L);
      if (L.auto) setTimeout(() => {
        if (this.line === L && L.then && this.root && this.root.isConnected) L.then();
      }, L.auto);
    };
    if (REDUCED) return this.finishTyping();
    this.typing = true;
    if (!L.silent) this.face.talk(true);
    let n = 0;
    const out = this.el(".ja");
    out.textContent = "";
    this.timer = setInterval(() => {
      if (!this.root.isConnected) return clearInterval(this.timer);
      out.textContent = L.ja.slice(0, ++n);
      if (n >= L.ja.length) this.finishTyping();
    }, this.typeMs);
  }

  showDone(L) {
    this.el(".ja").textContent = L.ja;
    this.el(".gloss").textContent = this.locale.tx(L.g);
    if (L.choice) this.renderChoices();
    else this.el(".more").hidden = !!L.then || this.i >= this.lines.length - 1;
  }

  renderChoices() {
    const box = this.el(".choices");
    box.innerHTML = this.line.choice
      .map((c, i) => `<button class="choice ${i === this.choiceIdx ? "on" : ""}" data-i="${i}"><span lang="ja">${esc(c.ja)}</span><span class="note">${esc(this.locale.tx(c.g))}</span></button>`)
      .join("");
    $$(".choice", box).forEach((b) => {
      b.onmouseenter = b.onfocus = () => this.setChoice(+b.dataset.i);
      b.onclick = (e) => {
        e.stopPropagation();
        this.pick(+b.dataset.i);
      };
    });
  }

  setChoice(i) {
    this.choiceIdx = i;
    $$(".choice", this.root).forEach((b, k) => b.classList.toggle("on", k === i));
  }

  pick(i) {
    if (this.busy || !this.line || !this.line.choice) return;
    this.onAct(this.line.choice[i].act);
  }

  advance() {
    if (this.typing) return this.finishTyping();
    const L = this.line;
    if (!L || this.busy || L.choice) return;
    if (L.then) return L.then();
    if (this.i < this.lines.length - 1) {
      this.i++;
      this.showLine();
    }
  }

  onKey(e) {
    if (!this.root || !this.root.isConnected) return;
    if (this.extraKeys && this.extraKeys(e, this)) return;
    const onBtn = e.target.closest && e.target.closest("button");
    if (this.choosing && (e.key === "ArrowDown" || e.key === "ArrowUp")) {
      e.preventDefault();
      const n = this.line.choice.length;
      this.setChoice((this.choiceIdx + (e.key === "ArrowDown" ? 1 : n - 1)) % n);
      return;
    }
    if ((e.key === "Enter" || e.key === " ") && !onBtn) {
      e.preventDefault();
      if (this.choosing) this.pick(this.choiceIdx);
      else this.advance();
    }
  }

  /** Language switched: re-gloss in place without retyping. */
  refresh() {
    if (!this.root) return;
    this.el(".whoGl").textContent = this.locale.tx(this.who.g);
    if (this.line && !this.typing) {
      this.el(".gloss").textContent = this.locale.tx(this.line.g);
      if (this.line.choice) this.renderChoices();
    }
  }

  destroy() {
    clearInterval(this.timer);
    this.face.unmount();
    this.unbindKeys();
    this.root = null;
  }
}
