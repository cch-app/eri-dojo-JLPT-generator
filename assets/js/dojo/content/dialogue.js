import { STRINGS } from "../i18n/strings.js";
import { LEVELS, SECTIONS } from "./levels.js";
import { HUTS, SUMMIT, TOTAL_STAMPS, TRAILS } from "./mountain.js";
import { keeperAt } from "./keepers.js";

/*
 * Everything the NPCs say. A line is {ja, g:[en, zh]} plus optional flags:
 *   choice: [{act, ja, g:[en, zh]}]  options shown under the line
 *   then:   () => void               runs when the line is advanced
 *   auto:   ms                       runs `then` by itself after a pause
 *   silent: true                     narration: the speaker's mouth stays shut
 * Builders are pure functions of the progress they are given.
 */
export const line = (ja, en, zh, extra = {}) => ({ ja, g: [en, zh], ...extra });
const opt = (act, ja, en, zh) => ({ act, ja, g: [en, zh] });
const both = (key, ...args) => [STRINGS.en[key](...args), STRINGS.zh[key](...args)];

const PROVERBS = [
  line("千里の道も一歩から。", "A journey of a thousand miles begins with a single step.", "千里之行，始於足下。"),
  line("継続は力なり。", "Persistence is power.", "持之以恆就是力量。"),
  line("七転び八起き。", "Fall seven times, rise eight.", "跌倒七次，第八次站起來。"),
  line("急がば回れ。", "When in a hurry, take the long way round.", "欲速則不達。"),
  line("塵も積もれば山となる。", "Even dust, piled up, becomes a mountain.", "積沙成塔。"),
  line("石の上にも三年。", "Sit on a stone for three years and even it grows warm.", "有志者，事竟成。"),
];

/* ---------- gate: crossroads and dojo doors ---------- */

export const GATE_CHOICES = {
  cross: [
    opt("left", "左の道を行く", "Take the left path · Reading Dojo", "走左邊的路・讀解道場"),
    opt("right", "右の道を行く", "Take the right path · Listening Dojo", "走右邊的路・聽解道場"),
    opt("repeat", "もう一度話を聞く", "Hear the gatekeeper again", "再聽一次守門人的話"),
  ],
  read: [
    opt("enter", "門をくぐる", "Pass through the gate", "穿過大門"),
    opt("back", "分かれ道に戻る", "Return to the crossroads", "回到岔路口"),
  ],
  listen: [
    opt("knock", "門を叩く", "Knock on the gate", "敲敲大門"),
    opt("back", "分かれ道に戻る", "Return to the crossroads", "回到岔路口"),
  ],
};

export function crossLines(progress) {
  const ask = line("さて、どちらの道を行く？", "Now, which path will you take?", "那麼，你要走哪一條路？", { choice: GATE_CHOICES.cross });
  if (progress.isReturning) {
    const r = progress.rank();
    return [
      line(`おお、戻ったか。${r.ja}の挑戦者よ。`, `Ah, you have returned, ${r.g[0].toLowerCase()} challenger.`, `喔，你回來了，${r.g[1]}的挑戰者。`),
      line("今日も修行に励むがよい。", "Train hard again today.", "今天也要努力修行。"),
      ask,
    ];
  }
  return [
    line("よく来たな、挑戦者よ。ここは言の葉の里の分かれ道。", "Welcome, challenger. You stand at the crossroads of the Village of Words.", "歡迎你，挑戰者。這裡是言葉之鄉的岔路口。"),
    line("わしはこの山の門番。日本語の道を志す者を案内しておる。", "I am the gatekeeper of this mountain. I guide those who seek the way of Japanese.", "我是這座山的守門人，負責引導立志學習日語的人。"),
    line("道標を見よ。左の道は読解道場、右の道は聴解道場へと続く。", "Look at the signpost. The left path climbs to the Reading Dojo, the right path to the Listening Dojo.", "看看路標。左邊的路通往讀解道場，右邊的路通往聽解道場。"),
    line("誰もが白帯から始まる。N5を越えねば、次の帯は締められぬ。", "Everyone begins with the white belt. Pass N5 before you can tie on the next.", "每個人都從白帶開始。不通過 N5，就無法繫上下一條腰帶。"),
    ask,
  ];
}

