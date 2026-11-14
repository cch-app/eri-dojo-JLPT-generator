/**
 * One keyboard owner at a time: the topmost bound handler (a modal above a
 * view's dialogue) receives keydown events; everything below it waits.
 */
export class KeyScopes {
  constructor(target = document) {
    this.stack = [];
    target.addEventListener("keydown", (e) => {
      const top = this.stack[this.stack.length - 1];
      if (top) top(e);
    }, true);
  }

  bind(handler) {
    this.stack.push(handler);
    return () => {
      const i = this.stack.lastIndexOf(handler);
      if (i >= 0) this.stack.splice(i, 1);
    };
  }
}
