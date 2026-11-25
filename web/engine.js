// The environment exposes visible actions and scores the selected action afterwards.
const games = ['Sudoku', 'Memory pairs', 'Bubble launch', 'Snakes & Ladders'];
const range = n => Array.from({length: n}, (_, i) => i);
const pick = list => list[Math.floor(Math.random() * list.length)];
function shuffled(items) {
  const copy = items.slice();
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}
const cells = range(36), digits = range(6).map(i => i + 1);
const row = i => Math.floor(i / 6), col = i => i % 6;
const box = i => 2 * Math.floor(row(i) / 2) + Math.floor(col(i) / 3);
const peers = cells.map(i => cells.filter(j => j !== i && (row(i) === row(j) || col(i) === col(j) || box(i) === box(j))));
const candidates = (board, i) => digits.filter(d => peers[i].every(j => board[j] !== d));
function solutions(board, limit = 2) {
  let best, choices;
  for (const i of cells) {
    if (board[i]) continue;
    const options = candidates(board, i);
    if (!options.length) return 0;
    if (!choices || options.length < choices.length) { best = i; choices = options; }
  }
  if (!choices) return 1;
  let count = 0;
  for (const d of choices) {
    board[best] = d;
    count += solutions(board, limit - count);
    board[best] = 0;
    if (count >= limit) break;
  }
  return count;
}
class Sudoku {
  constructor() {
    const order = shuffled(digits);
    const groups = (n, size) => shuffled(range(n)).flatMap(g => shuffled(range(size)).map(i => g * size + i));
    const rows = groups(3, 2), cols = groups(2, 3);
    this.answer = rows.flatMap(r => cols.map(c => order[(3*r + Math.floor(r/2) + c) % 6]));
    this.board = this.answer.slice();
    let blanks = 0;
    for (const i of shuffled(cells)) {
      this.board[i] = 0;
      if (solutions(this.board) === 1) blanks++;
      else this.board[i] = this.answer[i];
      if (blanks === 22) break;
    }
    this.givens = this.board.slice();
    this.rejected = new Set();
    this.focus = this.board.indexOf(0);
  }
  actions() {
    return cells.filter(i => !this.board[i]).flatMap(i => {
      const options = candidates(this.board, i).filter(d => !this.rejected.has(i*10+d));
      return options.map(d => [[i,d], options.length + ' candidate(s)']);
    });
  }
  move([i,d]) {
    this.focus = i;
    const ok = this.answer[i] === d;
    if (ok) this.board[i] = d;
    else this.rejected.add(i*10+d);
    const done = !this.board.includes(0);
    return {reward: ok ? 1 : -1, done, won: done, text: 'R' + (row(i)+1) + ' · C' + (col(i)+1) + '  /  ' + d + (ok ? ' accepted' : ' rejected')};
  }
}
class Memory {
  constructor() {
    this.deck = shuffled(Array.from('ABCDEFGHABCDEFGH'));
    this.seen = new Map(); this.matched = new Set();
    this.first = null; this.show = []; this.focus = 0;
  }
  actions() {
    const free = range(16).filter(i => !this.matched.has(i) && i !== this.first);
    return free.map(i => {
      if (!this.seen.has(i)) return [i, 'unseen'];
      const value = this.seen.get(i);
      const pair = this.first === null ? free.some(j => i !== j && this.seen.get(j) === value) : this.seen.get(this.first) === value;
      return [i, pair ? 'known pair' : 'seen single'];
    });
  }
  move(i) {
    this.seen.set(i, this.deck[i]); this.focus = i;
    if (this.first === null) {
      this.first = i; this.show = [i];
      return {reward:0, done:false, won:false, text:'Revealed card ' + this.deck[i]};
    }
    this.show = [this.first, i]; this.first = null;
    const pair = this.deck[this.show[0]] === this.deck[i];
    if (pair) this.show.forEach(j => this.matched.add(j));
    const done = this.matched.size === 16;
    return {reward:pair ? 2 : -1, done, won:done, text:pair ? 'Matched pair ' + this.deck[i] : 'Different cards · positions remembered'};
  }
}
const portals = {4:22,13:34,26:47,42:64,60:81,78:96,28:8,52:31,68:48,83:61,94:71,98:79};
class Race {
  constructor() { this.pos = [0,0]; this.turn = 0; this.focus = 1; }
  actions() { return [[null,'roll']]; }
  move() {
    const p = this.turn, die = pick(digits), landing = this.pos[p] + die;
    if (landing <= 100) this.pos[p] = portals[landing] ?? landing;
    this.focus = Math.max(1, this.pos[p]); this.turn = 1 - p;
    const done = this.pos[p] === 100;
    return {reward:0, done, won:done && p === 0, text:'Fly ' + (p+1) + ' rolled ' + die + ' · square ' + this.pos[p]};
  }
}
// An integer identifies one socket on the staggered bubble board.
const socket = (r,c) => r*10+c;
const center = k => [16 + 32*(k%10) + 16*(Math.floor(k/10)%2), 16 + 28*Math.floor(k/10)];
function neighbors(k) {
  const r = Math.floor(k/10), c = k%10, offset = r%2;
  return [[r,c-1],[r,c+1],[r-1,c-1+offset],[r-1,c+offset],[r+1,c-1+offset],[r+1,c+offset]]
    .filter(([y,x]) => y >= 0 && x >= 0 && x < 10-y%2).map(([y,x]) => socket(y,x));
}
function connected(board, seeds, color) {
  const found = new Set(seeds);
  for (const k of found) for (const j of neighbors(k)) {
    if (board.has(j) && (color === undefined || board.get(j) === color)) found.add(j);
  }
  return found;
}
class Bubbles {
  constructor() {
    this.board = new Map();
    for (const r of range(4)) for (const c of range(10-r%2)) this.board.set(socket(r,c), pick(range(4)));
    this.color = pick([...this.board.values()]);
    this.shots = 0; this.path = []; this.focus = [160,318];
  }
  trace(angle) {
    let x = 160, y = 318, dx = 7*Math.sin(angle);
    const dy = -7*Math.cos(angle), path = [[x,y]];
    while (y > 16) {
      x += dx; y += dy;
      if (x < 16 || x > 304) { x = Math.max(16,Math.min(304,x)); dx *= -1; }
      path.push([x,y]);
      const distance = k => { const [a,b] = center(k); return Math.hypot(x-a,y-b); };
      const hits = [...this.board.keys()].filter(k => distance(k) <= 31);
      if (!hits.length && y > 16) continue;
      const free = [...new Set(hits.flatMap(neighbors).concat(y <= 16 ? range(10) : []))].filter(k => !this.board.has(k));
      if (free.length) return [free.sort((a,b) => distance(a)-distance(b) || a-b)[0], path];
      break;
    }
    return [null,path];
  }
  actions() {
    this.routes = new Map();
    for (let step = -9; step <= 9; step++) {
      const [k,path] = this.trace(step*.13);
      if (k !== null && !this.routes.has(k)) this.routes.set(k,path);
    }
    const actions = [...this.routes.keys()].map(k => [k,Math.min(2,neighbors(k).filter(j => this.board.get(j) === this.color).length) + ' adjacent matches']);
    return actions.length ? actions : [[null,'blocked']];
  }
  move(k) {
    if (k === null) return {reward:-2, done:true, won:false, text:'No open shot'};
    this.focus = center(k); this.path = this.routes.get(k); this.shots++;
    this.board.set(k,this.color);
    const before = this.board.size, cluster = connected(this.board,[k],this.color);
    if (cluster.size >= 3) {
      for (const j of cluster) this.board.delete(j);
      const anchored = connected(this.board,[...this.board.keys()].filter(j => j < 10));
      for (const j of this.board.keys()) if (!anchored.has(j)) this.board.delete(j);
    }
    const popped = before-this.board.size, won = this.board.size === 0;
    if (!won) this.color = pick([...this.board.values()]);
    const done = won || this.shots >= 160 || [...this.board.keys()].some(j => center(j)[1]+15 >= 286);
    return {reward:popped ? Math.min(6,popped) : -1, done, won, text:'Shot ' + this.shots + ' · ' + popped + ' cleared'};
  }
}
const worlds = {'Sudoku':Sudoku,'Memory pairs':Memory,'Bubble launch':Bubbles,'Snakes & Ladders':Race};
function newBrain() {
  return {version:1, values:Object.fromEntries(games.map(g => [g,{}])), results:Object.fromEntries(games.map(g => [g,[]]))};
}
function choose(table, actions, training) {
  if (training && Math.random() < .12) return pick(actions);
  const value = ([,key]) => table[key]?.[1] ?? 0;
  const best = Math.max(...actions.map(value));
  return pick(actions.filter(a => value(a) === best));
}
function learn(table,key,reward) {
  const [n,mean] = table[key] ?? [0,0];
  table[key] = [n+1, mean + (reward-mean)/(n+1)];
}
function parseBrain(text) {
  const data = JSON.parse(text);
  const object = v => v !== null && typeof v === 'object' && !Array.isArray(v);
  const require = ok => { if (!ok) throw new Error('Invalid Flight Lab save'); };
  require(data?.version === 1);
  for (const section of [data.values,data.results]) require(object(section) && Object.keys(section).length === games.length && games.every(g => Object.hasOwn(section,g)));
  for (const game of games) {
    require(object(data.values[game]) && Array.isArray(data.results[game]));
    for (const pair of Object.values(data.values[game])) require(Array.isArray(pair) && pair.length === 2 && Number.isSafeInteger(pair[0]) && pair[0] > 0 && Number.isFinite(pair[1]) && Math.abs(pair[1]) <= 10);
    for (const r of data.results[game]) require(object(r) && Number.isSafeInteger(r.moves) && r.moves > 0 && typeof r.training === 'boolean' && typeof r.won === 'boolean');
  }
  return data;
}