export function doorLines(dojo) {
  if (dojo.open)
    return [
      line(`着いたな。ここが${dojo.ja}だ。`, `Here we are. This is the ${dojo.g[0]}.`, `到了。這裡就是${dojo.g[1]}。`),
      line("門をくぐるか？", "Will you pass through the gate?", "要穿過這道門嗎？", { choice: GATE_CHOICES.read }),
    ];
  return [
    line(`ここが${dojo.ja}……だが、門は閉ざされておる。`, `This is the ${dojo.g[0]}… but its gate is shut.`, `這裡是${dojo.g[1]}……但大門緊閉著。`),
    line("まだ修繕中なのだ。まずは読解道場で腕を磨くがよい。", "It is still under repair. Sharpen your skills in the Reading Dojo first.", "這裡還在修繕中。先到讀解道場磨練實力吧。"),
    line("どうする？", "What will you do?", "你打算怎麼做？", { choice: GATE_CHOICES.listen }),
  ];
}

export function pickPathLine(side, then) {
  return side === "left"
    ? line("よかろう。左の石段を登るがよい。", "Very well. Climb the steps on the left.", "很好。登上左邊的石階吧。", { then, auto: 1500 })
    : line("よかろう。右の石段を登るがよい。", "Very well. Climb the steps on the right.", "很好。登上右邊的石階吧。", { then, auto: 1500 });
}

export function climbLine(dir) {
  return dir > 0
    ? line("（石段を登っている……）", "(Climbing the stone steps…)", "（正在攀登石階……）", { silent: true })
    : line("（石段を下りている……）", "(Walking back down the steps…)", "（正在走下石階……）", { silent: true });
}

export function enterLine(progress, then) {
  return progress.isReturning
    ? line("よかろう。門を開けよう。", "Very well. I shall open the gate.", "很好，我這就為你開門。", { then, auto: 2200 })
    : line("よかろう。白帯を締め、N5の試練から始めるがよい。", "Very well. Tie on the white belt and begin with the N5 trial.", "很好。繫上白帶，從 N5 的試煉開始吧。", { then, auto: 2200 });
}

export function knockLines() {
  return [
    line("……返事はない。", "…No answer.", "……沒有回應。"),
    line("言ったであろう、修繕中だと。", "As I said, it is under repair.", "我說過了，這裡還在修繕中。"),
    line("どうする？", "What will you do?", "你打算怎麼做？", { choice: GATE_CHOICES.listen }),
  ];
}

export function backToCrossLine(then) {
  return line("では、分かれ道へ戻ろう。", "Then let us return to the crossroads.", "那麼，我們回到岔路口吧。", { then, auto: 1400 });
}

/* ---------- huts ---------- */

const retreatOpt = () =>
  opt("retreat", "小屋へ戻る", `${STRINGS.en.retreat} · ${STRINGS.en.retreatSub}`, `${STRINGS.zh.retreat}・${STRINGS.zh.retreatSub}`);

