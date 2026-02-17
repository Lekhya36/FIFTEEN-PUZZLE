import random
import tkinter as tk
from tkinter import font as tkfont
import time
import sys

sys.setrecursionlimit(10000)

# ======================
# GAME CONSTANTS
# ======================
SIZE = 4
GOAL = list(range(1, SIZE * SIZE)) + [0]
INF = float("inf")

# ======================
# GUI COLORS
# ======================
BG_COLOR = "#E8F6F3"
TILE_COLOR = "#FFF9C4"
EMPTY_SLOT = "#A9DFBF"
TEXT_COLOR = "#2D3436"
BTN_START = "#58D68D"
BTN_RESET = "#EC7063"
BTN_GREY = "#BDC3C7"

# ======================
# BOARD UTILITIES
# ======================
def find_empty(board):
    return board.index(0)

def get_valid_moves(board):
    e = find_empty(board)
    r, c = divmod(e, SIZE)
    moves = []
    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < SIZE and 0 <= nc < SIZE:
            moves.append(nr * SIZE + nc)
    return moves

def swap(board, i, j):
    b = board.copy()
    b[i], b[j] = b[j], b[i]
    return b

def shuffle_board(board, steps=20):  # reduced for speed
    cur = board.copy()
    for _ in range(steps):
        m = random.choice(get_valid_moves(cur))
        cur = swap(cur, find_empty(cur), m)
    return cur

def manhattan(board):
    d = 0
    for i, v in enumerate(board):
        if v == 0:
            continue
        gi = GOAL.index(v)
        r1, c1 = divmod(i, SIZE)
        r2, c2 = divmod(gi, SIZE)
        d += abs(r1 - r2) + abs(c1 - c2)
    return d

# ======================
# IDA* (DIVIDE & CONQUER + DP)
# ======================
def get_divide_conquer_dp_move(board):
    bound = manhattan(board)
    path = [board]
    memo = {}

    while True:
        t = ida_search(path, 0, bound, memo)
        if isinstance(t, int):
            return t
        if t == INF:
            return fallback_move(board)
        bound = t

def ida_search(path, g, bound, memo):
    node = path[-1]
    f = g + manhattan(node)

    if f > bound:
        return f
    if node == GOAL:
        return -1

    state = tuple(node)
    if state in memo and memo[state] <= g:
        return INF
    memo[state] = g

    min_cost = INF
    empty = find_empty(node)

    for move in get_valid_moves(node):
        child = swap(node, empty, move)
        if child in path:
            continue

        path.append(child)
        t = ida_search(path, g + 1, bound, memo)

        if t == -1:
            return move if g == 0 else -1

        min_cost = min(min_cost, t)
        path.pop()

    return min_cost

def fallback_move(board):
    empty = find_empty(board)
    return min(
        get_valid_moves(board),
        key=lambda m: manhattan(swap(board, empty, m))
    )

# ======================
# GAME GUI
# ======================
class FifteenGame:
    def __init__(self, root):
        self.root = root
        self.root.title("15 Puzzle – IDA* Solver")
        self.root.geometry("500x620")
        self.root.configure(bg=BG_COLOR)

        self.board = GOAL.copy()
        self.turn = "HUMAN"
        self.is_started = False
        self.game_over = False
        self.start_time = None

        self.setup_fonts()
        self.build_ui()
        self.update_ui()
        self.update_clock()

    def setup_fonts(self):
        self.title_f = tkfont.Font(size=26, weight="bold")
        self.tile_f = tkfont.Font(size=20, weight="bold")
        self.btn_f = tkfont.Font(size=10, weight="bold")

    def build_ui(self):
        tk.Label(self.root, text="15 PUZZLE (IDA*)",
                 font=self.title_f, bg=BG_COLOR).pack(pady=10)

        self.time_lbl = tk.Label(self.root, text="00:00",
                                 font=self.btn_f, bg=BG_COLOR)
        self.time_lbl.pack()

        self.grid = tk.Frame(self.root, bg=EMPTY_SLOT, padx=10, pady=10)
        self.grid.pack(pady=20)

        self.buttons = []
        for i in range(16):
            b = tk.Button(
                self.grid, text="", width=5, height=2,
                font=self.tile_f,
                command=lambda i=i: self.human_move(i)
            )
            b.grid(row=i//4, column=i%4, padx=5, pady=5)
            self.buttons.append(b)

        ctrl = tk.Frame(self.root, bg=BG_COLOR)
        ctrl.pack(pady=10)

        tk.Button(ctrl, text="START", bg=BTN_START,
                  font=self.btn_f, command=self.start_game).grid(row=0, column=0, padx=10)

        tk.Button(ctrl, text="RESET", bg=BTN_RESET,
                  font=self.btn_f, command=self.restart_game).grid(row=0, column=1, padx=10)

        self.status = tk.Label(self.root, text="Press START",
                               font=self.btn_f, bg=BG_COLOR)
        self.status.pack()

    def update_clock(self):
        if self.is_started and not self.game_over:
            elapsed = int(time.time() - self.start_time)
            m, s = divmod(elapsed, 60)
            self.time_lbl.config(text=f"{m:02d}:{s:02d}")
        self.root.after(1000, self.update_clock)

    def start_game(self):
        self.board = shuffle_board(GOAL)
        self.turn = "HUMAN"
        self.is_started = True
        self.game_over = False
        self.start_time = time.time()
        self.status.config(text="Your Turn")
        self.update_ui()

    def restart_game(self):
        self.board = shuffle_board(GOAL)
        self.turn = "HUMAN"
        self.game_over = False
        self.is_started = True
        self.start_time = time.time()
        self.status.config(text="Your Turn")
        self.update_ui()

    def human_move(self, idx):
        if not self.is_started or self.turn != "HUMAN":
            return
        if idx not in get_valid_moves(self.board):
            return

        self.make_move(idx)
        if self.board != GOAL:
            self.turn = "CPU"
            self.status.config(text="AI Thinking...")
            self.root.after(400, self.cpu_move)

    def cpu_move(self):
        move = get_divide_conquer_dp_move(self.board)
        if move is None:
            return
        self.make_move(move)
        self.turn = "HUMAN"
        self.status.config(text="Your Turn")

    def make_move(self, idx):
        empty = find_empty(self.board)
        self.board = swap(self.board, empty, idx)
        if self.board == GOAL:
            self.game_over = True
            self.status.config(text="PUZZLE SOLVED 🎉")
        self.update_ui()

    def update_ui(self):
        for i, v in enumerate(self.board):
            if v == 0:
                self.buttons[i].config(text="", state="disabled", bg=EMPTY_SLOT)
            else:
                self.buttons[i].config(text=str(v), state="normal", bg=TILE_COLOR)

# ======================
# MAIN
# ======================
if __name__ == "__main__":
    root = tk.Tk()
    FifteenGame(root)
    root.mainloop()
