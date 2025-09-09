
import random

N = 8

def conflicts(state):
    h = 0
    s = list(state)
    for i in range(N):
        for j in range(i+1, N):
            if s[i] == s[j] or abs(s[i]-s[j]) == abs(i-j):
                h += 1
    return h

def random_state():
    return tuple(random.randint(0, N-1) for _ in range(N))

def neighbors(state):
    result = []
    for col in range(N):
        for row in range(N):
            if state[col] != row:
                new_state = list(state)
                new_state[col] = row
                result.append(tuple(new_state))
    return result

def random_restart_hill_climb(max_restarts=50):
    for restart in range(max_restarts):
        current = random_state()
        path = [current]
        while True:
            h = conflicts(current)
            if h == 0:
                return path, current, restart
            next_state = min(neighbors(current), key=lambda n: conflicts(n))
            if conflicts(next_state) >= h:
                break 
            current = next_state
            path.append(current)
    return None, None, max_restarts

def print_board(state):
    for r in range(N):
        row = ""
        for c in range(N):
            row += "Q " if state[c] == r else ". "
        print(row)
    print()

path, solution, restarts = random_restart_hill_climb()

if solution:
    print(f"Solved after {restarts} restarts!\n")
    for state in path:
        print(f"Conflicts: {conflicts(state)}")
        print_board(state)
else:
    print("Failed to solve within restart limit.")