/** What the gatekeeper says at the hut (or mid-trail), ending in a choice of what to do next. */
export function hutLines(progress, { arrived }) {
  const p = progress.pos, k = progress.k, L = progress.practiceLevel, hut = HUTS[p];
  if (k > 0) {
    const [en, zh] = both("continueTo", k + 1);
    return [
      line(`ここは${TRAILS[p].ja}の途中、第${k}関を越えたところだ。`, `You're on the ${TRAILS[p].g[0]}, just past checkpoint ${k}.`, `你正走在${TRAILS[p].g[1]}上，剛通過第 ${k} 關。`),
      line("進むか、引き返すか。決めるのはお前だ。", "Press on or turn back. The choice is yours.", "要前進還是撤退，由你決定。", {
        choice: [opt("continue", "先へ進む", en, zh), retreatOpt()],
      }),
    ];
  }
  const ask = p < SUMMIT
    ? line("稽古するか、先へ進むか？", "Will you practice, or move on?", "要練習，還是繼續前進？", {
        choice: [
          opt("practice", "稽古する", `Practice ${L.id} · no penalty`, `練習 ${L.id}・沒有懲罰`),
          opt("setout", "先へ進む", `Set out for checkpoint 1 · ${TRAILS[p].g[0]}`, `出發前往第 1 關・${TRAILS[p].g[1]}`),
        ],
      })
    : line("頂で、好きなだけ稽古するがよい。", "Practice here at the summit as long as you like.", "在山頂盡情練習吧。", {
        choice: [opt("practice", "稽古する", "Practice N1", "練習 N1")],
      });

  if (arrived) {
    if (p === SUMMIT)
      return [
        line("頂上だ！言の葉山を制した者として、師範の名を授ける。", "The summit! As one who has conquered Mount Kotonoha, you are named Master.", "登頂了！作為征服言葉山的人，授予你「師範」之名。"),
        line(`標高${hut.alt}メートル。ここから見える景色は、お前だけのものだ。`, `Altitude ${hut.alt} m. The view from here belongs to you alone.`, `海拔 ${hut.alt} 公尺。這裡的景色只屬於你。`),
        ask,
      ];
    const b = LEVELS[p - 1];
    return [
      line(`${hut.ja}に到着した！標高${hut.alt}メートル。`, `You reached the ${hut.g[0]}! Altitude ${hut.alt} m.`, `抵達${hut.g[1]}！海拔 ${hut.alt} 公尺。`),
      line(`${b.belt}を締めよ。お前はもう、${b.id}の挑戦者だ。`, `Tie on the ${b.name[0].toLowerCase()}. You are now an ${b.id} challenger.`, `繫上${b.name[1]}吧。你現在是 ${b.id} 的挑戰者了。`),
      line(`次の${TRAILS[p].ja}には、まだ見ぬ関守たちが待っておる……。`, `On the ${TRAILS[p].g[0]} ahead, keepers you have never met are waiting…`, `前方的${TRAILS[p].g[1]}上，還有你從未見過的關守在等著……`),
      ask,
    ];
  }
  if (!progress.seenIntro) {
    progress.markIntroSeen();
    return [
      line("言の葉山の頂に立てば、どんな日本語の文も読めるという。", "It is said that whoever stands atop Mount Kotonoha can read any Japanese text.", "傳說站上言葉山頂的人，能讀懂任何日語文章。"),
      line("小屋では好きなだけ稽古できる。覚悟ができたら、先へ進め。", "At a hut you may practice as much as you like. When you're ready, move on.", "在山屋裡你可以盡情練習。準備好了，就繼續前進。"),
      line("道には三つの関所があり、それぞれに関守がおる。一問でも誤れば、この小屋に逆戻りだ。", "Each trail has three checkpoints, each with its own keeper. Miss a single question and you're back at this hut.", "每條路上有三個關卡，各有一位關守。只要錯一題，就會退回這個山屋。"),
      line("関所を越えるたびに、関守の印がもらえる。全部で十五。集めてみるがよい。", "Each checkpoint you clear earns that keeper's stamp. There are fifteen. See if you can collect them all.", "每通過一個關卡，就能得到關守的印章。總共十五個，試著全部收集吧。"),
      ask,
    ];
  }
  const pv = PROVERBS[Math.floor(Math.random() * PROVERBS.length)];
  const n = progress.stampCount, left = TOTAL_STAMPS - n;
  return [
    line(`今日の言葉。「${pv.ja.replace(/。$/, "")}」`, `Today's saying: "${pv.g[0]}"`, `今日格言：「${pv.g[1].replace(/。$/, "")}」`),
    line(`登山印は${n}個。頂まで、あと${left}の関所だ。`, `You hold ${n} stamps. ${left} checkpoints remain to the summit.`, `你擁有 ${n} 個登山印。距離山頂還有 ${left} 個關卡。`),
    ask,
  ];
}

