// Procedural renderer ported from the Erin Dojo design; keep the drawing maths in sync with it.
/* ================= Bamboo: segmented stalks with node rings and drooping leaves that sway ================= */
const Bamboo=(()=>{
  function culm(r,opt){
    const nodes=7+Math.floor(r()*3),leaves=[];
    for(let n=Math.floor(nodes*.45);n<=nodes;n++){
      const cnt=r()<.65?2+Math.floor(r()*3):0;
      for(let j=0;j<cnt;j++)leaves.push({t:n/nodes,a:(r()<.5?-1:1)*(.45+r()*1),len:.6+r()*.6,ph:r()*6.28});
    }
    return{...opt,nodes,leaves,ph:r()*6.28};
  }
  // pt(t) maps 0..1 along the stalk to a screen point; w is the base width in px
  function draw(g,c,pt,w,ts,col,leafCol,flutter){
    const K=c.nodes;
    for(let k=0;k<K;k++){
      const a=pt(k/K),b=pt((k+1)/K);if(!a||!b)return;
      const lw=Math.max(.6,w*(1-.45*k/K));
      g.strokeStyle=col;g.lineWidth=lw;g.lineCap="butt";
      g.beginPath();g.moveTo(a[0],a[1]);g.lineTo(b[0],b[1]);g.stroke();
      g.strokeStyle="rgba(190,214,170,.22)";g.lineWidth=Math.max(.4,lw*.22);      // moonlit edge
      g.beginPath();g.moveTo(a[0]-lw*.28,a[1]);g.lineTo(b[0]-lw*.28,b[1]);g.stroke();
      g.strokeStyle="rgba(210,228,190,.35)";g.lineWidth=Math.max(.5,lw*.2);       // node ring
      g.beginPath();g.moveTo(b[0]-lw*.62,b[1]);g.lineTo(b[0]+lw*.62,b[1]);g.stroke();
    }
    g.fillStyle=leafCol;
    for(const L of c.leaves){
      const p=pt(L.t);if(!p)continue;
      const ang=L.a+Math.sin(ts*2.3+L.ph)*.2*flutter,len=w*9*L.len;
      const dx=Math.sin(ang)*len,dy=Math.abs(Math.cos(ang))*len*.5+len*.28;
      g.beginPath();g.moveTo(p[0],p[1]);
      g.quadraticCurveTo(p[0]+dx*.5-dy*.14,p[1]+dy*.5-len*.1,p[0]+dx,p[1]+dy);
      g.quadraticCurveTo(p[0]+dx*.5+dy*.14,p[1]+dy*.5+len*.05,p[0],p[1]);g.fill();
    }
  }
  return{culm,draw};
})();

export { Bamboo };
