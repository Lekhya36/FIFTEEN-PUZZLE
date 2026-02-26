import tkinter as tk
from tkinter import simpledialog, messagebox
import random
import heapq
from collections import deque

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

def shuffle_board(goal, size, steps):
    cur = tuple(goal)
    prev_e = None
    for _ in range(steps):
        moves = get_valid_moves(list(cur), size)
        e = cur.index(0)
        filtered = [m for m in moves if m != prev_e]
        if not filtered:
            filtered = moves
        m = random.choice(filtered)
        prev_e = e
        cur = swap_board(cur, e, m)
    return list(cur)

def count_correct(board, goal):
    return sum(1 for i in range(len(board))
               if board[i] == goal[i] and board[i] != 0)

def get_quadrant_cells(size):
    if size == 4:
        buf_rows = {1, 2}
        buf_cols = {1, 2}
    else:  # 5x5
        buf_rows = {2}
        buf_cols = {2}

    buffer_cells = set()
    for r in range(size):
        for c in range(size):
            if r in buf_rows or c in buf_cols:
                buffer_cells.add((r, c))

    non_buf = [(r,c) for r in range(size) for c in range(size)
               if (r,c) not in buffer_cells]

    if size == 4:
        mid_r = size // 2
        mid_c = size // 2
    else:
        mid_r = size // 2
        mid_c = size // 2

    q0 = {(r,c) for (r,c) in non_buf if r < mid_r and c < mid_c}
    q1 = {(r,c) for (r,c) in non_buf if r < mid_r and c >= mid_c}
    q2 = {(r,c) for (r,c) in non_buf if r >= mid_r and c < mid_c}
    q3 = {(r,c) for (r,c) in non_buf if r >= mid_r and c >= mid_c}

    return buf_rows, buf_cols, buffer_cells, [q0, q1, q2, q3]


def cells_to_indices(cells, size):
    return {r*size+c for (r,c) in cells}
def solve_zone(board, size, goal_t, solve_positions, locked=None, max_nodes=200000):
    """
    Solve only the tiles at `solve_positions` to their goal values.
    Other tiles in locked must not move.
    Empty tile may wander anywhere on the board.
    """
    board = tuple(board)
    goal_t = tuple(goal_t)
    if locked is None:
        locked = set()

    def is_done(b):
        return all(b[p] == goal_t[p] for p in solve_positions)

    if is_done(board):
        return [board]

    goal_pos_map = {v: divmod(i, size) for i, v in enumerate(goal_t)}

    def h(b):
        dist = 0
        for p in solve_positions:
            v = b[p]
            if v == 0:
                continue
            gr, gc = goal_pos_map.get(v, divmod(p, size))
            cr, cc = divmod(p, size)
            dist += abs(gr-cr) + abs(gc-cc)
        return dist

    def locked_ok(b):
        for idx in locked:
            if b[idx] != goal_t[idx]:
                return False
        return True

    visited = {board: 0}
    heap = [(h(board), 0, board, [board])]
    nodes = 0

    while heap:
        f, g, state, path = heapq.heappop(heap)
        nodes += 1
        if nodes > max_nodes:
            return None
        if is_done(state):
            return path
        if visited.get(state, g) < g:
            continue

        e = state.index(0)
        for m in get_valid_moves(list(state), size):
            ns = swap_board(state, e, m)
            if not locked_ok(ns):
                continue
            ng = g + 1
            if ns not in visited or visited[ns] > ng:
                visited[ns] = ng
                heapq.heappush(heap, (ng + h(ns), ng, ns, path + [ns]))

    return None
