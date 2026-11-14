// Procedural renderer ported from the Erin Dojo design; keep the drawing maths in sync with it.
import { rng } from "../core/random.js";

/* ================= Weeping willows beside the torii: trunk, arching branches, hanging fronds that sway ================= */
const Willow=(()=>{
  // A steady breeze from the left with rolling gusts. s = side of the torii (-1 left, +1 right); units of U (one dojo width)
  const quad=(p0,p1,p2,u)=>[(1-u)*(1-u)*p0[0]+2*(1-u)*u*p1[0]+u*u*p2[0],(1-u)*(1-u)*p0[1]+2*(1-u)*u*p1[1]+u*u*p2[1]];
  const LEAF=[[40,60,38],[58,84,48],[78,108,60],[112,140,84]];
  function make(seed,s){
    const r=rng(seed),top=[s*.06,-.9],limbs=[],fronds=[];
    for(let b=0;b<8;b++){                                      // limbs arch up and out from the crown
      const a=-.65+b*.25+(r()-.5)*.08;
      const tip=[s*(.06+a*.62),-1.3-.3*Math.cos(a*1.2)+r()*.07];
      limbs.push({mid:[(top[0]+tip[0])/2+s*a*.1,Math.min(top[1],tip[1])-.15-r()*.05],tip,w:.6+r()*.5});
    }
    for(let i=0;i<90;i++){                                     // fronds hang from points along the limbs
      const L=limbs[Math.floor(r()*limbs.length)],p=quad(top,L.mid,L.tip,.3+r()*.7);
      fronds.push({x:p[0]+(r()-.5)*.05,y:p[1]+r()*.05,len:.4+r()*.8,ph:r()*6.28,depth:r(),
        leaves:[...Array(12)].map((_,j)=>({t:.07+j*.075+r()*.03,side:j%2?-1:1,rot:(r()-.5)*.3,c:Math.floor(r()*3)}))});
    }
    fronds.sort((a,b)=>a.depth-b.depth);                       // back fronds first
    return{s,top,limbs,fronds};
  }
  function draw(g,w,bx,by,U,ts,fogA){
    const a=1-(fogA||0)*.7,P=(x,y)=>[bx+x*U,by+y*U];
    const wind=.2+.09*Math.sin(ts*.5)+.04*Math.sin(ts*1.6+1);  // always blowing left → right: strands lean ~15–30°
    // trunk with a flared base and a moonlit edge
    const tt=P(w.top[0],w.top[1]),bend=w.s*.13;
    g.fillStyle=`rgba(32,25,19,${a})`;g.beginPath();
    g.moveTo(bx-.07*U,by);g.quadraticCurveTo(bx-.03*U,by-.08*U,bx-.035*U,by-.18*U);
    g.quadraticCurveTo(bx+(bend-.04)*U,by-.55*U,tt[0]-.024*U,tt[1]);g.lineTo(tt[0]+.024*U,tt[1]);
    g.quadraticCurveTo(bx+(bend+.05)*U,by-.5*U,bx+.04*U,by-.18*U);g.quadraticCurveTo(bx+.035*U,by-.08*U,bx+.08*U,by);g.closePath();g.fill();
    g.strokeStyle=`rgba(150,140,124,${.22*a})`;g.lineWidth=Math.max(.7,U*.007);
    g.beginPath();g.moveTo(bx-.03*U,by-.15*U);g.quadraticCurveTo(bx+(bend-.03)*U,by-.55*U,tt[0]-.014*U,tt[1]);g.stroke();
    // limbs, swaying a little with the gusts
    g.lineCap="round";
    for(const L of w.limbs){
      const s0=tt,m=P(L.mid[0]+wind*.03,L.mid[1]),e=P(L.tip[0]+wind*.05,L.tip[1]);
      g.strokeStyle=`rgba(38,29,21,${a})`;g.lineWidth=Math.max(1,U*.02*L.w);
      g.beginPath();g.moveTo(s0[0],s0[1]);g.quadraticCurveTo(m[0],m[1],e[0],e[1]);g.stroke();
    }
    // fronds: bend downwind more toward the tip, with a gust wave travelling across the crown
    const paths=LEAF.map(()=>new Path2D()),twigs=new Path2D();
    const ll=U*.03,lw=U*.008;
    for(const f of w.fronds){
      const st=P(f.x,f.y),wave=.06*Math.sin(ts*.5-f.x*3.2),ws=wind+wave,pts=[];
      for(let k=0;k<=10;k++){
        const t=k/10,flut=Math.sin(ts*2.4+f.ph+t*3.2)*.018*t;
        pts.push([st[0]+(ws*Math.pow(t,1.4)*f.len+flut+w.s*.02*t)*U, st[1]+f.len*U*t*(1-.12*ws*t)]);
      }
      twigs.moveTo(pts[0][0],pts[0][1]);for(const q of pts)twigs.lineTo(q[0],q[1]);
      const tone=f.depth<.4?0:1;
      for(const lf of f.leaves){
        const fi=lf.t*10,i=Math.min(9,Math.floor(fi)),fr=fi-i,p0=pts[i],p1=pts[i+1];
        const x=p0[0]+(p1[0]-p0[0])*fr,y=p0[1]+(p1[1]-p0[1])*fr;
        const ang=Math.atan2(p1[1]-p0[1],p1[0]-p0[0])+lf.side*.32+lf.rot;     // leaves lie close along the strand
        const cx=x+Math.cos(ang)*ll*.5,cy=y+Math.sin(ang)*ll*.5;
        const pa=paths[Math.min(3,lf.c+tone)];
        pa.moveTo(cx+Math.cos(ang)*ll*.5,cy+Math.sin(ang)*ll*.5);     // start a new shape per leaf so leaves don't join up
        pa.ellipse(cx,cy,ll*.5,lw*.5,ang,0,Math.PI*2);
      }
    }
    g.strokeStyle=`rgba(54,62,38,${.75*a})`;g.lineWidth=Math.max(.5,U*.0035);g.stroke(twigs);
    LEAF.forEach((c,i)=>{g.fillStyle=`rgba(${c[0]},${c[1]},${c[2]},${(i===3?.7:.88)*a})`;g.fill(paths[i])});
  }
  return{make,draw};
})();

export { Willow };
