import random
import tkinter as tk
from tkinter import font as tkfont
import heapq
import time

#GAME CONSTANTS 
SIZE = 4
GOAL = list(range(1, SIZE * SIZE)) + [0]

#GUI COLOURS
BG_COLOR = "#E8F6F3"      
TILE_COLOR = "#FFF9C4"    
EMPTY_SLOT = "#A9DFBF"    
TEXT_COLOR = "#2D3436"    
CARD_BLUE = "#D6EAF8"     
BTN_START = "#58D68D"    
BTN_RESET = "#EC7063"     
BTN_GREY = "#BDC3C7"     

#TO FIND THE EMPTY SPACE
def find_empty(board):
    return board.index(0)
#VALID MOVES
def get_valid_moves(board):
    e = find_empty(board)
    r, c = divmod(e, SIZE)
    moves = []
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < SIZE and 0 <= nc < SIZE:
            moves.append(nr * SIZE + nc)
    return moves

def swap(board, i, j):
    b = board.copy()
    b[i], b[j] = b[j], b[i]
    return b

def shuffle_board(board, steps=40):
    cur = board.copy()
    for _ in range(steps):
        moves = get_valid_moves(cur)
        t = random.choice(moves)
        cur = swap(cur, find_empty(cur), t)
    return cur
    
#GREEDY LOGIC 
def manhattan(board):
    d = 0
    for i, v in enumerate(board):
        if v == 0: continue
        gi = GOAL.index(v)
        r1, c1 = divmod(i, SIZE)
        r2, c2 = divmod(gi, SIZE)
        d += abs(r1 - r2) + abs(c1 - c2)
    return d
#SORTING 
def insertion_sort_moves(moves):
    for i in range(1, len(moves)):
        key = moves[i]
        j = i - 1
        while j >= 0 and moves[j][1] > key[1]:
            moves[j + 1] = moves[j]
            j -= 1
        moves[j + 1] = key
    return moves

#A*ALGORITHM 
def get_a_star_move(start_board):
    queue = []
    initial_h = manhattan(start_board)
    heapq.heappush(queue, (initial_h, 0, start_board, None))
    visited = {tuple(start_board): 0}
    
    iterations = 0
    while queue and iterations < 3000:
        iterations += 1
        f, g, current, first_move = heapq.heappop(queue)
        if current == GOAL: return first_move
        
        empty = find_empty(current)
        for move_idx in get_valid_moves(current):
            new_board = swap(current, empty, move_idx)
            t_board = tuple(new_board)
            new_g = g + 1
            if t_board not in visited or new_g < visited[t_board]:
                visited[t_board] = new_g
                h = manhattan(new_board)
                actual_first_move = move_idx if g == 0 else first_move
                heapq.heappush(queue, (new_g + h, new_g, new_board, actual_first_move))
                
    empty = find_empty(start_board)
    return min(get_valid_moves(start_board), key=lambda m: manhattan(swap(start_board, empty, m)))

