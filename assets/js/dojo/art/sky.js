// Procedural renderer ported from the Erin Dojo design; keep the drawing maths in sync with it.
import { rng } from "../core/random.js";
import { REDUCED } from "../core/motion.js";

/* Night sky: moon + drifting clouds + ground mist. */
/* Each scene passes a config function: (W,H,sceneEl,sceneRect) → {u, moon:{x,y,r}, clouds, fog, glows}.
   clouds: [kind,width,height,left x,centre y,speed px/s,opacity,seed]   fog: [width,height,left x,centre y,speed,opacity,seed,phase] */
const Sky=(()=>{
  let scene,cfgFn,cv,ctx,layer,lctx,mv,mctx,ro,raf=0,t0=0,lastDraw=0;
  let W=0,H=0,dpr=1,u=100,moon={x:0,y:0,r:20},clouds=[],fog=[],glows=[],fg=null;
  const TONE={cum:[118,124,148,80,72,52,.6],wisp:[118,124,148,80,72,52,.6],fog:[148,154,176,56,52,40,.3]};

  // Paint one cloud into its own small canvas once; frames only move it.
  function sprite(w,h,kind,seed){
    const r=rng(seed), pad=Math.ceil(h*.7);
    const c=document.createElement("canvas");
    c.width=Math.ceil((w+pad*2)*dpr);c.height=Math.ceil((h+pad*2)*dpr);
    const g=c.getContext("2d");g.scale(dpr,dpr);g.translate(pad,pad);
    const n=kind==="wisp"?30:kind==="fog"?64:46, tone=TONE[kind];
    for(let i=0;i<n;i++){
      const uu=kind==="fog"?r():(r()+r())/2;
      const x=w*(.08+.84*uu), centre=1-Math.abs(uu-.5)*2;
      let rx,ry,y,a;
      if(kind==="wisp"){rx=w*(.07+.09*r());ry=h*(.32+.2*r());y=h*(.5+(r()-.5)*.35);a=.09+.05*r();}
      else if(kind==="fog"){rx=w*(.05+.07*r());ry=h*(.28+.22*r());y=h*(.55+(r()-.5)*.4);a=.07+.05*r();}
      else{const rad=h*(.2+.3*centre)*(.7+.45*r());rx=rad*1.15;ry=rad*.8;y=h*(.66-.32*centre*r());a=.11+.06*r();}
      const top=1-y/h;
      const cr=Math.round(tone[0]+tone[3]*top),cg=Math.round(tone[1]+tone[4]*top),cb=Math.round(tone[2]+tone[5]*top);
      g.save();g.translate(x,y);g.scale(1,ry/rx);
      const grd=g.createRadialGradient(0,-rx*.25,0,0,0,rx);
      grd.addColorStop(0,`rgba(${cr},${cg},${cb},${a})`);
      grd.addColorStop(.55,`rgba(${cr},${cg},${cb},${a*.65})`);
      grd.addColorStop(1,`rgba(${cr},${cg},${cb},0)`);
      g.fillStyle=grd;g.beginPath();g.arc(0,0,rx,0,Math.PI*2);g.fill();g.restore();
    }
    g.globalCompositeOperation="source-atop";
    const sh=g.createLinearGradient(0,-pad,0,h+pad);
    sh.addColorStop(.35,"rgba(16,18,30,0)");sh.addColorStop(1,`rgba(16,18,30,${tone[6]})`);
    g.fillStyle=sh;g.fillRect(-pad,-pad,w+pad*2,h+pad*2);
    return{img:c,pad};
  }

  function layout(){
    const sr=scene.getBoundingClientRect();
    W=scene.clientWidth;H=scene.clientHeight;if(!W||!H)return;
    dpr=Math.min(window.devicePixelRatio||1,2);
    for(const c of [cv,layer,mv]){c.width=Math.round(W*dpr);c.height=Math.round(H*dpr)}
    const c=cfgFn(W,H,scene,sr);
    u=c.u;moon=c.moon;const k=u/180;
    clouds=c.clouds.map(([kind,w,h,x,yc,v,a,seed])=>({...sprite(w,h,kind,seed),w,h,x0:x,y:Math.max(-h*.15,yc-h/2),v:v*k,a}));
    fog=c.fog.map(([w,h,x,yc,v,a,seed,ph])=>({...sprite(w,h,"fog",seed),w,h,x0:x,y:yc-h/2,v:v*k,a,ph}));
    glows=c.glows||[];fg=c.fg||null;
    draw(performance.now());
  }

  function draw(now){
    const ts=REDUCED?0:(now-t0)/1000, {x:mx,y:my,r:mr}=moon;
    lctx.setTransform(dpr,0,0,dpr,0,0);lctx.clearRect(0,0,W,H);
    lctx.globalCompositeOperation="source-over";
    for(const c of clouds){
      const span=W+c.w+c.pad*2;
      const x=((c.x0+c.v*ts+c.w+c.pad)%span+span)%span-c.w-c.pad;
      lctx.globalAlpha=c.a;
      lctx.drawImage(c.img,x-c.pad,c.y-c.pad,c.w+c.pad*2,c.h+c.pad*2);
    }
    lctx.globalAlpha=1;
    lctx.globalCompositeOperation="source-atop";       // moonlight on nearby cloud edges
    const lit=lctx.createRadialGradient(mx,my,mr*.6,mx,my,mr*6);
    lit.addColorStop(0,"rgba(255,244,220,.75)");lit.addColorStop(.35,"rgba(240,230,210,.28)");lit.addColorStop(1,"rgba(240,230,210,0)");
    lctx.fillStyle=lit;lctx.fillRect(0,0,W,H);
    lctx.globalCompositeOperation="source-over";

    ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,W,H);
    let g=ctx.createRadialGradient(mx,my,mr,mx,my,mr*9);
    g.addColorStop(0,"rgba(239,230,210,.22)");g.addColorStop(.3,"rgba(200,195,200,.08)");g.addColorStop(1,"rgba(200,195,200,0)");
    ctx.fillStyle=g;ctx.fillRect(0,0,W,H);
    paintMoon(ctx,mx,my,mr);
    ctx.drawImage(layer,0,0,W,H);

    mctx.setTransform(dpr,0,0,dpr,0,0);mctx.clearRect(0,0,W,H);
    for(const f of fog){
      const span=W+f.w+f.pad*2;
      const x=((f.x0+f.v*ts+f.w+f.pad)%span+span)%span-f.w-f.pad;
      const y=f.y+Math.sin(ts*.25+f.ph)*u*.03;
      mctx.globalAlpha=f.a;
      mctx.drawImage(f.img,x-f.pad,y-f.pad,f.w+f.pad*2,f.h+f.pad*2);
    }
    mctx.globalAlpha=1;mctx.globalCompositeOperation="source-atop";   // lanterns warm the mist around them
    for(const p of glows){
      const gr=mctx.createRadialGradient(p.x,p.y,0,p.x,p.y,p.r);
      gr.addColorStop(0,"rgba(255,186,110,.6)");gr.addColorStop(1,"rgba(255,186,110,0)");
      mctx.fillStyle=gr;mctx.fillRect(p.x-p.r,p.y-p.r,p.r*2,p.r*2);
    }
    mctx.globalCompositeOperation="source-over";
    if(fg)fg(ts);
  }

  function loop(now){
    if(!cv||!cv.isConnected){stop();return}
    raf=requestAnimationFrame(loop);
    if(document.hidden||now-lastDraw<40)return;
    lastDraw=now;draw(now);
  }
  function mount(el,cfg){
    stop();
    scene=el;cfgFn=cfg;
    cv=el.querySelector(".sky");ctx=cv.getContext("2d");
    mv=el.querySelector(".mist");mctx=mv.getContext("2d");
    layer=document.createElement("canvas");lctx=layer.getContext("2d");
    t0=performance.now();
    layout();
    ro=new ResizeObserver(()=>layout());ro.observe(scene);
    if(!REDUCED)raf=requestAnimationFrame(loop);
  }
  function stop(){cancelAnimationFrame(raf);raf=0;if(ro){ro.disconnect();ro=null}}
  return{mount,stop};
})();

function paintMoon(c,mx,my,mr){
  let g=c.createRadialGradient(mx-mr*.3,my-mr*.3,mr*.1,mx,my,mr);
  g.addColorStop(0,"#fbf5e6");g.addColorStop(1,"#e4d9bf");
  c.fillStyle=g;c.beginPath();c.arc(mx,my,mr,0,Math.PI*2);c.fill();
  c.save();c.clip();
  for(const [dx,dy,rr] of [[-.3,-.15,.32],[.25,.2,.26],[.1,-.4,.18],[-.15,.4,.2]]){
    const m=c.createRadialGradient(mx+dx*mr,my+dy*mr,0,mx+dx*mr,my+dy*mr,rr*mr);
    m.addColorStop(0,"rgba(180,168,145,.32)");m.addColorStop(1,"rgba(180,168,145,0)");
    c.fillStyle=m;c.fillRect(mx-mr,my-mr,mr*2,mr*2);
  }
  c.restore();
}

export { Sky, paintMoon };
