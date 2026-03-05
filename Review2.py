import tkinter as tk
from tkinter import messagebox
import heapq
from collections import deque
import concurrent.futures


# COLORS

BG_COLOR       = "#EAF6F6"
FRAME_COLOR    = "#A9DFBF"
TILE_COLOR     = "#FFF4B2"
CORRECT_COLOR  = "#A3E4D7"
EMPTY_COLOR    = "#82C0A6"
BTN_COLOR      = "#58D68D"
HINT_COLOR     = "#F39C12"
CPU_MOVE_COLOR = "#AED6F1"
BUFFER_COLOR   = "#D7BDE2"
QUAD_COLORS    = ["#FADBD8", "#D6EAF8", "#D5F5E3", "#FDEBD0"]


# BOARD UTILITIES

def create_goal(size):
    return list(range(1, size * size)) + [0]

def find_empty(board):
    return board.index(0)

def get_valid_moves(board, size):
    e = find_empty(board)
    r, c = divmod(e, size)
    moves = []
    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
        nr, nc = r+dr, c+dc
        if 0 <= nr < size and 0 <= nc < size:
            moves.append(nr*size+nc)
    return moves

def swap_board(board, i, j):
    b = list(board)
    b[i], b[j] = b[j], b[i]
    return tuple(b)



def count_correct(board, goal):
    return sum(1 for i in range(len(board))
               if board[i] == goal[i] and board[i] != 0)


# QUADRANT DEFINITIONS

def get_quadrant_cells(size):
    if size == 4:
        buf_rows = {1, 2}
        buf_cols = {1, 2}
    else:
        buf_rows = {2}
        buf_cols = {2}

    buffer_cells = set()
    for r in range(size):
        for c in range(size):
            if r in buf_rows or c in buf_cols:
                buffer_cells.add((r, c))

    non_buf = [(r, c) for r in range(size) for c in range(size)
               if (r, c) not in buffer_cells]

    mid_r = size // 2
    mid_c = size // 2

    q0 = {(r,c) for (r,c) in non_buf if r < mid_r and c < mid_c}
    q1 = {(r,c) for (r,c) in non_buf if r < mid_r and c >= mid_c}
    q2 = {(r,c) for (r,c) in non_buf if r >= mid_r and c < mid_c}
    q3 = {(r,c) for (r,c) in non_buf if r >= mid_r and c >= mid_c}

    return buf_rows, buf_cols, buffer_cells, [q0, q1, q2, q3]

def cells_to_idx(cells, size):
    return {r*size+c for (r,c) in cells}

def get_adjacent_buffer_cells(quadrant_set, buffer_set, size):
    adj = set()
    for idx in quadrant_set:
        r, c = divmod(idx, size)
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            if 0 <= nr < size and 0 <= nc < size:
                nb = nr*size+nc
                if nb in buffer_set:
                    adj.add(nb)
    return adj


# BFS — move empty tile to target

def bfs_move_empty(board, size, target, locked=None):
    board = tuple(board)
    e = board.index(0)
    if e == target:
        return [board]
    if locked is None:
        locked = set()

    parent = {board: None}
    queue  = deque([board])

    while queue:
        state = queue.popleft()
        e     = state.index(0)
        prev  = parent[state]
        for m in get_valid_moves(list(state), size):
            if m in locked:
                continue
            ns = swap_board(state, e, m)
            if ns in parent:
                continue
           # skip if this move reverses the previous
            if prev is not None and ns == prev:
                continue
            parent[ns] = state
            if ns.index(0) == target:
                path = [ns]
                cur  = ns
                while parent[cur] is not None:
                    cur = parent[cur]
                    path.append(cur)
                return list(reversed(path))
            queue.append(ns)

    # Fallback without moving same tile to and fro
    visited = {board}
    queue2  = deque([(board, [board])])
    while queue2:
        state, path = queue2.popleft()
        e = state.index(0)
        for m in get_valid_moves(list(state), size):
            if m in locked:
                continue
            ns = swap_board(state, e, m)
            if ns in visited:
                continue
            visited.add(ns)
            np = path + [ns]
            if ns.index(0) == target:
                return np
            queue2.append((ns, np))
    return None


