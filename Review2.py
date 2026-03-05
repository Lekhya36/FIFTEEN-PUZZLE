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




def _branch_worker(args):
    """
    Runs in a dedicated OS process (via ProcessPoolExecutor).
    Solves gbfs_zone from the board state reached after making
    one specific first_move.  Returns full path or None.
    """
    (board, first_move, empty_pos,
     size, goal_t,
     solve_positions, locked,
     max_nodes, fill_only, working_zone) = args

    next_board = swap_board(board, empty_pos, first_move)
    path = gbfs_zone(next_board, size, goal_t,
                     solve_positions, locked,
                     max_nodes, fill_only, working_zone)
    if path:
        return [board] + list(path)   # prepend original board
    return None


# PARALLEL ZONE SOLVER
#
# TRUE parallelism via ProcessPoolExecutor (separate OS processes,
# no GIL contention):
#
#   1. Enumerate every tile adjacent to the empty cell = N candidates.
#   2. Build one job per candidate (removing that tile = one first move).
#   3. Submit ALL jobs to ProcessPoolExecutor at once.
#      → N processes run simultaneously on N CPU cores.
#   4. collect_first_done = False: wait for ALL to finish, pick shortest.
#      This ensures we always get the globally best path, not just the
#      first one to finish (which might be longer).
#   5. Return the shortest path → played back sequentially in the UI.

def parallel_solve_zone(board, size, goal_t, solve_positions, locked=None,
                        max_nodes=300000, fill_only=False, working_zone=None):
    board = tuple(board)
    if locked is None:
        locked = set()

    e           = board.index(0)
    valid_moves = get_valid_moves(list(board), size)

    # Filter to moves allowed by zone and lock constraints
    first_moves = []
    for m in valid_moves:
        if m in locked:
            continue
        if working_zone is not None and (e not in working_zone or
                                          m not in working_zone):
            continue
        first_moves.append(m)

    if not first_moves:
        return gbfs_zone(board, size, goal_t, solve_positions, locked,
                         max_nodes, fill_only, working_zone)

    # Pack all args as plain picklable types.
    # Sets → frozensets so they survive the pickle round-trip.
    jobs = [
        (board, m, e, size, tuple(goal_t),
         frozenset(solve_positions),
         frozenset(locked),
         max_nodes, fill_only,
         frozenset(working_zone) if working_zone is not None else None)
        for m in first_moves
    ]

    results = []
    try:
        # ProcessPoolExecutor: each job runs in a true separate OS process.
        # All N jobs are submitted at once → N-way real parallelism.
        with concurrent.futures.ProcessPoolExecutor(
                max_workers=len(jobs)) as executor:
            futures = [executor.submit(_branch_worker, job) for job in jobs]
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    if result is not None:
                        results.append(result)
                except Exception:
                    pass
    except Exception:
        pass   # multiprocessing unavailable → fall through to single-process

    if results:
        return min(results, key=len)   # shortest path across all branches

    # Single-process fallback
    return gbfs_zone(board, size, goal_t, solve_positions, locked,
                     max_nodes, fill_only, working_zone)




# GBFS FULL-BOARD 

def gbfs_full(board, goal_t, size, locked=None, max_nodes=500000):
    board  = tuple(board)
    goal_t = tuple(goal_t)
    if locked is None:
        locked = set()
    if board == goal_t:
        return [board]

    goal_pos = {}
    for i, v in enumerate(goal_t):
        if v != 0:
            goal_pos[v] = divmod(i, size)

    def h(b):
        dist = 0
        for i, v in enumerate(b):
            if v == 0:
                continue
            if v in goal_pos:
                gr, gc = goal_pos[v]
                cr, cc = divmod(i, size)
                dist += abs(gr - cr) + abs(gc - cc)
        return dist

    def locked_ok(b):
        return all(b[idx] == goal_t[idx] for idx in locked)

    parent  = {board: None}
    visited = set()
    heap    = [(h(board), board)]
    nodes   = 0

    while heap:
        f, state = heapq.heappop(heap)
        if state in visited:
            continue
        visited.add(state)
        nodes += 1
        if nodes > max_nodes:
            break

        if state == goal_t:
            path = []
            cur  = state
            while cur is not None:
                path.append(cur)
                cur = parent[cur]
            return list(reversed(path))

        prev_state = parent[state]
        e = state.index(0)
        for m in get_valid_moves(list(state), size):
            ns = swap_board(state, e, m)
            if ns in visited:
                continue
            # Anti-backtrack
            if prev_state is not None and ns == prev_state:
                continue
            if not locked_ok(ns):
                continue
            if ns not in parent:
                parent[ns] = state
                heapq.heapp

