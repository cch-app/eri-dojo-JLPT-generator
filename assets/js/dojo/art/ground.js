// Procedural renderer ported from the Erin Dojo design; keep the drawing maths in sync with it.
import { rng } from "../core/random.js";

/* ================= Dojo grounds: mountains, cedar forest, stone wall and 3D stone stairs ================= */
const Ground=(()=>{
  let noise=null;
  function grain(){                       // small noise tile used as stone texture
    if(noise)return noise;
    const c=document.createElement("canvas");c.width=c.height=96;
    const g=c.getContext("2d"),img=g.createImageData(96,96),r=rng(99);
    for(let i=0;i<img.data.length;i+=4){const v=r()*255;img.data[i]=img.data[i+1]=img.data[i+2]=v;img.data[i+3]=38}
    g.putImageData(img,0,0);return noise=c;
  }
  function poly(g,pts,fill){g.beginPath();g.moveTo(pts[0][0],pts[0][1]);for(let i=1;i<pts.length;i++)g.lineTo(pts[i][0],pts[i][1]);g.closePath();g.fillStyle=fill;g.fill()}
  function ridge(g,W,base,amp,seed,fill,rim){
    const r=rng(seed),n=9,pts=[];
    for(let i=0;i<=n;i++)pts.push([W*i/n,base-amp*(.35+.65*r())]);
    g.beginPath();g.moveTo(0,base+amp);g.lineTo(pts[0][0],pts[0][1]);
    for(let i=1;i<pts.length;i++){const p=pts[i-1],q=pts[i];g.quadraticCurveTo(p[0]+(q[0]-p[0])*.5,Math.min(p[1],q[1])-amp*.12,q[0],q[1])}
    g.lineTo(W,base+amp*3);g.lineTo(0,base+amp*3);g.closePath();g.fillStyle=fill;g.fill();
    if(rim){g.strokeStyle=rim;g.lineWidth=1;g.stroke()}
  }
  function cedar(g,x,base,h,col){
    g.fillStyle="#140f0c";g.fillRect(x-h*.025,base-h*.3,h*.05,h*.3);
    for(let t=0;t<5;t++){const y0=base-h*(.22+t*.16),w=h*(.2-t*.034);
      poly(g,[[x,y0-h*.26],[x+w,y0],[x-w,y0]],col)}
  }
  function lantern(g,x,yBase,s){              // stone tōrō, s = height in px
    g.fillStyle="#4a4641";g.fillRect(x-s*.2,yBase-s*.08,s*.4,s*.08);
    g.fillStyle="#5d5953";g.fillRect(x-s*.07,yBase-s*.5,s*.14,s*.42);
    g.fillStyle="#4a4641";g.fillRect(x-s*.17,yBase-s*.56,s*.34,s*.06);
    const fb=g.createRadialGradient(x,yBase-s*.68,0,x,yBase-s*.68,s*.14);
    fb.addColorStop(0,"#fff2c8");fb.addColorStop(1,"#e0883a");
    g.fillStyle=fb;g.fillRect(x-s*.12,yBase-s*.8,s*.24,s*.24);
    g.strokeStyle="#47433e";g.lineWidth=Math.max(1,s*.03);g.strokeRect(x-s*.12,yBase-s*.8,s*.24,s*.24);
    poly(g,[[x,yBase-s*1.02],[x+s*.26,yBase-s*.84],[x+s*.22,yBase-s*.79],[x-s*.22,yBase-s*.79],[x-s*.26,yBase-s*.84]],"#5a5650");
    return{x,y:yBase-s*.68};
  }

  function paint(cv,W,H,dw,yTop){
    const dpr=Math.min(window.devicePixelRatio||1,2);
    cv.width=Math.round(W*dpr);cv.height=Math.round(H*dpr);
    const g=cv.getContext("2d");g.setTransform(dpr,0,0,dpr,0,0);g.clearRect(0,0,W,H);
    const cx=W/2, r=rng(5), tex=g.createPattern(grain(),"repeat");

    // distant ranges and the cedar forest behind the dojo
    ridge(g,W,yTop-dw*.72,dw*.34,3,"#1a2032","rgba(170,182,214,.22)");
    ridge(g,W,yTop-dw*.36,dw*.24,8,"#141924","rgba(150,160,190,.14)");
    for(let x=-10;x<W+20;x+=dw*(.16+r()*.14)){
      const away=Math.abs(x-cx);if(away<dw*.95)continue;           // keep the dojo clear
      const h=dw*(.55+r()*.6)*(away<dw*1.6?.7:1);
      cedar(g,x,yTop+dw*.04,h,r()<.5?"#0f141b":"#121821");
    }
    // plateau edge, lit from the moon
    let lg=g.createLinearGradient(0,yTop-dw*.06,0,yTop+dw*.06);
    lg.addColorStop(0,"#3a332d");lg.addColorStop(1,"#26201b");
    g.fillStyle=lg;g.fillRect(0,yTop-dw*.04,W,dw*.1);

    // geometry of the stairs: narrow at the top, wide at the viewer
    const N=Math.max(7,Math.round((H-yTop)/(dw*.17))), hwTop=dw*.66, hwBot=Math.max(dw*1.55,W*.2);
    const wall=yTop+dw*.06;
    // bands: heights grow toward the viewer (perspective)
    const q=1.16;let sum=0;const hs=[];for(let i=0;i<N;i++){hs.push(Math.pow(q,i));sum+=hs[i]}
    const ys=[wall];for(let i=0;i<N;i++)ys.push(ys[i]+(H-wall)*hs[i]/sum);
    const hwAt=i=>hwTop+(hwBot-hwTop)*Math.pow(i/N,1.05);
    const side=hw=>hw*.2;                                         // width of the flanking stone walls

    // earthen bank on both sides of the stairs: the ground the bamboo grows from
    g.save();
    g.beginPath();g.rect(0,wall,W,H-wall);
    g.moveTo(cx-hwTop-side(hwTop),wall);g.lineTo(cx-hwBot-side(hwBot),H);g.lineTo(cx+hwBot+side(hwBot),H);g.lineTo(cx+hwTop+side(hwTop),wall);g.closePath();
    g.clip("evenodd");
    lg=g.createLinearGradient(0,wall,0,H);lg.addColorStop(0,"#2a241d");lg.addColorStop(.5,"#211c16");lg.addColorStop(1,"#17130f");
    g.fillStyle=lg;g.fillRect(0,wall,W,H-wall);
    g.fillStyle=tex;g.fillRect(0,wall,W,H-wall);
    // fallen leaves and low undergrowth, smaller and denser toward the dojo (farther away)
    for(let k=0;k<420;k++){
      const d=Math.pow(r(),.8),y=wall+(H-wall)*d,s=dw*(.03+.09*d)*(.6+r()*.8),x=r()*W;
      if(Math.abs(x-cx)<(hwTop+(hwBot-hwTop)*d)*1.2)continue;
      if(r()<.55){g.fillStyle=`rgba(${70+r()*40|0},${58+r()*30|0},${36+r()*16|0},${.25+r()*.3})`;g.beginPath();g.ellipse(x,y,s*.5,s*.18,r()*3,0,7);g.fill()}
      else{g.strokeStyle=`rgba(${34+r()*20|0},${52+r()*24|0},${30+r()*14|0},.8)`;g.lineWidth=Math.max(1,s*.12);
        g.beginPath();for(let b=0;b<4;b++){g.moveTo(x+b*s*.15,y);g.quadraticCurveTo(x+b*s*.15+(r()-.5)*s*.4,y-s*.5,x+b*s*.15+(r()-.5)*s*.7,y-s*(.7+r()*.5))}g.stroke()}
    }
    g.restore();

    // steps, far (top) to near (bottom): a tread (top face) then a riser (front face)
    const lamps=[];
    for(let i=0;i<N;i++){
      const y0=ys[i],y1=ys[i+1],band=y1-y0;
      const tf=.24+.16*(i/N);                                     // treads show more as they come closer
      const yt=y0+band*tf, hb=hwAt(i), hf=hwAt(i+1);
      // tread: back edge narrower than front edge
      const tg=g.createLinearGradient(0,y0,0,yt);
      tg.addColorStop(0,"#5d564e");tg.addColorStop(1,"#8f877c");
      poly(g,[[cx-hb,y0],[cx+hb,y0],[cx+hf,yt],[cx-hf,yt]],tg);
      // riser: vertical face, constant width
      const rg=g.createLinearGradient(0,yt,0,y1);
      rg.addColorStop(0,"#3b352f");rg.addColorStop(.25,"#4f4841");rg.addColorStop(1,"#5a524a");
      poly(g,[[cx-hf,yt],[cx+hf,yt],[cx+hf,y1],[cx-hf,y1]],rg);
      // block joints on the riser, offset per step
      g.strokeStyle="rgba(20,16,12,.55)";g.lineWidth=Math.max(1,dw*.01);
      const blocks=3+(i%2);let jx=cx-hf+hf*2*(.12+r()*.1);
      for(let b=1;b<blocks;b++){g.beginPath();g.moveTo(jx,yt+1);g.lineTo(jx,y1);g.stroke();jx+=hf*2/blocks*(.8+r()*.4)}
      // worn nosing highlight + shadow under it
      g.strokeStyle="rgba(235,225,205,.35)";g.lineWidth=Math.max(1,band*.05);
      g.beginPath();g.moveTo(cx-hf,yt);g.lineTo(cx+hf,yt);g.stroke();
      // side walls (sode-ishigaki): cap stone top + inner face
      for(const s of [-1,1]){
        const ib=cx+s*hb, ifr=cx+s*hf, ob=ib+s*side(hb), of=ifr+s*side(hf), lift=band*.55;
        poly(g,[[ib,y0-lift*.8],[ob,y0-lift*.8],[of,y1-lift],[ifr,y1-lift]],"#6e675e");        // cap
        poly(g,[[ib,y0-lift*.8],[ifr,y1-lift],[ifr,y1],[ib,y0]],"#3a342e");                    // inner face
        if(r()<.35){g.fillStyle="rgba(78,104,58,.45)";g.beginPath();g.ellipse((ob+of)/2,(y0+y1)/2-lift,side(hf)*.35,band*.12,0,0,7);g.fill()}
      }
      if(i===Math.round(N*.25)||i===Math.round(N*.6)||i===N-2)lamps.push({i,yb:y1-band*.55,hf});
    }
    g.fillStyle=tex;g.globalAlpha=.8;
    g.beginPath();g.moveTo(cx-hwTop,wall);g.lineTo(cx+hwTop,wall);g.lineTo(cx+hwBot,H);g.lineTo(cx-hwBot,H);g.closePath();g.fill();
    g.globalAlpha=1;

    // stone lanterns on the side walls
    const glows=[];
    for(const L of lamps){
      const s=dw*.42*(.55+.7*L.i/N);
      for(const sd of [-1,1]){const p=lantern(g,cx+sd*(L.hf+side(L.hf)*.5),L.yb,s);glows.push({x:p.x,y:p.y,r:s*1.6})}
    }
    // warm light pooling on stone, cool moonlight from the upper left, darker foreground
    g.globalCompositeOperation="lighter";
    for(const p of glows){const gr=g.createRadialGradient(p.x,p.y,0,p.x,p.y,p.r*1.6);gr.addColorStop(0,"rgba(255,160,70,.22)");gr.addColorStop(1,"rgba(255,160,70,0)");g.fillStyle=gr;g.fillRect(p.x-p.r*1.6,p.y-p.r*1.6,p.r*3.2,p.r*3.2)}
    g.globalCompositeOperation="source-over";
    for(const p of glows){const gr=g.createRadialGradient(p.x,p.y,0,p.x,p.y,p.r*.5);gr.addColorStop(0,"rgba(255,220,150,.55)");gr.addColorStop(1,"rgba(255,200,120,0)");g.fillStyle=gr;g.fillRect(p.x-p.r*.5,p.y-p.r*.5,p.r,p.r)}
    lg=g.createLinearGradient(0,yTop,0,H);lg.addColorStop(0,"rgba(8,8,14,0)");lg.addColorStop(1,"rgba(8,8,14,.45)");
    g.fillStyle=lg;g.fillRect(0,yTop,W,H-yTop);
    return{glows,geo:{cx,ys,hwAt,N,side}};
  }
  return{paint};
})();

export { Ground };
