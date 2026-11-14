import { openEventStream } from "./event-stream.js";

/** Streams freshly generated questions for one level and category. */
export class QuestionSource {
  constructor(api) {
    this.api = api;
  }

  /**
   * @returns {() => void} cancel
   * Callbacks: onQuestion(question), onDone(), onError({message, retryable})
   */
  stream({ level, section, category, count, uiLocale }, { onQuestion, onDone, onError }) {
    let cancel = () => {};
    let cancelled = false;
    this.api
      .launch({ level, section, category, count, uiLocale })
      .then((token) => {
        if (cancelled) return;
        let received = 0;
        cancel = openEventStream(this.api.questionStreamUrl(token), {
          onMessage: (msg, close) => {
            if (msg.type === "question") {
              received++;
              onQuestion(msg.question);
            } else if (msg.type === "done") {
              close();
              onDone();
            } else if (msg.type === "error") {
              close();
              onError({ message: msg.message || "", retryable: msg.retryable !== false });
            }
          },
          // a dropped connection after some questions arrived still leaves a usable set
          onDrop: () => (received ? onDone() : onError({ message: "", retryable: true })),
        });
      })
      .catch((e) => !cancelled && onError({ message: e.message || "", retryable: true }));
    return () => {
      cancelled = true;
      cancel();
    };
  }
}
