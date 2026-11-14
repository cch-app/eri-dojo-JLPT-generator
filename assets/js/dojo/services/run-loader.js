import { LEVELS, sectionById } from "../content/levels.js";

/**
 * Fills a QuizRun from a QuestionSource, one section after another (the
 * server's workers each hold one stream, so sections are not fetched in
 * parallel). Notifies `onChange` after every question and when finished.
 */
export class RunLoader {
  constructor({ source, locale, dojo }) {
    this.source = source;
    this.locale = locale;
    this.dojo = dojo;
    this.cancelCurrent = null;
    this.error = null; // {message, retryable} once generation has failed
  }

  load(run, onChange) {
    this.cancel();
    this.error = null;
    const level = LEVELS[run.levelIndex].id;
    const queue = run.plan.map((p) => ({ ...p }));
    const nextSection = () => {
      const p = queue.shift();
      if (!p) {
        if (!run.items.length) this.error ??= { message: "", retryable: true }; // every stream ended empty-handed
        run.finishSupply();
        this.cancelCurrent = null;
        onChange();
        return;
      }
      this.cancelCurrent = this.source.stream(
        {
          level,
          section: this.dojo.section,
          category: sectionById(p.sectionId).category,
          count: p.count,
          uiLocale: this.locale.serverLocale,
        },
        {
          onQuestion: (q) => {
            run.supply(p.sectionId, q);
            onChange();
          },
          onDone: () => {
            run.closeSection(p.sectionId);
            nextSection();
          },
          onError: (error) => {
            run.closeSection(p.sectionId);
            // No questions at all, or a failure that every later section would hit too
            // (no credits, bad key): stop here instead of spending more requests.
            if (!run.items.length || !error.retryable) {
              if (!run.items.length) this.error = error;
              queue.splice(0).forEach((rest) => run.closeSection(rest.sectionId));
            }
            nextSection();
          },
        },
      );
    };
    nextSection();
  }

  cancel() {
    if (this.cancelCurrent) this.cancelCurrent();
    this.cancelCurrent = null;
  }
}
