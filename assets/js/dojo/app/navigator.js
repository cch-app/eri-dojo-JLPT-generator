/**
 * Swaps screens inside #app. Every view implements mount(root), unmount() and
 * refresh(); unmounting stops whatever it animated or streamed.
 */
export class Navigator {
  constructor(root, factories) {
    this.root = root;
    this.factories = factories;
    this.current = null;
  }

  go(name, params = {}) {
    const make = this.factories[name];
    if (!make) throw new Error(`Unknown view: ${name}`);
    if (this.current) this.current.unmount();
    this.current = make(params);
    this.current.mount(this.root);
  }

  /** Re-render the current view in the new language. */
  refresh() {
    this.current && this.current.refresh();
  }
}
