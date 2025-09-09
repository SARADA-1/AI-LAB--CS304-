import heapq
import itertools
import random

def swap(state, pos1, pos2):
    state_ = list(state)
    state_[pos1], state_[pos2] = state_[pos2], state_[pos1]
    return tuple(state_)

def next_states(state):
    next_state = []
    empty_block_idx = state.index(0)
    row = empty_block_idx // 3
    col = empty_block_idx % 3

    if row > 0:
        next_state.append((swap(state, empty_block_idx, empty_block_idx - 3), "UP"))
    if row < 2:
        next_state.append((swap(state, empty_block_idx, empty_block_idx + 3), "DOWN"))
    if col > 0:
        next_state.append((swap(state, empty_block_idx, empty_block_idx - 1), "LEFT"))
    if col < 2:
        next_state.append((swap(state, empty_block_idx, empty_block_idx + 1), "RIGHT"))

    return next_state

def manhattan(state, goal):
    h = 0
    for i, val in enumerate(state):
        if val == 0:
            continue
        goal_idx = goal.index(val)
        h += abs(goal_idx // 3 - i // 3) + abs(goal_idx % 3 - i % 3)
    return h

def reconstruct_path(parent, end_state):
    states = []
    moves = []
    curr = end_state
    while curr is not None:
        prev, mv = parent[curr]
        states.append(curr)
        moves.append(mv)
        curr = prev
    states.reverse()
    moves.reverse()
    return states, moves[1:]

def a_star(initial_state, goal_state, heruistic):
    parent = {initial_state: (None, None)}
    g_score = {initial_state: 0}
    closed = set()

    counter = itertools.count()
    start_f = heruistic(initial_state, goal_state)
    open_heap = [(start_f, next(counter), initial_state)]

    while open_heap:
        f, _, state = heapq.heappop(open_heap)

        if state == goal_state:
            return reconstruct_path(parent, state)

        if state in closed:
            continue
        closed.add(state)

        current_g = g_score[state]

        for neighbour, move in next_states(state):
            tentative_g = current_g + 1 
            if neighbour in closed:
                continue

            if tentative_g < g_score.get(neighbour, float('inf')):
                parent[neighbour] = (state, move)
                g_score[neighbour] = tentative_g
                f_score = tentative_g + heruistic(neighbour, goal_state)
                heapq.heappush(open_heap, (f_score, next(counter), neighbour))

    return None

def rbfs(initial_state, goal_state, heuristic):
    def rbfs_rec(state, path, f, f_limit):
        if state == goal_state:
            return path, f

        successors = []
        for nxt, move in next_states(state):
            if nxt not in [p[0] for p in path]:  # avoid revisiting path
                g = len(path)
                f_val = g + heuristic(nxt, goal_state)
                successors.append([f_val, nxt, move])

        if not successors:
            return None, float('inf')

        while True:
            successors.sort(key=lambda x: x[0])
            best_f, best, best_move = successors[0]
            if best_f > f_limit:
                return None, best_f
            alt = successors[1][0] if len(successors) > 1 else float('inf')
            result, new_f = rbfs_rec(best, path+[(best, best_move)], best_f, min(f_limit, alt))
            successors[0][0] = new_f
            if result is not None:
                return result, new_f

    path, _ = rbfs_rec(initial_state, [(initial_state, None)], heuristic(initial_state, goal_state), float('inf'))
    if path:
        states = [s for s, _ in path]
        moves = [m for _, m in path][1:]
        return states, moves
    return None


def is_solvable(state):
    arr = [x for x in state if x != 0]
    inversions = 0
    for i in range(len(arr)):
        for j in range(i+1, len(arr)):
            if arr[i] > arr[j]:
                inversions += 1
    return inversions % 2 == 0

def generate_random_state():
    while True:
        nums = list(range(9))
        random.shuffle(nums)
        state = tuple(nums)
        if is_solvable(state):
            return state


initial_state = generate_random_state()
goal_state = (1,2,3,4,5,6,7,8,0)

print("____A* SOLUTION____")    
if a_star(initial_state, goal_state, manhattan) is not None:
    states, moves = a_star(initial_state, goal_state, manhattan)
    print(f'Initial State: {states[0]}')
    for i in range(len(moves)):
        print(f'Move: {moves[i]}')
        print(f'State: {states[i+1]}')
    print(f'Total Moves = {len(moves)}')
else:
    print("No solution.")

print("____RBFS SOLUTION____")    
if rbfs(initial_state, goal_state, manhattan) is not None:
    states, moves = rbfs(initial_state, goal_state, manhattan)
    print(f'Initial State: {states[0]}')
    for i in range(len(moves)):
        print(f'Move: {moves[i]}')
        print(f'State: {states[i+1]}')
    print(f'Total Moves = {len(moves)}')
else:
    print("No solution.")