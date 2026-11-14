import { $, $$ } from "../core/dom.js";

const MAP_ICON = `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 6.5l6-2.5 6 2.5 6-2.5v13.5l-6 2.5-6-2.5-6 2.5z" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/><path d="M9 4v13.5M15 6.5V20" stroke="currentColor" stroke-width="1.6"/><path d="M5.5 14.5l2.5-3 3 2 3.5-4.5 3 2.5" fill="none" stroke="#b2452f" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>`;

/** Brand seal, the trail-map button and the EN / 繁中 switch. */
export class Topbar {
  constructor({ root, locale, onMap }) {
    Object.assign(this, { root, locale, onMap });
  }

  render() {
    const { locale } = this;
    this.root.innerHTML = `
      <div class="brand"><span class="brand-seal" lang="ja" aria-hidden="true">道</span><span>${locale.t("brand")}</span></div>
      <div class="tb-right">
        <button type="button" class="icon-btn" id="mapBtn" aria-label="${locale.t("mapBtn")}" title="${locale.t("mapBtn")}">${MAP_ICON}</button>
        <div class="lang-switch" role="group" aria-label="${locale.t("language")}">
          <button type="button" data-l="en" lang="en" aria-pressed="${locale.lang === "en"}">EN</button>
          <button type="button" data-l="zh" lang="zh-Hant" aria-pressed="${locale.lang === "zh"}">繁中</button>
        </div>
      </div>`;
    $$(".lang-switch button", this.root).forEach((b) => (b.onclick = () => locale.set(b.dataset.l)));
    $("#mapBtn", this.root).onclick = () => this.onMap();
  }

  focusMapButton() {
    const b = $("#mapBtn", this.root);
    b && b.focus();
  }
}