def move_tile_into_zone(board, size, tile_value, target_zone, locked=None):
    board = tuple(board)
    if locked is None:
        locked = set()

    try:
        tile_pos = board.index(tile_value)
    except ValueError:
        return None

    if tile_pos in target_zone:
        return [board]

    def h(state):
        t_pos = state.index(tile_value)
        e_pos = state.index(0)
        tr, tc = divmod(t_pos, size)
        min_t_dist = min(
            abs(divmod(z, size)[0] - tr) + abs(divmod(z, size)[1] - tc)
            for z in target_zone
        )
        er, ec = divmod(e_pos, size)
        e_to_t = abs(tr - er) + abs(tc - ec)
        return min_t_dist * 3 + e_to_t

    parent  = {board: (None, 0)}
    visited = set()
    heap    = [(h(board), 0, board)]

    while heap:
        f, g, state = heapq.heappop(heap)
        if state in visited:
            continue
        visited.add(state)

        if state.index(tile_value) in target_zone:
            path = []
            cur  = state
            while cur is not None:
                path.append(cur)
                cur = parent[cur][0]
            return list(reversed(path))

        prev_state = parent[state][0]
        e = state.index(0)
        for m in get_valid_moves(list(state), size):
            if m in locked:
                continue
            ns = swap_board(state, e, m)
            if ns in visited:
                continue
            # Anti-backtrack
            if prev_state is not None and ns == prev_state:
                continue
            if ns not in parent or parent[ns][1] > g + 1:
                parent[ns] = (state, g + 1)
                heapq.heappush(heap, (h(ns) + g + 1, g + 1, ns))

    return None

# ─────────────────────────────────────────────────────────────
# RUNTIME GRAPH
# ─────────────────────────────────────────────────────────────
def show_runtime_graph(step_times):
    """Show a line chart of solve time (ms) per step after puzzle completion."""
    labels = [f"Step {i}" for i in range(len(step_times))]
    values = [t * 1000 for t in step_times]          # seconds → ms

    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_facecolor("#EAF6F6")
    ax.set_facecolor("#f0fbf8")

    x = list(range(len(labels)))

    ax.plot(x, values, color="#2563eb", linewidth=2.5,
            marker="o", markersize=8, markerfacecolor="#10b981",
            markeredgecolor="white", markeredgewidth=1.5)
    ax.fill_between(x, values, alpha=0.12, color="#2563eb")

    for xi, yi in zip(x, values):
        ax.annotate(f"{yi:.1f} ms", (xi, yi),
                    textcoords="offset points", xytext=(0, 10),
                    ha="center", fontsize=9, color="#1e3a5f")

    avg = sum(values) / len(values)
    ax.axhline(avg, color="#f59e0b", linestyle="--",
               linewidth=1.3, label=f"Avg: {avg:.1f} ms")

    ax.set_title("D&C Solver — Compute Time per Step",
                 fontsize=13, fontweight="bold", color="#1e3a5f", pad=12)
    ax.set_xlabel("Step", fontsize=11, color="#374151")
    ax.set_ylabel("Time (ms)", fontsize=11, color="#374151")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    ax.tick_params(colors="#374151")
    ax.grid(color="#d1fae5", linestyle="--", linewidth=0.8)
    for spine in ax.spines.values():
        spine.set_edgecolor("#A9DFBF")

    ax.legend(facecolor="#EAF6F6", labelcolor="#374151", fontsize=10)
    plt.tight_layout()
    plt.show()

# GAME CLASS