/* ---------- checkpoints ---------- */

export function checkpointIntroLines(progress) {
  const seg = progress.pos, k = progress.k, K = keeperAt(seg, k), L = LEVELS[seg], s = SECTIONS[k], hut = HUTS[seg];
  return [
    line(K.intro[0], K.intro[1], K.intro[2]),
    line(
      `第${k + 1}の関所、${s.ja}の試練。全問正解でなければ、${hut.ja}まで戻ってもらう。`,
      `Checkpoint ${k + 1}: the ${L.id} ${STRINGS.en.sect[s.id].toLowerCase()} trial. Miss even one and you go back down to the ${hut.g[0]}.`,
      `第 ${k + 1} 關：${L.id} ${STRINGS.zh.sect[s.id]}試煉。只要錯一題，就得退回${hut.g[1]}。`,
    ),
    line("助言は一度だけ。迷ったら「ヒント」を使うがよい。", "You get one hint, only one. Use it when you're truly stuck.", "提示只有一次，真的卡住時再用吧。", {
      choice: [opt("begin", "試練を受ける", "Take the trial", "接受試煉"), opt("back", "小屋へ戻る", "Go back to the hut", "回到山屋")],
    }),
  ];
}

/** The keeper's verdict after a trial. `outcome` comes from Progress.recordCheckpoint. */
export function checkpointResultLines(outcome, passed, stampCount) {
  const { seg, k, arrived } = outcome, K = keeperAt(seg, k), hut = HUTS[seg];
  if (!passed)
    return [
      line(K.fail[0], K.fail[1], K.fail[2]),
      line(`（${hut.ja}まで引き返した……。この道の関所は、最初からやり直しだ。）`, `(You head back down to the ${hut.g[0]}… This trail's checkpoints start over.)`, `（你退回了${hut.g[1]}……這條路的關卡必須從頭開始。）`, { silent: true }),
      line("（間違えた問題は、小屋の稽古で何度でも練習できる。）", "(You can practice the questions you missed at the hut as many times as you like.)", "（答錯的題目，可以在山屋反覆練習。）", {
        silent: true,
        choice: [opt("map", "小屋へ戻る", "Return to the hut", "回到山屋")],
      }),
    ];
  const stampLine = line(`（${K.ja}の印を手に入れた！ 登山印 ${stampCount}／15）`, `(You received ${K.en}'s stamp! Trail stamps ${stampCount}/15)`, `（獲得了${K.zh}的印章！登山印 ${stampCount}／15）`, { silent: true });
  if (arrived) {
    const nh = HUTS[seg + 1];
    return [
      line(K.pass[0], K.pass[1], K.pass[2]),
      stampLine,
      line(`（この先に${nh.ja}の灯りが見える。）`, `(The lights of the ${nh.g[0]} shine ahead.)`, `（前方看得見${nh.g[1]}的燈火。）`, {
        silent: true,
        choice: [opt("map", "小屋に入る", `Enter the ${nh.g[0]}`, `進入${nh.g[1]}`)],
      }),
    ];
  }
  const NK = keeperAt(seg, k + 1);
  const [en, zh] = both("continueTo", k + 2);
  return [
    line(K.pass[0], K.pass[1], K.pass[2]),
    stampLine,
    line(`（次の関所では、${NK.role[0]}の${NK.ja}が待っているらしい……。）`, `(They say ${NK.en}, a ${NK.role[1].toLowerCase()}, waits at the next checkpoint…)`, `（據說下一關有${NK.role[2]}${NK.zh}在等著……）`, {
      silent: true,
      choice: [opt("next", "先へ進む", en, zh), retreatOpt()],
    }),
  ];
}
