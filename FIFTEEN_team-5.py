import tkinter as tk
from tkinter import messagebox
import random

BG_COLOR       = "#0f172a"
FRAME_COLOR    = "#111827"
TILE_COLOR     = "#1f2937"
CORRECT_COLOR  = "#064e3b"
EMPTY_COLOR    = "#0b3d3d"

NEON_BLUE      = "#00f5ff"
NEON_GREEN     = "#00ffae"

BTN_BLUE       = "#2563eb"
BTN_GREEN      = "#10b981"

# ─────────────────────────────────────────────
# BOARD UTILITIES
# ─────────────────────────────────────────────

def create_goal(size):
    return tuple(list(range(1, size * size)) + [0])

def find_empty(board):
    return board.index(0)

def get_neighbors(board, size):
    neighbors = []
    e = find_empty(board)
    r, c = divmod(e, size)

    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
        nr, nc = r+dr, c+dc
        if 0 <= nr < size and 0 <= nc < size:
            ni = nr * size + nc
            b = list(board)
            b[e], b[ni] = b[ni], b[e]
            neighbors.append(tuple(b))
    return neighbors

def shuffle_board(goal, size, steps):
    cur = goal
    for _ in range(steps):
        cur = random.choice(get_neighbors(cur, size))
    return list(cur)

def count_correct(board, goal):
    return sum(1 for i in range(len(board))
               if board[i] == goal[i] and board[i] != 0)

# ─────────────────────────────────────────────
# HEURISTIC (Manhattan Distance)
# ─────────────────────────────────────────────

def manhattan(board, goal, size):
    goal_pos = {v: divmod(i, size) for i, v in enumerate(goal)}
    dist = 0
    for i, v in enumerate(board):
        if v == 0:
            continue
        r, c = divmod(i, size)
        gr, gc = goal_pos[v]
        dist += abs(r-gr) + abs(c-gc)
    return dist

# ─────────────────────────────────────────────
# IDA* SOLVER 

def ida_star(start, goal, size):

    start = tuple(start)
    goal = tuple(goal)

    threshold = manhattan(start, goal, size)
    path = [start]

    def search(g, threshold):
        node = path[-1]
        f = g + manhattan(node, goal, size)

        if f > threshold:
            return f

        if node == goal:
            return "FOUND"

        minimum = float("inf")

        for neighbor in get_neighbors(node, size):

            if neighbor not in path:

                path.append(neighbor)

                temp = search(g + 1, threshold)

                if temp == "FOUND":
                    return "FOUND"

                if temp < minimum:
                    minimum = temp

                path.pop()

        return minimum

    while True:
        temp = search(0, threshold)

        if temp == "FOUND":
            return path

        if temp == float("inf"):
            return None

        threshold = temp

# ─────────────────────────────────────────────
# GAME CLASS
# ─────────────────────────────────────────────

