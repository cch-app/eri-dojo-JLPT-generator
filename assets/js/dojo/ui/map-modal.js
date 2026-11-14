import { $, ja } from "../core/dom.js";
import { HUTS, TOTAL_STAMPS, TRAILS, altAt } from "../content/mountain.js";
import { rankLabel } from "./rank.js";
import { trailMapSVG } from "./trail-map.js";

/** Where-am-I header shared by the map overlay and the hut view. */
export function locationTitle(progress) {
  const p = progress.pos;
  return progress.onTrail ? `${ja(TRAILS[p].ja)} · ${ja(`第${progress.k}関`)}` : ja(HUTS[p].ja);
}

/** Trail-map overlay, reachable from every screen. "Go to the trail" is offered unless a test is in progress. */
export class MapModal {
  constructor({ progress, locale, keys, onClosed }) {
    Object.assign(this, { progress, locale, keys, onClosed });
    this.el = null;
  }

  get isOpen() {
    return !!this.el;
  }

  /** @param {{onGo: (() => void) | null}} o pass onGo=null while leaving is not allowed */
  open({ onGo }) {
    this.close(true);
    this.onGo = onGo;
    const { progress: pr, locale } = this;
    const m = document.createElement("div");
    m.className = "map-modal";
    m.setAttribute("role", "dialog");
    m.setAttribute("aria-modal", "true");
    m.setAttribute("aria-label", locale.t("mapTitle"));
    m.innerHTML = `<div class="mm-card">
        <div class="mm-head"><div><div class="eyebrow">${pr.onTrail ? locale.t("onTrail") : locale.t("youAreHere")}</div>
          <b>${locationTitle(pr)}</b>
          <span>${locale.t("alt", altAt(pr.node))} · ${rankLabel(pr.rank(), locale)} · ${ja("登山印")} ${pr.stampCount}/${TOTAL_STAMPS}</span></div>
          <button class="icon-btn" id="mmClose" aria-label="${locale.t("close")}">✕</button></div>
        <div class="mm-map">${trailMapSVG(pr, locale)}</div>
        <div class="mm-actions">${onGo ? `<button class="btn shu" id="mmGo">${locale.t("goTrail")}</button>` : `<span class="mm-note">${locale.t("finishFirst")}</span>`}<button class="btn ghost-l" id="mmClose2">${locale.t("close")}</button></div>
      </div>`;
    document.body.appendChild(m);
    this.el = m;
    m.onclick = (e) => e.target === m && this.close();
    $("#mmClose", m).onclick = $("#mmClose2", m).onclick = () => this.close();
    const go = $("#mmGo", m);
    if (go) go.onclick = () => {
      this.close(true);
      onGo();
    };
    this.unbindKeys = this.keys.bind((e) => {
      if (e.key === "Escape") {
        e.preventDefault();
        this.close();
      }
    });
    $("#mmClose", m).focus();
  }

  /** Re-render in place (language switch) keeping the same offer. */
  refresh() {
    if (this.el) this.open({ onGo: this.onGo });
  }

  close(silent) {
    if (!this.el) return;
    this.el.remove();
    this.el = null;
    this.unbindKeys && this.unbindKeys();
    if (!silent) this.onClosed && this.onClosed();
  }
}
