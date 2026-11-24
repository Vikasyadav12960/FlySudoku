"""FlySudoku • an autonomous desktop experiment."""
import math
import random
import tkinter as tk
from tkinter import filedialog, messagebox

from arcade_rules import PORTALS, center
from fly_policy import Brain, NAMES
from fly_worlds import WORLDS, Sudoku, Memory, Race, Bubbles

BG, PANEL, LINE = "#101720", "#182632", "#324755"
INK, MUTED, MINT, GOLD = "#eff4ef", "#b2c4cc", "#9ef1c8", "#ffcb78"
COLORS = [MINT,GOLD,"#ec9da9","#a6b5ff"]


def text(parent, value, size=11, color=INK, bg=BG, **kw):
    return tk.Label(parent,text=value,bg=bg,fg=color,font=("Segoe UI",size),
                    anchor="w",justify="left",**kw)


def button(parent,title,cmd):
    return tk.Button(parent,text=title,command=cmd,relief="flat",borderwidth=0,
                     bg=LINE,fg=INK,activebackground=MINT,activeforeground=BG,
                     font=("Segoe UI",10,"bold"),padx=9,pady=5,cursor="hand2")


def fly_sprite(cv,x,y,phase):
    flap = 3*math.sin(phase)
    for sign in (-1,1):
        for dy in (-4,0,4):
            cv.create_line(x+sign*3,y+dy,x+sign*9,y+dy+3,fill="#e6c792",tags="fly")
        cv.create_oval(x+sign*3-7,y-8-flap,x+sign*9+6,y+2,fill="#c3e8db",outline="#578176",tags="fly")
    cv.create_oval(x-4,y-4,x+4,y+9,fill="#273632",outline=GOLD,tags="fly")
    cv.create_oval(x-5,y-7,x+5,y-1,fill="#dc8e65",outline=BG,tags="fly")


