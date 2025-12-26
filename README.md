# FIFTEEN-PUZZLE
A modern, gamified Fifteen Puzzle game built with Python and Tkinter, featuring a Human vs CPU mode powered by the A* search algorithm and Manhattan distance heuristic. Includes an interactive GUI, score tracking, timer
1️⃣Board Setup
The board size is 4×4
Tiles contain numbers 1 to 15
0 represents the empty space

2️⃣ Shuffling the Board
The board is shuffled using valid moves only
This ensures the puzzle is always solvable

3️⃣ Valid Moves Logic
A tile can move up, down, left, or right
Only tiles next to the empty space are allowed

4️⃣ Manhattan Distance (Heuristic)
Calculates how far tiles are from their correct position
Used by AI to decide the best move

5️⃣ AI Logic – A* Algorithm
Uses:
g(n) → number of moves
h(n) → Manhattan distance
f(n) = g(n) + h(n)

6️⃣ Human vs CPU Turns
Human clicks tiles to move
CPU automatically makes a move after human
Turns alternate until puzzle is solved

7️⃣ Scoring System
Score increases if a move reduces Manhattan distance
Separate scores for Human and CPU

8️⃣ Timer
Starts when the game start
Pauses when the game is paused
Displayed in MM:SS format

9️⃣ Game End
Game ends when board reaches the goal state
Winner decided based on score
Popup message displays result

**Key Concepts Used
Tkinter GUI
A* Search Algorithm
Heuristic Function
Manhattan Distance
Priority Queue (heapq)
Game State Management