# GBFS ZONE SOLVER

def gbfs_zone(board, size, goal_t, solve_positions, locked=None,
              max_nodes=300000, fill_only=False, working_zone=None):
    board  = tuple(board)
    goal_t = tuple(goal_t)
    if locked is None:
        locked = set()

    # Deserialise frozensets received from subprocess 
    if isinstance(locked, frozenset):
        locked = set(locked)
    if isinstance(solve_positions, frozenset):
        solve_positions = set(solve_positions)
    if working_zone is not None and isinstance(working_zone, frozenset):
        working_zone = set(working_zone)

    goal_pos_map = {}
    for i, v in enumerate(goal_t):
        if v != 0:
            goal_pos_map[v] = divmod(i, size)

    def h(b):
        dist = 0
        for i in range(len(b)):
            v = b[i]
            if v == 0:
                continue
            if v in goal_pos_map:
                if goal_t.index(v) in solve_positions:
                    cr, cc = divmod(i, size)
                    if fill_only:
                        if i not in solve_positions:
                            min_d = 999
                            for sp in solve_positions:
                                sr, sc = divmod(sp, size)
                                d = abs(sr - cr) + abs(sc - cc)
                                if d < min_d:
                                    min_d = d
                            dist += min_d
                    else:
                        gr, gc = goal_pos_map[v]
                        dist += abs(gr - cr) + abs(gc - cc)
        if fill_only:
            missing = [goal_t[p] for p in solve_positions
                       if goal_t[p] != 0 and
                       b[p] not in {goal_t[p2] for p2 in solve_positions
                                    if goal_t[p2] != 0}]
            if missing:
                locs = [i for i in range(len(b)) if b[i] in missing]
                if locs:
                    er, ec = divmod(b.index(0), size)
                    dist += min(abs(divmod(m, size)[0]-er) +
                                abs(divmod(m, size)[1]-ec) for m in locs)
        return dist

    def locked_ok(b):
        return all(b[idx] == goal_t[idx] for idx in locked if goal_t[idx] != 0)

    def is_done(b):
        if fill_only:
            required = {goal_t[p] for p in solve_positions if goal_t[p] != 0}
            in_zone  = {b[p] for p in solve_positions}
            return required.issubset(in_zone)
        return all(b[p] == goal_t[p] for p in solve_positions)

    if is_done(board):
        return [board]

    parent  = {board: (None, 0)}
    visited = set()
    heap    = [(h(board) * 10, h(board), 0, board)]
    nodes   = 0

    while heap:
        f, current_h, g, state = heapq.heappop(heap)
        if state in visited:
            continue
        visited.add(state)
        nodes += 1
        if nodes > max_nodes:
            break

        if is_done(state):
            path = []
            cur  = state
            while cur is not None:
                path.append(cur)
                cur = parent[cur][0]
            return list(reversed(path))

        prev_state = parent[state][0]
        e = state.index(0)
        for m in get_valid_moves(list(state), size):
            if working_zone is not None and (e not in working_zone or
                                             m not in working_zone):
                continue
            ns = swap_board(state, e, m)
            if ns in visited:
                continue
            # Anti-backtrack: skip reversal of previous move
            if prev_state is not None and ns == prev_state:
                continue
            if not locked_ok(ns):
                continue
            if ns not in parent or parent[ns][1] > g + 1:
                parent[ns] = (state, g + 1)
                new_h = h(ns)
                new_f = (g + 1) + 10 * new_h
                heapq.heappush(heap, (new_f, new_h, g + 1, ns))

    return None