class PuzzleGame:
    def __init__(self, root):
        self.root = root
        self.root.title("15 Game - IDA*")
        self.root.configure(bg=BG_COLOR)
        self.root.geometry("650x720")

        self.size = 4
        self.goal = create_goal(self.size)

        self.build_ui()
        self.start_game()

    # ───────── UI ─────────

    def build_ui(self):

        tk.Label(self.root,
                 text="SLIDING PUZZLE",
                 font=("Arial", 22, "bold"),
                 fg=NEON_BLUE,
                 bg=BG_COLOR).pack(pady=10)

        menu_frame = tk.Frame(self.root, bg=BG_COLOR)
        menu_frame.pack()

        tk.Label(menu_frame,
                 text="Board Size:",
                 font=("Arial", 12),
                 fg="white",
                 bg=BG_COLOR).grid(row=0, column=0, padx=5)

        self.size_var = tk.StringVar(value="4x4")

        size_menu = tk.OptionMenu(menu_frame,
                                  self.size_var,
                                  "4x4",
                                  "5x5")
        size_menu.config(bg="#1e293b", fg="white",
                         activebackground=NEON_BLUE,
                         highlightthickness=0,
                         width=6)
        size_menu.grid(row=0, column=1, padx=5)

        tk.Button(menu_frame,
                  text="Apply",
                  bg=BTN_GREEN,
                  fg="white",
                  relief="flat",
                  command=self.change_size).grid(row=0, column=2, padx=5)

        self.score_lbl = tk.Label(self.root,
                                  font=("Arial", 14, "bold"),
                                  fg=NEON_GREEN,
                                  bg=BG_COLOR)
        self.score_lbl.pack(pady=8)

        self.board_outer = tk.Frame(self.root,
                                    bg=NEON_BLUE,
                                    padx=4, pady=4)
        self.board_outer.pack(pady=15)

        self.board_frame = tk.Frame(self.board_outer,
                                    bg=FRAME_COLOR,
                                    padx=15, pady=15)
        self.board_frame.pack()

        self.buttons = []

        btn_frame = tk.Frame(self.root, bg=BG_COLOR)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame,
                  text="⚡ Auto Play",
                  bg=BTN_BLUE,
                  fg="white",
                  relief="flat",
                  command=self.cpu_auto_solve).grid(row=0, column=0, padx=10)

        tk.Button(btn_frame,
                  text="🔄 Restart",
                  bg=BTN_GREEN,
                  fg="white",
                  relief="flat",
                  command=self.start_game).grid(row=0, column=1, padx=10)

        self.animate_neon()

    def animate_neon(self):
        current = self.board_outer.cget("bg")
        self.board_outer.config(bg=NEON_GREEN if current == NEON_BLUE else NEON_BLUE)
        self.root.after(800, self.animate_neon)

    # ───────── GAME SETUP ─────────

    def change_size(self):
        self.size = 5 if self.size_var.get() == "5x5" else 4
        self.goal = create_goal(self.size)
        self.start_game()

    def build_board_buttons(self):

        for widget in self.board_frame.winfo_children():
            widget.destroy()

        self.buttons.clear()

        for i in range(self.size * self.size):
            b = tk.Button(self.board_frame,
                          width=4 if self.size == 5 else 5,
                          height=2,
                          font=("Arial", 14, "bold"),
                          fg="white",
                          bg=TILE_COLOR,
                          relief="flat",
                          command=lambda i=i: self.human_move(i))
            b.grid(row=i//self.size,
                   column=i%self.size,
                   padx=6, pady=6)
            self.buttons.append(b)

    def start_game(self):

        self.shuffle_steps = 35 if self.size == 4 else 45

        self.board = shuffle_board(self.goal,
                                   self.size,
                                   self.shuffle_steps)

        self.human_score = 0
        self.cpu_score = 0
        self.human_moves = 0
        self.cpu_moves = 0
        self.prev_correct = count_correct(self.board, self.goal)

        self.turn = "HUMAN"
        self.auto_mode = False

        self.build_board_buttons()
        self.update_ui()

    # ───────── UI UPDATE ─────────

    def update_ui(self):
        for i, v in enumerate(self.board):
            btn = self.buttons[i]
            if v == 0:
                btn.config(text="", bg=EMPTY_COLOR)
            else:
                btn.config(text=str(v),
                           bg=CORRECT_COLOR if v == self.goal[i]
                           else TILE_COLOR)

        self.score_lbl.config(
            text=f"Human: {self.human_score} ({self.human_moves})    "
                 f"CPU: {self.cpu_score} ({self.cpu_moves})"
        )

    def update_score(self, player):
        now = count_correct(self.board, self.goal)
        gained = now - self.prev_correct
        if gained > 0:
            if player == "HUMAN":
                self.human_score += gained
            else:
                self.cpu_score += gained
        self.prev_correct = now

    # ───────── MOVES ─────────

    def human_move(self, idx):
        if self.turn != "HUMAN":
            return

        for nb in get_neighbors(tuple(self.board), self.size):
            if nb[idx] == 0:
                self.board = list(nb)
                self.human_moves += 1
                self.update_score("HUMAN")
                break

        self.update_ui()

        if tuple(self.board) == self.goal:
            self.declare_winner()
            return

        self.turn = "CPU"
        self.root.after(500, self.cpu_turn)

    def cpu_turn(self):

        solution = ida_star(self.board,
                            self.goal,
                            self.size)

        if not solution or len(solution) < 2:
            return

        self.board = list(solution[1])
        self.cpu_moves += 1
        self.update_score("CPU")
        self.update_ui()

        if tuple(self.board) == self.goal:
            self.declare_winner()
            return

        if not self.auto_mode:
            self.turn = "HUMAN"
        else:
            self.root.after(250, self.cpu_turn)

    def cpu_auto_solve(self):
        self.auto_mode = True
        self.turn = "CPU"
        self.cpu_turn()

    def declare_winner(self):
        self.turn = None
        self.auto_mode = False

        winner = "Human" if self.human_score > self.cpu_score else "CPU"

        messagebox.showinfo(
            "Puzzle Solved!",
            f"Winner: {winner}\n\n"
            f"Human Score: {self.human_score}\n"
            f"CPU Score: {self.cpu_score}"
        )

# MAIN
if __name__ == "__main__":
    root = tk.Tk()
    PuzzleGame(root)
    root.mainloop()