def solve_full(board, goal_t, size, locked=None, max_nodes=500000):
    board = tuple(board)
    goal_t = tuple(goal_t)
    if locked is None:
        locked = set()
    if board == goal_t:
        return [board]

    goal_pos = {v: divmod(i, size) for i, v in enumerate(goal_t)}

    def h(b):
        dist = 0
        for i, v in enumerate(b):
            if v == 0: continue
            gr, gc = goal_pos[v]
            cr, cc = divmod(i, size)
            dist += abs(gr-cr) + abs(gc-cc)
        return dist

    def locked_ok(b):
        for idx in locked:
            if b[idx] != goal_t[idx]:
                return False
        return True

    visited = {board: 0}
    heap = [(h(board), 0, board, [board])]
    nodes = 0

    while heap:
        f, g, state, path = heapq.heappop(heap)
        nodes += 1
        if nodes > max_nodes:
            return None
        if state == goal_t:
            return path
        if visited.get(state, g) < g:
            continue
        e = state.index(0)
        for m in get_valid_moves(list(state), size):
            ns = swap_board(state, e, m)
            if not locked_ok(ns):
                continue
            ng = g + 1
            if ns not in visited or visited[ns] > ng:
                visited[ns] = ng
                heapq.heappush(heap, (ng+h(ns), ng, ns, path+[ns]))
    return None
    


def full_solve_dc(board, goal, size):
    """
    TRUE Divide & Conquer — Quadrant Based:

    DIVIDE:  Split board into 4 independent quadrants + shared buffer (cross).
    CONQUER: Solve each quadrant independently as its own sub-problem.
    COMBINE: Merge via buffer — buffer solved last, then empty passed between quadrants.

    Phases:
      0. Move empty tile into buffer zone (setup for D&C)
      1. For each quadrant: pull needed tiles from buffer → place in quadrant (D&C phase)
      2. Score quadrants by heuristic → determine solve order (parallel analysis)
      3. Solve buffer zone (independent sub-problem)
      4. Each quadrant independently solves itself using solve_zone (locked others)
      5. Pass empty tile to next quadrant → final quadrant pushes empty to goal
    """
    current = list(board)
    goal_t  = tuple(goal)
    full_path = [tuple(current)]

    if tuple(current) == goal_t:
        return full_path

    buf_rows, buf_cols, buffer_cells, quadrants = get_quadrant_cells(size)
    buf_idx   = cells_to_indices(buffer_cells, size)
    quad_idx  = [cells_to_indices(q, size) for q in quadrants]

    def append_seg(seg):
        nonlocal current
        if not seg or len(seg) <= 1:
            return
        for st in seg[1:]:
            full_path.append(tuple(st))
        current = list(full_path[-1])

    def cur_t():
        return tuple(current)

    # ── Phase 0: Move empty into buffer ──────────────────────
    e_now = find_empty(current)
    if e_now not in buf_idx:
        er, ec = divmod(e_now, size)
        target_buf = min(buf_idx, key=lambda idx:
            abs(divmod(idx,size)[0]-er) + abs(divmod(idx,size)[1]-ec))
        seg = bfs_move_empty(current, size, target_buf)
        if seg:
            append_seg(seg)

    # ── Phase 1: D&C — Pull buffer tiles into their quadrants ─
    for qi, q_set in enumerate(quad_idx):
        allowed_zone = buf_idx | q_set

        needed = {goal_t[pos]: pos for pos in q_set}

        for tile_val, g_pos in needed.items():
            t_pos = list(current).index(tile_val)
            if t_pos not in buf_idx:
                continue

            seg = slide_tile_to(current, size, t_pos, g_pos, allowed_zone)
            if seg:
                append_seg(seg)

    # ── Phase 2: Heuristic scoring — determine solve order ───
    def quad_score(qi):
        return sum(1 for pos in quad_idx[qi] if current[pos] == goal_t[pos])

    solve_order = sorted(range(4), key=quad_score)

    # ── Phase 3: Solve buffer zone (independent sub-problem) ─
    pre_locked = set()
    for qi in range(4):
        for pos in quad_idx[qi]:
            if current[pos] == goal_t[pos]:
                pre_locked.add(pos)

    buf_seg = solve_zone(current, size, goal_t, buf_idx, locked=pre_locked,
                         max_nodes=150000)
    if buf_seg:
        append_seg(buf_seg)

    if cur_t() == goal_t:
        return full_path

    # ── Phase 4: Each quadrant independently solves itself ───
    all_locked = set()

    for qi in solve_order:
        q_set = quad_idx[qi]

        locked_now = set(all_locked)
        for qj in range(4):
            if qj != qi:
                for pos in quad_idx[qj]:
                    if current[pos] == goal_t[pos]:
                        locked_now.add(pos)

        e_now = find_empty(current)
        if e_now not in buf_idx:
            er, ec = divmod(e_now, size)
            t_buf = min(buf_idx, key=lambda idx:
                abs(divmod(idx,size)[0]-er) + abs(divmod(idx,size)[1]-ec))
            seg = bfs_move_empty(current, size, t_buf, locked=locked_now)
            if seg:
                append_seg(seg)

        seg = solve_zone(current, size, goal_t, q_set,
                         locked=locked_now, max_nodes=300000)
        if seg:
            for state in seg[1:]:
                full_path.append(tuple(state))
                current = list(state)
                if all(current[p] == goal_t[p] for p in q_set):
                    break

        for pos in q_set:
            if current[pos] == goal_t[pos]:
                all_locked.add(pos)

        if cur_t() == goal_t:
            return full_path

    # ── Phase 5: Final cleanup ────────────────────────────────
    remaining = {p for p in range(size*size) if current[p] != goal_t[p]}

    if remaining:
        seg = solve_zone(current, size, goal_t, remaining,
                         locked=all_locked, max_nodes=400000)
        if seg:
            append_seg(seg)

    if cur_t() != goal_t:
        seg = solve_full(current, goal_t, size,
                         locked=all_locked, max_nodes=800000)
        if seg is None:
            seg = solve_full(current, goal_t, size, max_nodes=1500000)
        if seg:
            append_seg(seg)

    return full_path


