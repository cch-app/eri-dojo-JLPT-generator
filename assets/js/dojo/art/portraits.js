// Procedural renderer ported from the Erin Dojo design; keep the drawing maths in sync with it.
/* Gatekeeper portrait: painted-style SVG built in code. Warm lantern key light from the left, cool moon rim light from the right. */
function buildGatekeeper(){
  let seed=7;const r=()=>{seed|=0;seed=seed+0x6D2B79F5|0;let t=Math.imul(seed^seed>>>15,1|seed);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296};
  const f=n=>n.toFixed(1);
  // hair strands as quadratic curves
  function strands(n,from,to,bend,col,wMin,wMax,aMin,aMax){
    let s="";
    for(let i=0;i<n;i++){
      const u=r(),[x0,y0]=from(u),[x1,y1]=to(u);
      const mx=(x0+x1)/2+(r()-.5)*bend,my=(y0+y1)/2+(r()-.5)*bend*.4;
      s+=`<path d="M${f(x0)} ${f(y0)}Q${f(mx)} ${f(my)} ${f(x1)} ${f(y1)}" stroke="${col(r())}" stroke-width="${f(wMin+(wMax-wMin)*r())}" stroke-opacity="${(aMin+(aMax-aMin)*r()).toFixed(2)}" fill="none" stroke-linecap="round"/>`;
    }
    return s;
  }
  const white=v=>v<.45?"#f2eee6":v<.75?"#dcd6cc":v<.92?"#bdb6ac":"#8f887f";
  const lerp=(a,b,t)=>a+(b-a)*t;

  // beard: strands start on a band under the nose/cheeks and fall to a soft point
  // beard grows from the jaw line (ear to ear, dipping under the lip) and falls to a soft point
  const beard=strands(340,
    u=>{const x=lerp(61,139,u);return[x+(r()-.5)*3,96+(1-Math.abs(x-100)/39)*24+(r()-.5)*4]},
    u=>{const x=lerp(80,120,u);return[x+(r()-.5)*6,lerp(176,194,r())-Math.abs(x-100)*1.3]},
    6,white,.3,.85,.25,.7);
  // mustache: two drooping sweeps from under the nose
  const mustL=strands(130,u=>[lerp(99,86,u),lerp(110,113,r())],u=>[lerp(93,70,u)+(r()-.5)*3,lerp(117,133,u)+(r()-.5)*3],4,white,.4,1,.5,.9);
  const mustR=strands(130,u=>[lerp(101,114,u),lerp(110,113,r())],u=>[lerp(107,130,u)+(r()-.5)*3,lerp(117,133,u)+(r()-.5)*3],4,white,.4,1,.5,.9);
  // brows: long, bushy, drooping outward
  const browL=strands(90,u=>[lerp(95,78,u),lerp(72,75,r())],u=>[lerp(80,62,u),lerp(74,84,u)+(r()-.5)*2],4,white,.4,1,.6,.95);
  const browR=strands(90,u=>[lerp(105,122,u),lerp(72,75,r())],u=>[lerp(120,138,u),lerp(74,84,u)+(r()-.5)*2],4,white,.4,1,.6,.95);
  // stray side hair above the ears
  const sideL=strands(30,u=>[lerp(60,66,u),lerp(66,80,r())],u=>[lerp(54,60,u),lerp(86,98,r())],6,white,.5,1,.35,.7);
  const sideR=strands(30,u=>[lerp(134,140,u),lerp(66,80,r())],u=>[lerp(140,146,u),lerp(86,98,r())],6,white,.5,1,.35,.7);

  const eye=(cx,flip)=>`
    <ellipse cx="${cx}" cy="83" rx="11" ry="6.5" fill="url(#gk-socket)"/>
    <path d="M${cx-6.5} 83.4 Q${cx} ${79.6} ${cx+6.5} 83.4 Q${cx} 86 ${cx-6.5} 83.4Z" fill="#d6c8b4"/>
    <circle cx="${cx+flip*.6}" cy="83" r="2.6" fill="#3a2618"/>
    <circle cx="${cx+flip*.6}" cy="83" r="1.2" fill="#0e0906"/>
    <circle cx="${cx+flip*.6-.9}" cy="82.2" r=".55" fill="#fff" opacity=".85"/>
    <path class="lid" d="M${cx-7.5} 83 Q${cx} ${77.5} ${cx+7.5} 83 Q${cx} 86.5 ${cx-7.5} 83Z" fill="url(#gk-skinLid)" opacity="0"/>
    <path d="M${cx-8} 83.2 Q${cx} ${77.4} ${cx+8} 83.2 Q${cx} 79.8 ${cx-8} 83.2Z" fill="#b98262"/>
    <path d="M${cx-7.4} 83 Q${cx} ${79.6} ${cx+7.4} 83" stroke="#4a2c1e" stroke-width="1.1" fill="none" stroke-linecap="round"/>
    <path d="M${cx-9} 90 Q${cx} 94 ${cx+9} 90 Q${cx} 88 ${cx-9} 90Z" fill="#8a5a40" opacity=".25"/>
    <path d="M${cx-8} 80 Q${cx} ${75.5} ${cx+8.5} 80.5" stroke="#7a5038" stroke-width=".7" fill="none" opacity=".7"/>
    <path d="M${cx-6} 87.5 Q${cx} 90 ${cx+6.5} 87.4" stroke="#8a5a40" stroke-width=".7" fill="none" opacity=".6"/>
    <path d="M${cx-5} 90.5 Q${cx} 92.5 ${cx+5.5} 90.4" stroke="#8a5a40" stroke-width=".5" fill="none" opacity=".4"/>
    <path d="M${cx+flip*9} 81 l${flip*4} -2 M${cx+flip*9} 83.5 l${flip*4.5} .5 M${cx+flip*8.5} 86 l${flip*4} 2" stroke="#7a4e36" stroke-width=".5" opacity=".55"/>`;

  return `<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg" role="img">
  <defs>
    <radialGradient id="gk-bg" cx="35%" cy="30%" r="85%"><stop offset="0" stop-color="#5a4130"/><stop offset=".6" stop-color="#2a1d14"/><stop offset="1" stop-color="#120c08"/></radialGradient>
    <radialGradient id="gk-skin" cx="38%" cy="38%" r="70%"><stop offset="0" stop-color="#f0cfae"/><stop offset=".45" stop-color="#d4a07c"/><stop offset=".8" stop-color="#a06a4a"/><stop offset="1" stop-color="#6e4630"/></radialGradient>
    <radialGradient id="gk-skinLid" cx="50%" cy="20%" r="80%"><stop offset="0" stop-color="#d9a882"/><stop offset="1" stop-color="#b07c5a"/></radialGradient>
    <radialGradient id="gk-socket" cx="50%" cy="40%" r="60%"><stop offset="0" stop-color="#7a4a32" stop-opacity=".55"/><stop offset="1" stop-color="#7a4a32" stop-opacity="0"/></radialGradient>
    <radialGradient id="gk-nose" cx="45%" cy="40%" r="60%"><stop offset="0" stop-color="#f2d0b0"/><stop offset=".7" stop-color="#c88e68"/><stop offset="1" stop-color="#c88e68" stop-opacity="0"/></radialGradient>
    <radialGradient id="gk-cheek" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#d07a62" stop-opacity=".35"/><stop offset="1" stop-color="#d07a62" stop-opacity="0"/></radialGradient>
    <linearGradient id="gk-rim" x1="0" x2="1"><stop offset=".6" stop-color="#b8c4e0" stop-opacity="0"/><stop offset="1" stop-color="#b8c4e0" stop-opacity=".45"/></linearGradient>
    <linearGradient id="gk-band" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#d4583c"/><stop offset=".5" stop-color="#a83a26"/><stop offset="1" stop-color="#6e2216"/></linearGradient>
    <linearGradient id="gk-haori" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#3a4a6c"/><stop offset=".5" stop-color="#26324b"/><stop offset="1" stop-color="#121a2a"/></linearGradient>
    <linearGradient id="gk-beardFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e8e2d6"/><stop offset=".7" stop-color="#bdb6aa"/><stop offset="1" stop-color="#8e887f" stop-opacity=".2"/></linearGradient>
    <linearGradient id="gk-staff" x1="0" x2="1"><stop offset="0" stop-color="#4a3020"/><stop offset=".45" stop-color="#9a6e44"/><stop offset="1" stop-color="#3a2416"/></linearGradient>
    <filter id="gk-grain" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" seed="4"/><feColorMatrix values="0 0 0 0 .35  0 0 0 0 .22  0 0 0 0 .14  0 0 0 .5 0"/><feComposite in2="SourceGraphic" operator="in"/></filter>
    <filter id="gk-soft"><feGaussianBlur stdDeviation="1.2"/></filter>
    <filter id="gk-hair" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation=".35"/></filter>
    <filter id="gk-fluff" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="2.4"/></filter>
    <clipPath id="gk-headClip"><path id="gk-headPath" d="M100 22C131 22 144 46 144 74C144 93 141 106 134 116C126 129 114 137 100 137C86 137 74 129 66 116C59 106 56 93 56 74C56 46 69 22 100 22Z"/></clipPath>
  </defs>

  <rect width="200" height="200" fill="url(#gk-bg)"/>
  <!-- lantern glow behind left shoulder -->
  <circle cx="18" cy="120" r="70" fill="#e8913f" opacity=".18" filter="url(#gk-soft)"/>

  <!-- staff behind the shoulder -->
  <rect x="158" y="0" width="9" height="200" rx="4" fill="url(#gk-staff)"/>
  <path d="M160 30v14M164 70v10M161 110v8" stroke="#2a180e" stroke-width=".8" opacity=".6"/>

  <!-- neck -->
  <path d="M82 120C82 136 80 146 76 152L124 152C120 146 118 136 118 120Z" fill="#a8704e"/>

  <!-- body: indigo haori over white juban -->
  <path d="M4 200C8 170 30 154 66 146L100 150L134 146C170 154 192 170 196 200Z" fill="url(#gk-haori)"/>
  <path d="M30 168C40 176 46 188 48 200M170 168C160 176 154 188 152 200" stroke="#0c1220" stroke-width="2" fill="none" opacity=".5"/>
  <path d="M74 146L100 196L126 146L118 145L100 180L82 145Z" fill="#ebe3d0"/>
  <path d="M66 147L100 204L108 200L80 146Z" fill="#1a1612"/>
  <path d="M134 147L100 204L92 200L120 146Z" fill="#1a1612"/>

  <!-- ears -->
  <ellipse cx="57" cy="90" rx="7.5" ry="13" fill="#c08562"/>
  <ellipse cx="143" cy="90" rx="7.5" ry="13" fill="#9a6446"/>
  <path d="M55 84q4 6 0 12M145 84q-4 6 0 12" stroke="#6e4430" stroke-width="1" fill="none" opacity=".6"/>

  <!-- head -->
  <use href="#gk-headPath" fill="url(#gk-skin)"/>
  <g clip-path="url(#gk-headClip)">
    <rect x="50" y="20" width="100" height="120" filter="url(#gk-grain)" opacity=".35"/>
    <ellipse cx="82" cy="40" rx="18" ry="10" fill="#fff4e4" opacity=".35" filter="url(#gk-soft)"/>
    <use href="#gk-headPath" fill="url(#gk-rim)"/>
    <!-- forehead lines between band and brows -->
    <path d="M78 66Q100 62 122 66M82 70Q100 67 118 70" stroke="#8a5a40" stroke-width=".7" fill="none" opacity=".45"/>
    <!-- temples, cheekbones, shadow under the brow ridge, age spots -->
    <ellipse cx="62" cy="76" rx="8" ry="16" fill="#6e4430" opacity=".35" filter="url(#gk-soft)"/>
    <ellipse cx="139" cy="76" rx="8" ry="16" fill="#4a2c20" opacity=".45" filter="url(#gk-soft)"/>
    <ellipse cx="100" cy="78" rx="30" ry="4" fill="#7a4a32" opacity=".28" filter="url(#gk-soft)"/>
    <ellipse cx="80" cy="95" rx="9" ry="4" fill="#f6dcc2" opacity=".35" filter="url(#gk-soft)"/>
    <ellipse cx="128" cy="112" rx="10" ry="14" fill="#5a3424" opacity=".3" filter="url(#gk-soft)"/>
    <circle cx="118" cy="38" r="2" fill="#a26a48" opacity=".45"/><circle cx="86" cy="33" r="1.4" fill="#a26a48" opacity=".4"/><circle cx="125" cy="70" r="1.2" fill="#a26a48" opacity=".4"/>
    <ellipse cx="78" cy="100" rx="12" ry="8" fill="url(#gk-cheek)"/>
    <ellipse cx="122" cy="100" rx="12" ry="8" fill="url(#gk-cheek)"/>
    <!-- nose -->
    <path d="M97 84C96 92 94 99 92 104" stroke="#a87050" stroke-width="1" fill="none" opacity=".5"/>
    <path d="M101 84C102 92 104 99 106 104" stroke="#f6dcc2" stroke-width="1.2" fill="none" opacity=".45"/>
    <ellipse cx="100" cy="103" rx="9" ry="7" fill="url(#gk-nose)"/>
    <path d="M91 104Q94 109 97 107M109 104Q106 109 103 107" stroke="#7a4a32" stroke-width="1" fill="none" opacity=".7"/>
    <ellipse cx="96.5" cy="107.5" rx="2" ry="1.1" fill="#4a2c1e" opacity=".8"/>
    <ellipse cx="103.5" cy="107.5" rx="2" ry="1.1" fill="#4a2c1e" opacity=".8"/>
    <path d="M88 104Q84 110 82 118M112 104Q116 110 118 118" stroke="#8a5a40" stroke-width=".8" fill="none" opacity=".5"/>
  </g>
  ${eye(85,-1)}${eye(115,1)}

  <!-- hachimaki headband with knot -->
  <path d="M57 50C78 43 122 43 143 50L144 61C122 55 78 55 56 61Z" fill="url(#gk-band)"/>
  <path d="M60 54C80 49 120 49 140 54" stroke="#e57a5c" stroke-width=".7" fill="none" opacity=".6"/>
  <path d="M143 52q8 -2 11 3q-3 6 -11 4Z" fill="#9a3020"/>
  <path d="M152 56q10 4 14 16q-6 -2 -10 -10Z M150 58q4 10 2 22q-4 -6 -5 -16Z" fill="#8a2a1a"/>

  <!-- hair, brows, mouth, beard -->
  <g filter="url(#gk-hair)">${sideL}${sideR}</g>
  <path d="M59 94C58 122 70 154 88 186C95 197 105 197 112 186C130 154 142 122 141 94C134 110 122 121 100 123C78 121 66 110 59 94Z" fill="url(#gk-beardFill)" filter="url(#gk-fluff)"/>
  <ellipse cx="100" cy="121" rx="15" ry="5" fill="#3a2a22" opacity=".45" filter="url(#gk-soft)"/>
  <ellipse class="mouth" cx="100" cy="120" rx="6" ry="2.6" fill="#1e0e0a" opacity="0"/>
  <path d="M74 80C80 74 92 72 96 74L94 78C86 77 80 79 74 84Z M126 80C120 74 108 72 104 74L106 78C114 77 120 79 126 84Z" fill="#e6e0d6" opacity=".55" filter="url(#gk-fluff)"/>
  <path d="M100 110C92 110 80 118 72 130C84 126 94 120 100 116C106 120 116 126 128 130C120 118 108 110 100 110Z" fill="#e6e0d6" opacity=".7" filter="url(#gk-fluff)"/>
  <g filter="url(#gk-hair)">${beard}${mustL}${mustR}${browL}${browR}</g>
</svg>`;
}

