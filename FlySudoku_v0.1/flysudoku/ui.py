from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import threading
from .environment import SudokuEnv, valid
from .agent import LinearAgent
from .experiment import train, evaluate, EXPERIMENTS

BG, PANEL, FG, MUTED, ACCENT = "#0b1020", "#141d33", "#edf2ff", "#91a0bd", "#8b7cff"
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FlySudoku | Learning Lab")
        self.geometry("1040x720")
        self.minsize(900, 650)
        self.configure(bg=BG)
        self.env = SudokuEnv(seed=2026)
        self.agent = LinearAgent()
        self.selected = None
        self.training = False
        self._style()
        self._build()
        self._draw_board()
        self._refresh_stats()

    def _style(self):
        s = ttk.Style(self); s.theme_use("clam")
        s.configure("TNotebook", background=BG, borderwidth=0)
        s.configure("TNotebook.Tab", background=PANEL, foreground=FG, padding=(18, 10))
        s.map("TNotebook.Tab", background=[("selected", ACCENT)])
        s.configure("TProgressbar", troughcolor=PANEL, background=ACCENT)

    def _build(self):
        header = tk.Frame(self, bg=BG); header.pack(fill="x", padx=26, pady=(22, 12))
        tk.Label(header, text="FLYSUDOKU", bg=BG, fg=FG, font=("Segoe UI", 23, "bold")).pack(side="left")
        tk.Label(header, text="  /  LEARNING LAB  ·  V0.1", bg=BG, fg=ACCENT, font=("Segoe UI", 10, "bold")).pack(side="left", pady=(9,0))
        self.status = tk.StringVar(value="Ready · untrained policy")
        tk.Label(header, textvariable=self.status, bg=BG, fg=MUTED, font=("Segoe UI", 10)).pack(side="right", pady=12)
        self.tabs = ttk.Notebook(self); self.tabs.pack(fill="both", expand=True, padx=24, pady=10)
        self.play_tab = tk.Frame(self.tabs, bg=BG); self.train_tab = tk.Frame(self.tabs, bg=BG)
        self.tabs.add(self.play_tab, text="  PLAY  "); self.tabs.add(self.train_tab, text="  TRAIN & EVALUATE  ")
        self._build_play(); self._build_train()
        footer = tk.Label(self, text="OFFLINE EXPERIMENT  •  NO PRETRAINED SUDOKU SOLVER  •  PYTHON STANDARD LIBRARY",
                          bg=BG, fg="#64728f", font=("Segoe UI", 8))
        footer.pack(pady=(0,12))

    def _card(self, parent, title):
        frame = tk.Frame(parent, bg=PANEL, highlightbackground="#273452", highlightthickness=1)
        tk.Label(frame, text=title.upper(), bg=PANEL, fg=MUTED, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=16, pady=(13,8))
        return frame

    def _build_play(self):
        left = tk.Frame(self.play_tab, bg=BG); left.pack(side="left", fill="both", expand=True, padx=(0,12), pady=16)
        right = tk.Frame(self.play_tab, bg=BG); right.pack(side="right", fill="y", padx=(12,0), pady=16)
        self.board_frame = tk.Frame(left, bg=BG); self.board_frame.pack(pady=12)
        self.cells = []
        for r in range(4):
            row=[]
            for c in range(4):
                b=tk.Button(self.board_frame, text="", width=4, height=2, font=("Segoe UI",22,"bold"),
                            bg="#18243d", fg=FG, activebackground="#35466b", relief="flat",
                            command=lambda rr=r,cc=c:self._select(rr,cc))
                b.grid(row=r,column=c,padx=(3 if c%2==0 else 1,3),pady=(3 if r%2==0 else 1,3))
                row.append(b)
            self.cells.append(row)
        self.message = tk.StringVar(value="Select an empty cell, then choose a digit.")
        tk.Label(left, textvariable=self.message, bg=BG, fg=MUTED, font=("Segoe UI",11), wraplength=480).pack(pady=8)
        actions=self._card(right,"Actions"); actions.pack(fill="x", pady=(0,12))
        inner=tk.Frame(actions,bg=PANEL); inner.pack(padx=14,pady=(0,14))
        for i in range(1,5):
            tk.Button(inner,text=str(i),width=4,bg="#273653",fg=FG,relief="flat",
                      font=("Segoe UI",13,"bold"),command=lambda v=i:self._place(v)).grid(row=0,column=i-1,padx=3,pady=4)
        for label,cmd in [("New puzzle",self._new_puzzle),("Solve check",self._check),("Agent move",self._agent_move)]:
            tk.Button(inner,text=label,bg=ACCENT if label=="Agent move" else "#273653",fg="white",
                      relief="flat",width=17,pady=8,command=cmd).grid(sticky="ew",pady=4)
        info=self._card(right,"Experiment"); info.pack(fill="x")
        self.stats=tk.StringVar()
        tk.Label(info,textvariable=self.stats,bg=PANEL,fg=FG,justify="left",font=("Consolas",10),wraplength=230).pack(padx=14,pady=(0,14))

    def _build_train(self):
        wrap=tk.Frame(self.train_tab,bg=BG); wrap.pack(fill="both",expand=True,padx=24,pady=24)
        card=self._card(wrap,"Training configuration"); card.pack(fill="x")
        row=tk.Frame(card,bg=PANEL); row.pack(fill="x",padx=16,pady=(0,16))
        tk.Label(row,text="Episodes",bg=PANEL,fg=FG).pack(side="left")
        self.episodes=tk.StringVar(value="500")
        tk.Entry(row,textvariable=self.episodes,width=10,bg="#202d49",fg=FG,insertbackground=FG,relief="flat").pack(side="left",padx=10,ipady=7)
        tk.Label(row,text="Seed",bg=PANEL,fg=FG).pack(side="left",padx=(20,0))
        self.seed=tk.StringVar(value="2026")
        tk.Entry(row,textvariable=self.seed,width=10,bg="#202d49",fg=FG,insertbackground=FG,relief="flat").pack(side="left",padx=10,ipady=7)
        self.train_button=tk.Button(row,text="TRAIN AGENT",bg=ACCENT,fg="white",relief="flat",padx=20,pady=9,command=self._start_training)
        self.train_button.pack(side="right")
        self.progress=ttk.Progressbar(wrap,mode="determinate",maximum=100); self.progress.pack(fill="x",pady=16)
        self.train_log=tk.Text(wrap,height=14,bg=PANEL,fg=FG,insertbackground=FG,relief="flat",font=("Consolas",10),state="disabled")
        self.train_log.pack(fill="both",expand=True)
        controls=tk.Frame(wrap,bg=BG); controls.pack(fill="x",pady=12)
        tk.Button(controls,text="Evaluate on 100 unseen puzzles",bg="#273653",fg=FG,relief="flat",padx=16,pady=10,command=self._evaluate).pack(side="left")
        tk.Button(controls,text="Load checkpoint",bg="#273653",fg=FG,relief="flat",padx=16,pady=10,command=self._load).pack(side="left",padx=10)
        tk.Button(controls,text="Save checkpoint",bg="#273653",fg=FG,relief="flat",padx=16,pady=10,command=self._save).pack(side="left")
        self.eval_result=tk.StringVar(value="Evaluation has not been run.")
        tk.Label(wrap,textvariable=self.eval_result,bg=BG,fg=ACCENT,font=("Segoe UI",11)).pack(anchor="w",pady=5)

    def _draw_board(self):
        for r in range(4):
            for c in range(4):
                v=self.env.board[r][c]; fixed=(r,c) in self.env.fixed
                bg="#263755" if fixed else ("#352f63" if self.selected==(r,c) else "#18243d")
                self.cells[r][c].configure(text=str(v) if v else "·",bg=bg,
                    fg="#ffffff" if fixed or v else "#aab8d3")
    def _select(self,r,c):
        if (r,c) in self.env.fixed: self.message.set("That is a fixed clue."); return
        self.selected=(r,c); self._draw_board()
    def _place(self,v):
        if self.selected is None: self.message.set("Select an empty cell first."); return
        r,c=self.selected
        _,reward,done,msg=self.env.step((r,c,v))
        self.message.set(f"{msg}  (feedback {reward:+.0f})")
        self._draw_board(); self._refresh_stats()
        if done and self.env.is_solved(): messagebox.showinfo("Solved","Puzzle completed correctly.")
    def _new_puzzle(self):
        self.env=SudokuEnv(seed=self.env.rng.randrange(1_000_000_000)); self.selected=None
        self.message.set("New puzzle generated with a unique solution."); self._draw_board(); self._refresh_stats()
    def _check(self):
        if self.env.is_solved(): self.message.set("Solved correctly.")
        elif self.env.done: self.message.set("This board ended incorrectly.")
        else: self.message.set("Not complete yet. The environment does not reveal the solution.")
    def _agent_move(self):
        actions=self.env.legal_actions()
        if not actions: self.message.set("No locally legal moves remain."); return
        a=self.agent.choose(self.env.observation(),actions)
        _,reward,done,msg=self.env.step(a)
        self.selected=(a[0],a[1]); self.message.set(f"Agent chose cell ({a[0]+1},{a[1]+1}) = {a[2]}. {msg} ({reward:+.0f})")
        self._draw_board(); self._refresh_stats()
    def _refresh_stats(self):
        self.stats.set(f"Agent episodes : {self.agent.episodes}\nFixed clues    : {len(self.env.fixed)}\nEmpty cells     : {sum(v==0 for row in self.env.board for v in row)}\nPolicy weights  : {len(self.agent.weights)}\nMode            : trial & error")
    def _append_log(self,text):
        self.train_log.configure(state="normal"); self.train_log.insert("end",text+"\n"); self.train_log.see("end"); self.train_log.configure(state="disabled")
    def _start_training(self):
        if self.training: return
        try:
            n=int(self.episodes.get()); seed=int(self.seed.get())
            if not 1<=n<=100000: raise ValueError
        except ValueError:
            messagebox.showerror("Invalid settings","Episodes must be an integer from 1 to 100000 and seed must be an integer."); return
        self.training=True; self.train_button.configure(state="disabled")
        self.status.set("Training in progress…"); self.progress.configure(value=0)
        def progress(done,total,reward,solved):
            self.after(0,lambda:self._training_update(done,total,reward,solved))
        def worker():
            try:
                train(self.agent,n,seed,progress)
                self.after(0,lambda:self._training_done(None))
            except Exception as e:
                self.after(0,lambda:self._training_done(e))
        threading.Thread(target=worker,daemon=True).start()
    def _training_update(self,done,total,reward,solved):
        self.progress.configure(value=done*100/max(1,int(self.episodes.get())))
        if done==1 or done%25==0:
            self._append_log(f"Episode {self.agent.episodes:5d} | reward {total:7.2f} | solved {solved}")
    def _training_done(self,error):
        self.training=False; self.train_button.configure(state="normal")
        if error:
            self.status.set("Training error"); self._append_log("ERROR: "+str(error)); messagebox.showerror("Training error",str(error))
        else:
            self.status.set("Training complete"); self._append_log("Checkpoint saved to experiments/agent_checkpoint.json")
        self._refresh_stats()
    def _evaluate(self):
        try:
            result=evaluate(self.agent,100,90210)
            self.eval_result.set(f"Unseen puzzles: {result['solved']}/{result['episodes']} solved ({result['solve_rate']:.1%}) · mean reward {result['mean_reward']:.2f} · mean moves {result['mean_moves']:.1f}")
            self._append_log("Evaluation: "+str(result))
        except Exception as e: messagebox.showerror("Evaluation error",str(e))
    def _save(self):
        try:
            self.agent.save(EXPERIMENTS/"agent_checkpoint.json"); messagebox.showinfo("Saved","Checkpoint saved.")
        except Exception as e: messagebox.showerror("Save error",str(e))
    def _load(self):
        path=EXPERIMENTS/"agent_checkpoint.json"
        if not path.exists(): messagebox.showwarning("No checkpoint","Train the agent first."); return
        try:
            self.agent=LinearAgent.load(path); self._refresh_stats(); messagebox.showinfo("Loaded","Checkpoint loaded.")
        except Exception as e: messagebox.showerror("Load error",str(e))

def main():
    try:
        App().mainloop()
    except Exception as exc:
        messagebox.showerror("FlySudoku startup error", f"{exc}\n\nCheck Python includes Tkinter and run from the project folder.")
        raise