# GAME CLASS

class PuzzleGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Sliding Puzzle — Quadrant D&C")
        self.root.configure(bg=BG_COLOR)

        self.solution_path = []
        self.solution_step = 0
        self.hint_index    = None
        self.cpu_animating = False

        self.ask_settings()
        self.build_ui()
        self.start_game()

    # ── Settings ─────────────────────────────────────────────
    def ask_settings(self):
        size_choice = simpledialog.askstring(
            "Board Size",
            "Choose puzzle size:\n  15  →  4×4 puzzle\n  24  →  5×5 puzzle"
        )
        if size_choice == "24":
            self.size = 5
            self.shuffle_steps = 40
        else:
            self.size = 4
            self.shuffle_steps = 35
        self.goal = create_goal(self.size)

    # ── Build UI ──────────────────────────────────────────────
    def build_ui(self):
        tk.Label(self.root, text="SLIDING PUZZLE",
                 font=("Arial", 22, "bold"), bg=BG_COLOR).pack(pady=(12,2))

        self.score_lbl = tk.Label(self.root, font=("Arial", 14, "bold"), bg=BG_COLOR)
        self.score_lbl.pack(pady=(8,2))

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
                          command=lambda i=i: self.human_move(i))
            b.grid(row=i//self.size, column=i%self.size, padx=4, pady=4)
            self.buttons.append(b)

        btn_frame = tk.Frame(self.root, bg=BG_COLOR)
        btn_frame.pack(pady=12)

        tk.Button(btn_frame, text="🔄  New Game",
                  bg=BTN_COLOR, font=("Arial", 11, "bold"),
                  width=13, command=self.start_game).grid(row=0, column=0, padx=8)

        tk.Button(btn_frame, text="💡  Hint",
                  bg=HINT_COLOR, fg="white", font=("Arial", 11, "bold"),
                  width=13, command=self.show_hint).grid(row=0, column=1, padx=8)

        tk.Button(btn_frame, text="🤖  CPU Auto",
                  bg="#5DADE2", fg="white", font=("Arial", 11, "bold"),
                  width=13, command=self.cpu_auto_solve).grid(row=0, column=2, padx=8)

        self.moves_lbl = tk.Label(self.root, font=("Arial", 10),
                                  bg=BG_COLOR, fg="#555")
        self.moves_lbl.pack(pady=(0,10))

        legend = tk.Frame(self.root, bg=BG_COLOR)
        legend.pack(pady=(0,8))
        for text, color in [("Buffer(shared)", BUFFER_COLOR),
                             ("Q1-TL", QUAD_COLORS[0]), ("Q2-TR", QUAD_COLORS[1]),
                             ("Q3-BL", QUAD_COLORS[2]), ("Q4-BR", QUAD_COLORS[3])]:
            tk.Label(legend, text=f" {text} ", bg=color,
                     font=("Arial", 9), relief="ridge").pack(side="left", padx=2)

    # ── Start Game ────────────────────────────────────────────
    def start_game(self):
        self.cpu_animating = False
        self.solution_path = []
        self.solution_step = 0
        self.hint_index    = None
        self.human_score   = 0
        self.cpu_score     = 0
        self.human_moves   = 0
        self.cpu_moves     = 0

        self.board = shuffle_board(self.goal, self.size, self.shuffle_steps)
        self.prev_correct = count_correct(self.board, self.goal)
        self.turn    = "HUMAN"
        self.running = True

        _, _, buf_cells, quad_cells = get_quadrant_cells(self.size)
        self.buffer_idx_set = cells_to_indices(buf_cells, self.size)
        self.quad_idx_flat  = [cells_to_indices(q, self.size) for q in quad_cells]

        self.update_ui()
        self.set_status("🟢 Your turn!")

    # ── UI helpers ────────────────────────────────────────────
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
        valid_moves = get_valid_moves(self.board, self.size) if self.turn == "HUMAN" else []

        for i, v in enumerate(self.board):
            btn = self.buttons[i]
            if v == 0:
                btn.config(text="", bg=EMPTY_COLOR, state="disabled", relief="sunken")
            else:
                is_correct = (v == self.goal[i])
                is_hint    = (i == self.hint_index)
                is_cpu_hi  = (i == highlighted)
                is_valid   = (i in valid_moves)

                if is_cpu_hi:    bg = CPU_MOVE_COLOR
                elif is_hint:    bg = HINT_COLOR
                elif is_correct: bg = CORRECT_COLOR
                else:            bg = self.get_zone_color(i)

                fg     = "white" if is_hint else "#2C3E50"
                relief = "groove" if is_valid and not is_hint else "raised"
                state  = "normal" if self.turn == "HUMAN" else "disabled"
                btn.config(text=str(v), bg=bg, fg=fg, state=state, relief=relief)

        self.score_lbl.config(
            text=f"👤 Human: {self.human_score}    🤖 CPU: {self.cpu_score}")
        self.moves_lbl.config(
            text=f"Moves —  You: {self.human_moves}   CPU: {self.cpu_moves}")

    def update_score(self, player):
        now = count_correct(self.board, self.goal)
        gained = now - self.prev_correct
        if gained > 0:
            if player == "HUMAN": self.human_score += gained
            else:                 self.cpu_score   += gained
        self.prev_correct = now

    # ── Human move ────────────────────────────────────────────
    def human_move(self, idx):
        if not self.running or self.turn != "HUMAN":
            return
        if idx not in get_valid_moves(self.board, self.size):
            self.set_status("⚠️  Invalid! Only click tiles next to the empty space.")
            return

        self.hint_index = None
        e = find_empty(self.board)
        self.board = list(swap_board(tuple(self.board), e, idx))
        self.human_moves += 1
        self.update_score("HUMAN")
        self.solution_path = []
        self.solution_step = 0
        self.update_ui()

        if self.board == self.goal:
            self.show_result("Human")
            return

        self.turn = "CPU"
        self.set_status("🤖 CPU is thinking (D&C Quadrant Solver)...")
        self.update_ui()
        self.root.after(450, self.cpu_turn)

    # ── Ensure solution is computed ───────────────────────────
    def _ensure_solution(self):
        if not self.solution_path:
            self.set_status("🤖 Computing D&C quadrant solution... please wait")
            self.root.update()
            self.solution_path = full_solve_dc(self.board, self.goal, self.size)
            self.solution_step = 0

            if (not self.solution_path or
                    list(self.solution_path[-1]) != self.goal):
                self.set_status("🤖 Trying fallback solver...")
                self.root.update()
                fallback = solve_full(self.board, tuple(self.goal), self.size,
                                      max_nodes=2000000)
                if fallback:
                    self.solution_path = fallback
                    self.solution_step = 0
                else:
                    self.solution_path = []
                    return False
        return True

    # ── CPU single turn ───────────────────────────────────────
    def cpu_turn(self):
        if not self.running:
            return
        if not self._ensure_solution():
            self.set_status("❌ CPU couldn't find solution. Try New Game.")
            self.turn = "HUMAN"
            self.update_ui()
            return

        if self.solution_step + 1 >= len(self.solution_path):
            self.turn = "HUMAN"
            self.update_ui()
            return

        next_state = self.solution_path[self.solution_step + 1]
        self.solution_step += 1
        old_board  = self.board[:]
        self.board = list(next_state)
        self.cpu_moves += 1
        self.update_score("CPU")

        moved_tile = next(
            (i for i in range(len(self.board))
             if self.board[i] != 0 and old_board[i] == 0), None)

        self.update_ui(highlighted=moved_tile)

        if self.board == self.goal:
            self.show_result("CPU")
            return

        self.turn = "HUMAN"
        self.set_status("🟢 Your turn!")
        self.root.after(500, self.update_ui)

    # ── Hint ──────────────────────────────────────────────────
    def show_hint(self):
        if not self.running or self.turn != "HUMAN":
            self.set_status("⚠️  Hint only available on your turn!")
            return
        if not self._ensure_solution():
            self.set_status("💡 Couldn't compute hint right now.")
            return
        if self.solution_step + 1 >= len(self.solution_path):
            self.set_status("💡 You're almost there — keep going!")
            return

        next_state      = self.solution_path[self.solution_step + 1]
        self.hint_index = list(next_state).index(0)
        self.update_ui()
        self.set_status("💡 Hint: Click the orange highlighted tile!")
        self.root.after(3500, self.clear_hint)

    def clear_hint(self):
        self.hint_index = None
        if self.running and self.turn == "HUMAN":
            self.update_ui()
            self.set_status("🟢 Your turn!  Click a tile next to the empty space.")

    # ── CPU Auto Solve ────────────────────────────────────────
    def cpu_auto_solve(self):
        if not self.running or self.cpu_animating:
            return
        if not self._ensure_solution():
            self.set_status("❌ Could not compute solution. Try New Game.")
            return

        self.turn          = "CPU"
        self.cpu_animating = True
        self.hint_index    = None
        self.set_status("🤖 CPU Auto-Solving with Quadrant D&C...")
        self.update_ui()
        self.root.after(300, self._auto_step)

    def _auto_step(self):
        if not self.cpu_animating or not self.running:
            return

        if self.solution_step + 1 >= len(self.solution_path):
            self.cpu_animating = False
            self.turn = "HUMAN"
            self.update_ui()
            return

        next_state = self.solution_path[self.solution_step + 1]
        self.solution_step += 1
        old_board  = self.board[:]
        self.board = list(next_state)
        self.cpu_moves += 1
        self.update_score("CPU")

        moved_tile = next(
            (i for i in range(len(self.board))
             if self.board[i] != 0 and old_board[i] == 0), None)

        self.update_ui(highlighted=moved_tile)
        remaining = len(self.solution_path) - 1 - self.solution_step
        self.set_status(f"🤖 CPU solving... {remaining} moves remaining")

        if self.board == self.goal:
            self.cpu_animating = False
            self.show_result("CPU")
            return

        self.root.after(270, self._auto_step)

    # ── Result ────────────────────────────────────────────────
    def show_result(self, winner):
        self.running       = False
        self.cpu_animating = False
        emoji = "🏆" if winner == "Human" else "🤖"
        messagebox.showinfo(
            "Puzzle Solved! 🎉",
            f"{emoji}  {winner} solved the puzzle!\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Final Score\n"
            f"  👤 Human : {self.human_score} pts  ({self.human_moves} moves)\n"
            f"  🤖 CPU   : {self.cpu_score} pts  ({self.cpu_moves} moves)\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
        )

# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    PuzzleGame(root)
    root.mainloop()








