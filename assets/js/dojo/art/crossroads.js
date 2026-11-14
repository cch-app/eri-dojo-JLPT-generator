// Procedural renderer ported from the Erin Dojo design; keep the drawing maths in sync with it.
import { rng } from "../core/random.js";

/* ================= Crossroads landscape (SVG) ================= */
function crossLand(){
  const r=rng(31);
  let trees="";
  const hill=(x0,x1,base,top)=>{for(let x=x0;x<x1;x+=10+r()*16){const h=40+r()*50,yb=base(x);
    trees+=`<path d="M${x.toFixed(0)} ${(yb-h).toFixed(0)}l${(h*.24).toFixed(0)} ${(h*.55).toFixed(0)}h-${(h*.1).toFixed(0)}l${(h*.18).toFixed(0)} ${(h*.45).toFixed(0)}h-${(h*.64).toFixed(0)}l${(h*.18).toFixed(0)} -${(h*.45).toFixed(0)}h-${(h*.1).toFixed(0)}z" fill="${r()<.5?"#0d1219":"#10161e"}"/>`}};
  hill(0,380,x=>300+Math.pow((x-290)/160,2)*40,0);
  hill(620,1000,x=>300+Math.pow((x-710)/160,2)*40,0);
  const tor=(x,y)=>`<g transform="translate(${x} ${y})">
    <path d="M-16 -36h32l-3 6h-26z" fill="#2a2a30"/><rect x="-11" y="-30" width="22" height="16" fill="#3a2a1e"/>
    <rect x="-12" y="-12" width="2.6" height="14" fill="#c4412a"/><rect x="9.4" y="-12" width="2.6" height="14" fill="#c4412a"/>
    <rect x="-14" y="-12" width="28" height="2" fill="#c4412a"/><path d="M-16 -14.5h32l-1 2.5h-30z" fill="#120d0a"/></g>`;
  const dots=(pts)=>pts.map(([x,y])=>`<circle class="glow-src" cx="${x}" cy="${y}" r="2.2" fill="#ffc77a"/>`).join("");
  return `<svg class="land" viewBox="0 0 1000 600" preserveAspectRatio="xMidYMax slice" aria-hidden="true">
    <defs>
      <linearGradient id="cr-dirt" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#6b5745"/><stop offset=".6" stop-color="#4c3e32"/><stop offset="1" stop-color="#3a3029"/></linearGradient>
      <linearGradient id="cr-ground" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#211a15"/><stop offset="1" stop-color="#140f0c"/></linearGradient>
      <radialGradient id="cr-pool" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#ffb060" stop-opacity=".35"/><stop offset="1" stop-color="#ffb060" stop-opacity="0"/></radialGradient>
    </defs>
    <path d="M0 330L80 292L160 312L250 246L330 286L420 234L500 272L590 224L680 282L760 238L850 292L930 252L1000 292V600H0Z" fill="#1a2032" stroke="rgba(170,182,214,.22)"/>
    <path d="M0 372C90 330 180 296 290 294C380 294 430 356 500 368C570 356 620 294 710 294C820 296 910 330 1000 372V600H0Z" fill="#131923"/>
    ${trees}
    ${tor(290,296)}${tor(710,296)}
    ${dots([[300,318],[318,334],[304,350],[328,364],[350,380],[378,394]])}
    ${dots([[700,318],[682,334],[696,350],[672,364],[650,380],[622,394]])}
    <path d="M0 410C160 396 330 392 500 396C670 392 840 396 1000 410V600H0Z" fill="url(#cr-ground)"/>
    <path d="M380 600C420 540 452 500 470 478L530 478C548 500 580 540 620 600Z" fill="url(#cr-dirt)"/>
    <path d="M470 482C440 452 400 424 350 400L368 396C418 414 478 444 530 478Z" fill="url(#cr-dirt)"/>
    <path d="M530 482C560 452 600 424 650 400L632 396C582 414 522 444 470 478Z" fill="url(#cr-dirt)"/>
    <ellipse cx="420" cy="470" rx="70" ry="22" fill="url(#cr-pool)"/><ellipse cx="580" cy="470" rx="70" ry="22" fill="url(#cr-pool)"/>
    <g fill="#5a5650"><rect x="413" y="452" width="14" height="4"/><rect x="417" y="438" width="6" height="14"/><path d="M410 438l10-7 10 7z"/>
      <rect x="573" y="452" width="14" height="4"/><rect x="577" y="438" width="6" height="14"/><path d="M570 438l10-7 10 7z"/></g>
    <rect class="glow-src" x="416.5" y="440" width="7" height="6" fill="#ffd28a"/><rect class="glow-src" x="576.5" y="440" width="7" height="6" fill="#ffd28a"/>
    <g stroke="#2e3a24" stroke-width="2" opacity=".7">${[...Array(40)].map(()=>{const x=r()*1000,y=420+r()*180;return `<path d="M${x.toFixed(0)} ${y.toFixed(0)}l-3 -8M${(x+3).toFixed(0)} ${y.toFixed(0)}l2 -9"/>`}).join("")}</g>
  </svg>`;
}

export { crossLand };