# GAMIFIED GUI
class FifteenGame:
    def _init_(self, root):
        self.root = root
        self.root.title("15 Puzzle Adventure")
        self.root.geometry("620x750")
        self.root.configure(bg=BG_COLOR)
        
        # Game State
        self.is_started = False
        self.is_paused = False
        self.game_over = False
        self.board = GOAL.copy()
        self.turn = "HUMAN"
        self.human_moves = 0
        self.cpu_moves = 0
        self.h_score = 0
        self.c_score = 0
        self.start_time = None
        self.elapsed_time = 0
        
        self.setup_fonts()
        self.build_ui()
        self.update_clock()
        self.update_ui()

    def setup_fonts(self):
        self.title_f = tkfont.Font(family="Comic Sans MS", size=32, weight="bold")
        self.card_val_f = tkfont.Font(family="Verdana", size=16, weight="bold")
        self.card_lbl_f = tkfont.Font(family="Verdana", size=9, weight="bold")
        self.tile_f = tkfont.Font(family="Comic Sans MS", size=22, weight="bold")
        self.btn_f = tkfont.Font(family="Verdana", size=10, weight="bold")

    def create_stat_card(self, parent, label):
        frame = tk.Frame(parent, bg=CARD_BLUE, padx=15, pady=8, highlightbackground="#AED6F1", highlightthickness=2)
        tk.Label(frame, text=label, font=self.card_lbl_f, bg=CARD_BLUE, fg="#5D6D7E").pack()
        val_lbl = tk.Label(frame, text="0", font=self.card_val_f, bg=CARD_BLUE, fg=TEXT_COLOR)
        val_lbl.pack()
        return frame, val_lbl

    def build_ui(self):
     
        header = tk.Frame(self.root, bg=BG_COLOR, pady=20)
        header.pack(fill="x")
        
        tk.Label(header, text="FIFTEEN PUZZLE GAME", font=self.title_f, bg=BG_COLOR, fg="#16A085").pack()

        stats_frame = tk.Frame(self.root, bg=BG_COLOR)
        stats_frame.pack(pady=10)

        
        self.human_card, self.h_score_lbl = self.create_stat_card(stats_frame, "HUMAN SCORE")
        self.human_card.grid(row=0, column=0, padx=10)
        
        
        self.time_card, self.time_val = self.create_stat_card(stats_frame, "TIME")
        self.time_val.config(text="00:00")
        self.time_card.grid(row=0, column=1, padx=10)

    
        self.cpu_card, self.c_score_lbl = self.create_stat_card(stats_frame, "CPU SCORE")
        self.cpu_card.grid(row=0, column=2, padx=10)

    
        self.grid_container = tk.Frame(self.root, bg=EMPTY_SLOT, padx=10, pady=10)
        self.grid_container.pack(pady=15)

        self.buttons = []
        for i in range(16):
            btn = tk.Button(
                self.grid_container, text="", width=5, height=2,
                font=self.tile_f, relief="flat", cursor="hand2",
                command=lambda i=i: self.human_move(i)
            )
            btn.grid(row=i//4, column=i%4, padx=5, pady=5)
            self.buttons.append(btn)

        # Controls
        ctrl_frame = tk.Frame(self.root, bg=BG_COLOR)
        ctrl_frame.pack(pady=10)

        self.btn_pause = tk.Button(ctrl_frame, text="START", font=self.btn_f, bg=BTN_START, fg="white", 
                                   relief="flat", width=12, pady=8, command=self.toggle_pause)
        self.btn_pause.grid(row=0, column=0, padx=10)

        tk.Button(ctrl_frame, text="RESET", font=self.btn_f, bg=BTN_RESET, fg="white", 
                  relief="flat", width=12, pady=8, command=self.restart_game).grid(row=0, column=1, padx=10)

        self.status_lbl = tk.Label(self.root, text="Press Start to Play!", font=self.btn_f, bg=BG_COLOR, fg="#7F8C8D")
        self.status_lbl.pack(pady=5)

    # CLOCK  TIMING
    def update_clock(self):
        if self.is_started and not self.is_paused and not self.game_over:
            self.elapsed_time = int(time.time() - self.start_time)
            mins, secs = divmod(self.elapsed_time, 60)
            self.time_val.config(text=f"{mins:02d}:{secs:02d}")
        self.root.after(1000, self.update_clock)

    def toggle_pause(self):
        if not self.is_started:
            self.start_game()
            return
        if self.game_over: return
        
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.btn_pause.config(text="RESUME", bg=BTN_START)
            self.status_lbl.config(text="Paused", fg="#F39C12")
        else:
            self.btn_pause.config(text="PAUSE", bg=BTN_GREY)
            self.status_lbl.config(text="AI Thinking..." if self.turn == "CPU" else "Your Turn!")
            if self.turn == "CPU": self.root.after(500, self.cpu_move)
        self.update_ui()

    def start_game(self):
        self.is_started = True
        self.start_time = time.time()
        self.board = shuffle_board(GOAL, 30)
        self.btn_pause.config(text="PAUSE", bg=BTN_GREY)
        self.status_lbl.config(text="Your Turn!", fg="#27AE60")
        self.update_ui()

    def restart_game(self):
        self.board = shuffle_board(GOAL, 40)
        self.human_moves = 0
        self.cpu_moves = 0
        self.h_score = 0
        self.c_score = 0
        self.elapsed_time = 0
        self.start_time = time.time()
        self.is_started = True
        self.is_paused = False
        self.game_over = False
        self.turn = "HUMAN"
        self.btn_pause.config(text="PAUSE", bg=BTN_GREY)
        self.status_lbl.config(text="Your Turn!", fg="#27AE60")
        self.update_ui()

    def human_move(self, idx):
        if not self.is_started or self.is_paused or self.game_over or self.turn != "HUMAN": return
        if idx not in get_valid_moves(self.board): return

        self.process_move(idx, "HUMAN")
        if not self.game_over:
            self.turn = "CPU"
            self.status_lbl.config(text="AI is thinking...", fg="#E74C3C")
            self.root.after(800, self.cpu_move)

    def cpu_move(self):
        if not self.is_started or self.is_paused or self.game_over: return
        best_move = get_a_star_move(self.board)
        self.process_move(best_move, "CPU")
        self.turn = "HUMAN"
        self.status_lbl.config(text="Your Turn!", fg="#27AE60")
        self.update_ui()

    def process_move(self, move_idx, player):
        empty = find_empty(self.board)
        before = manhattan(self.board)
        self.board = swap(self.board, empty, move_idx)
        after = manhattan(self.board)

        if player == "HUMAN":
            self.human_moves += 1
            if after < before: self.h_score += 1
        else:
            self.cpu_moves += 1
            if after < before: self.c_score += 1

        if self.board == GOAL:
            self.update_ui()
            self.end_game()
        else:
            self.update_ui()

    def update_ui(self):
        for i, v in enumerate(self.board):
            if (not self.is_started or self.is_paused) and v != 0:
                self.buttons[i].config(text="?", state="disabled", bg="#D5DBDB", fg="#7F8C8D")
            elif v == 0:
                bg_color = "#F7DC6F" if self.game_over else EMPTY_SLOT
                self.buttons[i].config(text="", state="disabled", bg=bg_color)
            else:
                tile_bg = "#F7DC6F" if self.game_over else TILE_COLOR
                self.buttons[i].config(text=str(v), state="normal", bg=tile_bg, fg=TEXT_COLOR)
        
        self.h_score_lbl.config(text=str(self.h_score))
        self.c_score_lbl.config(text=str(self.c_score))
    #FINAL GAME LOGIC
    def end_game(self):
        self.game_over = True
        self.btn_pause.config(state="disabled", bg=BTN_GREY)
        
        if self.h_score > self.c_score:
            msg = " VICTORY! \nYou outsmarted the AI!"
            color = "#2ECC71"
        elif self.c_score > self.h_score:
            msg = "CPU WINS! \nBetter luck next time!"
            color = "#E74C3C"
        else:
            msg = " IT'S A DRAW! \nGreat minds think alike!"
            color = "#3498DB"

        self.status_lbl.config(text="PUZZLE SOLVED!", fg=color)
        
        # POPUP GUI
        popup = tk.Toplevel(self.root)
        popup.title("Game Over")
        popup.geometry("320x220")
        popup.configure(bg="white")
        popup.transient(self.root)
        popup.grab_set()

    
        x = self.root.winfo_x() + 150
        y = self.root.winfo_y() + 200
        popup.geometry(f"+{x}+{y}")

        tk.Label(popup, text=msg, font=("Verdana", 12, "bold"), bg="white", fg=color, pady=20, wraplength=250).pack()
        tk.Button(popup, text="PLAY AGAIN", font=self.btn_f, bg=BTN_START, fg="white", 
                  relief="flat", width=15, pady=5, command=lambda: [popup.destroy(), self.restart_game()]).pack(pady=10)
        tk.Button(popup, text="CLOSE", font=self.btn_f, bg=BTN_GREY, fg="white", 
                  relief="flat", width=15, pady=5, command=popup.destroy).pack()

if __name__ == "_main_":
    root = tk.Tk()
    FifteenGame(root)

    root.mainloop()
