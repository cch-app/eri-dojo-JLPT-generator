/* Erin Dojo — composition root: builds the services once and hands them to every view. */
import { $, scrollTop } from "./core/dom.js";
import { safeStorage } from "./core/storage.js";
import { readConfig } from "./app/config.js";
import { Navigator } from "./app/navigator.js";
import { DOJOS } from "./content/dojos.js";
import { Progress } from "./domain/progress.js";
import { Locale } from "./i18n/locale.js";
import { DojoApi } from "./services/api.js";
import { Coach } from "./services/coach.js";
import { QuestionSource } from "./services/question-source.js";
import { RunLoader } from "./services/run-loader.js";
import { KeyScopes } from "./ui/keyboard.js";
import { MapModal } from "./ui/map-modal.js";
import { Topbar } from "./ui/topbar.js";
import { CheckpointResultView } from "./views/checkpoint-result-view.js";
import { CheckpointView } from "./views/checkpoint-view.js";
import { GateView } from "./views/gate-view.js";
import { HutView } from "./views/hut-view.js";
import { PracticeResultView } from "./views/practice-result-view.js";
import { QuizView } from "./views/quiz-view.js";

const config = readConfig();
const locale = new Locale({ storage: safeStorage, serverDefault: config.uiLocale });
const progress = new Progress(safeStorage);
const keys = new KeyScopes();
const api = new DojoApi(config.endpoints);
const source = new QuestionSource(api);
const dojo = DOJOS.read;

const ctx = {
  config,
  locale,
  progress,
  keys,
  api,
  dojo,
  coach: new Coach(api),
  createLoader: () => new RunLoader({ source, locale, dojo }),
  go: (name, params) => nav.go(name, params),
};

const nav = new Navigator($("#app"), {
  gate: () => new GateView(ctx),
  hut: () => new HutView(ctx),
  checkpoint: () => new CheckpointView(ctx),
  quiz: (p) => new QuizView(ctx, p),
  practiceResult: (p) => new PracticeResultView(ctx, p),
  checkpointResult: (p) => new CheckpointResultView(ctx, p),
});

const topbar = new Topbar({ root: $("#topbar"), locale, onMap: openMap });
const mapModal = new MapModal({ progress, locale, keys, onClosed: () => topbar.focusMapButton() });

function openMap() {
  const view = nav.current;
  if (view && view.focusMap) return view.focusMap();
  mapModal.open({
    onGo: view && view.locksNavigation ? null : () => {
      nav.go("hut");
      scrollTop();
    },
  });
}

locale.onChange(() => {
  topbar.render();
  mapModal.refresh();
  nav.refresh();
});

topbar.render();
nav.go("gate");
