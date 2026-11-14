// Procedural renderer ported from the Erin Dojo design; keep the drawing maths in sync with it.
import { clamp, rng } from "../core/random.js";
import { REDUCED } from "../core/motion.js";
import { Bamboo } from "./bamboo.js";
import { paintMoon } from "./sky.js";
import { Willow } from "./willow.js";

/* ================= Climb: first-person ascent up the mountain steps ================= */
const Climb=(()=>{
  let raf=0;
  const N=24,D=1,RISE=.52,HALF=1.05,EYE=1.55;
  const FOG=[30,28,40];
  const mix=(c,a)=>`rgb(${Math.round(c[0]+(FOG[0]-c[0])*a)},${Math.round(c[1]+(FOG[1]-c[1])*a)},${Math.round(c[2]+(FOG[2]-c[2])*a)})`;
  const groundAt=z=>clamp(z,0,N*D)*RISE/D;
  function run(cv,dir,done){
    cancelAnimationFrame(raf);
    const dpr=Math.min(window.devicePixelRatio||1,2),W=cv.clientWidth,H=cv.clientHeight;
    cv.width=Math.round(W*dpr);cv.height=Math.round(H*dpr);
    const g=cv.getContext("2d");g.setTransform(dpr,0,0,dpr,0,0);
    // going down, the challenger turns around: the camera faces downhill and tilts down, so the moon and torii are behind them
    const back=dir<0,fz=back?-1:1;
    const pitch=Math.atan(RISE/D)*(back?-.75:.6),cosP=Math.cos(pitch),sinP=Math.sin(pitch);
    const f=Math.min(W,H*1.3)*.85,cx=W/2,cy=H*.55;
    const r=rng(12);
    const items=[];
    for(let i=-6;i<N+2;i++)items.push({t:"step",i,z:i*D+.5});
    for(let z=-4;z<N*D+10;z+=.8+r()*.8)for(const s of [-1,1])if(r()<.8)items.push({t:"tree",x:s*(HALF+3.2+r()*3.4),z:z+r()*.5,h:8+r()*6,c:r()<.5?[18,26,30]:[22,30,34]});
    for(let z=-4;z<N*D+3;z+=.7+r()*.9)for(const s of [-1,1]){          // clumps of 2–4 stalks, uneven distance from the steps
      const cxk=s*(HALF+1.25+r()*r()*2.2),czk=z+r()*.4,n=2+Math.floor(r()*3);   // curb stones end at HALF+0.35
      items.push({t:"tuft",x:cxk,z:czk});
      for(let j=0;j<n;j++)items.push({t:"bamboo",x:cxk+(r()-.5)*.3,z:czk+(r()-.5)*.3,c:Bamboo.culm(r,{h:7+r()*5,w:.06+r()*.05,lean:(r()-.5)*.05})});
    }
    for(let i=2;i<N;i+=3)for(const s of [-1,1])items.push({t:"lamp",x:s*(HALF+.3),z:i*D+.5,i});
    items.push({t:"torii",z:N*D+1.6});
    const climbWillows=[[-1,-.64,.64,-.07,305],[1,.66,.62,-.07,306],[-1,-1.62,.84,-.015,303],[1,1.6,.88,-.015,304],[-1,-1.05,1,.03,301],[1,1.05,1,.03,302]]
      .map(([s,x,sc,yo,seed])=>({...Willow.make(seed,s),x,sc,yo}));
    items.sort((a,b)=>back?a.z-b.z:b.z-a.z);                     // far first, in the direction the camera faces
    // every step is built from individual stones: slabs on the tread, offset blocks on the riser, moss, specks, fallen leaves
    const LAMPZ=[];for(let i=2;i<N;i+=3)LAMPZ.push(i*D+.5);
    const stepData=[];
    for(let i=0;i<N;i++){
      const cuts=(n)=>{const xs=[-HALF];for(let j=1;j<n;j++)xs.push(-HALF+2*HALF*j/n+(r()-.5)*.35);xs.push(HALF);return xs};
      const tx=cuts(2+Math.floor(r()*2)),rx=cuts(2+Math.floor(r()*2));
      stepData.push({
        tread:tx.slice(0,-1).map((x,j)=>({x0:x,x1:tx[j+1],sh:.88+r()*.24})),
        riser:rx.slice(0,-1).map((x,j)=>({x0:x,x1:rx[j+1],sh:.85+r()*.25})),
        specks:[...Array(14)].map(()=>({x:(r()*2-1)*HALF*.95,z:.08+r()*.84,d:r()<.6})),
        moss:[...Array(r()<.7?1+Math.floor(r()*3):0)].map(()=>{const s=r()<.5?-1:1;return{x:s*(HALF-.08-r()*.25),z:.55+r()*.4,rr:.08+r()*.14}}),
        leaves:[...Array(Math.floor(r()*4))].map(()=>({x:(r()*2-1)*HALF*.8,z:.15+r()*.75,rot:r()*3.14,c:r()<.5?[150,124,64]:[118,108,58]})),
        curb:[.85+r()*.25,.85+r()*.25]});
    }
    const warmAt=z=>{let w=0;for(const lz of LAMPZ)w+=Math.exp(-Math.pow(z-lz,2)/1.6);return Math.min(1,w)};
    // granite grey, lightly warmed near lanterns
    const stone=(c,sh,w,a)=>{const t=[c[0]*sh+(255-c[0]*sh)*.12*w,c[1]*sh+(176-c[1]*sh)*.09*w,c[2]*sh+(110-c[2]*sh)*.04*w];return mix(t,a)};
    const stars=[...Array(40)].map(()=>[r()*W,r()*H*.45,r()*1.2+.3]);
    const ridgeP=[...Array(10)].map((_,i)=>[W*i/9,H*(.3+r()*.12)]);
    const T=2900,start=performance.now();
    const zA=dir>0?-2.5:N*D-5.5, zB=dir>0?N*D-5.5:-2.5;

    function P(x,y,z,cam){
      const ry=y-cam.y,rz=(z-cam.z)*fz,yy=ry*cosP-rz*sinP,zz=ry*sinP+rz*cosP;
      return zz<.08?null:[cx+f*(x-cam.x)*fz/zz,cy-f*yy/zz,zz];
    }
    function quad(pts,cam,col){
      const s=pts.map(p=>P(p[0],p[1],p[2],cam));if(s.some(v=>!v))return;
      const a=clamp((s[0][2]-3)/20,0,.88);
      g.beginPath();g.moveTo(s[0][0],s[0][1]);for(let i=1;i<s.length;i++)g.lineTo(s[i][0],s[i][1]);g.closePath();
      g.fillStyle=mix(col,a);g.fill();
    }
    function gpoly(pts,cam,c0,c1){                               // fill with a gradient from the first edge to the opposite edge
      const s=pts.map(q=>P(q[0],q[1],q[2],cam));if(s.some(v=>!v))return null;
      const m0=[(s[0][0]+s[1][0])/2,(s[0][1]+s[1][1])/2],m1=[(s[2][0]+s[3][0])/2,(s[2][1]+s[3][1])/2];
      const gr=g.createLinearGradient(m0[0],m0[1],m1[0],m1[1]);gr.addColorStop(0,c0);gr.addColorStop(1,c1);
      g.beginPath();g.moveTo(s[0][0],s[0][1]);for(let k=1;k<s.length;k++)g.lineTo(s[k][0],s[k][1]);g.closePath();g.fillStyle=gr;g.fill();
      return s;
    }
    function seg(a,b,cam,col,w){const A=P(a[0],a[1],a[2],cam),B=P(b[0],b[1],b[2],cam);if(!A||!B)return;
      g.strokeStyle=col;g.lineWidth=Math.max(.5,w*f/((A[2]+B[2])/2));g.beginPath();g.moveTo(A[0],A[1]);g.lineTo(B[0],B[1]);g.stroke()}
    function blob(x,y,z,rx,ry,rot,col,cam){const c=P(x,y,z,cam);if(!c)return;const k=f/c[2];
      g.fillStyle=col;g.beginPath();g.ellipse(c[0],c[1],Math.max(.5,rx*k),Math.max(.4,ry*k*.45),rot,0,7);g.fill()}
    function frame(now){
      const p=clamp((now-start)/T,0,1),e=p<.5?2*p*p:1-Math.pow(-2*p+2,2)/2;
      const z=zA+(zB-zA)*e,ph=z/D;
      const cam={x:Math.sin(Math.PI*ph)*.04,z,y:groundAt(z)+EYE+Math.abs(Math.sin(Math.PI*ph))*.08};
      // sky, stars, moon, far ridge (moves slowly: it is far away)
      let sg=g.createLinearGradient(0,0,0,H);sg.addColorStop(0,"#0b0f1b");sg.addColorStop(.6,"#262234");sg.addColorStop(1,"#2c2534");
      g.fillStyle=sg;g.fillRect(0,0,W,H);
      g.fillStyle="rgba(255,255,255,.7)";for(const s of stars)g.fillRect(s[0],s[1],s[2],s[2]);
      if(!back){const mr=Math.max(10,Math.min(W,H)*.045);paintMoon(g,W*.5,H*.13,mr)}   // the moon only lies ahead when climbing up
      const shift=(cam.y-EYE)*H*.012;
      g.beginPath();g.moveTo(0,H);for(const q of ridgeP)g.lineTo(q[0],q[1]+shift);g.lineTo(W,H);g.closePath();g.fillStyle="#1a1f30";g.fill();
      // ground plane below the first step and the plateau above the last
      quad([[-60,0,-40],[60,0,-40],[60,0,0],[-60,0,0]],cam,[30,26,24]);   // valley floor at the foot of the steps
      for(const it of items){
        if(it.t==="step"){
          const i=it.i;
          if(i<0||i>=N)continue;                                    // nothing beyond the top step: the plateau starts there
          const y=(i+1)*RISE,z0=i*D,z1=(i+1)*D;
          // side embankment slope under the trees
          quad([[-30,i*RISE,z0],[-HALF-.35,i*RISE,z0],[-HALF-.35,y,z1],[-30,y,z1]],cam,[26,30,28]);
          quad([[HALF+.35,i*RISE,z0],[30,i*RISE,z0],[30,y,z1],[HALF+.35,y,z1]],cam,[26,30,28]);
          const S=stepData[i],mid=P(0,y,z0+.5,cam);if(!mid)continue;
          const a=clamp((mid[2]-3)/20,0,.88),wm=warmAt(z0+.5),y0=i*RISE;
          // riser: offset blocks, dark under the nosing, lighter toward the bottom (faces away when walking down)
          if(!back)for(const b of S.riser){
            gpoly([[b.x0,y,z0],[b.x1,y,z0],[b.x1,y0,z0],[b.x0,y0,z0]],cam,stone([38,37,36],b.sh,wm,a),stone([72,70,67],b.sh,wm,a));
            if(b.x0>-HALF)seg([b.x0,y-.03,z0],[b.x0,y0,z0],cam,`rgba(14,11,9,${.7*(1-a)})`,.012);
          }
          // tread: slabs, shaded from the worn front edge to the back where it meets the next riser
          for(const b of S.tread){
            gpoly([[b.x0,y,z0],[b.x1,y,z0],[b.x1,y,z1],[b.x0,y,z1]],cam,stone([128,126,121],b.sh,wm,a),stone([76,74,71],b.sh,wm,a));
            if(b.x0>-HALF)seg([b.x0,y,z0],[b.x0,y,z1],cam,`rgba(18,14,11,${.65*(1-a)})`,.012);
          }
          if(a<.85){
            for(const s of S.specks)blob(s.x,y,z0+s.z,.018,.018,0,s.d?`rgba(30,26,22,${.35*(1-a)})`:`rgba(190,182,168,${.22*(1-a)})`,cam);
            for(const m of S.moss)blob(m.x,y,z0+m.z,m.rr,m.rr*.8,0,`rgba(64,92,48,${.55*(1-a)})`,cam);
            for(const l of S.leaves)blob(l.x,y,z0+l.z,.07,.018,l.rot,`rgba(${l.c[0]},${l.c[1]},${l.c[2]},${.75*(1-a)})`,cam);
          }
          // worn nosing highlight, and the contact shadow where the riser meets the step below
          seg([-HALF,y,z0],[HALF,y,z0],cam,`rgba(232,222,204,${(.32+.2*wm)*(1-a)})`,.014);
          if(!back)seg([-HALF,y0+.01,z0],[HALF,y0+.01,z0],cam,`rgba(10,8,6,${.6*(1-a)})`,.02);
          // curb stones: separate blocks with a dark gap between them
          for(const s of [-1,1]){
            const sh=S.curb[s<0?0:1],za=z0+.03,zb=z1-.03;
            gpoly([[s*HALF,y,za],[s*HALF,y,zb],[s*HALF,y+.28,zb],[s*HALF,y+.28,za]],cam,stone([38,37,36],sh,wm,a),stone([64,62,59],sh,wm,a));
            gpoly([[s*HALF,y+.28,za],[s*(HALF+.35),y+.28,za],[s*(HALF+.35),y+.28,zb],[s*HALF,y+.28,zb]],cam,stone([108,105,100],sh,wm,a),stone([80,78,74],sh,wm,a));
            const ox=s*(HALF+.35),ga=y0+(za-z0)*RISE,gb=y0+(zb-z0)*RISE;   // outer face down to the sloping bank: a solid block
            gpoly([[ox,y+.28,za],[ox,y+.28,zb],[ox,gb,zb],[ox,ga,za]],cam,stone([58,56,53],sh,wm,a),stone([30,29,28],sh,wm,a));
            gpoly([[s*HALF,y+.28,za],[ox,y+.28,za],[ox,ga,za],[s*HALF,y,za]],cam,stone([70,68,64],sh,wm,a),stone([44,42,40],sh,wm,a));
            seg([s*HALF,y+.28,za],[ox,y+.28,za],cam,`rgba(220,210,192,${.22*(1-a)})`,.01);
          }
          if(i===N-1)quad([[-30,N*RISE,N*D],[30,N*RISE,N*D],[30,N*RISE,N*D+40],[-30,N*RISE,N*D+40]],cam,[34,30,28]);
        }else if(it.t==="tree"){
          const b=groundAt(it.z),base=P(it.x,b,it.z,cam);if(!base)continue;
          const k=f/base[2],a=clamp((base[2]-3)/20,0,.9)*.55;      // trees stay dark silhouettes in the mist
          g.fillStyle=mix([34,24,18],a);g.fillRect(base[0]-.12*k,base[1]-it.h*.35*k,.24*k,it.h*.35*k+1);
          g.fillStyle=mix(it.c,a);
          for(let t=0;t<5;t++){const y0=base[1]-it.h*k*(.25+t*.15),w=it.h*k*(.17-t*.028);
            g.beginPath();g.moveTo(base[0],y0-it.h*k*.24);g.lineTo(base[0]+w,y0);g.lineTo(base[0]-w,y0);g.closePath();g.fill()}
        }else if(it.t==="tuft"){
          const b=P(it.x,groundAt(it.z),it.z,cam);if(!b||b[2]<1.1)continue;
          const k=f/b[2],a=clamp((b[2]-3)/20,0,.9)*.6;
          g.fillStyle="rgba(6,5,4,.5)";g.beginPath();g.ellipse(b[0],b[1],.35*k,.08*k,0,0,7);g.fill();
          g.strokeStyle=mix([40,60,34],a);g.lineWidth=Math.max(.6,.025*k);g.beginPath();
          for(let q=0;q<7;q++){const gx=b[0]+(q-3)*.07*k;g.moveTo(gx,b[1]);g.quadraticCurveTo(gx+.04*k*(q%2?1:-1),b[1]-.12*k,gx+.09*k*(q-3)/3,b[1]-.2*k)}
          g.stroke();
        }else if(it.t==="bamboo"){
          const b=groundAt(it.z)+.1,c=it.c,ts=now/1000,base=P(it.x,b,it.z,cam);if(!base||base[2]<1.1)continue;   // already beside the viewer
          const near=Math.exp(-Math.pow(it.z-cam.z,2)/3);              // stalks you brush past bend more
          const sw=Math.sin(ts*1.6+c.ph)*(.18+.5*near)+Math.sin(ts*.6+c.ph*2)*.12;
          const pt=t=>{const q=P(it.x+c.lean*c.h*t+sw*t*t,b+c.h*t,it.z,cam);return q&&q[2]>.8?[q[0],q[1]]:null};
          const a=clamp((base[2]-3)/20,0,.9)*.6,w=f*c.w/base[2];
          Bamboo.draw(g,c,pt,w,ts,mix([62,92,56],a),mix([30,52,34],a),1+near*2);
        }else if(it.t==="lamp"){
          const y=(it.i+1)*RISE+.28,b=P(it.x,y,it.z,cam);if(!b)continue;
          const k=f/b[2],s=1.1*k,a=clamp((b[2]-3)/24,0,.85);
          const gr=g.createRadialGradient(b[0],b[1]-s*.68,0,b[0],b[1]-s*.68,s*1.1);
          gr.addColorStop(0,`rgba(255,170,80,${.2*(1-a)})`);gr.addColorStop(1,"rgba(255,170,80,0)");
          g.fillStyle=gr;g.fillRect(b[0]-s*1.1,b[1]-s*1.78,s*2.2,s*2.2);
          g.fillStyle=mix([90,86,80],a);g.fillRect(b[0]-s*.07,b[1]-s*.5,s*.14,s*.5);g.fillRect(b[0]-s*.17,b[1]-s*.56,s*.34,s*.06);
          g.fillStyle=`rgba(255,${Math.round(200-a*60)},${Math.round(120-a*40)},${1-a*.6})`;g.fillRect(b[0]-s*.12,b[1]-s*.8,s*.24,s*.24);
          g.fillStyle=mix([84,80,75],a);g.beginPath();g.moveTo(b[0],b[1]-s*1.02);g.lineTo(b[0]+s*.26,b[1]-s*.82);g.lineTo(b[0]-s*.26,b[1]-s*.82);g.closePath();g.fill();
        }else if(it.t==="torii"){
          const y=N*RISE,z0=it.z;
          for(const w of climbWillows){                               // the same grove around the torii, far trees first
            const b=P(w.x*2.05,y,z0+.2-w.yo*6,cam);if(!b)continue;
            Willow.draw(g,w,b[0],b[1],2.05*w.sc*f/b[2],now/1000,clamp((b[2]-3)/20,0,.9));
          }
          const red=[196,65,42],blk=[16,12,10];
          for(const s of [-1,1])quad([[s*1.25-.13,y,z0],[s*1.25+.13,y,z0],[s*1.2+.11,y+3.1,z0],[s*1.2-.11,y+3.1,z0]],cam,red);
          quad([[-1.6,y+2.35,z0],[1.6,y+2.35,z0],[1.6,y+2.55,z0],[-1.6,y+2.55,z0]],cam,red);
          quad([[-1.75,y+2.9,z0],[1.75,y+2.9,z0],[1.75,y+3.1,z0],[-1.75,y+3.1,z0]],cam,red);
          quad([[-2.05,y+3.32,z0],[-1.8,y+3.1,z0],[1.8,y+3.1,z0],[2.05,y+3.32,z0],[0,y+3.26,z0]],cam,blk);
        }
      }
      // breath of mist and a vignette
      const vg=g.createRadialGradient(cx,H*.55,Math.min(W,H)*.3,cx,H*.55,Math.max(W,H)*.75);
      vg.addColorStop(0,"rgba(0,0,0,0)");vg.addColorStop(1,"rgba(0,0,0,.55)");g.fillStyle=vg;g.fillRect(0,0,W,H);
      if(p>.82){g.fillStyle=`rgba(14,11,9,${(p-.82)/.18})`;g.fillRect(0,0,W,H)}     // fade out into the arrival
      if(p<1&&cv.isConnected)raf=requestAnimationFrame(frame);else if(cv.isConnected)done();
    }
    if(REDUCED){done();return}
    raf=requestAnimationFrame(frame);
  }
  return{run,stop:()=>cancelAnimationFrame(raf)};
})();

export { Climb };
