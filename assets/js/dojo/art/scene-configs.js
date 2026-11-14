// Procedural renderer ported from the Erin Dojo design; keep the drawing maths in sync with it.
import { clamp, rng } from "../core/random.js";
import { Bamboo } from "./bamboo.js";
import { Ground } from "./ground.js";
import { Willow } from "./willow.js";

/* --- scene configs: where the moon, clouds and mist sit in each scene --- */
function crossCfg(W,H,scene,sr){
  const u=Math.min(H*.36,W*.3);
  const moon={x:W*.5,y:H*.13,r:Math.max(12,u*.15)};
  const glows=[...scene.querySelectorAll(".glow-src")].map(el=>{const b=el.getBoundingClientRect();
    return{x:b.left-sr.left+b.width/2,y:b.top-sr.top+b.height/2,r:Math.max(14,Math.max(b.width,b.height)*7)}});
  return{u,moon,glows,
    clouds:[["cum",u*2.4,u*.8,moon.x-u*3.1,moon.y-u*.05,4,.95,11],["cum",u*2,u*.6,moon.x+u*.8,moon.y+u*.25,3,.85,23],
            ["wisp",u*2.3,u*.26,moon.x-u*1.6,moon.y+moon.r*.4,5.5,.95,41],["wisp",u*2.8,u*.2,moon.x-u*.3,moon.y-u*.45,7,.6,53],
            ["cum",u*1.8,u*.5,W*.02,H*.4,2.5,.6,37],["wisp",u*2,u*.22,W*.72,H*.36,6,.6,67]],
    fog:[[W*.8,u*.45,-W*.1,H-u*.25,6,.75,71,0],[W*.7,u*.4,W*.4,H-u*.05,-4.5,.7,83,1.7],
         [W*.7,u*.3,W*.12,H*.62,4,.55,97,3.1],[W*.5,u*.2,W*.5,H*.54,-6,.45,109,4.4]]};
}
function doorCfg(W,H,scene,sr){
  const door=scene.querySelector(".dojo-door"),kas=scene.querySelector(".kasagi");
  const dw=door.offsetWidth,yTop=H*.66,topT=kas.getBoundingClientRect().top-sr.top;
  const {glows,geo}=Ground.paint(scene.querySelector(".ground"),W,H,dw,yTop);
  // bamboo grows in clumps on the banks: uneven distance from the path, mostly upright, sized by perspective
  const bc=scene.querySelector(".bamboo"),dpr=Math.min(window.devicePixelRatio||1,2);
  bc.width=Math.round(W*dpr);bc.height=Math.round(H*dpr);
  const bg=bc.getContext("2d"),br=rng(77),culms=[],gg=scene.querySelector(".ground").getContext("2d");
  const yAt=d=>{const f=d*geo.N,i=Math.min(geo.N-1,Math.floor(f));return geo.ys[i]+(geo.ys[i+1]-geo.ys[i])*(f-i)};
  const hwD=d=>geo.hwAt(d*geo.N);
  const hw0=geo.hwAt(0);
  for(const s of [-1,1]){
    const clumps=11+Math.floor(br()*4);
    for(let k=0;k<clumps;k++){
      const d=clamp(.05+.95*((k+br()*.8)/clumps),0,1);           // spread down the bank, jittered
      const hw=hwD(d),sc=hw/hw0;                                   // perspective scale at this depth
      const away=hw*(1.75+br()*br()*1.5);                          // side walls end at 1.2×hw; stay well beyond them and the lanterns
      const cxk=geo.cx+s*away,cy=yAt(d)+dw*.03*sc;
      const n=2+Math.floor(br()*3);
      for(let j=0;j<n;j++){
        const x=cxk+(br()-.5)*hw*.22,y=cy+(br()-.5)*dw*.05*sc;
        culms.push(Bamboo.culm(br,{x,y,h:H*.5*sc*(.75+br()*.45),w:dw*.026*sc*(.8+br()*.45),lean:(br()-.5)*.05+s*.012,d:y/H}));
      }
      // shadow and grass where the clump meets the ground
      gg.setTransform(dpr,0,0,dpr,0,0);
      gg.fillStyle="rgba(8,6,4,.45)";gg.beginPath();gg.ellipse(cxk,cy+dw*.01*sc,hw*.2,dw*.04*sc,0,0,7);gg.fill();
      gg.strokeStyle="rgba(42,62,36,.85)";gg.lineWidth=Math.max(1,dw*.008*sc);gg.beginPath();
      for(let b=0;b<9;b++){const gx=cxk+(br()-.5)*hw*.34;gg.moveTo(gx,cy+dw*.015*sc);gg.quadraticCurveTo(gx+(br()-.5)*dw*.05*sc,cy-dw*.04*sc,gx+(br()-.5)*dw*.08*sc,cy-dw*(.05+br()*.05)*sc)}
      gg.stroke();
    }
  }
  // a denser grove just right of the door: close to the path (outside the side wall at 1.2×hw), rising beside the torii
  for(let k=0;k<4;k++){
    const d=.05+k*.085+br()*.03,hw=hwD(d),sc=hw/hw0,cxk=geo.cx+hw*(1.36+br()*.22),cy=yAt(d)+dw*.03*sc,n=3+Math.floor(br()*3);
    for(let j=0;j<n;j++)culms.push(Bamboo.culm(br,{x:cxk+(br()-.3)*hw*.2,y:cy+(br()-.5)*dw*.04*sc,h:H*.62*sc*(.8+br()*.4),w:dw*.026*sc*(.85+br()*.4),lean:(br()-.5)*.04+.01,d:0}));
    gg.setTransform(dpr,0,0,dpr,0,0);
    gg.fillStyle="rgba(8,6,4,.45)";gg.beginPath();gg.ellipse(cxk,cy+dw*.01*sc,hw*.16,dw*.035*sc,0,0,7);gg.fill();
    gg.strokeStyle="rgba(42,62,36,.85)";gg.lineWidth=Math.max(1,dw*.008*sc);gg.beginPath();
    for(let b=0;b<7;b++){const gx=cxk+(br()-.5)*hw*.26;gg.moveTo(gx,cy+dw*.015*sc);gg.quadraticCurveTo(gx+(br()-.5)*dw*.05*sc,cy-dw*.04*sc,gx+(br()-.5)*dw*.08*sc,cy-dw*(.05+br()*.05)*sc)}
    gg.stroke();
  }
  culms.sort((a,b)=>a.y-b.y);                                     // far (higher on screen) first
  // a weeping willow on each side of the torii, rooted on the plateau just outside the pillars
  const wc=scene.querySelector(".willow");wc.width=Math.round(W*dpr);wc.height=Math.round(H*dpr);
  // a small willow grove around the torii: [side, x offset (dojo widths), size, depth offset, seed]; smaller = further back
  const WILLOWS=[[-1,-.64,.64,-.07,305],[1,.66,.62,-.07,306],[-1,-1.62,.84,-.015,303],[1,1.6,.88,-.015,304],[-1,-1.05,1,.03,301],[1,1.05,1,.03,302]];
  const wg=wc.getContext("2d"),willows=WILLOWS.map(([s,x,sc,yo,seed])=>({...Willow.make(seed,s),x,sc,yo}));
  const fg=ts=>{
    wg.setTransform(dpr,0,0,dpr,0,0);wg.clearRect(0,0,W,H);
    for(const w of willows){                                         // listed far to near
      const bx=W/2+w.x*dw,by=yTop+w.yo*dw,U=dw*w.sc;
      wg.fillStyle="rgba(8,6,4,.45)";wg.beginPath();wg.ellipse(bx,by,U*.2,U*.035,0,0,7);wg.fill();
      Willow.draw(wg,w,bx,by,U,ts,w.sc<.8?.35:w.sc<.95?.15:0);        // distant trees fade a little into the night
    }
    bg.setTransform(dpr,0,0,dpr,0,0);bg.clearRect(0,0,W,H);
    for(const c of culms){
      const sw=Math.sin(ts*.9+c.ph)*.6+Math.sin(ts*.37+c.ph*2)*.4;     // gentle, irregular breeze
      const pt=t=>[c.x+c.lean*c.h*t+sw*c.h*.03*t*t,c.y-c.h*t];
      const d=clamp((c.y/H-.6)/.4,0,1);
      Bamboo.draw(bg,c,pt,c.w,ts,`rgb(${Math.round(36+28*d)},${Math.round(54+40*d)},${Math.round(38+20*d)})`,`rgba(${Math.round(22+16*d)},${Math.round(40+26*d)},${Math.round(28+12*d)},.93)`,1);
    }
  };
  const mr=Math.max(12,dw*.15);
  const moon={x:W/2,y:Math.max(mr+8,topT-mr-dw*.1),r:mr};          // centred, just above the torii
  return{u:dw,moon,glows,fg,
    clouds:[["cum",dw*2.4,dw*.8,moon.x-dw*3.1,moon.y+dw*.05,4,.95,11],["cum",dw*2,dw*.62,moon.x+dw*.95,moon.y+dw*.3,3,.85,23],
            ["wisp",dw*2.3,dw*.24,moon.x-dw*1.6,moon.y+mr*.45,5.5,.9,41],["wisp",dw*2.8,dw*.2,moon.x-dw*1.2,moon.y-dw*.55,7,.6,53],
            ["cum",dw*1.7,dw*.5,W*.76,H*.28,2.4,.7,37],["wisp",dw*1.8,dw*.22,W*.02,H*.36,6,.65,67]],
    fog:[[W*.8,dw*.5,-W*.1,H-dw*.3,6,.8,71,0],[W*.7,dw*.42,W*.4,H-dw*.06,-4.5,.75,83,1.7],
         [W*.6,dw*.36,W*.2,yTop-dw*.3,4,.62,97,3.1],[W*.45,dw*.2,W*.55,topT+dw*.45,-6,.45,109,4.4]]};
}

export { crossCfg, doorCfg };
