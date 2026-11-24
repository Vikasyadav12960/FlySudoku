"""FlySudoku desktop arcade. Launch with python arcade.py or PLAY.cmd."""
import math
from pathlib import Path
import random
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, messagebox

from arcade_rules import CELLS, PEERS, PORTALS, attach, center, neighbors, puzzle, race_move, sockets

BG, PANEL, INK, MUTED = "#121a24", "#243346", "#faf5eb", "#bbcad7"
MINT, GOLD, CORAL = "#90edc5", "#f3cd7e", "#ffa492"
COLORS = [MINT, GOLD, CORAL, "#a8baff"]


def label(parent, text="", size=11, color=INK):
    return tk.Label(parent, text=text, bg=BG, fg=color, font=("Segoe UI", size),
                    justify="left", wraplength=680)


def button(parent, text, command):
    return tk.Button(parent, text=text, command=command, font=("Segoe UI", 10, "bold"),
                     bg=PANEL, fg=INK, activebackground=MINT, activeforeground=BG,
                     relief="flat", padx=10, pady=4, cursor="hand2")


class Game(tk.Frame):
    def __init__(self, parent, title, instructions):
        super().__init__(parent, bg=BG, padx=8, pady=6)
        label(self, title, 19, MINT).pack()
        label(self, instructions, 10, MUTED).pack(pady=(0, 5))
        self.board = tk.Frame(self, bg=BG)
        self.board.pack()
        self.tools = tk.Frame(self, bg=BG)
        self.tools.pack(pady=5)
        self.status = label(self, color=GOLD)
        self.status.pack()

    def action(self, text, command):
        btn = button(self.tools, text, command)
        btn.pack(side="left", padx=3)
        return btn

    def say(self, text):
        self.status.config(text=text)


class Sudoku(Game):
    def __init__(self, parent):
        super().__init__(parent, "Six by six", "Fill each row, column and outlined 2 × 3 box with 1–6. Select a square, then type or tap a digit.")
        self.cells = []
        for i in CELLS:
            r, c = divmod(i, 6)
            b = button(self.board, "", lambda ix=i: self.select(ix))
            b.config(width=3, font=("Consolas", 18, "bold"))
            b.grid(row=r, column=c, padx=(4 if c == 3 else 1, 1), pady=(4 if r in (2,4) else 1, 1))
            b.bind("<Key>", lambda e, ix=i: self.key(e, ix))
            self.cells.append(b)
        keys = tk.Frame(self, bg=BG)
        keys.pack(before=self.tools, pady=3)
        for digit in range(1, 7):
            button(keys, str(digit), lambda v=digit: self.put(v)).pack(side="left", padx=2)
        self.level = ttk.Combobox(self.tools, values=["Easy", "Standard", "Challenge"], width=10, state="readonly")
        self.level.set("Standard")
        self.level.pack(side="left")
        self.level.bind("<<ComboboxSelected>>", lambda _: self.reset())
        self.action("New puzzle", self.reset)
        self.action("Undo", self.undo)
        self.action("Erase", lambda: self.put(0))
        self.action("Hint", self.hint)
        self.reset()

    def reset(self):
        self.fixed, self.solution = puzzle({"Easy":14,"Standard":20,"Challenge":24}[self.level.get()])
        self.values = self.fixed.copy()
        self.history = []
        self.select(self.values.index(0))

    def select(self, i):
        self.index = i
        self.cells[i].focus_set()
        self.draw()

    def key(self, event, i):
        self.index = i
        if event.char and event.char in "123456":
            self.put(int(event.char))
        elif event.keysym in ("BackSpace", "Delete"):
            self.put(0)
        elif event.keysym in ("Up","Down","Left","Right"):
            step = {"Up":-6,"Down":6,"Left":-1,"Right":1}[event.keysym]
            self.select((i + step) % 36)

    def put(self, value):
        i = self.index
        if self.fixed[i]:
            self.say("Printed clue. Choose an empty or mint square.")
            return
        if self.values[i] != value:
            self.history.append((i, self.values[i]))
            self.values[i] = value
        self.select(i)

    def undo(self):
        if self.history:
            i, old = self.history.pop()
            self.values[i] = old
            self.select(i)

    def hint(self):
        wrong = [i for i in CELLS if self.values[i] != self.solution[i]]
        if wrong:
            self.index = self.index if self.index in wrong else wrong[0]
            self.put(self.solution[self.index])

    def draw(self):
        conflicts = {i for i in CELLS if self.values[i] and any(self.values[j] == self.values[i] for j in PEERS[i])}
        for i, b in enumerate(self.cells):
            bg = "#65413c" if i in conflicts else "#40554c" if i == self.index else PANEL
            b.config(text=self.values[i] or " ", fg=INK if self.fixed[i] else MINT, bg=bg,
                     highlightthickness=1, highlightbackground=GOLD if i == self.index else bg)
        if self.values == self.solution:
            self.say("Solved! Choose New puzzle to play again.")
        elif conflicts:
            self.say("Repeated digits highlighted. Check the row, column and box.")
        else:
            self.say(f"Row {self.index//6+1}, column {self.index%6+1}   ·   {self.values.count(0)} squares left")


