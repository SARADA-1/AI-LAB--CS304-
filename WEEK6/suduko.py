import time
import random
import pandas as pd
import tracemalloc
from copy import deepcopy

def print_board(bo):
    for i in range(len(bo)):
        if i % 3 == 0 and i != 0:
            print("- - - - - - - - - - - -")
        for j in range(len(bo[0])):
            if j % 3 == 0 and j != 0:
                print(" | ", end="")
            if j == 8:
                print(bo[i][j])
            else:
                print(str(bo[i][j]) + " ", end="")


def find_empty(bo):
    for i in range(len(bo)):
        for j in range(len(bo[0])):
            if bo[i][j] == 0:
                return (i, j) 
    return None


def is_valid(bo, num, pos):
    for j in range(len(bo[0])):
        if bo[pos[0]][j] == num and pos[1] != j:
            return False

    for i in range(len(bo)):
        if bo[i][pos[1]] == num and pos[0] != i:
            return False

    box_x = pos[1] // 3
    box_y = pos[0] // 3
    for i in range(box_y * 3, box_y * 3 + 3):
        for j in range(box_x * 3, box_x * 3 + 3):
            if bo[i][j] == num and (i, j) != pos:
                return False
    return True

def generate_sudoku(difficulty):
    base_board = [[0 for _ in range(9)] for _ in range(9)]
    
    def fill_board(bo):
        find = find_empty(bo)
        if not find: 
            return True
        
        row, col = find
        numbers = list(range(1, 10))
        random.shuffle(numbers)

        for num in numbers:
            if is_valid(bo, num, (row, col)):
                bo[row][col] = num
                if fill_board(bo): 
                    return True
                bo[row][col] = 0
        return False
        
    fill_board(base_board)
    cells = [(r, c) for r in range(9) for c in range(9)]
    random.shuffle(cells)
    
    for r, c in cells[:difficulty]:
        base_board[r][c] = 0
        
    return base_board

def solve_simple_backtracking(bo):
    find = find_empty(bo)
    if not find:
        return True
    else:
        row, col = find

    for i in range(1, 10):
        if is_valid(bo, i, (row, col)):
            bo[row][col] = i
            if solve_simple_backtracking(bo):
                return True
            bo[row][col] = 0
    return False

def solve_mrv(bo):
    min_r = min_c = None
    min_options = None
    for r in range(9):
        for c in range(9):
            if bo[r][c] == 0:
                opts = candidates(bo, r, c)
                if min_options is None or len(opts) < len(min_options):
                    min_options = opts
                    min_r, min_c = r, c
                if len(min_options) == 1:
                    break
        if min_options is not None and len(min_options) == 1:
            break

    if min_r is None:
        return True 

    for n in list(min_options):
        bo[min_r][min_c] = n
        if solve_mrv(bo):
            return True
        bo[min_r][min_c] = 0
    return False

def candidates(bo, r, c):
    opts = set(range(1,10))
    opts -= set(bo[r])
    opts -= {bo[i][c] for i in range(9)}
    sr, sc = (r//3)*3, (c//3)*3
    for i in range(sr, sr+3):
        for j in range(sc, sc+3):
            opts.discard(bo[i][j])
    return opts


def measure(func, bo):
    b = deepcopy(bo)
    tracemalloc.start()
    t0 = time.perf_counter()
    solved = func(b)
    t1 = time.perf_counter()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {
        "solved": bool(solved),
        "time_s": t1 - t0,
        "peak_mem_kb": peak / 1024.0,
        "solution": b if solved else None
    }


difficulty = 60 
puzzle_board = generate_sudoku(difficulty)

print(f"Generated Sudoku Puzzle (Difficulty: {difficulty} empty cells)")
print_board(puzzle_board)

plain_result = measure(solve_simple_backtracking, puzzle_board)

print("Plain solver solved?:", plain_result["solved"])
if plain_result["solved"]:
    print("Solution found by plain solver:\n")
    print_board(plain_result["solution"])

mrv_result = measure(solve_mrv, puzzle_board)
print("MRV solver solved?:", mrv_result["solved"])
if mrv_result["solved"]:
    print("Solution found by MRV solver:\n")
    print_board(mrv_result["solution"])

df = pd.DataFrame([
        {
            "method": "Plain Backtracking",
            "time_s": round(plain_result["time_s"], 6),
            "peak_mem_kb": round(plain_result["peak_mem_kb"], 2),
            "solved": plain_result["solved"]
        },
        {
            "method": "MRV Heuristic",
            "time_s": round(mrv_result["time_s"], 6),
            "peak_mem_kb": round(mrv_result["peak_mem_kb"], 2),
            "solved": mrv_result["solved"]
        }
    ])

print("\nComparison table:\n")
print(df.to_string(index=False))