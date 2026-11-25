const $ = id => document.getElementById(id);
const ink = '#293222', paper = '#fbfcf1', sage = '#4e703b', violet = '#775395';
const gameIcons = ['▦','◈','◌','⚄'];
const board = $('board'), ctx = board.getContext('2d');
const titles = {'Sudoku':'6×6 Sudoku','Memory pairs':'Memory pairs','Bubble launch':'Bubble launch','Snakes & Ladders':'Snakes & Ladders'};
let brain = newBrain(), game = 'Sudoku', world, training = true, paused = false;
let moves = 0, done = false, last = null, timer, flight, position;
const events = [];
function fly(c,x,y,size,angle = -.45) {
  c.save(); c.translate(x,y); c.rotate(angle); c.scale(size,size);
  const oval = (a,b,rx,ry,color,tilt=0) => {
    c.beginPath(); c.ellipse(a,b,rx,ry,tilt,0,Math.PI*2); c.fillStyle=color; c.fill(); c.strokeStyle=ink; c.lineWidth=.7; c.stroke();
  };
  for (const side of [-1,1]) {
    c.strokeStyle=ink; c.lineWidth=1.1;
    for (let n=0;n<3;n++) {
      c.beginPath(); c.moveTo(-5+n*4,side*2); c.lineTo(-12+n*9,side*(8+n)); c.lineTo(-15+n*12,side*(10+n)); c.stroke();
    }
  }
  oval(-7,0,10,4.6,'#a9ba65'); oval(0,0,6,5,ink);
  for (const side of [-1,1]) {
    c.save(); c.scale(1,side); c.rotate(.55);
    oval(-10,-1,13.8,4.8,'rgba(222,235,198,.88)');
    c.beginPath(); c.moveTo(1,-1); c.lineTo(-22,-1); c.moveTo(-6,-1); c.lineTo(-13,-5); c.moveTo(-9,-1); c.lineTo(-16,2); c.stroke(); c.restore();
  }
  oval(6,0,4.2,4.8,ink); oval(7.5,-2.5,2.8,2.4,'#d4744b'); oval(7.5,2.5,2.8,2.4,'#d4744b');
  c.restore();
}
fly($('specimen').getContext('2d'),132,64,4,-.45);
function rectangle(x,y,w,h,color) { ctx.fillStyle=color; ctx.fillRect(x,y,w,h); }
function line(x,y,xx,yy,color,width=1) {
  ctx.strokeStyle=color; ctx.lineWidth=width;
  ctx.beginPath(); ctx.moveTo(x,y); ctx.lineTo(xx,yy); ctx.stroke();
}
function label(value,x,y,size,color=ink,font='monospace') {
  ctx.font=size+'px '+font; ctx.fillStyle=color; ctx.textAlign='center'; ctx.textBaseline='middle'; ctx.fillText(value,x,y);
}
function circle(x,y,r,color) {
  ctx.fillStyle=color; ctx.beginPath(); ctx.arc(x,y,r,0,2*Math.PI); ctx.fill();
}
function lattice(n, side) {
  const s=side/n;
  for (let i=0;i<=n;i++) {
    line(20+i*s,20,20+i*s,20+side,ink,.7);
    line(20,20+i*s,20+side,20+i*s,ink,.7);
  }
}
function sudokuBoard() {
  const s=52, side=312;
  rectangle(20,20,side,side,paper);
  for (const i of cells) {
    const x=20+col(i)*s, y=20+row(i)*s;
    if (i===world.focus) rectangle(x,y,s,s,last?.reward < 0 ? '#f1cfb5' : '#dfefac');
    if (world.board[i]) label(world.board[i],x+s/2,y+s/2+1,30,world.givens[i] ? ink : sage,'Georgia');
    else if (i!==world.focus) circle(x+s/2,y+s/2,1,'#c3c8b3');
  }
  lattice(6,side);
  for (const c of [0,3,6]) line(20+c*s,20,20+c*s,332,ink,2);
  for (const r of [0,2,4,6]) line(20,20+r*s,332,20+r*s,ink,2);
  for (const i of range(6)) { label(i+1,46+s*i,10,9,sage); label(i+1,10,46+s*i,9,sage); }
  return [20+col(world.focus)*s+39,20+row(world.focus)*s+10];
}
function memoryBoard() {
  for (const i of range(16)) {
    const x=19+(i%4)*79, y=19+Math.floor(i/4)*79;
    const matched=world.matched.has(i), shown=matched || world.show.includes(i);
    rectangle(x,y,72,72,matched ? '#cee49e' : shown ? paper : '#4a5943');
    label(shown ? world.deck[i] : '✣',x+36,y+37,shown ? 34 : 23,shown ? ink : '#c1d0aa','Georgia');
  }
  return [70+(world.focus%4)*79,32+Math.floor(world.focus/4)*79];
}
const orbColors=['#bbc879','#d39778','#a295bd','#80b8af'];
function orb(x,y,color) {
  circle(x,y,14,ink); circle(x,y,13,orbColors[color]);
  label('ABCD'[color],x,y+1,12);
}
function bubbleBoard() {
  ctx.save(); ctx.translate(16,10); rectangle(0,0,320,332,paper);
  for (let i=1;i<world.path.length;i+=2) circle(...world.path[i],1.2,'#939c89');
  for (const [k,color] of world.board) orb(...center(k),color);
  if (!done) orb(160,318,world.color);
  ctx.restore();
  return [16+world.focus[0],10+world.focus[1]-10];
}
function square(n) {
  const i=Math.max(1,n)-1,r=Math.floor(i/10);
  return [36+(r%2 ? 9-i%10 : i%10)*31,315-r*31];
}
function raceBoard() {
  rectangle(20,20,310,310,paper); lattice(10,310);
  for (const [from,to] of Object.entries(portals)) {
    const a=square(Number(from)),b=square(to);
    line(...a,...b,to>Number(from) ? '#b4c793' : '#d9b8b1',3);
  }
  for (let n=1;n<=100;n++) { const [x,y]=square(n); label(n,x,y,10); }
  world.pos.forEach((n,p) => {
    const [x,y]=square(n); circle(x+(p ? 7 : -7),y+8,5,p ? violet : sage);
  });
  const [x,y]=square(world.focus); return [x,y-7];
}
const drawWorld={'Sudoku':sudokuBoard,'Memory pairs':memoryBoard,'Bubble launch':bubbleBoard,'Snakes & Ladders':raceBoard};
function draw(animate=false) {
  cancelAnimationFrame(flight);
  const start=position, at=performance.now();
  const duration=animate && !matchMedia('(prefers-reduced-motion: reduce)').matches ? Math.min(240,Number($('speed').value)*.7) : 0;
  function frame(now) {
    ctx.setTransform(board.width/352,0,0,board.height/352,0,0); ctx.clearRect(0,0,352,352);
    const target=drawWorld[game](), t=start && duration ? Math.min(1,(now-at)/duration) : 1;
    position=t===1 ? target : start.map((v,i) => v+(target[i]-v)*t);
    fly(ctx,...position,game==='Snakes & Ladders' ? .6 : .85);
    if (t<1) flight=requestAnimationFrame(frame);
  }
  frame(at);
}
function log(text) {
  events.unshift([moves,text]); events.length=Math.min(3,events.length);
  $('events').replaceChildren(...events.map(([n,msg]) => {
    const li=document.createElement('li'), count=document.createElement('span');
    count.textContent=String(n).padStart(3,'0'); li.append(count,document.createTextNode(msg)); return li;
  }));
}
function update(animate=false) {
  $('title').textContent=titles[game];
  $('moves').textContent=moves;
  $('rounds').textContent=brain.results[game].length;
  $('reward').textContent=last ? (last.reward>0 ? '+' : '')+last.reward : '—';
  $('state').textContent=paused ? 'Paused' : done ? 'Round finished' : game==='Snakes & Ladders' ? 'Racing' : training ? 'Training' : 'Evaluating';
  $('state').dataset.paused=paused;
  $('play').textContent=paused ? '▶  Resume' : 'Ⅱ  Pause';
  $('modeHint').textContent=game==='Snakes & Ladders' ? 'Two flies race by chance. Each finish records an outcome.' : training ? 'The fly explores on 12% of moves and learns from each reward.' : 'The fly uses its saved action values. Learning is paused.';
  board.setAttribute('aria-label',titles[game]+'. '+(game==='Sudoku' ? 'Rows: '+range(6).map(r=>world.board.slice(r*6,r*6+6).map(d=>d||'blank').join(', ')).join('; ')+'. ' : '')+(last?.text ?? 'Fresh round'));
  draw(animate);
}
function schedule() {
  clearTimeout(timer);
  if (!paused) timer=setTimeout(tick,done ? Math.max(850,Number($('speed').value)) : Number($('speed').value));
}
function fresh() {
  world=new worlds[game](); moves=0; done=false; last=null; position=null; events.length=0;
  log('Fresh round'); update(); schedule();
}
function tick() {
  if (done) { fresh(); return; }
  const table=brain.values[game], [action,key]=choose(table,world.actions(),training);
  last=world.move(action); moves++; done=last.done;
  if (training && game!=='Snakes & Ladders') learn(table,key,last.reward);
  log(last.text);
  if (done) {
    brain.results[game].push({moves,won:last.won,training});
    log(game==='Snakes & Ladders' ? ('Fly '+(last.won ? 1 : 2)+' won') : last.won ? 'Round complete' : 'Round ended');
  }
  update(true); schedule();
}
games.forEach((name,i) => {
  const button=document.createElement('button'), icon=document.createElement('span');
  icon.textContent=gameIcons[i]; icon.setAttribute('aria-hidden','true'); button.append(icon,name);
  button.setAttribute('aria-pressed',name===game);
  button.onclick=() => {
    if (game===name) return;
    game=name;
    for (const tab of $('games').children) tab.setAttribute('aria-pressed',tab===button);
    fresh();
  };
  $('games').append(button);
});
$('mode').onchange=() => { training=$('mode').value==='train'; fresh(); };
$('play').onclick=() => { paused=!paused; update(); schedule(); };
$('step').onclick=() => { paused=true; clearTimeout(timer); tick(); };
$('speed').onchange=schedule;
$('restart').onclick=fresh;
$('save').onclick=() => {
  const url=URL.createObjectURL(new Blob([JSON.stringify(brain)],{type:'application/json'}));
  const a=document.createElement('a'); a.href=url; a.download='flysudoku-results.json'; a.click();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
  $('feedback').textContent='Training results exported.';
};
$('load').onclick=()=>$('file').click();
$('file').onchange=async e => {
  const file=e.target.files[0]; if (!file) return;
  try {
    const loaded=parseBrain(await file.text());
    brain=loaded; training=false; $('mode').value='evaluate'; fresh();
    $('feedback').textContent='Results loaded for evaluation.';
  } catch { $('feedback').textContent='Could not read this save. Choose a Flight Lab v1 JSON file.'; }
  e.target.value='';
};
fresh();