class Race(Game):
    def __init__(self, parent):
        super().__init__(parent, "Snakes & Ladders", "Two players share the die. Climb mint ladders, slide down coral snakes. Land exactly on 100 to win.")
        self.canvas = tk.Canvas(self.board, width=340, height=340, bg=BG, highlightthickness=0)
        self.canvas.pack()
        self.roll_button = self.action("Roll die", self.roll)
        self.action("New race", self.reset)
        self.reset()

    @staticmethod
    def point(n):
        r, c = divmod(n-1, 10)
        return (9-c if r%2 else c)*34+17, (9-r)*34+17

    def reset(self):
        self.pos = [0,0]
        self.turn = 0
        self.roll_button.config(state="normal")
        self.say("Player 1 rolls first. Both players start off the board.")
        self.draw()

    def roll(self):
        p = self.turn
        if 100 in self.pos:
            return
        die = random.randint(1,6)
        old = self.pos[p]
        landing, end = race_move(old, die)
        self.pos[p] = end
        text = f"P{p+1} rolled {die}. "
        if old+die > 100:
            text += f"Overshoot — stay on {old}."
        elif landing != end:
            text += f"{'Ladder' if end > landing else 'Snake'} from {landing} to {end}."
        else:
            text += f"Landed on {end}."
        self.turn = 1-p
        self.say(text + (f" Player {p+1} wins!" if end == 100 else f" Player {self.turn+1} rolls next."))
        if end == 100:
            self.roll_button.config(state="disabled")
        self.draw()

    def draw(self):
        cv = self.canvas
        cv.delete("all")
        for n in range(1,101):
            x,y = self.point(n)
            cv.create_rectangle(x-16,y-16,x+16,y+16,fill=PANEL if n%2 else "#304256",width=0)
        for a,b in PORTALS.items():
            x,y = self.point(a)
            u,v = self.point(b)
            if b>a:
                dx,dy = u-x,v-y
                length = math.hypot(dx,dy)
                ox,oy = -3*dy/length,3*dx/length
                for sign in (-1,1):
                    cv.create_line(x+sign*ox,y+sign*oy,u+sign*ox,v+sign*oy,fill=MINT)
                for k in range(1,9):
                    px,py = x+dx*k/9,y+dy*k/9
                    cv.create_line(px-ox,py-oy,px+ox,py+oy,fill=MINT)
            else:
                cv.create_line(x,y,(x+u)/2+18,(y+v)/2,u,v,smooth=True,fill=CORAL,width=3,arrow="last")
        for n in range(1,101):
            x,y = self.point(n)
            cv.create_text(x-8,y-9,text=str(n),fill=INK,font=("Consolas",8,"bold"))
        for p,n in enumerate(self.pos):
            if n:
                x,y = self.point(n)
                x += -6 if p==0 else 7
                cv.create_oval(x-7,y-6,x+7,y+8,fill=(GOLD,MINT)[p],outline=BG)
                cv.create_text(x,y+1,text=str(p+1),font=("Arial",8,"bold"))


