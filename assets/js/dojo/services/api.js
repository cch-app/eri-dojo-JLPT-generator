/** HTTP boundary to the Flask app: signed tokens in, SSE stream URLs out. */
export class DojoApi {
  constructor(endpoints, fetchImpl = window.fetch.bind(window)) {
    this.endpoints = endpoints;
    this.fetch = fetchImpl;
  }

  async postJson(url, body) {
    const res = await this.fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json().catch(() => ({ ok: false, error: `HTTP ${res.status}` }));
    if (!res.ok || !data.ok) throw new Error(data.error || `HTTP ${res.status}`);
    return data;
  }

  /** Authorize one generation stream. */
  async launch({ level, section, category, count, uiLocale }) {
    const data = await this.postJson(this.endpoints.launch, {
      level, section, category, num_questions: count, ui_locale: uiLocale,
    });
    return data.token;
  }

  /** Sign a finished run so the coach can analyze it. */
  async session({ level, section, questions, answers, uiLocale }) {
    const data = await this.postJson(this.endpoints.session, {
      level, section, questions, answers, ui_locale: uiLocale,
    });
    return data.token;
  }

  questionStreamUrl(token) {
    return `${this.endpoints.questions}?token=${encodeURIComponent(token)}`;
  }

  analysisStreamUrl(token) {
    return `${this.endpoints.analysis}?token=${encodeURIComponent(token)}`;
  }

  get feedbackPdfUrl() {
    return this.endpoints.feedbackPdf;
  }
}