class PuzzleGame:
    def __init__(self, root, size):
        self.root = root; self.SIZE = size; self.GOAL = make_goal(size)
        lbl = "15" if size == 4 else "25"
        root.title(f"{lbl} Puzzle — Player vs CPU")
        root.configure(bg=BG_MAIN); root.resizable(True, True)
        root.geometry("1040x760" if size == 4 else "1080x780")

        self.board          = list(self.GOAL)
        self.is_started     = False
        self.game_over      = False
        self.computing      = False
        self.current_turn   = "player"
        self.auto_mode      = False
        self.auto_paused    = False
        self.trace          = []
        self.trace_idx      = 0
        self._total_steps   = 0
        self._total_backs   = 0
        self.p1_moves       = 0
        self.cpu_steps_done = 0
        self._hi            = None
        self._hi_action     = None
        self._hint_idx      = None
        self._solution      = []
        self._solve_ms      = 0.0
        self.start_time     = None

        self._fonts(); self._build_ui(); self._draw(); self._clock()

    def _fonts(self):
        sz = 24 if self.SIZE == 4 else 18
        self.F_HDR    = tkfont.Font(family="Georgia", size=15, weight="bold")
        self.F_SUB    = tkfont.Font(family="Verdana", size=8)
        self.F_TILE   = tkfont.Font(family="Georgia", size=sz, weight="bold")
        self.F_BTN    = tkfont.Font(family="Verdana", size=9,  weight="bold")
        self.F_STAT_V = tkfont.Font(family="Verdana", size=16, weight="bold")
        self.F_STAT_L = tkfont.Font(family="Verdana", size=8)
        self.F_SEC    = tkfont.Font(family="Verdana", size=8,  weight="bold")
        self.F_STATUS = tkfont.Font(family="Verdana", size=10, weight="bold")
        self.F_ACT    = tkfont.Font(family="Verdana", size=10, weight="bold")
        self.F_TURN   = tkfont.Font(family="Georgia", size=13, weight="bold")

    def _build_ui(self):
        lbl = "15 PUZZLE" if self.SIZE == 4 else "25 PUZZLE"

        top = tk.Frame(self.root, bg=HDR_BG, pady=10); top.pack(fill="x")
        tk.Label(top, text=f"{lbl}  —  PLAYER vs CPU",
                 font=self.F_HDR, bg=HDR_BG, fg="#FFFFFF").pack(side="left", padx=18)
        tk.Label(top, text="Shared board  ·  One move each",
                 font=self.F_SUB, bg=HDR_BG, fg="#AEB6BF").pack(side="right", padx=18)

        main = tk.Frame(self.root, bg=BG_MAIN)
        main.pack(fill="both", expand=True, padx=14, pady=12)
        main.columnconfigure(0, weight=1); main.columnconfigure(1, weight=0)
        main.rowconfigure(0, weight=1)

        left = tk.Frame(main, bg=BG_MAIN)
        left.grid(row=0, column=0, sticky="nsew")
        left.rowconfigure(0, weight=1); left.columnconfigure(0, weight=1)
        wrap = tk.Frame(left, bg=BG_MAIN)
        wrap.place(relx=0.5, rely=0.5, anchor="center")

        self.turn_banner = tk.Label(wrap, text="", font=self.F_TURN,
                                     bg=P1_COLOR, fg="white", pady=10, padx=20)
        self.turn_banner.pack(fill="x", pady=(0,8))

        outer = tk.Frame(wrap, bg=HDR_BG, padx=5, pady=5); outer.pack()
        self.grid_frame = tk.Frame(outer, bg=HDR_BG); self.grid_frame.pack()
        tw = 5 if self.SIZE == 4 else 4
        self.buttons = []
        for i in range(self.SIZE * self.SIZE):
            b = tk.Button(self.grid_frame, text="", font=self.F_TILE,
                          relief="flat", cursor="hand2",
                          width=tw, height=2, bd=0,
                          command=lambda i=i: self._click(i))
            b.grid(row=i//self.SIZE, column=i%self.SIZE, padx=4, pady=4)
            self.buttons.append(b)

        score_row = tk.Frame(wrap, bg=BG_MAIN); score_row.pack(fill="x", pady=(8,0))
        tk.Label(score_row, text="Your moves:", font=self.F_STAT_L,
                 bg=BG_MAIN, fg=TEXT_MID).pack(side="left")
        self.p1_moves_lbl = tk.Label(score_row, text="0", font=self.F_BTN,
                                      bg=BG_MAIN, fg=P1_COLOR)
        self.p1_moves_lbl.pack(side="left", padx=(4,24))
        tk.Label(score_row, text="CPU steps:", font=self.F_STAT_L,
                 bg=BG_MAIN, fg=TEXT_MID).pack(side="left")
        self.cpu_steps_lbl = tk.Label(score_row, text="0", font=self.F_BTN,
                                       bg=BG_MAIN, fg=P2_COLOR)
        self.cpu_steps_lbl.pack(side="left", padx=(4,0))

        right = tk.Frame(main, bg=BG_PANEL, width=244,
                         highlightbackground="#D5D8DC", highlightthickness=1)
        right.grid(row=0, column=1, sticky="nsew", padx=(14,0))
        right.pack_propagate(False)
        self._build_panel(right)

        bot = tk.Frame(self.root, bg=HDR_BG); bot.pack(fill="x", side="bottom")
        self.step_bar = tk.Label(bot, text="Steps: 0 / 0",
                                 font=self.F_STAT_L, bg=HDR_BG, fg="#AEB6BF",
                                 padx=12, pady=5)
        self.step_bar.pack(side="left")
        self.status = tk.Label(bot, text="Press  START  to begin!",
                               font=self.F_STATUS, bg=HDR_BG, fg="#FFFFFF",
                               pady=7, padx=14, anchor="w")
        self.status.pack(side="left", fill="x", expand=True)

    def _build_panel(self, p):
        def sec(t):
            tk.Label(p, text=t, font=self.F_SEC,
                     bg=BG_PANEL, fg=TEXT_MID).pack(pady=(10,3))
        def div():
            tk.Frame(p, bg="#E0E7EF", height=1).pack(fill="x", padx=12, pady=3)
        def mkbtn(t, bg, cmd):
            b = tk.Button(p, text=t, font=self.F_BTN, bg=bg, fg="white",
                          relief="flat", pady=8, cursor="hand2",
                          activebackground=bg, command=cmd)
            b.pack(fill="x", padx=12, pady=2); return b

        sec("HOW TO PLAY")
        tk.Label(p, text="1. YOU move one tile\n2. CPU makes ONE step\n3. Alternate until solved!",
                 font=self.F_STAT_L, bg=BG_PANEL, fg=TEXT_DARK,
                 justify="left").pack(padx=16, pady=2, anchor="w")

        div(); sec("CURRENT TURN")
        self.turn_card = tk.Label(p, text="--", font=self.F_TURN,
                                   bg=BG_CARD, fg=TEXT_DARK, pady=9)
        self.turn_card.pack(fill="x", padx=12)

        div(); sec("CPU STATS")
        sc = tk.Frame(p, bg=BG_PANEL); sc.pack(fill="x", padx=12)
        self.lbl_backs = self._srow(sc, "Backtracks:", "--")
        self.lbl_steps = self._srow(sc, "CPU steps:",  "--")

        div(); sec("TIME")
        tc = tk.Frame(p, bg=BG_CARD, padx=10, pady=6); tc.pack(fill="x", padx=12)
        self.t_lbl = tk.Label(tc, text="00:00", font=self.F_STAT_V,
                              bg=BG_CARD, fg=BTN_BLUE)
        self.t_lbl.pack()

        div(); sec("LEGEND")
        leg = tk.Frame(p, bg=BG_PANEL); leg.pack(fill="x", padx=12)
        for txt, color in [("CPU Trying",     TRY_BG),
                           ("Backtrack tile", BACK_BG),
                           ("Hint tile",      HINT_BG),
                           ("Correct pos.",   TILE_CORRECT)]:
            row = tk.Frame(leg, bg=BG_PANEL, pady=2); row.pack(fill="x")
            dot = tk.Frame(row, bg=color, width=13, height=13)
            dot.pack(side="left", padx=(0,6)); dot.pack_propagate(False)
            tk.Label(row, text=txt, font=self.F_STAT_L,
                     bg=BG_PANEL, fg=TEXT_DARK).pack(side="left")

        div(); sec("CURRENT ACTION")
        self.action_lbl = tk.Label(p, text="--", font=self.F_ACT,
                                   bg=BG_PANEL, fg=TEXT_DARK,
                                   wraplength=214, justify="center")
        self.action_lbl.pack(pady=3, padx=10)

        div()
        mkbtn("▶  START  (New Game)", BTN_START, self._start_game)
        mkbtn("↺  RESET",             BTN_RESET, self._reset)

        div()
        self.btn_hint = tk.Button(p, text="💡  HINT  (show best move)",
                                   font=self.F_BTN, bg=HINT_BG, fg="white",
                                   relief="flat", pady=8, cursor="hand2",
                                   activebackground=HINT_BG, command=self._show_hint)
        self.btn_hint.pack(fill="x", padx=12, pady=2)

        div()
        self.btn_auto = tk.Button(p, text="⚡  AUTO PLAY  (CPU solves)",
                                   font=self.F_BTN, bg=BTN_PURPLE, fg="white",
                                   relief="flat", pady=8, cursor="hand2",
                                   activebackground=BTN_PURPLE, command=self._toggle_auto)
        self.btn_auto.pack(fill="x", padx=12, pady=2)

        div()
        tk.Button(p, text="📈  RUNTIME GRAPH",
                  font=self.F_BTN, bg=BTN_TEAL, fg="white",
                  relief="flat", pady=8, cursor="hand2",
                  activebackground=BTN_TEAL,
                  command=self._open_graph
                  ).pack(fill="x", padx=12, pady=2)

        div(); sec("SPEED")
        spf = tk.Frame(p, bg=BG_PANEL); spf.pack(fill="x", padx=12, pady=(2,8))
        tk.Label(spf, text="Slow", font=self.F_STAT_L,
                 bg=BG_PANEL, fg=TEXT_DIM).pack(side="left")
        self.sv = tk.IntVar(value=550)
        tk.Scale(spf, from_=20, to=820, orient="horizontal",
                 variable=self.sv, bg=BG_PANEL, troughcolor=BG_CARD,
                 highlightthickness=0, showvalue=False
                 ).pack(side="left", fill="x", expand=True)
        tk.Label(spf, text="Fast", font=self.F_STAT_L,
                 bg=BG_PANEL, fg=TEXT_DIM).pack(side="left")

    def _srow(self, parent, label, val):
        row = tk.Frame(parent, bg=BG_PANEL, pady=2); row.pack(fill="x")
        tk.Label(row, text=label, font=self.F_STAT_L,
                 bg=BG_PANEL, fg=TEXT_MID, anchor="w").pack(side="left")
        v = tk.Label(row, text=val, font=self.F_BTN,
                     bg=BG_PANEL, fg=TEXT_DARK, anchor="e")
        v.pack(side="right"); return v

    def _clock(self):
        if self.is_started and not self.game_over and self.start_time:
            m, s = divmod(int(time.time()-self.start_time), 60)
            self.t_lbl.config(text=f"{m:02d}:{s:02d}")
        self.root.after(1000, self._clock)

    def _draw(self, hi=None, action=None, hint_idx=None):
        can_click = (
            self.current_turn == "player"
            and self.is_started
            and not self.game_over
            and not self.computing
            and not self.auto_mode
        )
        for i, v in enumerate(self.board):
            btn = self.buttons[i]
            if v == 0:
                btn.config(text="", state="disabled",
                           bg=EMPTY_BG, activebackground=EMPTY_BG); continue
            if not self.is_started:
                btn.config(text="?", bg="#D6EAF8", fg="#555555",
                           state="disabled", activebackground="#D6EAF8"); continue
            bg = TILE_BG; fg = TILE_FG
            if v == self.GOAL[i]:            bg = TILE_CORRECT; fg = TILE_CORRECT_FG
            if hint_idx is not None and i == hint_idx: bg = HINT_BG; fg = HINT_FG
            if hi is not None and i == hi:
                if   action == "try":  bg = TRY_BG;  fg = TRY_FG
                elif action == "back": bg = BACK_BG; fg = BACK_FG
                elif action == "done": bg = DONE_BG; fg = DONE_FG
            state = "normal" if can_click else "disabled"
            btn.config(text=str(v), bg=bg, fg=fg, state=state, activebackground=bg)

    def _set_turn_ui(self):
        if self.computing:
            self.turn_banner.config(text="  Solving...  Please wait", bg=BTN_GREY)
            self.turn_card.config(text="Solving...", bg=BTN_GREY, fg="white")
            self.status.config(text="  Calculating solution — please wait...", fg="#FFFFFF")
        elif self.auto_mode and not self.auto_paused:
            self.turn_banner.config(text="  AUTO PLAY — CPU solving", bg=BTN_PURPLE)
            self.turn_card.config(text="AUTO PLAY", bg=BTN_PURPLE, fg="white")
        elif self.current_turn == "player":
            self.turn_banner.config(text="  YOUR TURN — click a tile", bg=P1_COLOR)
            self.turn_card.config(text="YOUR TURN", bg=P1_COLOR, fg="white")
            self.status.config(text="  YOUR TURN!  Click any tile next to the empty space.", fg="#FFFFFF")
        else:
            self.turn_banner.config(text="  CPU TURN — watch the backtracking", bg=P2_COLOR)
            self.turn_card.config(text="CPU TURN", bg=P2_COLOR, fg="white")
            self.status.config(text="  CPU is making its step...", fg="#FFFFFF")

    def _show_hint(self):
        if not self.is_started or self.game_over or self.computing: return
        if self.current_turn != "player": return
        cur = tuple(self.board); hint_tile = None
        for j in range(len(self._solution)-1):
            if self._solution[j] == cur:
                hint_tile = moved_tile(cur, self._solution[j+1]); break
        if hint_tile is None:
            self.status.config(text="  Computing hint...", fg=HINT_BG); self.root.update()
            fresh = slove_puzzle(cur, self.SIZE, self.GOAL)
            if fresh and len(fresh) > 1:
                self._solution = fresh; hint_tile = moved_tile(cur, fresh[1])
        if hint_tile is None: return
        self._hint_idx = hint_tile
        self._draw(hint_idx=hint_tile)
        self.status.config(text=f"  💡 HINT: Move tile [{self.board[hint_tile]}]  (orange)!", fg=HINT_BG)
        self.root.after(1500, self._clear_hint)

    def _clear_hint(self):
        self._hint_idx = None
        self._draw(hi=self._hi, action=self._hi_action)
        if self.current_turn == "player" and not self.game_over:
            self.status.config(text="  YOUR TURN!  Click any tile next to the empty space.", fg="#FFFFFF")

    def _start_game(self):
        if self.computing: return
        self.board          = list(shuffle_board(self.SIZE))
        self.is_started     = True
        self.start_time     = time.time()
        self.game_over      = False
        self.auto_mode      = False
        self.auto_paused    = False
        self.current_turn   = "player"
        self.p1_moves       = 0
        self.cpu_steps_done = 0
        self._hi            = None; self._hi_action = None; self._hint_idx = None
        self.trace          = []; self.trace_idx = 0; self._solution = []; self._solve_ms = 0.0
        self.p1_moves_lbl.config(text="0"); self.cpu_steps_lbl.config(text="0")
        self.lbl_backs.config(text="--"); self.lbl_steps.config(text="--")
        self.action_lbl.config(text="--", fg=TEXT_DARK)
        self.step_bar.config(text="Solving...")
        self.btn_auto.config(text="⚡  AUTO PLAY  (CPU solves)")
        self._draw(); self.computing = True; self._set_turn_ui()
        threading.Thread(target=self._bg_solve, daemon=True).start()

    def _reset(self):
        self.auto_mode = False; self.auto_paused = False; self.computing = False
        self._start_game()

    def _bg_solve(self):
        t0  = time.time()
        sol = slove_puzzle(tuple(self.board), self.SIZE, self.GOAL)
        ms  = (time.time()-t0)*1000
        if sol is None: self.root.after(0, self._no_solution)
        else:
            trace = build_trace(sol, self.SIZE)
            self.root.after(0, lambda: self._on_ready(sol, trace, ms))

    def _no_solution(self):
        self.computing = False
        self.status.config(text="  No solution found — press RESET.", fg=BACK_BG)

    def _on_ready(self, sol, trace, ms):
        self.computing    = False
        self._solution    = sol
        self._solve_ms    = ms
        self.trace        = trace
        self.trace_idx    = 0
        self._total_steps = len(trace)
        self._total_backs = sum(1 for e in trace if e[0] == "back")
        self.step_bar.config(text=f"Steps: 0 / {self._total_steps}")
        self.lbl_backs.config(text=str(self._total_backs))
        self.lbl_steps.config(text=str(self._total_steps))
        self._set_turn_ui(); self._draw()
        if self.auto_mode: self._do_cpu_step()

    def _click(self, idx):
        if self.current_turn != "player": return
        if not self.is_started or self.game_over or self.computing: return
        if self.auto_mode: return
        if idx not in get_moves(self.board, self.SIZE): return
        self._hi = None; self._hi_action = None; self._hint_idx = None
        self.board = list(apply_move(tuple(self.board), idx))
        self.p1_moves += 1; self.p1_moves_lbl.config(text=str(self.p1_moves))
        self._draw()
        if tuple(self.board) == self.GOAL: self._end_game(player_won=True); return
        self.current_turn = "cpu"; self._set_turn_ui(); self._draw()
        self.root.after(max(60, 840-self.sv.get()), self._do_cpu_step)

    def _do_cpu_step(self):
        if self.game_over or self.computing: return
        if self.trace_idx >= len(self.trace): self._finish_cpu_turn(); return

        action, board_t, hi = self.trace[self.trace_idx]
        self.trace_idx += 1; self.cpu_steps_done += 1
        self.board = list(board_t); self._hi = hi; self._hi_action = action

        self.cpu_steps_lbl.config(text=str(self.cpu_steps_done))
        self.lbl_steps.config(text=str(self.cpu_steps_done))
        backs = sum(1 for e in self.trace[:self.trace_idx] if e[0] == "back")
        self.lbl_backs.config(text=str(backs))
        self.step_bar.config(text=f"Steps: {self.trace_idx} / {self._total_steps}")
        self._draw(hi=hi, action=action)

        tile_val = board_t[hi] if (hi is not None and hi < len(board_t)) else "?"
        r = hi//self.SIZE+1 if hi is not None else "?"
        c = hi% self.SIZE+1 if hi is not None else "?"

        if action == "try":
            self.action_lbl.config(text=f"CPU Trying\nTile [{tile_val}] at ({r},{c})", fg=TRY_BG)
            self.status.config(
                text=f"  CPU TRYING  →  Tile [{tile_val}] at ({r},{c})"
                     f"   |  Step {self.trace_idx}/{self._total_steps}", fg="#FFFFFF")
        elif action == "back":
            self.action_lbl.config(text=f"🔴 BACKTRACK!\nTile [{tile_val}] ({r},{c})", fg=BACK_BG)
            self.status.config(
                text=f"  🔴 BACKTRACKING!  Tile [{tile_val}] at ({r},{c})"
                     f" — dead end!  |  Step {self.trace_idx}/{self._total_steps}", fg=BACK_BG)
        elif action == "done":
            self.action_lbl.config(text="✅ CPU SOLVED!", fg=DONE_BG)
            self.status.config(text="  ✅ CPU solved the board!", fg=DONE_BG)
            self._draw(hi=hi, action=action)
            self.root.after(800, lambda: self._end_game(player_won=False)); return

        if tuple(self.board) == self.GOAL:
            self.root.after(400, lambda: self._end_game(player_won=False)); return

        delay = max(60, 840-self.sv.get())
        if self.auto_mode and not self.auto_paused:
            self.root.after(delay, self._do_cpu_step)
        else:
            self.root.after(delay, self._finish_cpu_turn)

    def _finish_cpu_turn(self):
        if self.game_over: return
        self.current_turn = "player"; self._set_turn_ui()
        self._draw(hi=self._hi, action=self._hi_action)

    def _toggle_auto(self):
        if not self.is_started or self.computing:
            self.auto_mode = True
            if not self.is_started: self._start_game()
            self.btn_auto.config(text="⏸  PAUSE Auto Play"); return
        if not self.auto_mode:
            self.auto_mode = True; self.auto_paused = False
            self.current_turn = "cpu"
            self.btn_auto.config(text="⏸  PAUSE Auto Play")
            self._set_turn_ui(); self._do_cpu_step()
        else:
            self.auto_paused = not self.auto_paused
            if self.auto_paused:
                self.btn_auto.config(text="▶  RESUME Auto Play")
                self.status.config(text="  Auto Play paused. Press RESUME.", fg="#FFFFFF")
            else:
                self.btn_auto.config(text="⏸  PAUSE Auto Play"); self._do_cpu_step()

    def _open_graph(self):
        if not self.is_started:
            self.status.config(
                text="  ⚠  Press START first — graph needs puzzle data!", fg=HINT_BG)
            return
        if self.computing:
            self.status.config(
                text="  ⏳  Still computing — wait a moment then try again.", fg=HINT_BG)
            return
        RuntimeGraphWindow(
            self.root, self.trace, self._solution,
            self.SIZE, self._solve_ms, self.p1_moves, self.cpu_steps_done
        )

    def _end_game(self, player_won=False):
        if self.game_over: return
        self.game_over = True; self.auto_mode = False
        winner = "🏆  YOU WIN!" if player_won else "🤖  CPU solved it!"
        wcolor = P1_COLOR if player_won else P2_COLOR
        backs  = sum(1 for e in self.trace[:self.trace_idx] if e[0] == "back")
        self.status.config(
            text=f"{winner}   Your moves: {self.p1_moves}   "
                 f"CPU steps: {self.cpu_steps_done}   Backtracks: {backs}",
            fg=wcolor)
        self.root.after(300, lambda: self._popup(winner, wcolor, backs))

    def _popup(self, winner, wcolor, backs):
        pop = tk.Toplevel(self.root)
        pop.title("Game Complete!")
        pop.configure(bg=BG_PANEL); pop.resizable(False, False)
        pop.transient(self.root); pop.grab_set()
        pw, ph = 360, 240
        self.root.update_idletasks()
        rx = self.root.winfo_x()+(self.root.winfo_width() -pw)//2
        ry = self.root.winfo_y()+(self.root.winfo_height()-ph)//2
        pop.geometry(f"{pw}x{ph}+{rx}+{ry}")

        # header
        hdr = tk.Frame(pop, bg=wcolor, pady=22); hdr.pack(fill="x")
        tk.Label(hdr, text="GAME COMPLETE!",
                 font=tkfont.Font(family="Georgia", size=22, weight="bold"),
                 bg=wcolor, fg="white").pack()

        # only 2 stats: Your Moves + CPU Backtracks
        body = tk.Frame(pop, bg=BG_PANEL, pady=16); body.pack(fill="x", padx=32)
        lf = tkfont.Font(family="Verdana", size=10)
        vf = tkfont.Font(family="Verdana", size=16, weight="bold")

        for label, val, color in [
            ("Your Moves",     str(self.p1_moves), P1_COLOR),
            ("CPU Backtracks", f"{backs:,}",        BTN_RESET),
        ]:
            row = tk.Frame(body, bg=BG_CARD, padx=18, pady=12)
            row.pack(fill="x", pady=4)
            tk.Label(row, text=label, font=lf,
                     bg=BG_CARD, fg=TEXT_MID, anchor="w").pack(side="left")
            tk.Label(row, text=val, font=vf,
                     bg=BG_CARD, fg=color, anchor="e").pack(side="right")

        # buttons
        bf = tkfont.Font(family="Verdana", size=10, weight="bold")
        br = tk.Frame(pop, bg=BG_PANEL, pady=10); br.pack()
        tk.Button(br, text="▶  Play Again", font=bf,
                  bg=BTN_START, fg="white", relief="flat",
                  padx=18, pady=8, cursor="hand2",
                  command=lambda: [pop.destroy(), self._reset()]
                  ).pack(side="left", padx=8)
        tk.Button(br, text="✕  Close", font=bf,
                  bg=BTN_GREY, fg="white", relief="flat",
                  padx=18, pady=8, cursor="hand2",
                  command=pop.destroy
                  ).pack(side="left", padx=8)


if __name__ == "__main__":
    root = tk.Tk()
    Launcher(root)
    root.mainloop()









