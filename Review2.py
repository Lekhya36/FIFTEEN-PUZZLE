import random, sys, time, threading, heapq
import tkinter as tk
from tkinter import font as tkfont

sys.setrecursionlimit(500000)

# COLOURS
BG_MAIN         = "#F5F7FA"
BG_PANEL        = "#FFFFFF"
BG_CARD         = "#F0F4F8"
HDR_BG          = "#34495E"
TILE_BG         = "#AED6F1"
TILE_FG         = "#000000"
TILE_CORRECT    = "#A9DFBF"
TILE_CORRECT_FG = "#000000"
EMPTY_BG        = "#D5D8DC"
TRY_BG          = "#8E44AD"
TRY_FG          = "#FFFFFF"
BACK_BG         = "#E74C3C"
BACK_FG         = "#FFFFFF"
HINT_BG         = "#F39C12"
HINT_FG         = "#FFFFFF"
DONE_BG         = "#27AE60"
DONE_FG         = "#FFFFFF"
TEXT_DARK       = "#2C3E50"
TEXT_MID        = "#566573"
TEXT_DIM        = "#AAB7B8"
BTN_START       = "#27AE60"
BTN_RESET       = "#C0392B"
BTN_BLUE        = "#2980B9"
BTN_PURPLE      = "#7D3C98"
BTN_GREY        = "#7F8C8D"
BTN_TEAL        = "#16A085"
BTN_ORANGE      = "#E67E22"
P1_COLOR        = "#2980B9"
P2_COLOR        = "#E67E22"

# ── BOARD HELPERS ───
def make_goal(size):
    return tuple(range(1, size * size)) + (0,)

def get_moves(board, size):
    e = board.index(0); r, c = divmod(e, size); out = []
    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
        nr, nc = r+dr, c+dc
        if 0 <= nr < size and 0 <= nc < size:
            out.append(nr*size + nc)
    return out

def apply_move(board, idx):
    b = list(board); e = b.index(0); b[e], b[idx] = b[idx], b[e]; return tuple(b)

def shuffle_board(size):
    steps = 40 if size == 4 else 30
    b = list(make_goal(size)); prev = None
    for _ in range(steps):
        moves = get_moves(b, size)
        if prev in moves and len(moves) > 1: moves.remove(prev)
        chosen = random.choice(moves); prev = b.index(0)
        b = list(apply_move(tuple(b), chosen))
    return tuple(b)

def moved_tile(prev_b, cur_b):
    for i in range(len(cur_b)):
        if cur_b[i] != prev_b[i] and cur_b[i] != 0: return i
    return None


class PureBacktrackSolver:
    def __init__(self, start, size, goal):
        self.start      = tuple(start)
        self.size       = size
        self.goal_t     = tuple(goal)
        self.trace      = []
        self.backtracks = 0
        self.found      = False

    def solve(self):
        for depth_limit in range(1, 300):
            self.trace = []
            self.found = False
            self._bt([self.start], {self.start}, depth_limit)
            if self.found:
                break
        return self.trace



def _bt(self, path, seen, limit):
        if self.found:
            return
        cur = path[-1]

        moved = None
        if len(path) >= 2:
            prev = path[-2]
            for i in range(len(cur)):
                if cur[i] != prev[i] and cur[i] != 0:
                    moved = i; break

        # PURPLE: trying this move
        self.trace.append(("try", cur, moved))

        if cur == self.goal_t:
            self.trace.append(("done", cur, moved))
            self.found = True
            return

        if len(path) - 1 >= limit:
            return

        for tile_idx in get_moves(list(cur), self.size):
            nb = apply_move(cur, tile_idx)
            if nb in seen:
                continue
            path.append(nb); seen.add(nb)
            self._bt(path, seen, limit)
            path.pop(); seen.discard(nb)
            if self.found:
                return
            # RED: dead end — backtracking
            bt = None
            for i in range(len(nb)):
                if nb[i] != cur[i] and nb[i] != 0:
                    bt = i; break
            self.trace.append(("back", cur, bt))
            self.backtracks += 1

