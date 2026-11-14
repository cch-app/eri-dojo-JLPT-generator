import { LEVELS } from "../content/levels.js";
import { CHECKPOINTS_PER_TRAIL, SUMMIT } from "../content/mountain.js";

const KEY = "erin-dojo-v2";

const fresh = () => ({ pos: 0, k: 0, stamps: {}, practice: {}, seenIntro: false });
const stampKey = (seg, k) => `${seg}-${k}`;

/**
 * The challenger's climb, persisted in the browser.
 *
 * pos = hut index (0 trailhead … 5 summit); k = checkpoints cleared on the trail
 * ahead of that hut (0 = resting at the hut). Clearing all three of a trail's
 * checkpoints moves you up to the next hut; failing one sends you back down.
 */
export class Progress {
  constructor(storage) {
    this.storage = storage;
    this.state = this.load();
    this.arrivalPending = false; // set when a climb just reached a new hut (shown once)
  }

  load() {
    try {
      const s = JSON.parse(this.storage.get(KEY));
      if (s && typeof s.pos === "number") return { ...fresh(), ...s };
    } catch (e) {
      // corrupted save: start over
    }
    return fresh();
  }

  save() {
    this.storage.set(KEY, JSON.stringify(this.state));
  }

  get pos() {
    return this.state.pos;
  }

  get k() {
    return this.state.k;
  }

  get onTrail() {
    return this.state.k > 0;
  }

  get atSummit() {
    return this.state.pos === SUMMIT;
  }

  /** Map node you're standing on. */
  get node() {
    return this.state.pos * 4 + this.state.k;
  }

  get stampCount() {
    return Object.keys(this.state.stamps).length;
  }

  get clearedCount() {
    return Math.min(15, this.state.pos * CHECKPOINTS_PER_TRAIL + this.state.k);
  }

  hasStamp(seg, k) {
    return !!this.state.stamps[stampKey(seg, k)];
  }

  get isReturning() {
    return this.state.pos > 0 || this.state.k > 0 || this.stampCount > 0;
  }

  /** At a hut you practice the level of the trail ahead (N1 once at the summit). */
  get practiceLevel() {
    return LEVELS[Math.min(this.state.pos, LEVELS.length - 1)];
  }

  /** The level tested on the trail ahead. */
  get trailLevel() {
    return LEVELS[this.state.pos];
  }

  practiceCount(levelId) {
    return (this.state.practice[levelId] || { count: 0 }).count;
  }

  rank() {
    const pos = this.state.pos;
    if (pos === 0) return { ja: "入門", g: ["Beginner", "入門"], color: "transparent", unranked: true };
    if (pos === SUMMIT) return { ja: "師範", g: ["Master · Black belt", "師範・黑帶"], color: LEVELS[4].color };
    const l = LEVELS[pos - 1];
    return { ja: l.belt, g: l.name, color: l.color };
  }

  get seenIntro() {
    return this.state.seenIntro;
  }

  markIntroSeen() {
    this.state.seenIntro = true;
    this.save();
  }

  /** Read and clear the "you just arrived at a new hut" flag. */
  consumeArrival() {
    const v = this.arrivalPending;
    this.arrivalPending = false;
    return v;
  }

  recordPractice(levelId, score) {
    const pr = this.state.practice[levelId] || { best: 0, count: 0 };
    pr.count++;
    pr.best = Math.max(pr.best, score);
    this.state.practice[levelId] = pr;
    this.save();
    return pr.count;
  }

  /** Apply a checkpoint result; returns what changed. */
  recordCheckpoint(passed) {
    const seg = this.state.pos, k = this.state.k;
    let arrived = false, newStamp = false;
    if (passed) {
      newStamp = !this.hasStamp(seg, k);
      this.state.stamps[stampKey(seg, k)] = true;
      this.state.k++;
      if (this.state.k === CHECKPOINTS_PER_TRAIL) {
        this.state.pos++;
        this.state.k = 0;
        arrived = true;
        this.arrivalPending = true;
      }
    } else {
      this.state.k = 0; // back down to the hut this trail started from
    }
    this.save();
    return { seg, k, arrived, newStamp };
  }

  retreat() {
    if (this.state.k === 0) return;
    this.state.k = 0;
    this.save();
  }

  reset() {
    this.state = fresh();
    this.arrivalPending = false;
    this.save();
  }
}