class Lab:
    def __init__(self,root,rng=None):
        self.root = root
        self.rng = rng or random.Random()
        self.brain = Brain()
        self.training = True
        self.running = True
        self.speed = tk.StringVar(root,value="Watch")
        self.xy = (184,150)
        self.target = self.xy
        self.frame = 0
        self.tick_id = self.animation_id = None
        self.shot_progress = 1
        root.title("FlySudoku · Flight Lab")
        root.configure(bg=BG)
        root.minsize(710,530)
        head = tk.Frame(root,bg=BG,padx=15,pady=6)
        head.pack(fill="x")
        text(head,"Flight Lab",22,MINT).pack(side="left")
        self.badge = text(head,"AUTONOMOUS  /  TRAINING",10,GOLD)
        self.badge.pack(side="right")
        body = tk.Frame(root,bg=BG)
        body.pack(fill="both",expand=True,padx=14)
        rail = tk.Frame(body,bg=PANEL,padx=12,pady=10)
        rail.pack(side="left",fill="y",padx=(0,12))
        text(rail,"Choose a game",14,bg=PANEL).pack(anchor="w",pady=(0,6))
        self.choices = {}
        for name in NAMES:
            b = button(rail,name,lambda n=name:self.select(n))
            b.pack(fill="x",pady=2)
            self.choices[name] = b
        text(rail,"Experiment",14,bg=PANEL).pack(anchor="w",pady=(14,4))
        self.pause = button(rail,"Pause",self.toggle)
        self.pause.pack(fill="x",pady=2)
        self.mode = button(rail,"Evaluate policy",self.switch_mode)
        self.mode.pack(fill="x",pady=2)
        for title,cmd in [("Save result…",self.save),("Load result…",self.load)]:
            button(rail,title,cmd).pack(fill="x",pady=2)
        tk.OptionMenu(rail,self.speed,"Watch","Fast","Slow").pack(fill="x",pady=5)
        self.caption = text(rail,"",10,MUTED,PANEL,wraplength=190)
        self.caption.pack(anchor="w",pady=5)
        stage = tk.Frame(body,bg=BG)
        stage.pack(fill="both",expand=True)
        self.heading = text(stage,"",18)
        self.heading.pack(anchor="w")
        self.cv = tk.Canvas(stage,width=380,height=332,bg=PANEL,highlightthickness=1,highlightbackground=LINE)
        self.cv.pack(fill="x")
        self.status = text(stage,"",11,GOLD,wraplength=460)
        self.status.pack(anchor="w",pady=(6,1))
        self.metrics = text(stage,"",10,MUTED,wraplength=465)
        self.metrics.pack(anchor="w")
        self.feedback = text(stage,"",10,MINT,wraplength=465)
        self.feedback.pack(anchor="w",pady=2)
        self.cv.bind("<Configure>",lambda e:self.draw() if hasattr(self,"world") else None)
        self.select(NAMES[0])
        self.animate()
        root.protocol("WM_DELETE_WINDOW",self.close)

    def select(self,name):
        self.game = name
        for n,b in self.choices.items():
            b.config(bg=MINT if n==name else LINE,fg=BG if n==name else INK)
        self.heading.config(text=name + ("  /  6 × 6" if name=="Sudoku" else ""))
        self.caption.config(text={"Sudoku":"The fly tries digits, keeps accepted moves and learns which candidate groups pay off.",
            "Memory pairs":"The fly remembers revealed cards and learns which kinds of flips earn rewards.",
            "Bubble launch":"The fly tests aim angles and learns from the bubbles each shot clears.",
            "Snakes & Ladders":"Two flies race automatically. Every turn is a die roll, so this game records outcomes only."}[name])
        self.start_round()
        self.schedule()

    def start_round(self):
        self.world = WORLDS[self.game](self.rng)
        self.moves = self.reward = 0
        self.finished = False
        self.shot_progress = 1
        self.status.config(text="Observing a fresh board…")
        self.feedback.config(text="The next action is chosen automatically.")
        self.target = (self.cv.winfo_width()/2,145)
        self.draw()
        self.stats()

    def stats(self):
        records = self.brain.results[self.game]
        phase = [r for r in records if r["training"]==self.training]
        wins = sum(r["won"] for r in phase)
        outcome = "fly 1 wins" if self.game=="Snakes & Ladders" else "wins"
        self.metrics.config(text=f"{self.moves} moves · round reward {self.reward:+d}   |   {len(phase)} completed · {wins} {outcome} in this mode")

    def schedule(self):
        if self.tick_id is not None:
            self.root.after_cancel(self.tick_id)
            self.tick_id = None
        if self.running:
            delay = {"Fast":65,"Watch":700,"Slow":1500}[self.speed.get()]
            self.tick_id = self.root.after(delay,self.step)

    def step(self):
        self.tick_id = None
        if not self.running:
            return
        if self.finished:
            self.start_round()
        else:
            action,key = self.brain.choose(self.game,self.world.actions(),self.rng,self.training)
            reward,ended,won,info = self.world.move(action)
            self.moves += 1
            self.reward += reward
            trainable = self.game!="Snakes & Ladders"
            if self.training and trainable:
                self.brain.learn(self.game,key,reward)
            self.finished = ended or self.moves>=500
            if self.finished:
                self.brain.results[self.game].append(dict(moves=self.moves,won=bool(ended and won),training=self.training))
            self.status.config(text=info + ("   ·   Round complete" if self.finished else ""))
            if trainable:
                visits,mean = self.brain.values[self.game].get(key,[0,0])
                self.feedback.config(text=f"{key}  /  reward {reward:+d}  /  learned mean {mean:+.2f} from {visits} trials")
            else:
                self.feedback.config(text="Chance simulation · no policy update")
            self.shot_progress = 0 if isinstance(self.world,Bubbles) and action is not None else 1
            self.draw()
            self.stats()
        self.schedule()

    def toggle(self):
        self.running = not self.running
        self.pause.config(text="Pause" if self.running else "Resume")
        self.schedule()

    def switch_mode(self):
        self.training = not self.training
        self.badge.config(text="AUTONOMOUS  /  "+("TRAINING" if self.training else "EVALUATION"))
        self.mode.config(text="Evaluate policy" if self.training else "Train fly")
        self.start_round()
        self.schedule()

    def save(self):
        path = filedialog.asksaveasfilename(defaultextension=".json",filetypes=[("Fly result","*.json")])
        if path:
            try:
                self.brain.save(path)
                self.feedback.config(text="Saved learned action values and completed round results.")
            except OSError as err:
                messagebox.showerror("Could not save",str(err))

    def load(self):
        path = filedialog.askopenfilename(filetypes=[("Fly result","*.json")])
        if path:
            try:
                brain = Brain.load(path)
            except (OSError,ValueError,OverflowError) as err:
                messagebox.showerror("Could not load",str(err))
                return
            self.brain = brain
            self.training = True
            self.switch_mode()
            self.feedback.config(text="Loaded result. Evaluating the saved policy on a fresh board.")

    def draw(self):
        cv,w = self.cv,self.world
        cv.delete("all")
        ox = (max(380,cv.winfo_width())-320)/2
        if isinstance(w,Sudoku):
            for i,value in enumerate(w.board):
                r,c = divmod(i,6)
                x,y = ox+c*52,10+r*52
                cv.create_rectangle(x,y,x+50,y+50,fill="#385449" if self.moves and i==w.focus else "#243442",outline="")
                if value:
                    cv.create_text(x+25,y+25,text=value,font=("Consolas",21,"bold"),fill=INK if w.givens[i] else MINT)
                if i==w.focus:
                    self.target = (x+40,y+12)
            for k in (2,4):
                cv.create_line(ox,9+52*k,ox+311,9+52*k,fill=GOLD,width=2)
            cv.create_line(ox+155,10,ox+155,321,fill=GOLD,width=2)
        elif isinstance(w,Memory):
            for i in range(16):
                r,c = divmod(i,4)
                x,y = ox+c*80,10+r*78
                visible = i in w.show or i in w.matched
                cv.create_rectangle(x,y,x+74,y+70,fill="#315449" if i in w.matched else LINE,outline="")
                cv.create_text(x+37,y+35,text=w.deck[i] if visible else "·",fill=MINT if visible else MUTED,font=("Georgia",24))
                if i==w.focus:
                    self.target = (x+60,y+16)
        elif isinstance(w,Race):
            def pos(n):
                r,c = divmod(max(1,n)-1,10)
                return ox+(9-c if r%2 else c)*32+16,16+(9-r)*32
            for n in range(1,101):
                x,y = pos(n)
                cv.create_rectangle(x-15,y-15,x+15,y+15,fill=LINE,outline="")
            for a,b in PORTALS.items():
                cv.create_line(*pos(a),*pos(b),fill=MINT if b>a else COLORS[2],width=2,arrow="last")
            for n in range(1,101):
                x,y = pos(n)
                cv.create_text(x-6,y-6,text=n,font=("Consolas",8),fill=INK)
            for p,n in enumerate(w.pos):
                if n:
                    x,y = pos(n)
                    cv.create_text(x-5+11*p,y+4,text=str(p+1),fill=COLORS[p],font=("Consolas",13,"bold"))
            self.target = pos(w.focus)
        else:
            active = self.shot_progress<1 and bool(w.path)
            board = w.before if active else w.board
            for q,color in board.items():
                x,y = center(q)
                self.orb(ox+x,y,color)
            cv.create_line(ox,286,ox+320,286,dash=(4,5),fill=COLORS[2])
            cv.create_polygon(ox+145,325,ox+175,325,ox+160,294,fill=MUTED)
            if active:
                x,y = w.path[min(len(w.path)-1,int(self.shot_progress*len(w.path)))]
                self.orb(ox+x,y,w.last_color)
            else:
                self.orb(ox+160,316,w.color)
            self.target = (ox+w.focus[0],w.focus[1])
        fly_sprite(cv,*self.xy,self.frame*.32)

    def orb(self,x,y,color):
        self.cv.create_oval(x-14,y-14,x+14,y+14,fill=COLORS[color],outline=BG)
        self.cv.create_text(x,y,text="ABCD"[color],fill=BG,font=("Consolas",11,"bold"))

    def animate(self):
        if self.running:
            self.frame += 1
            self.xy = tuple(v+(t-v)*.24 for v,t in zip(self.xy,self.target))
            if self.shot_progress<1:
                self.shot_progress = min(1,self.shot_progress+.09)
                self.draw()
            else:
                self.cv.delete("fly")
                fly_sprite(self.cv,*self.xy,self.frame*.32)
        self.animation_id = self.root.after(32,self.animate)

    def close(self):
        for timer in (self.tick_id,self.animation_id):
            if timer is not None:
                self.root.after_cancel(timer)
        self.root.destroy()


if __name__ == "__main__":
    window = tk.Tk()
    Lab(window)
    window.mainloop()
