import { REDUCED } from "../core/motion.js";
import { buildGatekeeper } from "../art/portraits.js";

let gatekeeperSvg = null; // built once, reused on every visit to the gate
const gatekeeper = () => (gatekeeperSvg ??= buildGatekeeper());

/** A painted portrait in a dialog box that blinks on its own and moves its mouth while talking. */
export class NpcFace {
  mount(box, svg) {
    this.unmount();
    this.el = box;
    box.innerHTML = svg || gatekeeper();
    this.lids = [...box.querySelectorAll(".lid")];
    this.mouth = box.querySelector(".mouth");
    this.scheduleBlink();
  }

  setLids(v) {
    this.lids.forEach((l) => l.setAttribute("opacity", v));
  }

  scheduleBlink() {
    clearTimeout(this.blinkT);
    if (REDUCED) return;
    this.blinkT = setTimeout(() => {
      if (!this.el || !this.el.isConnected) return;
      this.setLids(1);
      setTimeout(() => {
        this.setLids(0);
        this.scheduleBlink();
      }, 150);
    }, 2400 + Math.random() * 2800);
  }

  talk(on) {
    clearInterval(this.talkT);
    if (!this.el) return;
    const anim = on && !REDUCED;
    this.el.classList.toggle("talking", anim);
    let open = false;
    if (anim)
      this.talkT = setInterval(() => {
        open = !open;
        this.mouth && this.mouth.setAttribute("opacity", open ? 0.85 : 0);
      }, 130);
    else this.mouth && this.mouth.setAttribute("opacity", 0);
  }

  unmount() {
    clearTimeout(this.blinkT);
    clearInterval(this.talkT);
    this.el = null;
  }
}
