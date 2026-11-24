"""Autonomous environments. actions() observes the board; move() scores the choice."""
import math
from arcade_rules import CELLS, DIGITS, PEERS, attach, center, neighbors, puzzle, race_move, sockets
from fly_policy import NAMES


class Sudoku:
    def __init__(self, rng):
        self.board, self.answer = puzzle(22, rng)
        self.givens = self.board.copy()
        self.rejected = set()
        self.focus = 0

    def actions(self):
        options = []
        for i in CELLS:
            if self.board[i]:
                continue
            choices = DIGITS - {self.board[j] for j in PEERS[i]}
            choices -= {n for n in choices if (i,n) in self.rejected}
            for digit in choices:
                options.append(((i,digit), f"{len(choices)} candidate(s)"))
        return options

    def move(self, action):
        i,digit = action
        self.focus = i
        valid = digit == self.answer[i]
        if valid:
            self.board[i] = digit
        else:
            self.rejected.add(action)
        message = f"Row {i//6+1}, column {i%6+1} · tried {digit} · " + ("accepted" if valid else "rejected")
        return (1 if valid else -1), 0 not in self.board, 0 not in self.board, message


class Memory:
    def __init__(self,rng):
        self.deck = list("ABCDEFGH")*2
        rng.shuffle(self.deck)
        self.seen = {}
        self.matched = set()
        self.first = None
        self.show = []
        self.focus = 0

    def actions(self):
        free = [i for i in range(16) if i not in self.matched and i != self.first]
        options = []
        for i in free:
            key = "unseen"
            if i in self.seen:
                if self.first is None:
                    paired = any(j != i and self.seen.get(j) == self.seen[i] for j in free)
                else:
                    paired = self.seen[i] == self.seen[self.first]
                key = "known pair" if paired else "seen single"
            options.append((i,key))
        return options

    def move(self,i):
        self.seen[i] = self.deck[i]
        self.focus = i
        if self.first is None:
            self.first = i
            self.show = [i]
            return 0,False,False,f"Turned over {self.deck[i]}."
        self.show = [self.first,i]
        match = self.deck[self.first] == self.deck[i]
        if match:
            self.matched.update(self.show)
        self.first = None
        won = len(self.matched)==16
        return (2 if match else -1),won,won,"Pair found." if match else "Different symbols. Both positions remembered."


class Race:
    def __init__(self,rng):
        self.rng = rng
        self.pos = [0,0]
        self.turn = 0
        self.focus = 1

    def actions(self):
        return [(None,"roll")]

    def move(self,action):
        p = self.turn
        die = self.rng.randint(1,6)
        start = self.pos[p]
        land,end = race_move(start,die)
        self.pos[p] = end
        self.focus = max(1,end)
        self.turn = 1-p
        reason = "overshoot" if start+die>100 else "ladder" if end>land else "snake" if end<land else "move"
        return 0,end==100,p==0 and end==100,f"Fly {p+1} rolled {die} · {reason} · square {end}"


class Bubbles:
    def __init__(self,rng):
        self.rng = rng
        self.board = {(r,c):rng.randrange(4) for r in range(4) for c in sockets(r)}
        self.color = rng.choice(list(self.board.values()))
        self.path = []
        self.routes = {}
        self.focus = (160,318)
        self.removed = 0
        self.shots = 0
        self.revision = 0

    def trace(self,angle):
        # Bounce a ray off the walls until it touches the ceiling or an orb.
        x,y = 160,318
        dx,dy = 7*math.sin(angle),-7*math.cos(angle)
        path = [(x,y)]
        while y>16:
            x,y = x+dx,y+dy
            if x<16 or x>304:
                x = min(304,max(16,x))
                dx = -dx
            path.append((x,y))
            near_row = round((y-16)/28)
            hits = []
            for r in range(max(0,near_row-1),near_row+2):
                col = round((x-16-16*(r%2))/32)
                for c in range(col-1,col+2):
                    q = (r,c)
                    if q in self.board and math.dist(center(q),(x,y))<=31:
                        hits.append(q)
            if hits or y<=16:
                free = {q for p in hits for q in neighbors(p) if q not in self.board}
                if y<=16:
                    free.update((0,c) for c in sockets(0) if (0,c) not in self.board)
                if free:
                    return min(free,key=lambda q:(math.dist(center(q),(x,y)),q)),path
                break
        return None,path

    def actions(self):
        self.routes = {}
        actions = []
        for step in range(-9,10):
            q,path = self.trace(step*.13)
            if q is None or q in self.routes:
                continue
            self.routes[q] = path
            matches = sum(self.board.get(n)==self.color for n in neighbors(q))
            actions.append((q,f"{min(2,matches)} adjacent matches"))
        return actions or [(None,"blocked")]

    def move(self,q):
        if q is None:
            return -2,True,False,"No open shot."
        self.path = self.routes[q]
        self.focus = center(q)
        self.shots += 1
        self.last_color = self.color
        self.before = self.board.copy()
        popped = attach(self.board,q,self.color)
        self.removed += popped
        self.revision += 1
        won = not self.board
        ended = won or any(center(p)[1]+15>=286 for p in self.board) or self.shots>=160
        if self.board:
            self.color = self.rng.choice(list(self.board.values()))
        return (min(6,popped) if popped else -1),ended,won,f"Shot {self.shots} · {popped} bubbles cleared."


WORLDS = dict(zip(NAMES,(Sudoku,Race,Bubbles,Memory)))
