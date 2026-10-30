/* Original, dependency-free isometric scene. Illustrative geometry, not a surveyed digital twin. */
window.SolumScene = class {
 constructor(canvas,options={}) {
  this.canvas=canvas;this.ctx=canvas.getContext('2d');this.chapter=options.chapter||'flood';this.mode='3d';this.level=options.level??.36;this.angle=0;this.zoom=1;this.playing=!matchMedia('(prefers-reduced-motion: reduce)').matches;this.t=0;this.last=0;this.drag=null;
  this.buildings=[];for(let x=0;x<9;x++)for(let y=0;y<8;y++){if(x===4||y===3||y===6||(x>6&&y>4))continue;const seed=(x*17+y*31)%13;this.buildings.push({x:x*45-190,y:y*45-155,w:23+seed%3*3,d:23,h:22+seed*4,color:seed%4===0?'#c0d8c5':'#f0f4e9'});}
  canvas.addEventListener('keydown',e=>{if(e.key==='ArrowLeft'||e.key==='ArrowRight'){e.preventDefault();this.angle+=e.key==='ArrowLeft'?-.12:.12;this.draw()}});
  this.inView=true;if(typeof IntersectionObserver!=='undefined'){new IntersectionObserver(entries=>{this.inView=entries[0].isIntersecting}).observe(canvas);}
  this.resize=new ResizeObserver(()=>this.draw());this.resize.observe(canvas);
  canvas.addEventListener('pointerdown',e=>{this.drag={x:e.clientX,a:this.angle};canvas.setPointerCapture(e.pointerId)});canvas.addEventListener('pointermove',e=>{if(this.drag){this.angle=this.drag.a+(e.clientX-this.drag.x)/300;this.draw()}});canvas.addEventListener('pointerup',()=>this.drag=null);canvas.addEventListener('pointercancel',()=>this.drag=null);
  const tick=(now)=>{if(!this.canvas.isConnected)return;if(this.playing&&this.inView&&document.visibilityState==='visible'&&now-this.last>40){this.t+=.025;this.last=now;this.draw()}requestAnimationFrame(tick)};requestAnimationFrame(tick);this.draw();
 }
 setChapter(ch){this.chapter=ch;this.t=0;this.draw()}
 setMode(m){this.mode=m;this.draw()}
 setLevel(v){this.level=v;this.draw()}
 project(x,y,z=0){const a=this.angle;const xx=x*Math.cos(a)-y*Math.sin(a), yy=x*Math.sin(a)+y*Math.cos(a);return[this.cx+(xx-yy)*this.s*.86,this.cy+(xx+yy)*this.s*(this.mode==='2d'?.68:.43)-z*this.s];}
 poly(points,fill,stroke){const c=this.ctx;c.beginPath();points.forEach((p,i)=>{const v=this.project(...p);i?c.lineTo(...v):c.moveTo(...v)});c.closePath();c.fillStyle=fill;c.fill();if(stroke){c.strokeStyle=stroke;c.lineWidth=.6;c.stroke()}}
 line(points,col,width=1){const c=this.ctx;c.beginPath();points.forEach((p,i)=>{const v=this.project(...p);i?c.lineTo(...v):c.moveTo(...v)});c.strokeStyle=col;c.lineWidth=width*this.s;c.stroke()}
 box(x,y,w,d,h,col){if(this.mode==='2d')h=0;this.poly([[x,y,0],[x+w,y,0],[x+w,y,h],[x,y,h]],'#b4c9b8');this.poly([[x+w,y,0],[x+w,y+d,0],[x+w,y+d,h],[x+w,y,h]],'#92ad99');this.poly([[x,y,h],[x+w,y,h],[x+w,y+d,h],[x,y+d,h]],col,'#749e7f50');if(h>20){for(let k=9;k<h-5;k+=12){this.line([[x+w+.2,y+4,k],[x+w+.2,y+d-4,k]],'#d5e3d7',2);this.line([[x+4,y-.2,k],[x+w-4,y-.2,k]],'#e3eadf',2)}}}
 tree(x,y){this.line([[x,y,0],[x,y,16]],'#6a8872',2);const p=this.project(x,y,22);const c=this.ctx;c.fillStyle='#559966';c.beginPath();c.ellipse(p[0],p[1],7*this.s,11*this.s,0,0,Math.PI*2);c.fill();c.fillStyle='#72ab7c';c.beginPath();c.ellipse(p[0]-2*this.s,p[1]-3*this.s,4*this.s,7*this.s,0,0,Math.PI*2);c.fill()}
 label(x,y,z,text,color='#0f7a37'){const p=this.project(x,y,z),c=this.ctx;c.font=`600 ${Math.max(10,11*this.s)}px sans-serif`;const w=c.measureText(text).width+22;c.fillStyle='#ffffffed';c.shadowColor='#234c2418';c.shadowBlur=14;c.beginPath();c.roundRect(p[0]-w/2,p[1]-14,w,27,7);c.fill();c.shadowBlur=0;c.fillStyle=color;c.fillText(text,p[0]-w/2+11,p[1]+3)}
 draw(){const el=this.canvas,c=this.ctx,r=el.getBoundingClientRect();if(!r.width||!r.height)return;const dpr=Math.min(devicePixelRatio||1,2);el.width=r.width*dpr;el.height=r.height*dpr;c.scale(dpr,dpr);const w=r.width,h=r.height;this.cx=w/2;this.cy=h*.53;this.s=Math.min(w/780,h/450)*1.25*this.zoom;const bg=c.createRadialGradient(w*.5,h*.4,20,w*.5,h*.5,w*.7);bg.addColorStop(0,'#f0f6ec');bg.addColorStop(1,'#d5e6d8');c.fillStyle=bg;c.fillRect(0,0,w,h);
  c.save();c.translate(this.cx,this.cy+130*this.s);c.scale(1,.25);c.fillStyle='#718d7720';c.filter='blur(18px)';c.beginPath();c.ellipse(0,0,290*this.s,110*this.s,0,0,Math.PI*2);c.fill();c.restore();
  this.poly([[-245,-205,0],[245,-205,0],[245,205,0],[-245,205,0]],'#c8ddbd');this.poly([[-245,205,0],[245,205,0],[245,205,-18],[-245,205,-18]],'#9ab49e');this.poly([[245,-205,0],[245,205,0],[245,205,-18],[245,-205,-18]],'#8ba895');
  // Urban street grid and Adyar-inspired water corridor.
  for(let x=-210;x<220;x+=45)this.poly([[x,-205,1],[x+9,-205,1],[x+9,205,1],[x,205,1]],'#f5f5e9');for(let y=-175;y<200;y+=45)this.poly([[-245,y,1],[245,y,1],[245,y+9,1],[-245,y+9,1]],'#f5f5e9');
  const water=this.mode==='water'?'#77b7c9':'#a3cdd3';this.poly([[-245,125,2],[-120,105,2],[-20,145,2],[80,130,2],[245,155,2],[245,205,2],[85,180,2],[-25,190,2],[-140,149,2],[-245,170,2]],water);
  for(let i=0;i<10;i++){const x=-220+i*45;this.line([[x,151+Math.sin(i)*10,3],[x+22,153+Math.sin(i)*10,3]],'#d5edef',1)}
  if(this.mode==='water'){this.poly([[-170,-80,3],[-45,-95,3],[100,70,3],[-120,100,3]],'#75b8ce55');this.label(30,175,10,'Water corridor');this.label(-80,0,20,'Illustrative catchment');}
  if(this.chapter==='landslide'){this.poly([[-245,-205,0],[-120,-205,150],[-5,-205,0]],'#84a88a');this.poly([[-120,-205,150],[-10,-110,0],[-5,-205,0]],'#689576');this.poly([[-120,-205,150],[-245,-205,0],[-210,-55,0],[-10,-110,0]],'#a1bc8e');for(let j=0;j<9;j++){const f=(this.t*.18+j*.11)%1;this.box(-110-f*50,-180+f*120,12,10,9,'#af9674')}}
  const buildings=[...this.buildings].sort((a,b)=>{const aa=this.project(a.x,a.y)[1],bb=this.project(b.x,b.y)[1];return aa-bb});buildings.forEach(b=>{if(this.chapter==='landslide'&&b.y< -90&&b.x< -70)return;this.box(b.x,b.y,b.w,b.d,b.h,b.color)});
  // Marina-style civic landmark and raised park.
  this.box(135,-80,44,46,24,'#faf1d9');this.box(147,-68,20,22,45,'#f9f1dc');const tp=this.project(157,-57,55);c.fillStyle='#f0dcaf';c.beginPath();c.arc(tp[0],tp[1],12*this.s,Math.PI,0);c.fill();
  for(let i=0;i<12;i++)this.tree(-220+i*36,90+(i%2)*13);for(let i=0;i<6;i++)this.tree(195,-140+i*42);
  if(this.chapter==='flood'&&this.mode!=='water'){const spread=this.level*(.93+.07*Math.sin(this.t));this.poly([[-220,65,7],[-170,-85*spread,7],[-40,-125*spread,7],[100,-50*spread,7],[215,95,7],[220,170,7],[-220,160,7]],`rgba(92,173,198,${.18+spread*.35})`);for(let i=0;i<8;i++){const x=-160+i*42,y=40+Math.sin(this.t+i)*10;this.line([[x,y,10],[x+20,y+4,10]],'#e3f8ff99',1.4)}}
  if(this.chapter==='cyclone'){for(let k=0;k<5;k++){const points=[];for(let a=0;a<Math.PI*4;a+=.12){const rr=10+a*7+k*7;points.push([Math.cos(a+this.t)*rr,Math.sin(a+this.t)*rr,100+k*12])}this.line(points,`rgba(112,143,151,${.48-k*.05})`,2.5)}for(let j=0;j<45;j++){const xx=(j*97%w),yy=(j*41+this.t*150)%h;c.strokeStyle='#638f9c50';c.lineWidth=1;c.beginPath();c.moveTo(xx,yy);c.lineTo(xx-8,yy+17);c.stroke()}}
  if(w>500){this.label(-150,-120,110,this.chapter==='landslide'?'Slope movement':this.chapter==='cyclone'?'Strong winds':'Chennai · concept model');this.label(120,70,78,this.chapter==='flood'?'Understand exposure':'Prepare together');}c.font='10px sans-serif';c.fillStyle='#67816d';c.fillText('ILLUSTRATIVE GEOMETRY · NOT A LIVE HAZARD MAP',18,21);
 }
};
