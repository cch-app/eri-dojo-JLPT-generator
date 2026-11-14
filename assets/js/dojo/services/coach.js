import { openEventStream } from "./event-stream.js";

/** Asks the AI coach to read a finished run and write feedback (Markdown rendered to safe HTML server-side). */
export class Coach {
  constructor(api) {
    this.api = api;
  }

  /**
   * Callbacks: onDone({html, token}) where token signs the run *with* its
   * feedback (for the PDF download), onError({message, retryable}). Returns cancel().
   */
  review({ level, section, results, uiLocale }, { onDone, onError }) {
    let cancel = () => {};
    let cancelled = false;
    this.api
      .session({
        level,
        section,
        uiLocale,
        questions: results.map((r) => r.question),
        answers: results.map((r) => r.pick),
      })
      .then((token) => {
        if (cancelled) return;
        cancel = openEventStream(this.api.analysisStreamUrl(token), {
          onMessage: (msg, close) => {
            if (msg.type === "done") {
              close();
              onDone({ html: msg.analysis_html || "", token: msg.token });
            } else if (msg.type === "error") {
              close();
              onError({ message: msg.message || "", retryable: msg.retryable !== false });
            }
          },
          onDrop: () => onError({ message: "", retryable: true }),
        });
      })
      .catch((e) => !cancelled && onError({ message: e.message || "", retryable: true }));
    return () => {
      cancelled = true;
      cancel();
    };
  }
}
