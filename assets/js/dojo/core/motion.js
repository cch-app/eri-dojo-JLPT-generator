/** Honour the OS "reduce motion" setting everywhere (typing, canvases, climbs). */
export const REDUCED = !!(
  window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches
);