class Memory(Game):
    def __init__(self, parent):
        super().__init__(parent,"Memory pairs","Flip two cards. Match all eight pairs in as few turns as you can.")
        self.cards = []
        self.timer = None
        for i in range(16):
            b = button(self.board,"?",lambda ix=i:self.flip(ix))
            b.config(width=5,height=2,font=("Segoe UI",16,"bold"))
            b.grid(row=i//4,column=i%4,padx=3,pady=3)
            self.cards.append(b)
        self.action("Shuffle & restart", self.reset)
        self.reset()

    def reset(self):
        if self.timer is not None:
            self.after_cancel(self.timer)
        self.timer = None
        self.deck = ["Sun","Moon","Leaf","Star","Rain","Snow","Sky","Sea"]*2
        random.shuffle(self.deck)
        self.flipped = []
        self.matched = set()
        self.turns = 0
        for b in self.cards:
            b.config(text="?",bg=PANEL,fg=INK)
        self.say("Pick your first card.")

    def flip(self, i):
        if self.timer or i in self.flipped or i in self.matched:
            return
        self.cards[i].config(text=self.deck[i],bg=GOLD,fg=BG)
        self.flipped.append(i)
        if len(self.flipped)==1:
            self.say("Pick its partner.")
            return
        self.turns += 1
        a,b = self.flipped
        if self.deck[a] == self.deck[b]:
            self.matched.update((a,b))
            for j in self.flipped:
                self.cards[j].config(bg=MINT)
            self.flipped.clear()
            self.say(f"{len(self.matched)//2}/8 pairs · {self.turns} turns" if len(self.matched)<16 else f"All pairs found in {self.turns} turns!")
        else:
            self.say("Different cards. Remember their places.")
            self.timer = self.after(850,self.hide_pair)

    def hide_pair(self):
        for j in self.flipped:
            self.cards[j].config(text="?",bg=PANEL,fg=INK)
        self.flipped.clear()
        self.timer = None


class Bubbles(Game):
    def __init__(self, parent):
        super().__init__(parent,"Bubble launch","Aim and click, or use ← → and Space. Match 3 touching symbols. Clear the ceiling before a bubble reaches the line.")
        self.canvas = tk.Canvas(self.board,width=320,height=340,bg="#192334",highlightthickness=0,takefocus=True)
        self.canvas.pack()
        self.canvas.bind("<Motion>", self.aim)
        self.canvas.bind("<Button-1>", self.click)
        self.canvas.bind("<Left>", lambda _:self.rotate(-.1))
        self.canvas.bind("<Right>", lambda _:self.rotate(.1))
        self.canvas.bind("<space>", lambda _:self.fire())
        self.action("Aim left",lambda:self.rotate(-.12))
        self.action("Launch",self.fire)
        self.action("Aim right",lambda:self.rotate(.12))
        self.action("New field",self.reset)
        self.timer = None
        self.reset()

    def reset(self):
        if self.timer is not None:
            self.after_cancel(self.timer)
        self.timer = None
        self.field = {(r,c):random.randrange(4) for r in range(4) for c in sockets(r)}
        self.shot = None
        self.angle = 0
        self.color = random.choice(list(self.field.values()))
        self.score = 0
        self.over = False
        self.say("Aim at a matching group. The walls bounce your shot.")
        self.draw()

    def rotate(self, delta):
        self.angle = max(-1.25,min(1.25,self.angle+delta))
        self.draw()

    def aim(self,event):
        if event.y < 316:
            self.angle = max(-1.25,min(1.25,math.atan2(event.x-160,318-event.y)))
            self.draw()

    def click(self,event):
        self.canvas.focus_set()
        self.aim(event)
        if event.y<316:
            self.fire()

    def fire(self):
        if self.shot or self.over:
            return
        self.shot = [160,318,math.sin(self.angle)*6,-math.cos(self.angle)*6]
        self.tick()

    def tick(self):
        self.timer = None
        x,y,vx,vy = self.shot
        x += vx
        y += vy
        if x<16 or x>304:
            x = min(304,max(16,x))
            vx = -vx
        hits = [p for p in self.field if math.dist(center(p),(x,y))<=31]
        if hits or y<=16:
            candidates = {q for p in hits for q in neighbors(p) if q not in self.field}
            if y<=16:
                candidates.update((0,c) for c in sockets(0) if (0,c) not in self.field)
            if candidates:
                socket = min(candidates,key=lambda q:math.dist(center(q),(x,y)))
                self.score += attach(self.field,socket,self.color)
            self.shot = None
            self.over = not candidates or not self.field or any(center(p)[1]+15>=286 for p in self.field)
            if not self.field:
                self.say(f"Field cleared! {self.score} bubbles removed.")
            elif self.over:
                self.say(f"Field full. {self.score} bubbles removed. Select New field.")
            else:
                self.color = random.choice(list(self.field.values()))
                self.say(f"{self.score} bubbles removed. Aim your next shot.")
        else:
            self.shot = [x,y,vx,vy]
            self.timer = self.after(12,self.tick)
        self.draw()

    def orb(self,x,y,color):
        self.canvas.create_oval(x-14,y-14,x+14,y+14,fill=COLORS[color],outline="#dce6ea")
        self.canvas.create_text(x,y,text="ABCD"[color],fill=BG,font=("Consolas",12,"bold"))

    def draw(self):
        cv = self.canvas
        cv.delete("all")
        cv.create_line(0,286,320,286,fill=CORAL,dash=(5,5))
        for p,color in self.field.items():
            self.orb(*center(p),color)
        if not self.over:
            cv.create_line(160,318,160+math.sin(self.angle)*55,318-math.cos(self.angle)*55,fill=INK,width=3,arrow="last")
            x,y = self.shot[:2] if self.shot else (160,318)
            self.orb(x,y,self.color)


def learning_lab():
    lab = Path(__file__).resolve().parent / "FlySudoku_v0.1"
    if not (lab/"flysudoku"/"__main__.py").is_file():
        messagebox.showerror("Learning lab","Extract or clone the entire repository to include the learning lab.")
        return
    subprocess.Popen([sys.executable,"-m","flysudoku"],cwd=lab)


def build(root):
    root.title("FlySudoku Arcade")
    root.configure(bg=BG)
    root.minsize(630,540)
    header = tk.Frame(root,bg=BG,padx=16,pady=6)
    header.pack(fill="x")
    label(header,"FlySudoku Arcade",16).pack(side="left")
    button(header,"Open learning lab",learning_lab).pack(side="right")
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("TNotebook",background=BG,borderwidth=0)
    style.configure("TNotebook.Tab",padding=(13,7),background=PANEL,foreground=INK)
    style.map("TNotebook.Tab",background=[("selected",MINT)],foreground=[("selected",BG)])
    tabs = ttk.Notebook(root)
    tabs.pack(fill="both",expand=True,padx=8,pady=4)
    games = [Sudoku(tabs),Race(tabs),Bubbles(tabs),Memory(tabs)]
    for game,title in zip(games,["6×6 Sudoku","Snakes & Ladders","Bubble launch","Memory pairs"]):
        tabs.add(game,text=title)
    tabs.select(0)
    return games


if __name__ == "__main__":
    window = tk.Tk()
    build(window)
    window.mainloop()
