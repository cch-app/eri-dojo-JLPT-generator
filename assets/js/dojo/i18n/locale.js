import { STRINGS } from "./strings.js";

export const LANGS = ["en", "zh"];
const STORAGE_KEY = "erin-lang";
const COOKIE = "ui_locale";
// the server's locale codes (explanations, analysis and PDF are written in these)
const SERVER_LOCALE = { en: "en", zh: "zh_TW" };

function fromServerLocale(code) {
  return code === "zh_TW" ? "zh" : code === "en" ? "en" : null;
}

/**
 * The chosen interface language. Persists to localStorage and to the
 * `ui_locale` cookie so the server renders the page in the same language.
 */
export class Locale {
  constructor({ storage, serverDefault }) {
    this.storage = storage;
    this.listeners = new Set();
    this.lang = this.initial(serverDefault);
    this.applyToDocument();
  }

  initial(serverDefault) {
    const saved = this.storage.get(STORAGE_KEY);
    if (LANGS.includes(saved)) return saved;
    const fromServer = fromServerLocale(serverDefault);
    if (fromServer) return fromServer;
    const ls = (navigator.languages || [navigator.language || ""]).join(",").toLowerCase();
    return /(^|,)zh/.test(ls) ? "zh" : "en";
  }

  get serverLocale() {
    return SERVER_LOCALE[this.lang];
  }

  /** t("key", ...args): strings may be plain or functions of arguments. */
  t(key, ...args) {
    const v = STRINGS[this.lang][key];
    return typeof v === "function" ? v(...args) : v;
  }

  /** Pick the current language from an [en, zh] pair. */
  tx(pair) {
    return pair[this.lang === "zh" ? 1 : 0];
  }

  set(lang) {
    if (lang === this.lang || !LANGS.includes(lang)) return;
    this.lang = lang;
    this.storage.set(STORAGE_KEY, lang);
    document.cookie = `${COOKIE}=${SERVER_LOCALE[lang]}; Max-Age=${60 * 60 * 24 * 30}; Path=/; SameSite=Lax`;
    this.applyToDocument();
    this.listeners.forEach((fn) => fn(lang));
  }

  onChange(fn) {
    this.listeners.add(fn);
    return () => this.listeners.delete(fn);
  }

  applyToDocument() {
    document.documentElement.lang = this.lang === "zh" ? "zh-Hant" : "en";
  }
}