# TOP-LEVEL WORKER — must be at module level for pickle
#
# Python's multiprocessing serialises (pickles) functions and data
# across process boundaries. Nested functions can't be pickled.
# This worker sits at module level so every spawned process can
# import and call it cleanly.
#
# Each call receives one candidate first-move (one tile adjacent to
# the empty cell). It makes that move and runs a full gbfs_zone from
# the resulting board — completely independently, in its own OS process.

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
    def __init__(self, root):
        self.root = root
        self.root.title("Sliding Puzzle — Quadrant D&C Solver")
        self.root.configure(bg=BG_COLOR)

        self.solution_path = []
        self.solution_step = 0
        self.hint_index    = None
        self.cpu_animating = False
        self.board_loaded  = False

        self.size = 5
        self.goal = create_goal(self.size)
        self.build_ui()
        self.show_input_grid()

    def build_ui(self):
        tk.Label(self.root, text="SLIDING PUZZLE — D&C Solver",
                 font=("Arial", 20, "bold"), bg=BG_COLOR).pack(pady=(12,2))

        self.status_lbl = tk.Label(self.root, font=("Arial", 12),
                                   bg=BG_COLOR, fg="#2C3E50")
        self.status_lbl.pack(pady=(0,6))

        self.board_frame = tk.Frame(self.root, bg=FRAME_COLOR, padx=10, pady=10)
        self.board_frame.pack(pady=4)

        self.buttons = []
        for i in range(self.size * self.size):
            b = tk.Button(self.board_frame, width=5, height=2,
                          font=("Arial", 14, "bold"),
                          relief="raised", bd=3,
                          state="disabled")
            b.grid(row=i//self.size, column=i%self.size, padx=4, pady=4)
            self.buttons.append(b)

        step_frame = tk.Frame(self.root, bg=BG_COLOR)
        step_frame.pack(pady=(4, 4))

        tc = ("Arial", 10, "bold")
        self.btn_step = []
        configs = [
            ("Step 0: Empty→Buffer",  "#F8C471", self.do_step0),
            ("Step 1: Fill Quads",    "#A9DFBF", self.do_step1),
            ("Step 2: Solve Q0-Q2",   "#AED6F1", self.do_step2),
            ("Step 3: Buffer + Q4",   "#F1948A", self.do_step3),
        ]
        for col, (txt, bg, cmd) in enumerate(configs):
            b = tk.Button(step_frame, text=txt, bg=bg, font=tc,
                          state="disabled", command=cmd)
            b.grid(row=0, column=col, padx=4, pady=4)
            self.btn_step.append(b)

        ctrl_frame = tk.Frame(self.root, bg=BG_COLOR)
        ctrl_frame.pack(pady=(2, 4))

        self.btn_input = tk.Button(ctrl_frame, text="✏️  Enter Board",
                                   bg=BTN_COLOR, font=("Arial", 11, "bold"),
                                   width=14, command=self.show_input_grid)
        self.btn_input.pack()

        self.moves_lbl = tk.Label(self.root, font=("Arial", 10),
                                  bg=BG_COLOR, fg="#555")
        self.moves_lbl.pack(pady=(0,4))

        legend = tk.Frame(self.root, bg=BG_COLOR)
        legend.pack(pady=(0,8))
        for text, color in [
            ("Buffer", BUFFER_COLOR),
            ("Q1 TL", QUAD_COLORS[0]),
            ("Q2 TR", QUAD_COLORS[1]),
            ("Q3 BL", QUAD_COLORS[2]),
            ("Q4 BR", QUAD_COLORS[3]),
        ]:
            tk.Label(legend, text=f"  {text}  ", bg=color,
                     font=("Arial", 9, "bold"),
                     relief="ridge").pack(side="left", padx=3)

    def show_input_grid(self):
        if self.cpu_animating:
            return

        win = tk.Toplevel(self.root)
        win.title("Enter Board")
        win.configure(bg=BG_COLOR)
        win.grab_set()

        N = self.size
        tk.Label(win, text=f"Enter numbers 0–{N*N-1}\n(0 = empty tile)",
                 font=("Arial", 12, "bold"), bg=BG_COLOR).grid(
                     row=0, column=0, columnspan=N, pady=(12,6))

        entries = []
        for r in range(N):
            row_entries = []
            for c in range(N):
                e = tk.Entry(win, width=4, font=("Arial", 14, "bold"),
                             justify="center", relief="solid")
                e.grid(row=r+1, column=c, padx=4, pady=4)
                row_entries.append(e)
            entries.append(row_entries)

        if self.board_loaded:
            for r in range(N):
                for c in range(N):
                    val = self.board[r*N+c]
                    entries[r][c].insert(0, str(val))

        def load():
            try:
                vals = []
                for r in range(N):
                    for c in range(N):
                        txt = entries[r][c].get().strip()
                        vals.append(int(txt))
            except ValueError:
                messagebox.showerror("Invalid Input",
                                     "All cells must contain integers.",
                                     parent=win)
                return

            expected = set(range(N * N))
            if set(vals) != expected:
                messagebox.showerror("Invalid Input",
                                     f"Board must contain exactly the numbers "
                                     f"0 to {N*N-1} with no duplicates.",
                                     parent=win)
                return

            if not is_solvable(vals, N):
                messagebox.showerror("Unsolvable",
                                     "This board configuration is not solvable.\n"
                                     "Please enter a solvable arrangement.",
                                     parent=win)
                return

            self._load_board(vals)
            win.destroy()

        tk.Button(win, text="Load Board", bg=BTN_COLOR,
                  font=("Arial", 11, "bold"), command=load).grid(
                      row=N+1, column=0, columnspan=N, pady=10)

    def _load_board(self, vals):
        N = self.size
        self.board         = list(vals)
        self.board_loaded  = True
        self.cpu_animating = False
        self.solution_path = []
        self.solution_step = 0
        self.hint_index    = None
        self.cpu_moves     = 0

        _, _, buf_cells, quad_cells = get_quadrant_cells(N)
        self.buffer_idx_set = cells_to_idx(buf_cells, N)
        self.quad_idx_flat  = [cells_to_idx(q, N) for q in quad_cells]

        for b in self.btn_step:
            b.config(state="normal")

        self.update_ui()
        self.set_status("Board loaded! Run steps in order: Step 0 → 1 → 2 → 3")

    def set_status(self, msg):
        self.status_lbl.config(text=msg)

    def get_zone_color(self, idx):
        if idx in self.buffer_idx_set:
            return BUFFER_COLOR
        for qi, q_set in enumerate(self.quad_idx_flat):
            if idx in q_set:
                return QUAD_COLORS[qi]
        return TILE_COLOR

    def update_ui(self, highlighted=None):
        if not self.board_loaded:
            return
        for i, v in enumerate(self.board):
            btn = self.buttons[i]
            if v == 0:
                btn.config(text="", bg=EMPTY_COLOR,
                           state="disabled", relief="sunken")
            else:
                is_correct = (v == self.goal[i])
                is_cpu_hi  = (i == highlighted)

                if is_cpu_hi:    bg = CPU_MOVE_COLOR
                elif is_correct: bg = CORRECT_COLOR
                else:            bg = self.get_zone_color(i)

                btn.config(text=str(v), bg=bg, fg="#2C3E50",
                           state="disabled", relief="raised")

        self.moves_lbl.config(text=f"CPU moves so far: {self.cpu_moves}")

    def play_segment(self, path, msg):
        if not path or len(path) <= 1:
            self.set_status(f"⚠️ {msg} — already done or impossible.")
            return
        self.cpu_animating = True
        for b in self.btn_step:
            b.config(state="disabled")
        self.solution_path = [tuple(p) for p in path]
        self.solution_step = 0
        self.set_status(f"🤖 {msg}…")
        self.update_ui()
        self.root.after(300, self._auto_step)

    def _auto_step(self):
        if not self.cpu_animating:
            return

        if self.solution_step + 1 >= len(self.solution_path):
            self.cpu_animating = False
            for b in self.btn_step:
                b.config(state="normal")
            self.update_ui()
            solved = self.board == self.goal
            if solved:
                self.set_status("✅ Puzzle solved! 🎉")
                messagebox.showinfo("Solved!", "The puzzle is solved! 🎉")
            else:
                self.set_status("✅ Step complete. Continue with next step.")
            return

        next_state = self.solution_path[self.solution_step + 1]
        self.solution_step += 1
        old_board  = self.board[:]
        self.board = list(next_state)
        self.cpu_moves += 1

        moved_tile = next(
            (i for i in range(len(self.board))
             if self.board[i] != 0 and old_board[i] == 0), None)

        self.update_ui(highlighted=moved_tile)
        remaining = len(self.solution_path) - 1 - self.solution_step
        self.set_status(f"🤖 Animating… {remaining} moves left")
        self.root.after(250, self._auto_step)

    # ─────────────────────────────────────────────────────────
    # STEP 0
    # ─────────────────────────────────────────────────────────
    def do_step0(self):
        if not self.board_loaded or self.cpu_animating:
            return

        size    = self.size
        buf_idx = self.buffer_idx_set
        current = list(self.board)

        e_now = find_empty(current)
        if e_now in buf_idx:
            self.set_status("✅ Step 0: Empty already in buffer — nothing to do.")
            return

        er, ec = divmod(e_now, size)
        tgt = min(buf_idx, key=lambda idx:
                  abs(divmod(idx, size)[0]-er) + abs(divmod(idx, size)[1]-ec))
        seg = bfs_move_empty(current, size, tgt)
        self.play_segment(seg, "Step 0: Moving empty to buffer")

    # STEP 1
    def do_step1(self):
        if not self.board_loaded or self.cpu_animating:
            return

        current  = list(self.board)
        size     = self.size
        goal_t   = tuple(self.goal)
        buf_idx  = self.buffer_idx_set
        quad_idx = self.quad_idx_flat

        full_seg = [tuple(current)]

        def append_s(sg):
            nonlocal current
            if sg and len(sg) > 1:
                for st in sg[1:]:
                    full_seg.append(tuple(st))
                current = list(sg[-1])

        hard_locked = set()

        for qi in range(4):
            q_set   = quad_idx[qi]
            adj_buf = get_adjacent_buffer_cells(q_set, buf_idx, size)

            e_now = find_empty(current)
            if e_now not in buf_idx:
                er, ec = divmod(e_now, size)
                tgt = min(buf_idx, key=lambda idx:
                          abs(divmod(idx, size)[0]-er) + abs(divmod(idx, size)[1]-ec))
                sg = bfs_move_empty(current, size, tgt, locked=hard_locked)
                if sg:
                    append_s(sg)

            needed_tiles = {goal_t[p] for p in q_set if goal_t[p] != 0}

            for _attempt in range(len(needed_tiles) + 1):
                in_q    = {current[p] for p in q_set}
                missing = needed_tiles - in_q
                if not missing:
                    break

                progress = False
                for tile_val in list(missing):
                    tile_pos = current.index(tile_val)

                    if tile_pos in adj_buf:
                        sg = move_tile_into_zone(current, size, tile_val,
                                                 q_set, locked=hard_locked)
                        if sg:
                            append_s(sg)
                            progress = True
                            continue

                    if adj_buf:
                        sg = move_tile_into_zone(current, size, tile_val,
                                                 adj_buf, locked=hard_locked)
                        if sg:
                            append_s(sg)

                    if current.index(tile_val) not in q_set:
                        sg = move_tile_into_zone(current, size, tile_val,
                                                 q_set, locked=hard_locked)
                        if sg:
                            append_s(sg)
                            progress = True

                if not progress:
                    # Parallel: all first-move branches explored simultaneously
                    sg = parallel_solve_zone(current, size, goal_t, q_set,
                                             locked=hard_locked,
                                             max_nodes=400000,
                                             fill_only=True)
                    if sg:
                        append_s(sg)

            e_now = find_empty(current)
            if e_now not in buf_idx:
                if qi == 3:
                    evacuated = False
                    er, ec = divmod(e_now, size)
                    direct_adj_buf = [
                        nr*size+nc
                        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]
                        for nr, nc in [(er+dr, ec+dc)]
                        if 0 <= nr < size and 0 <= nc < size
                        and (nr*size+nc) in adj_buf
                    ]
                    if direct_adj_buf:
                        tgt_swap = direct_adj_buf[0]
                        board_t  = tuple(current)
                        new_b    = list(swap_board(board_t, e_now, tgt_swap))
                        full_seg.append(tuple(new_b))
                        current  = new_b
                        evacuated = True

                    if not evacuated:
                        unlocked_for_exit = hard_locked - adj_buf
                        er, ec = divmod(e_now, size)
                        tgt = min(buf_idx, key=lambda idx:
                                  abs(divmod(idx, size)[0]-er) + abs(divmod(idx, size)[1]-ec))
                        sg = bfs_move_empty(current, size, tgt,
                                            locked=unlocked_for_exit)
                        if sg:
                            append_s(sg)
                else:
                    er, ec = divmod(e_now, size)
                    tgt = min(buf_idx, key=lambda idx:
                              abs(divmod(idx, size)[0]-er) + abs(divmod(idx, size)[1]-ec))
                    sg = bfs_move_empty(current, size, tgt, locked=hard_locked)
                    if sg:
                        append_s(sg)

        self.play_segment(full_seg, "Step 1: Placing tiles into quadrants")


    # STEP 2

    def do_step2(self):
        if not self.board_loaded or self.cpu_animating:
            return

        current  = list(self.board)
        size     = self.size
        goal_t   = tuple(self.goal)
        buf_idx  = self.buffer_idx_set
        quad_idx = self.quad_idx_flat

        full_seg = [tuple(current)]

        def append_s(sg):
            nonlocal current
            if sg and len(sg) > 1:
                for st in sg[1:]:
                    full_seg.append(tuple(st))
                current = list(sg[-1])

        hard_locked = set()

        for qi in range(3):
            q_set        = quad_idx[qi]
            adj_buf      = get_adjacent_buffer_cells(q_set, buf_idx, size)
            working_zone = q_set | adj_buf

            if all(current[p] == goal_t[p] for p in q_set):
                hard_locked |= q_set
                continue

            needed = {goal_t[p] for p in q_set if goal_t[p] != 0}
            for tile_val in needed:
                tile_pos = current.index(tile_val)
                if tile_pos in adj_buf:
                    sg = move_tile_into_zone(current, size, tile_val,
                                             q_set, locked=hard_locked)
                    if sg:
                        append_s(sg)

            e_now = find_empty(current)
            if e_now not in working_zone:
                tgt = min(adj_buf,
                          key=lambda idx:
                          abs(divmod(idx, size)[0] - divmod(e_now, size)[0]) +
                          abs(divmod(idx, size)[1] - divmod(e_now, size)[1]))
                sg = bfs_move_empty(current, size, tgt, locked=hard_locked)
                if sg:
                    append_s(sg)

            # Parallel: all first-move branches for this quad solved simultaneously
            sg = parallel_solve_zone(current, size, goal_t, q_set,
                                     locked=hard_locked, max_nodes=800000,
                                     working_zone=working_zone)
            if sg:
                append_s(sg)

            e_now = find_empty(current)
            if e_now not in buf_idx:
                tgt = min(adj_buf,
                          key=lambda idx:
                          abs(divmod(idx, size)[0] - divmod(e_now, size)[0]) +
                          abs(divmod(idx, size)[1] - divmod(e_now, size)[1]))
                sg = bfs_move_empty(current, size, tgt, locked=hard_locked)
                if sg:
                    append_s(sg)

            if all(current[p] == goal_t[p] for p in q_set):
                hard_locked |= q_set
            else:
                for p in q_set:
                    if current[p] == goal_t[p] and goal_t[p] != 0:
                        hard_locked.add(p)

        e_now = find_empty(current)
        if e_now not in buf_idx:
            er, ec = divmod(e_now, size)
            tgt = min(buf_idx, key=lambda idx:
                      abs(divmod(idx, size)[0]-er) + abs(divmod(idx, size)[1]-ec))
            sg = bfs_move_empty(current, size, tgt, locked=hard_locked)
            if sg:
                append_s(sg)

        self.play_segment(full_seg, "Step 2: Island-solving Q0, Q1, Q2")

    # ─────────────────────────────────────────────────────────
    # STEP 3
    # ─────────────────────────────────────────────────────────
    def do_step3(self):
        if not self.board_loaded or self.cpu_animating:
            return

        current  = list(self.board)
        size     = self.size
        goal_t   = tuple(self.goal)
        buf_idx  = self.buffer_idx_set
        quad_idx = self.quad_idx_flat
        q4_set   = quad_idx[3]
        N        = size * size

        full_seg = [tuple(current)]

        def append_s(sg):
            nonlocal current
            if sg and len(sg) > 1:
                for st in sg[1:]:
                    full_seg.append(tuple(st))
                current = list(sg[-1])

        hl = set()
        for qi in range(3):
            q_set = quad_idx[qi]
            if all(current[p] == goal_t[p] for p in q_set):
                hl |= q_set
            else:
                for p in q_set:
                    if current[p] == goal_t[p] and goal_t[p] != 0:
                        hl.add(p)

        adj_buf_q4    = get_adjacent_buffer_cells(q4_set, buf_idx, size)
        non_adj_buf   = buf_idx - adj_buf_q4
        buffer_ready  = all(current[p] == goal_t[p] for p in non_adj_buf)
        buffer_solved = False

        if buffer_ready:
            working_zone_buf = buf_idx | q4_set

            e = find_empty(current)
            if e not in working_zone_buf:
                er, ec = divmod(e, size)
                tgt = min(working_zone_buf, key=lambda idx:
                          abs(divmod(idx, size)[0]-er) + abs(divmod(idx, size)[1]-ec))
                sg = bfs_move_empty(current, size, tgt, locked=hl)
                if sg:
                    append_s(sg)

            if not all(current[p] == goal_t[p] for p in buf_idx):
                buf_locked = hl | {i for i in range(N) if i not in working_zone_buf}
                # Parallel: buffer solve across all first-move branches simultaneously
                sg = parallel_solve_zone(current, size, goal_t, buf_idx,
                                         locked=buf_locked, max_nodes=1200000,
                                         working_zone=working_zone_buf)
                if sg:
                    append_s(sg)
                    buffer_solved = all(current[p] == goal_t[p] for p in buf_idx)
                else:
                    # Buffer not solvable — skip, go directly to Q4
                    buffer_solved = False
            else:
                buffer_solved = True

            if buffer_solved:
                for p in buf_idx:
                    if current[p] == goal_t[p]:
                        hl.add(p)

            if buffer_solved:
                for p in buf_idx:
                    if current[p] == goal_t[p]:
                        hl.add(p)
            else:
                # Buffer failed — remove ALL buffer positions from locked set
                # so buffer tiles can move freely inside adj_buf_q4 during Q4 solve
                hl -= buf_idx

        # Sub-step B: Solve Q4 — always runs, even when buffer failed
        q4_working_zone = q4_set | adj_buf_q4

        e = find_empty(current)
        if e not in q4_working_zone:
            er, ec = divmod(e, size)
            tgt = min(q4_working_zone, key=lambda idx:
                      abs(divmod(idx, size)[0]-er) + abs(divmod(idx, size)[1]-ec))
            sg = bfs_move_empty(current, size, tgt, locked=hl)
            if sg:
                append_s(sg)

        if not all(current[p] == goal_t[p] for p in q4_set):
            # Only lock tiles that are confirmed correct (hl), minus adj_buf_q4
            # which Q4 needs as workspace. Do NOT add non-working-zone positions
            # as locked — buffer tiles there may be unsolved, causing locked_ok
            # to reject every move. working_zone already restricts the search.
            q4_locked = hl - adj_buf_q4
            # Parallel: all first-move branches for Q4 solved simultaneously
            sg = parallel_solve_zone(current, size, goal_t, q4_set,
                                     locked=q4_locked, max_nodes=800000,
                                     working_zone=q4_working_zone)
            if sg:
                append_s(sg)

            if tuple(current) != tuple(goal_t):
                # Only lock confirmed-correct tiles outside Q4
                hl2 = hl - q4_set - buf_idx
                seg_fb = gbfs_full(current, goal_t, size,
                                   locked=hl2, max_nodes=1000000)
                if seg_fb:
                    append_s(seg_fb)

        if not buffer_ready:
            # Buffer was never attempted — unlock buffer so Q4 adj cells are free
            hl -= buf_idx

        if buffer_ready and not buffer_solved:
            label = "Step 3: Buffer unsolvable — solving Q4 directly"
        elif buffer_ready:
            label = "Step 3: Solving buffer (via Q4) then Q4"
        else:
            label = "Step 3: Solving Q4 directly"

        self.play_segment(full_seg, label)


# MAIN
# Required guard: on Windows, ProcessPoolExecutor spawns new
# interpreter processes that re-import this module. Without this
# guard every spawned process would try to open the Tkinter window.

if __name__ == "__main__":
    root = tk.Tk()
    PuzzleGame(root)
    root.mainloop()