class RuntimeGraph:
    """
    A separate Toplevel window that shows a live line graph of:
      - Steps Tried (purple line)
      - Backtracks   (red line)
    plotted against step number (x-axis) as the solver replays.
    """
    SAMPLE_EVERY = 10   # record a data point every N steps for performance

    def __init__(self, parent):
        self.win = tk.Toplevel(parent)
        self.win.title("Runtime Graph — Backtracks vs Steps")
        self.win.configure(bg=BG_PANEL)
        self.win.resizable(True, True)
        self.win.geometry("520x360")

        # Header
        hdr = tk.Frame(self.win, bg=HDR_BG, pady=8)
        hdr.pack(fill="x")
        hf = tkfont.Font(family="Verdana", size=10, weight="bold")
        tk.Label(hdr, text="RUNTIME GRAPH  —  Steps Tried & Backtracks",
                 font=hf, bg=HDR_BG, fg="#FFFFFF").pack()

        # Legend row
        lf = tk.Frame(self.win, bg=BG_PANEL, pady=4)
        lf.pack()
        sf = tkfont.Font(family="Verdana", size=8)
        for txt, col in [("● Steps Tried", TRY_BG), ("● Backtracks", BACK_BG)]:
            tk.Label(lf, text=txt, font=sf, bg=BG_PANEL, fg=col).pack(side="left", padx=14)

        # Canvas
        self.canvas = tk.Canvas(self.win, bg="#1C2833",
                                highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Data
        self.tries_data  = []   # cumulative tries per sample point
        self.backs_data  = []   # cumulative backtracks per sample point
        self._step_count = 0
        self._tries_cum  = 0
        self._backs_cum  = 0

        self.win.bind("<Configure>", lambda e: self._redraw())

    def reset(self):
        self.tries_data  = []
        self.backs_data  = []
        self._step_count = 0
        self._tries_cum  = 0
        self._backs_cum  = 0
        self.canvas.delete("all")

    def record(self, action):
        """Call this on every step during playback."""
        self._step_count += 1
        if action == "try":
            self._tries_cum += 1
        elif action == "back":
            self._backs_cum += 1

        if self._step_count % self.SAMPLE_EVERY == 0:
            self.tries_data.append(self._tries_cum)
            self.backs_data.append(self._backs_cum)
            self._redraw()

    def finalise(self):
        """Force a final redraw after solve completes."""
        self.tries_data.append(self._tries_cum)
        self.backs_data.append(self._backs_cum)
        self._redraw()

    def _redraw(self):
        c = self.canvas
        c.delete("all")
        W = c.winfo_width()
        H = c.winfo_height()
        if W < 50 or H < 50:
            return

        PAD_L, PAD_R, PAD_T, PAD_B = 52, 20, 20, 36

        n = len(self.tries_data)
        if n < 2:
            c.create_text(W//2, H//2, text="Waiting for data…",
                          fill="#AAB7B8",
                          font=("Verdana", 10))
            return

        # Background grid
        max_val = max(max(self.tries_data, default=1),
                      max(self.backs_data,  default=1), 1)

        chart_w = W - PAD_L - PAD_R
        chart_h = H - PAD_T - PAD_B

        # Grid lines (5 horizontal)
        grid_f = tkfont.Font(family="Verdana", size=7)
        for i in range(6):
            y = PAD_T + chart_h - int(i / 5 * chart_h)
            c.create_line(PAD_L, y, W - PAD_R, y,
                          fill="#2E4053", width=1)
            val = int(i / 5 * max_val)
            c.create_text(PAD_L - 6, y, text=str(val),
                          fill="#AAB7B8", anchor="e",
                          font=grid_f)

        # X-axis labels
        step_total = n * self.SAMPLE_EVERY
        for frac in [0, 0.25, 0.5, 0.75, 1.0]:
            xi = int(frac * (n - 1))
            x  = PAD_L + int(frac * chart_w)
            c.create_text(x, H - PAD_B + 10,
                          text=str(xi * self.SAMPLE_EVERY),
                          fill="#AAB7B8", font=grid_f)

        # Axes
        c.create_line(PAD_L, PAD_T, PAD_L, H - PAD_B,
                      fill="#AAB7B8", width=2)
        c.create_line(PAD_L, H - PAD_B, W - PAD_R, H - PAD_B,
                      fill="#AAB7B8", width=2)

        def to_coords(data, color, width=2):
            pts = []
            for i, val in enumerate(data):
                x = PAD_L + int(i / (n - 1) * chart_w)
                y = PAD_T + chart_h - int(val / max_val * chart_h)
                pts.extend([x, y])
            if len(pts) >= 4:
                c.create_line(*pts, fill=color, width=width,
                              smooth=True)

        to_coords(self.tries_data, TRY_BG,  width=2)
        to_coords(self.backs_data, BACK_BG, width=2)

        # Axis labels
        lf = tkfont.Font(family="Verdana", size=8)
        c.create_text(PAD_L + chart_w // 2, H - 6,
                      text="Step Number", fill="#AAB7B8", font=lf)
        # Rotated Y label via a window trick — just use a short text
        c.create_text(10, PAD_T + chart_h // 2,
                      text="Count", fill="#AAB7B8",
                      font=lf, angle=90)

        # Final values annotation
        ann_f = tkfont.Font(family="Verdana", size=8, weight="bold")
        c.create_text(W - PAD_R - 4,
                      PAD_T + chart_h - int(self.tries_data[-1] / max_val * chart_h) - 10,
                      text=f"{self.tries_data[-1]:,}",
                      fill=TRY_BG, anchor="e", font=ann_f)
        c.create_text(W - PAD_R - 4,
                      PAD_T + chart_h - int(self.backs_data[-1] / max_val * chart_h) + 10,
                      text=f"{self.backs_data[-1]:,}",
                      fill=BACK_BG, anchor="e", font=ann_f)



class Launcher:
    def __init__(self, root):
        self.root = root
        root.title("Sliding Puzzle — Backtracking Visualizer")
        root.geometry("620x440")
        root.configure(bg=BG_MAIN)
        root.resizable(True, True)
        self._build()

    def _build(self):
        tf  = tkfont.Font(family="Georgia",  size=28, weight="bold")
        sf  = tkfont.Font(family="Verdana",  size=9)
        bf  = tkfont.Font(family="Verdana",  size=12, weight="bold")
        smf = tkfont.Font(family="Verdana",  size=9)
        hf  = tkfont.Font(family="Verdana",  size=9,  weight="bold")

        # Header
        hdr = tk.Frame(self.root, bg=HDR_BG, pady=18)
        hdr.pack(fill="x")
        tk.Label(hdr, text="SLIDING PUZZLE",
                 font=tf, bg=HDR_BG, fg="#FFFFFF").pack()
        tk.Label(hdr, text="Backtracking Solver  —  Step-by-Step Visualizer",
                 font=sf, bg=HDR_BG, fg="#AEB6BF").pack(pady=(2,0))

        # Colour legend
        lf = tk.Frame(self.root, bg=BG_MAIN, pady=18); lf.pack()
        tk.Label(lf, text="COLOUR LEGEND", font=hf,
                 bg=BG_MAIN, fg=TEXT_MID).pack(pady=(0,10))
        leg = tk.Frame(lf, bg=BG_MAIN); leg.pack()
        for txt, bg, fg in [
            ("  PURPLE = Trying a move  ",   TRY_BG,  TRY_FG),
            ("  RED = Backtracking!  ",       BACK_BG, BACK_FG),
            ("  GREEN = Correct position  ", DONE_BG, DONE_FG),
        ]:
            b = tk.Frame(leg, bg=bg, padx=14, pady=10); b.pack(side="left", padx=8)
            tk.Label(b, text=txt, font=smf, bg=bg, fg=fg).pack()

        # Puzzle selection cards
        cards = tk.Frame(self.root, bg=BG_MAIN, pady=10)
        cards.pack(fill="x", padx=50)
        cards.columnconfigure(0, weight=1)
        cards.columnconfigure(1, weight=1)
        self._card(cards, "15 PUZZLE", "4 × 4 grid  ·  Numbers 1–15",
                   "#1A5276", BTN_BLUE,  lambda: self._go(4), 0)
        self._card(cards, "25 PUZZLE", "5 × 5 grid  ·  Numbers 1–24  ·  Harder!",
                   "#7D3C98", BTN_PURPLE, lambda: self._go(5), 1)

    def _card(self, parent, title, sub, title_color, btn_color, cmd, col):
        card = tk.Frame(parent, bg=BG_PANEL, padx=24, pady=20,
                        highlightbackground=btn_color, highlightthickness=2)
        card.grid(row=0, column=col, padx=12, pady=8, sticky="nsew")
        bf = tkfont.Font(family="Verdana", size=13, weight="bold")
        sf = tkfont.Font(family="Verdana", size=9)
        tk.Label(card, text=title, font=bf,
                 bg=BG_PANEL, fg=title_color).pack()
        tk.Label(card, text=sub, font=sf,
                 bg=BG_PANEL, fg=TEXT_MID).pack(pady=5)
        tk.Button(card, text=f"▶  Play {title}", font=bf,
                  bg=btn_color, fg="white", relief="flat",
                  padx=14, pady=8, cursor="hand2",
                  activebackground=btn_color, command=cmd).pack(pady=(12,0))

    def _go(self, size):
        self.root.destroy()
        r = tk.Tk()
        PuzzleGame(r, size)
        r.mainloop()




#  PUZZLE GAME
class PuzzleGame:
    def __init__(self, root, size):
        self.root  = root
        self.SIZE  = size
        self.GOAL  = make_goal(size)
        lbl        = "15" if size == 4 else "25"
        root.title(f"{lbl} Puzzle — Backtracking Visualizer")
        root.configure(bg=BG_MAIN)
        root.resizable(True, True)

        w = 920 if size == 4 else 960
        h = 660 if size == 4 else 680
        root.geometry(f"{w}x{h}")

        self.board        = self.GOAL.copy()
        self.is_started   = False
        self.game_over    = False
        self.auto_playing = False
        self.auto_paused  = False
        self.trace        = []
        self.trace_idx    = 0
        self.speed_ms     = 200
        self.last_solver  = None
        self.start_time   = None
        self.elapsed      = 0
        self._total_tries = 0
        self._total_backs = 0
        self._total_steps = 0

        # Runtime graph window (created once, reused)
        self._graph: RuntimeGraph | None = None

        self._fonts()
        self._build()
        self._draw()
        self._clock()

    # ── open / reset graph ───────────────────────────────────────────────────
    def _ensure_graph(self):
        if self._graph is None or not self._graph.win.winfo_exists():
            self._graph = RuntimeGraph(self.root)
        else:
            self._graph.reset()
            self._graph.win.lift()

    def _fonts(self):
        self.F_HDR    = tkfont.Font(family="Georgia", size=15, weight="bold")
        self.F_SUB    = tkfont.Font(family="Verdana", size=8)
        sz            = 24 if self.SIZE == 4 else 18
        self.F_TILE   = tkfont.Font(family="Georgia", size=sz, weight="bold")
        self.F_BTN    = tkfont.Font(family="Verdana", size=9,  weight="bold")
        self.F_STAT_V = tkfont.Font(family="Verdana", size=16, weight="bold")
        self.F_STAT_L = tkfont.Font(family="Verdana", size=8)
        self.F_SEC    = tkfont.Font(family="Verdana", size=8,  weight="bold")
        self.F_STATUS = tkfont.Font(family="Verdana", size=10, weight="bold")
        self.F_ACT    = tkfont.Font(family="Verdana", size=11, weight="bold")

    def _build(self):
        lbl = "15 PUZZLE" if self.SIZE == 4 else "25 PUZZLE"

        top = tk.Frame(self.root, bg=HDR_BG, pady=10)
        top.pack(fill="x")
        tk.Label(top, text=f"{lbl}  —  BACKTRACKING VISUALIZER",
                 font=self.F_HDR, bg=HDR_BG, fg="#FFFFFF").pack(side="left", padx=18)
        tk.Label(top, text="Watch every try, place & backtrack",
                 font=self.F_SUB, bg=HDR_BG, fg="#AEB6BF").pack(side="right", padx=18)

        main = tk.Frame(self.root, bg=BG_MAIN)
        main.pack(fill="both", expand=True, padx=14, pady=12)
        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=0)
        main.rowconfigure(0, weight=1)

        left = tk.Frame(main, bg=BG_MAIN)
        left.grid(row=0, column=0, sticky="nsew")
        left.rowconfigure(0, weight=1)
        left.columnconfigure(0, weight=1)

        self._left_frame = left
        wrap = tk.Frame(left, bg=BG_MAIN)
        wrap.place(relx=0.5, rely=0.5, anchor="center")

        outer = tk.Frame(wrap, bg=HDR_BG, padx=5, pady=5)
        outer.pack()

        self.grid_frame = tk.Frame(outer, bg=HDR_BG)
        self.grid_frame.pack()

        tw = 5 if self.SIZE == 4 else 4
        th = 2

        self.buttons = []
        for i in range(self.SIZE * self.SIZE):
            b = tk.Button(self.grid_frame,
                          text="",
                          font=self.F_TILE,
                          relief="flat",
                          cursor="hand2",
                          width=tw, height=th,
                          bd=0,
                          command=lambda i=i: self._click(i))
            b.grid(row=i//self.SIZE, column=i%self.SIZE,
                   padx=4, pady=4)
            self.buttons.append(b)

        right = tk.Frame(main, bg=BG_PANEL, width=225,
                         highlightbackground="#D5D8DC",
                         highlightthickness=1)
        right.grid(row=0, column=1, sticky="nsew", padx=(14,0))
        right.pack_propagate(False)
        self._build_panel(right)

        bot = tk.Frame(self.root, bg=HDR_BG)
        bot.pack(fill="x", side="bottom")
        self.step_bar = tk.Label(bot, text="Step 0 / 0",
                                 font=self.F_STAT_L, bg=HDR_BG, fg="#AEB6BF",
                                 padx=12, pady=5)
        self.step_bar.pack(side="left")
        self.status = tk.Label(bot,
                               text="Press  START  to begin!",
                               font=self.F_STATUS,
                               bg=HDR_BG, fg="#FFFFFF",
                               pady=7, padx=14, anchor="w")
        self.status.pack(side="left", fill="x", expand=True)

    def _build_panel(self, panel):

        def section(txt):
            tk.Label(panel, text=txt, font=self.F_SEC,
                     bg=BG_PANEL, fg=TEXT_MID).pack(pady=(13,3))

        def div():
            tk.Frame(panel, bg="#E0E7EF", height=1).pack(fill="x", padx=12, pady=5)

        def mkbtn(txt, bg, cmd, p=None):
            b = tk.Button(p or panel, text=txt, font=self.F_BTN,
                          bg=bg, fg="white", relief="flat",
                          pady=9, cursor="hand2",
                          activebackground=bg, command=cmd)
            b.pack(fill="x", padx=12, pady=2)
            return b

        section("STATISTICS")
        sc = tk.Frame(panel, bg=BG_PANEL); sc.pack(fill="x", padx=12)
        self.lbl_tries = self._srow(sc, "Steps tried:", "—")
        self.lbl_backs = self._srow(sc, "Backtracks:",  "—")

        div()
        section("TIME")
        tc = tk.Frame(panel, bg=BG_CARD, padx=10, pady=8)
        tc.pack(fill="x", padx=12)
        self.t_lbl = tk.Label(tc, text="00:00",
                              font=self.F_STAT_V,
                              bg=BG_CARD, fg=BTN_BLUE)
        self.t_lbl.pack()

        div()
        section("LEGEND")
        leg = tk.Frame(panel, bg=BG_PANEL); leg.pack(fill="x", padx=12)
        for txt, color in [("Trying cell",  TRY_BG),
                           ("Backtracking", BACK_BG),
                           ("Correct pos.", TILE_CORRECT)]:
            row = tk.Frame(leg, bg=BG_PANEL, pady=3); row.pack(fill="x")
            dot = tk.Frame(row, bg=color, width=16, height=16)
            dot.pack(side="left", padx=(0,8))
            dot.pack_propagate(False)
            tk.Label(row, text=txt, font=self.F_STAT_L,
                     bg=BG_PANEL, fg=TEXT_DARK).pack(side="left")

        div()
        section("CURRENT ACTION")
        self.action_lbl = tk.Label(panel, text="—",
                                   font=self.F_ACT,
                                   bg=BG_PANEL, fg=TEXT_DARK,
                                   wraplength=195, justify="center")
        self.action_lbl.pack(pady=4, padx=10)

        div()
        mkbtn("▶  START",      BTN_START,  self._start_game)
        mkbtn("↺  RESET",      BTN_RESET,  self._reset)

        div()
        mkbtn("▶  AUTO SOLVE", BTN_PURPLE, self._auto_start)
        # ── Runtime Graph button ──────────────────────────────────────────────
        mkbtn("📈  RUNTIME GRAPH", BTN_BLUE, self._show_graph)

        brow = tk.Frame(panel, bg=BG_PANEL); brow.pack(fill="x", padx=12, pady=2)
        tk.Button(brow, text="◀ Back", font=self.F_BTN,
                  bg=BTN_GREY, fg="white", relief="flat",
                  pady=8, cursor="hand2", activebackground=BTN_GREY,
                  command=self._step_back
                  ).pack(side="left", expand=True, fill="x", padx=(0,3))
        self.btn_pp = tk.Button(brow, text="⏸ Pause", font=self.F_BTN,
                                bg=BTN_BLUE, fg="white", relief="flat",
                                pady=8, cursor="hand2", activebackground=BTN_BLUE,
                                command=self._auto_pause)
        self.btn_pp.pack(side="left", expand=True, fill="x")

        div()
        section("SPEED")
        spf = tk.Frame(panel, bg=BG_PANEL); spf.pack(fill="x", padx=12, pady=4)
        tk.Label(spf, text="Slow", font=self.F_STAT_L,
                 bg=BG_PANEL, fg=TEXT_DIM).pack(side="left")
        self.sv = tk.IntVar(value=640)
        tk.Scale(spf, from_=20, to=820, orient="horizontal",
                 variable=self.sv, bg=BG_PANEL,
                 troughcolor=BG_CARD, highlightthickness=0,
                 showvalue=False, command=self._on_speed
                 ).pack(side="left", fill="x", expand=True)
        tk.Label(spf, text="Fast", font=self.F_STAT_L,
                 bg=BG_PANEL, fg=TEXT_DIM).pack(side="left")

    def _show_graph(self):
        """Open (or re-raise) the runtime graph window."""
        if self._graph is None or not self._graph.win.winfo_exists():
            self._graph = RuntimeGraph(self.root)
        else:
            self._graph.win.lift()
            self._graph.win.focus_force()

    def _srow(self, parent, label, value):
        row = tk.Frame(parent, bg=BG_PANEL, pady=2); row.pack(fill="x")
        tk.Label(row, text=label, font=self.F_STAT_L,
                 bg=BG_PANEL, fg=TEXT_MID, anchor="w").pack(side="left")
        v = tk.Label(row, text=value, font=self.F_BTN,
                     bg=BG_PANEL, fg=TEXT_DARK, anchor="e")
        v.pack(side="right")
        return v

    def _on_speed(self, _=None):
        self.speed_ms = max(20, 840 - self.sv.get())

    def _clock(self):
        if self.is_started and not self.game_over and not self.auto_paused:
            self.elapsed = int(time.time() - self.start_time)
            m, s = divmod(self.elapsed, 60)
            self.t_lbl.config(text=f"{m:02d}:{s:02d}")
        self.root.after(1000, self._clock)

    def _draw(self, hi=None, action=None):
        for i, v in enumerate(self.board):
            btn = self.buttons[i]
            if v == 0:
                btn.config(text="", state="disabled",
                           bg=EMPTY_BG, activebackground=EMPTY_BG)
                continue
            if not self.is_started:
                btn.config(text="?", bg="#D6EAF8", fg="#555555",
                           state="disabled", activebackground="#D6EAF8")
                continue
            bg = TILE_BG
            fg = TILE_FG
            if self.auto_playing and v == self.GOAL[i] and i != hi:
                bg = TILE_CORRECT
                fg = TILE_CORRECT_FG
            if i == hi:
                if action == "try":
                    bg = TRY_BG; fg = TRY_FG
                elif action == "back":
                    bg = BACK_BG; fg = BACK_FG
                elif action == "done":
                    bg = DONE_BG; fg = DONE_FG
            btn.config(text=str(v), bg=bg, fg=fg,
                       state="normal", activebackground=bg)

    def _start_game(self):
        self.board        = shuffle_board(self.SIZE, 12)
        self.is_started   = True
        self.start_time   = time.time()
        self.game_over    = False
        self.auto_playing = False
        self.trace = []; self.trace_idx = 0
        self.last_solver  = None
        self.lbl_tries.config(text="—")
        self.lbl_backs.config(text="—")
        self.action_lbl.config(text="—", fg=TEXT_DARK)
        self.step_bar.config(text="Step 0 / 0")
        self.status.config(
            text="Your Turn!  Click a tile next to the empty space.",
            fg="#FFFFFF")
        self._draw()



    def _reset(self):
        self.board        = shuffle_board(self.SIZE, 12)
        self.is_started   = True
        self.start_time   = time.time()
        self.game_over    = False
        self.auto_playing = False
        self.auto_paused  = False
        self.trace = []; self.trace_idx = 0
        self.last_solver  = None
        self.lbl_tries.config(text="—")
        self.lbl_backs.config(text="—")
        self.action_lbl.config(text="—", fg=TEXT_DARK)
        self.step_bar.config(text="Step 0 / 0")
        self.btn_pp.config(text="⏸ Pause")
        self.status.config(text="Board reset!  Your Turn!", fg="#FFFFFF")
        self._draw()

    def _click(self, idx):
        if self.auto_playing or not self.is_started or self.game_over:
            return
        if idx not in get_moves(self.board, self.SIZE):
            return
        self.board = list(apply_move(tuple(self.board), idx))
        if self.board == self.GOAL:
            self._draw()
            self._popup_solved(manual=True)
        else:
            self._draw()

    def _auto_start(self):
        if self.auto_playing:
            return
        if self.board == self.GOAL:
            self.status.config(text="Already solved! Press RESET first.")
            return
        if not self.is_started:
            self.board      = shuffle_board(self.SIZE, 12)
            self.is_started = True
            self.start_time = time.time()
            self.game_over  = False

        self.status.config(
            text="⏳  Running pure backtracking solver…", fg="#FFFFFF")
        self.action_lbl.config(text="Computing…", fg=BTN_BLUE)
        self.lbl_tries.config(text="—")
        self.lbl_backs.config(text="—")
        self.root.update()

        solver = PureBacktrackSolver(self.board, self.SIZE, self.GOAL)
        solver.solve()
        self.last_solver  = solver
        self.trace        = solver.trace
        self.trace_idx    = 0

        if not self.trace:
            self.status.config(text="No solution found.", fg=BACK_BG)
            return

        self._total_tries = sum(1 for a,_,__ in self.trace if a == "try")
        self._total_backs = sum(1 for a,_,__ in self.trace if a == "back")
        self._total_steps = len(self.trace)

        self.status.config(text="▶  Backtracking in progress…", fg="#FFFFFF")
        self.auto_playing = True
        self.auto_paused  = False
        self.game_over    = False
        self.btn_pp.config(text="⏸ Pause")

        # ── open & reset the runtime graph automatically ──────────────────────
        self._ensure_graph()

        self._play()

    def _play(self):
        if not self.auto_playing or self.auto_paused:
            return
        if self.trace_idx >= len(self.trace):
            self.auto_playing = False
            self.lbl_tries.config(text=f"{self._total_steps:,}")
            self.lbl_backs.config(text=f"{self._total_backs:,}")
            # Finalise graph
            if self._graph and self._graph.win.winfo_exists():
                self._graph.finalise()
            if self.board == self.GOAL:
                self.status.config(
                    text=f"✅  SOLVED!   Steps: {self._total_steps:,}  "
                         f"|  Backtracks: {self._total_backs:,}",
                    fg=DONE_BG)
                self.action_lbl.config(text="SOLVED! ✅", fg=DONE_BG)
                self.root.after(400, lambda: self._popup_solved(manual=False))
            else:
                self.status.config(text="Playback complete.", fg="#AEB6BF")
            return
        self._step_fwd()
        self.root.after(self.speed_ms, self._play)

    def _step_fwd(self):
        if self.trace_idx >= len(self.trace):
            return
        action, board_t, hi = self.trace[self.trace_idx]
        self.board      = list(board_t)
        self.trace_idx += 1

        self._draw(hi=hi, action=action)
        self.step_bar.config(text=f"Step {self.trace_idx} / {len(self.trace)}")

        # ── feed the graph ────────────────────────────────────────────────────
        if self._graph and self._graph.win.winfo_exists():
            self._graph.record(action)

        tile_val = board_t[hi] if (hi is not None and hi < len(board_t)) else "?"
        r = hi//self.SIZE+1 if hi is not None else "?"
        c = hi%self.SIZE+1  if hi is not None else "?"

        if action == "try":
            self.action_lbl.config(
                text=f"Trying ({r}, {c})\nTile  [{tile_val}]",
                fg=TRY_BG)
            self.status.config(
                text=f"🟣  Trying →  Tile [{tile_val}]  moved forward   "
                     f"│  Step {self.trace_idx}/{len(self.trace)}",
                fg="#FFFFFF")

        elif action == "back":
            self.action_lbl.config(
                text=f"Backtracking\nfrom ({r}, {c})",
                fg=BACK_BG)
            self.status.config(
                text=f"🔴  BACKTRACKING!  Tile [{tile_val}]  at ({r},{c}) — dead end, undoing!   "
                     f"│  Step {self.trace_idx}/{len(self.trace)}",
                fg=BACK_BG)

        elif action == "done":
            self.action_lbl.config(text="SOLVED! ✅", fg=DONE_BG)
            self.status.config(
                text="★  SOLUTION FOUND!  All tiles in correct position!",
                fg=DONE_BG)

    def _step_back(self):
        if not self.last_solver or self.trace_idx < 2:
            return
        self.trace_idx -= 2
        action, board_t, hi = self.trace[self.trace_idx]
        self.board = list(board_t)
        self.trace_idx += 1
        self._draw(hi=hi, action=action)
        self.step_bar.config(text=f"Step {self.trace_idx} / {len(self.trace)}")

    def _auto_pause(self):
        if not self.auto_playing:
            return
        self.auto_paused = not self.auto_paused
        if self.auto_paused:
            self._paused_at = time.time()
            self.btn_pp.config(text="▶ Resume")
            self.status.config(
                text="⏸  Paused.  Press Resume to continue.", fg="#FFFFFF")
        else:
            self.start_time += time.time() - self._paused_at
            self.btn_pp.config(text="⏸ Pause")
            self.status.config(text="▶  Resuming…", fg="#FFFFFF")
            self._play()


    def _popup_solved(self, manual=False):
        self.game_over = True

        pop = tk.Toplevel(self.root)
        pop.title("🏆 Puzzle Solved!")
        pop.configure(bg=BG_PANEL)
        pop.resizable(False, False)
        pop.transient(self.root)
        pop.grab_set()

        ph = 260 if not manual else 220
        pw = 400
        rx = self.root.winfo_x() + (self.root.winfo_width()  - pw) // 2
        ry = self.root.winfo_y() + (self.root.winfo_height() - ph) // 2
        pop.geometry(f"{pw}x{ph}+{rx}+{ry}")

        hdr = tk.Frame(pop, bg=DONE_BG, pady=14); hdr.pack(fill="x")
        tk.Label(hdr, text="🏆  GAME SOLVED!",
                 font=tkfont.Font(family="Georgia", size=18, weight="bold"),
                 bg=DONE_BG, fg="white").pack()

        body = tk.Frame(pop, bg=BG_PANEL, pady=14); body.pack(fill="x", padx=30)

        if not manual and self.last_solver:
            for label, val, color in [
                ("Steps Tried",  f"{self._total_steps:,}",  BTN_PURPLE),
                ("Backtracks",   f"{self._total_backs:,}",  BTN_RESET),
            ]:
                row = tk.Frame(body, bg=BG_CARD, padx=16, pady=10)
                row.pack(fill="x", pady=4)
                tk.Label(row, text=label,
                         font=tkfont.Font(family="Verdana", size=9),
                         bg=BG_CARD, fg=TEXT_MID, anchor="w").pack(side="left")
                tk.Label(row, text=val,
                         font=tkfont.Font(family="Verdana", size=14, weight="bold"),
                         bg=BG_CARD, fg=color, anchor="e").pack(side="right")
        else:
            tk.Label(body, text="You solved it manually!\nGreat job! 🎉",
                     font=tkfont.Font(family="Verdana", size=11),
                     bg=BG_PANEL, fg=TEXT_DARK, justify="center").pack(pady=6)

        bf = tkfont.Font(family="Verdana", size=10, weight="bold")
        btn_row = tk.Frame(pop, bg=BG_PANEL, pady=10); btn_row.pack()
        tk.Button(btn_row, text="▶  Play Again", font=bf,
                  bg=BTN_START, fg="white", relief="flat",
                  padx=20, pady=8, cursor="hand2",
                  command=lambda: [pop.destroy(), self._reset()]
                  ).pack(side="left", padx=10)
        tk.Button(btn_row, text="✕  Close", font=bf,
                  bg=BTN_GREY, fg="white", relief="flat",
                  padx=20, pady=8, cursor="hand2",
                  command=pop.destroy
                  ).pack(side="left", padx=10)

if __name__ == "__main__":
    root = tk.Tk()
    Launcher(root)
    root.mainloop()