/* ================= Checkpoint characters: painted SVG portraits from parameters ================= */
function buildCharacter(p){
  const id=p.id; let seed=p.seed||1;
  const r=()=>{seed|=0;seed=seed+0x6D2B79F5|0;let t=Math.imul(seed^seed>>>15,1|seed);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296};
  const f=n=>n.toFixed(1), lerp=(a,b,t)=>a+(b-a)*t;
  const SK={fair:["#f7dfc8","#e6b494","#b47e5c","#7a5038"],light:["#f0cfae","#d4a07c","#a06a4a","#6e4630"],tan:["#e4b68c","#c2865a","#8c5838","#5a3622"]}[p.skin||"light"];
  const old=p.age==="old",young=p.age==="young",fem=!!p.fem;
  const hc=p.hairCol||"#1c1612",hl=p.hairHi||"#3a3029";
  function strands(n,from,to,bend,cols,wMin,wMax,aMin,aMax){
    let s="";for(let i=0;i<n;i++){const u=r(),[x0,y0]=from(u),[x1,y1]=to(u);
      const mx=(x0+x1)/2+(r()-.5)*bend,my=(y0+y1)/2+(r()-.5)*bend*.4;
      s+=`<path d="M${f(x0)} ${f(y0)}Q${f(mx)} ${f(my)} ${f(x1)} ${f(y1)}" stroke="${cols[Math.floor(r()*cols.length)]}" stroke-width="${f(wMin+(wMax-wMin)*r())}" stroke-opacity="${(aMin+(aMax-aMin)*r()).toFixed(2)}" fill="none" stroke-linecap="round"/>`}
    return s;
  }
  const grey=p.beardCol==="grey"?["#d8d4cc","#b4aea6","#8e8880"]:p.beardCol==="white"?["#f2eee6","#dcd6cc","#bdb6ac"]:[hc,hl,"#2a221c"];
  const headD=fem
    ?"M100 26C129 26 141 48 141 75C141 95 136 110 128 120C120 131 110 136 100 136C90 136 80 131 72 120C64 110 59 95 59 75C59 48 71 26 100 26Z"
    :"M100 24C131 24 144 47 144 75C144 94 141 107 134 117C126 130 114 138 100 138C86 138 74 130 66 117C59 107 56 94 56 75C56 47 69 24 100 24Z";

  const eye=(cx,flip)=>{
    if(p.eyes==="closed")return `<path d="M${cx-7} 83Q${cx} 87.5 ${cx+7} 83" stroke="#3a2418" stroke-width="1.4" fill="none" stroke-linecap="round"/>
      <path d="M${cx-6} 88.5Q${cx} 90.5 ${cx+6} 88.4" stroke="#8a5a40" stroke-width=".5" fill="none" opacity=".4"/>`;
    const ir=young?3:2.6, hood=old?1:young?0:.5;
    return `<ellipse cx="${cx}" cy="83" rx="11" ry="6.5" fill="url(#${id}-socket)"/>
    <path d="M${cx-6.8} 83.4Q${cx} ${79.2-(young?.8:0)} ${cx+6.8} 83.4Q${cx} 86.4 ${cx-6.8} 83.4Z" fill="${young?"#e6dccb":"#d6c8b4"}"/>
    <circle cx="${cx+flip*.5}" cy="83" r="${ir}" fill="${p.iris||"#3a2618"}"/><circle cx="${cx+flip*.5}" cy="83" r="${ir*.46}" fill="#0e0906"/>
    <circle cx="${cx+flip*.5-.9}" cy="82" r=".65" fill="#fff" opacity=".9"/>
    <path class="lid" d="M${cx-7.5} 83Q${cx} 77.5 ${cx+7.5} 83Q${cx} 86.5 ${cx-7.5} 83Z" fill="url(#${id}-lidc)" opacity="0"/>
    ${hood?`<path d="M${cx-8} 83.2Q${cx} ${77.6} ${cx+8} 83.2Q${cx} ${80-hood*.4} ${cx-8} 83.2Z" fill="${SK[2]}" opacity=".75"/>`:""}
    <path d="M${cx-7.2} 83Q${cx} ${79.4-(young?.6:0)} ${cx+7.2} 83" stroke="#2a1a10" stroke-width="${fem?1.6:1.1}" fill="none" stroke-linecap="round"/>
    ${fem?`<path d="M${cx+flip*6.5} 82.4l${flip*2.2} -1.6" stroke="#2a1a10" stroke-width="1" stroke-linecap="round"/>`:""}
    <path d="M${cx-8} 80Q${cx} 75.8 ${cx+8.5} 80.4" stroke="#7a5038" stroke-width=".6" fill="none" opacity="${young?.25:.55}"/>
    ${old||p.age==="middle"?`<path d="M${cx-6} 87.6Q${cx} 90 ${cx+6.5} 87.4" stroke="#8a5a40" stroke-width=".6" fill="none" opacity="${old?.6:.3}"/>`:""}
    ${old?`<path d="M${cx+flip*9} 81l${flip*4} -2M${cx+flip*9} 83.5l${flip*4.5} .5M${cx+flip*8.5} 86l${flip*4} 2" stroke="#7a4e36" stroke-width=".5" opacity=".55"/>`:""}`;
  };

  // ---- hair (back layer, cap, front pieces) ----
  let hairBack="",hairCap="",hairFront="";
  const capPath=fem
    ?"M57 84C53 44 74 18 100 18C126 18 147 44 143 84C139 66 132 54 120 48C108 54 88 55 76 50C67 58 60 70 57 84Z"
    :"M55 80C53 42 74 18 100 18C126 18 147 42 145 80C140 62 132 52 118 47C106 52 86 52 76 49C67 56 59 66 55 80Z";
  const capTex=()=>`<g clip-path="url(#${id}-cap)">`+strands(70,u=>[lerp(60,140,u),lerp(20,28,r())],u=>[lerp(56,144,u)+(r()-.5)*8,lerp(44,70,r())],8,[hc,hl],.5,1.1,.35,.75)+`</g>`;   // texture stays inside the hairline
  switch(p.hair){
    case "short":case "topknot":case "bun":case "long":case "bob":case "ponytail":case "tied":
      hairCap=`<path d="${capPath}" fill="url(#${id}-hair)"/>${capTex()}`;break;
    case "shaved":hairCap=`<path d="M58 70C58 40 76 22 100 22C124 22 142 40 142 70C130 56 116 50 100 50C84 50 70 56 58 70Z" fill="#5a5450" opacity=".35"/>`;break;
    case "sides":hairCap=strands(40,u=>[lerp(58,64,u),lerp(62,78,r())],u=>[lerp(52,58,u),lerp(86,100,r())],6,grey,.5,1,.4,.8)+strands(40,u=>[lerp(136,142,u),lerp(62,78,r())],u=>[lerp(142,148,u),lerp(86,100,r())],6,grey,.5,1,.4,.8);break;
  }
  if(p.hair==="topknot")hairFront=`<path d="M92 20C92 8 108 8 108 20C106 24 94 24 92 20Z" fill="${hc}"/><rect x="95" y="18" width="10" height="4" rx="1.5" fill="#d8cfb8"/>`;
  if(p.hair==="bun")hairBack=`<circle cx="100" cy="17" r="15" fill="url(#${id}-hair)"/>${strands(20,u=>[lerp(88,112,u),8+r()*4],u=>[lerp(88,112,u),24+r()*4],6,[hc,hl],.5,1,.3,.6)}`+
    (p.pin?`<path d="M118 10L82 28" stroke="${p.pin}" stroke-width="1.6"/><circle cx="119" cy="9.5" r="3.4" fill="${p.pin}"/><circle cx="123" cy="13" r="2" fill="#f2e6c8"/>`:"");
  if(p.hair==="long")hairBack=`<path d="M58 70C50 110 52 150 46 178L72 178C70 150 68 120 70 96ZM142 70C150 110 148 150 154 178L128 178C130 150 132 120 130 96Z" fill="url(#${id}-hair)"/>${strands(40,u=>[lerp(52,64,u),80],u=>[lerp(46,70,u),176],5,[hc,hl],.5,1,.3,.7)}${strands(40,u=>[lerp(136,148,u),80],u=>[lerp(130,154,u),176],5,[hc,hl],.5,1,.3,.7)}`+
    (p.ribbon?`<rect x="44" y="150" width="28" height="5" fill="${p.ribbon}"/><rect x="128" y="150" width="28" height="5" fill="${p.ribbon}"/>`:"");
  if(p.hair==="bob")hairFront=`<path d="M57 80C55 100 58 116 66 124L74 122C68 110 66 96 67 84ZM143 80C145 100 142 116 134 124L126 122C132 110 134 96 133 84Z" fill="url(#${id}-hair)"/><path d="M68 52C80 62 92 64 100 60C108 64 120 62 132 52L130 46C118 54 82 54 70 46Z" fill="${hc}"/>`;
  if(p.hair==="ponytail")hairBack=`<path d="M112 18C140 6 160 30 152 70C148 100 156 128 150 150C140 120 138 96 140 70C142 46 130 30 112 30Z" fill="url(#${id}-hair)"/>${strands(30,u=>[lerp(118,146,u),20+u*20],u=>[lerp(140,152,u),lerp(100,148,r())],6,[hc,hl],.5,1,.3,.6)}`+
    `<rect x="110" y="14" width="10" height="8" rx="2" transform="rotate(-25 115 18)" fill="${p.band||"#efe9dc"}"/>`;
  if(p.hair==="tied")hairBack=`<path d="M100 20C126 18 150 34 148 60C150 76 156 92 160 104C146 96 140 84 138 70C134 46 120 32 100 30Z" fill="url(#${id}-hair)"/>${strands(30,u=>[lerp(110,150,u),24+u*30],u=>[lerp(140,160,u),lerp(80,104,r())],6,[hc,hl],.5,1,.3,.6)}`;

  // ---- headwear ----
  let headBack="",headFront="",faceShade="";
  if(p.head==="hachimaki")headFront=`<path d="M57 50C78 43 122 43 143 50L144 61C122 55 78 55 56 61Z" fill="${p.headCol}"/><path d="M60 54C80 49 120 49 140 54" stroke="#fff" stroke-width=".7" fill="none" opacity=".35"/><path d="M143 52q8 -2 11 3q-3 6 -11 4Z M152 56q10 4 14 16q-6 -2 -10 -10Z" fill="${p.headCol}" opacity=".9"/>`;
  if(p.head==="tenugui")headFront=`<path d="M54 64C52 34 74 16 100 16C126 16 148 34 146 64C134 54 120 50 100 50C80 50 66 54 54 64Z" fill="${p.headCol}"/>`+
    [...Array(14)].map((_,i)=>`<circle cx="${f(66+r()*68)}" cy="${f(24+r()*26)}" r="1.6" fill="#efe6d2" opacity=".7"/>`).join("")+
    `<path d="M140 52q14 -4 16 6q-8 4 -16 0Z M150 58q8 10 4 20q-6 -8 -8 -16Z" fill="${p.headCol}"/>`;
  if(p.head==="kasa"){headFront=`<path d="M14 66L100 6L186 66Q100 76 14 66Z" fill="url(#${id}-straw)"/>`+
    [...Array(18)].map((_,i)=>{const x=14+i*172/17;return `<path d="M100 8L${f(x)} 66" stroke="#6e5226" stroke-width=".6" opacity=".55"/>`}).join("")+
    `<path d="M14 66Q100 76 186 66" stroke="#4a3618" stroke-width="1.4" fill="none"/>`;
    faceShade=`<rect x="50" y="60" width="100" height="40" fill="url(#${id}-shade)"/>`;}
  if(p.head==="tokin")headFront=`<path d="M86 40L100 26L114 40L110 50H90Z" fill="#141210"/><path d="M90 50h20" stroke="#3a3632" stroke-width="1.2"/><path d="M100 50v12" stroke="#141210" stroke-width="1"/>`;
  if(p.head==="hood"){headBack=`<path d="M44 200C40 150 44 96 54 64C64 30 84 14 100 14C116 14 136 30 146 64C156 96 160 150 156 200Z" fill="url(#${id}-hood)"/>`;
    headFront=`<path d="M100 14C124 14 146 34 148 70C146 50 128 36 100 36C72 36 54 50 52 70C54 34 76 14 100 14Z" fill="url(#${id}-hood)"/><path d="M54 70C54 110 60 130 72 142M146 70C146 110 140 130 128 142" stroke="#c8c2b6" stroke-width="3" fill="none"/>`;}
  if(p.feather)headFront+=`<path d="M136 44C150 20 162 12 170 6C166 22 156 36 140 50Z" fill="#8a6a46"/><path d="M138 48L168 8" stroke="#3a2a1a" stroke-width=".8"/>`;

  // ---- beard / mouth ----
  let beard="",mouth="";
  const lip=fem?"#b65a50":"#9a5e4c";
  const mouthOpen=`<ellipse class="mouth" cx="100" cy="${fem?119:120}" rx="${fem?4.6:5.5}" ry="2.4" fill="#2a1210" opacity="0"/>`;
  if(!p.beard||p.beard==="none"||p.beard==="stubble"){
    mouth=`<path d="M${fem?93:92} ${fem?118.6:119.5}Q100 ${fem?121.6:121.8} ${fem?107:108} ${fem?118.6:119.5}" stroke="${lip}" stroke-width="${fem?2.2:1.4}" fill="none" stroke-linecap="round"/>
           <path d="M${fem?94:93} 118.4Q100 116.6 ${fem?106:107} 118.4" stroke="${lip}" stroke-width="${fem?1.4:.8}" fill="none" opacity=".75"/>${mouthOpen}`;
    if(p.beard==="stubble")beard=`<path d="M66 108C70 126 86 140 100 140C114 140 130 126 134 108C126 120 114 128 100 128C86 128 74 120 66 108Z" fill="#2a2420" opacity=".22"/>`+[...Array(70)].map(()=>`<circle cx="${f(70+r()*60)}" cy="${f(110+r()*28)}" r=".45" fill="#2a2420" opacity=".5"/>`).join("");
  }else{
    mouth=mouthOpen;
    const must=(len)=>strands(70,u=>[lerp(99,87,u),lerp(110,113,r())],u=>[lerp(93,93-len,u)+(r()-.5)*2,lerp(116,124+len*.4,u)],4,grey,.4,1,.5,.9)+
                      strands(70,u=>[lerp(101,113,u),lerp(110,113,r())],u=>[lerp(107,107+len,u)+(r()-.5)*2,lerp(116,124+len*.4,u)],4,grey,.4,1,.5,.9);
    if(p.beard==="mustache")beard=must(p.mustLen||16);
    if(p.beard==="goatee")beard=must(10)+strands(70,u=>[lerp(92,108,u),124+r()*3],u=>[lerp(96,104,u)+(r()-.5)*3,lerp(140,150+(p.goateeLen||0),r())],4,grey,.4,1,.5,.9);
    if(p.beard==="full"||p.beard==="sage"){
      const end=p.beard==="sage"?198:168;
      beard=`<path d="M59 94C58 120 70 ${end-30} 88 ${end-4}C95 ${end+6} 105 ${end+6} 112 ${end-4}C130 ${end-30} 142 120 141 94C134 110 122 121 100 123C78 121 66 110 59 94Z" fill="${grey[1]}" opacity=".85" filter="url(#${id}-fluff)"/>`+
        `<g filter="url(#${id}-hairf)">`+strands(p.beard==="sage"?320:230,u=>{const x=lerp(61,139,u);return[x+(r()-.5)*3,96+(1-Math.abs(x-100)/39)*24+(r()-.5)*4]},
          u=>{const x=lerp(80,120,u);return[x+(r()-.5)*6,lerp(end-14,end+2,r())-Math.abs(x-100)*(p.beard==="sage"?1.1:.9)]},6,grey,.3,.9,.3,.75)+must(18)+`</g>`;
    }
  }

  // ---- body ----
  const robe=p.robe||"#26324b",collar=p.collar||"#ebe3d0",lapel=p.lapel||"#1a1612";
  let body=`<path d="M4 200C8 170 30 154 66 146L100 150L134 146C170 154 192 170 196 200Z" fill="url(#${id}-robe)"/>
    <path d="M30 168C40 176 46 188 48 200M170 168C160 176 154 188 152 200" stroke="#000" stroke-width="2" fill="none" opacity=".25"/>
    <path d="M74 146L100 196L126 146L118 145L100 180L82 145Z" fill="${collar}"/>
    <path d="M66 147L100 204L108 200L80 146Z" fill="${lapel}"/><path d="M134 147L100 204L92 200L120 146Z" fill="${lapel}"/>`;
  if(p.kesa)body+=`<path d="M40 162L150 200L132 200L32 172Z" fill="${p.kesa}"/><path d="M44 164L146 198" stroke="#000" stroke-width=".6" opacity=".3"/>`;
  if(p.pom)body+=[[72,168],[100,176],[128,168]].map(([x,y])=>`<circle cx="${x}" cy="${y}" r="9" fill="${p.pom}" filter="url(#${id}-soft)"/><circle cx="${x}" cy="${y}" r="7" fill="${p.pom}"/>`).join("");
  if(p.check)body+=`<path d="M8 196C12 172 32 158 66 150L72 160C44 166 28 180 24 200Z" fill="url(#${id}-check)" opacity=".6"/><path d="M192 196C188 172 168 158 134 150L128 160C156 166 172 180 176 200Z" fill="url(#${id}-check)" opacity=".6"/>`;

  // ---- props ----
  let propBack="",propFront="";
  if(p.staff)propBack=`<rect x="158" y="0" width="9" height="200" rx="4" fill="url(#${id}-wood)"/>`;
  if(p.axe)propBack=`<rect x="150" y="30" width="7" height="170" rx="3" fill="url(#${id}-wood)" transform="rotate(14 154 115)"/><path d="M160 30L186 22L184 52L162 46Z" fill="#8e9298" transform="rotate(14 154 115)"/>`;
  if(p.glasses)propFront=`<g fill="none" stroke="#2a2018" stroke-width="1.3"><circle cx="85" cy="83.5" r="9"/><circle cx="115" cy="83.5" r="9"/><path d="M94 83q6 -3 12 0M76 82l-18 -4M124 82l18 -4"/></g><circle cx="82" cy="80" r="3" fill="#fff" opacity=".12"/><circle cx="112" cy="80" r="3" fill="#fff" opacity=".12"/>`;
  if(p.brush)propFront+=`<path d="M150 200L168 120" stroke="#3a2a1a" stroke-width="5" stroke-linecap="round"/><path d="M166 122L172 100L174 124Z" fill="#141210"/>`;

  // ---- brows ----
  const bcol=p.browCol==="grey"?["#d8d4cc","#b4aea6"]:p.browCol==="white"?["#f2eee6","#dcd6cc"]:[hc,hl];
  const bn=old?90:fem?40:60,bw=old?1:fem?.7:.9;
  const brows=strands(bn,u=>[lerp(95,79,u),lerp(72.5,75,r())],u=>[lerp(old?78:84,old?62:70,u),lerp(74,old?84:77,u)+(r()-.5)*1.5],old?4:2,bcol,.4,bw,.6,.95)+
              strands(bn,u=>[lerp(105,121,u),lerp(72.5,75,r())],u=>[lerp(old?122:116,old?138:130,u),lerp(74,old?84:77,u)+(r()-.5)*1.5],old?4:2,bcol,.4,bw,.6,.95);

  const wr=old?`<path d="M78 64Q100 60 122 64M82 68Q100 65 118 68" stroke="#8a5a40" stroke-width=".7" fill="none" opacity=".45"/>
    <path d="M88 104Q84 110 82 118M112 104Q116 110 118 118" stroke="#8a5a40" stroke-width=".8" fill="none" opacity=".5"/>`
    :p.age==="middle"?`<path d="M89 106Q85 112 84 118M111 106Q115 112 116 118" stroke="#8a5a40" stroke-width=".6" fill="none" opacity=".3"/>`:"";

  const showEars=!["long","bob","hood"].includes(p.hair)&&p.head!=="hood";
  return `<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <radialGradient id="${id}-bg" cx="35%" cy="30%" r="85%"><stop offset="0" stop-color="${p.bg||"#4a3a30"}"/><stop offset=".6" stop-color="#22180f"/><stop offset="1" stop-color="#100a06"/></radialGradient>
    <radialGradient id="${id}-skin" cx="38%" cy="38%" r="70%"><stop offset="0" stop-color="${SK[0]}"/><stop offset=".45" stop-color="${SK[1]}"/><stop offset=".8" stop-color="${SK[2]}"/><stop offset="1" stop-color="${SK[3]}"/></radialGradient>
    <radialGradient id="${id}-lidc" cx="50%" cy="20%" r="80%"><stop offset="0" stop-color="${SK[1]}"/><stop offset="1" stop-color="${SK[2]}"/></radialGradient>
    <radialGradient id="${id}-socket" cx="50%" cy="40%" r="60%"><stop offset="0" stop-color="#7a4a32" stop-opacity="${young?.3:.5}"/><stop offset="1" stop-color="#7a4a32" stop-opacity="0"/></radialGradient>
    <radialGradient id="${id}-nose" cx="45%" cy="40%" r="60%"><stop offset="0" stop-color="${SK[0]}"/><stop offset=".7" stop-color="${SK[1]}"/><stop offset="1" stop-color="${SK[1]}" stop-opacity="0"/></radialGradient>
    <radialGradient id="${id}-cheek" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#d4705c" stop-opacity="${fem?.45:.3}"/><stop offset="1" stop-color="#d4705c" stop-opacity="0"/></radialGradient>
    <linearGradient id="${id}-rim" x1="0" x2="1"><stop offset=".6" stop-color="#b8c4e0" stop-opacity="0"/><stop offset="1" stop-color="#b8c4e0" stop-opacity=".4"/></linearGradient>
    <linearGradient id="${id}-hair" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="${hl}"/><stop offset=".5" stop-color="${hc}"/><stop offset="1" stop-color="#0a0806"/></linearGradient>
    <linearGradient id="${id}-robe" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="${robe}" stop-opacity=".85"/><stop offset=".5" stop-color="${robe}"/><stop offset="1" stop-color="#0a0a10"/></linearGradient>
    <linearGradient id="${id}-hood" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f4f0e8"/><stop offset=".6" stop-color="#d6d0c4"/><stop offset="1" stop-color="#8e887e"/></linearGradient>
    <linearGradient id="${id}-straw" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#d8b46e"/><stop offset="1" stop-color="#8a6a36"/></linearGradient>
    <linearGradient id="${id}-shade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1a1008" stop-opacity=".55"/><stop offset="1" stop-color="#1a1008" stop-opacity="0"/></linearGradient>
    <linearGradient id="${id}-wood" x1="0" x2="1"><stop offset="0" stop-color="#4a3020"/><stop offset=".45" stop-color="#9a6e44"/><stop offset="1" stop-color="#3a2416"/></linearGradient>
    <pattern id="${id}-check" width="12" height="12" patternUnits="userSpaceOnUse"><rect width="6" height="6" fill="#2a2a30"/><rect x="6" y="6" width="6" height="6" fill="#2a2a30"/></pattern>
    <filter id="${id}-grain" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" seed="${p.seed}"/><feColorMatrix values="0 0 0 0 .35  0 0 0 0 .22  0 0 0 0 .14  0 0 0 .5 0"/><feComposite in2="SourceGraphic" operator="in"/></filter>
    <filter id="${id}-soft"><feGaussianBlur stdDeviation="1.2"/></filter>
    <filter id="${id}-hairf" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation=".35"/></filter>
    <filter id="${id}-fluff" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="2.4"/></filter>
    <clipPath id="${id}-hc"><path d="${headD}"/></clipPath>
    <clipPath id="${id}-cap"><path d="${capPath}"/></clipPath>
  </defs>
  <rect width="200" height="200" fill="url(#${id}-bg)"/>
  <circle cx="18" cy="120" r="70" fill="#e8913f" opacity=".14" filter="url(#${id}-soft)"/>
  ${propBack}${headBack}${hairBack}
  <path d="M82 120C82 136 80 146 76 152L124 152C120 146 118 136 118 120Z" fill="${SK[2]}"/>
  ${body}
  ${showEars?`<ellipse cx="${fem?60:57}" cy="90" rx="7" ry="12.5" fill="${SK[1]}"/><ellipse cx="${fem?140:143}" cy="90" rx="7" ry="12.5" fill="${SK[2]}"/>`:""}
  ${showEars&&p.earring?`<circle cx="60" cy="104" r="1.8" fill="${p.earring}"/>`:""}
  <path d="${headD}" fill="url(#${id}-skin)"/>
  <g clip-path="url(#${id}-hc)">
    <rect x="50" y="20" width="100" height="120" filter="url(#${id}-grain)" opacity="${young?.2:.35}"/>
    <ellipse cx="82" cy="40" rx="18" ry="10" fill="#fff4e4" opacity=".3" filter="url(#${id}-soft)"/>
    <path d="${headD}" fill="url(#${id}-rim)"/>
    <ellipse cx="139" cy="78" rx="8" ry="16" fill="#4a2c20" opacity=".4" filter="url(#${id}-soft)"/>
    <ellipse cx="100" cy="78" rx="30" ry="4" fill="#7a4a32" opacity=".22" filter="url(#${id}-soft)"/>
    <ellipse cx="128" cy="112" rx="10" ry="14" fill="#5a3424" opacity=".25" filter="url(#${id}-soft)"/>
    <ellipse cx="78" cy="101" rx="12" ry="8" fill="url(#${id}-cheek)"/><ellipse cx="122" cy="101" rx="12" ry="8" fill="url(#${id}-cheek)"/>
    ${wr}
    <path d="M97 86C96 93 94 99 92.5 104" stroke="${SK[2]}" stroke-width="1" fill="none" opacity=".5"/>
    <ellipse cx="100" cy="103" rx="${fem?7.5:9}" ry="${fem?6:7}" fill="url(#${id}-nose)"/>
    <path d="M${fem?93:91} 104Q94 108.5 97 107M${fem?107:109} 104Q106 108.5 103 107" stroke="#7a4a32" stroke-width=".9" fill="none" opacity=".65"/>
    <ellipse cx="96.6" cy="107.4" rx="1.8" ry="1" fill="#4a2c1e" opacity=".75"/><ellipse cx="103.4" cy="107.4" rx="1.8" ry="1" fill="#4a2c1e" opacity=".75"/>
    ${faceShade}
  </g>
  ${eye(85,-1)}${eye(115,1)}
  ${hairCap}${hairFront}${headFront}
  ${mouth}${beard}
  <g filter="url(#${id}-hairf)">${brows}</g>
  ${propFront}
</svg>`;
}

export { buildGatekeeper, buildCharacter };
