
from collections import deque

def swap(state,pos1,pos2):
        state_ = list(state)
        state_[pos1],state_[pos2] = state_[pos2],state_[pos1]
        return tuple(state_)

def next_states(state):
    next_state = []
    empty_block_idx = state.index(0)
    row = empty_block_idx // 3
    col = empty_block_idx % 3
    
    if row>0:
        next_state.append((swap(state,empty_block_idx,empty_block_idx-3),"UP"))
    
    if row<2:
        next_state.append((swap(state,empty_block_idx,empty_block_idx+3),"DOWN"))
    
    if col>0:
        next_state.append((swap(state,empty_block_idx,empty_block_idx-1),"LEFT"))
        
    if col<2:
        next_state.append((swap(state,empty_block_idx,empty_block_idx+1),"RIGHT"))
        
    return next_state

def states_moves(state,parent):
    curr_state = state
    states = []
    moves = []
    while curr_state is not None:
        states.append(curr_state)
        moves.append(parent[curr_state][1])
        curr_state = parent[curr_state][0]
    
    states.reverse()
    moves.reverse()
    return states,moves[1:]

def bfs_puzzle(initial_state,goal_state):
     queue = deque([initial_state])
     visited = set()
     parent = {initial_state:(None,None)}
     
     while queue:
         curr_state = queue.popleft()
         visited.add(curr_state)
         if curr_state == goal_state :
             return states_moves(goal_state,parent)
         
         for next_state,move in next_states(curr_state):
             if next_state not in visited:
                 queue.append(next_state)
                 parent[next_state] = (curr_state,move)
    
     return None

def dfs_puzzle(initial_state,goal_state):
    stack = [initial_state]
    visited = set()
    parent = {initial_state:(None,None)}
    
    while stack:
        curr_state = stack.pop()
        visited.add(curr_state)
        
        if curr_state == goal_state:
            return states_moves(goal_state,parent)
        
        for next_state,move in next_states(curr_state):
            if next_state not in visited:
                stack.append(next_state)
                parent[next_state] = (curr_state,move)
    return None           
 
initial_state = (1,2,3,4,0,5,6,7,8)
goal_state = (1,2,3,4,5,6,7,8,0)

print("____DFS SOLUTION____")    
if dfs_puzzle(initial_state,goal_state) is not None:
    states, moves = dfs_puzzle(initial_state,goal_state)
    print(f'Initial State: {states[0]}')
    for i in range(len(moves)):
        print(f'Move: {moves[i]}')
        print(f'State: {states[i+1]}')
    print(f'Total Moves = {len(moves)}')
else:
    print("No solution")
    

print("____BFS SOLUTION____")
if bfs_puzzle(initial_state,goal_state) is not None:
    states, moves = bfs_puzzle(initial_state,goal_state)
    print(f'Initial State: {states[0]}')
    for i in range(len(moves)):
        print(f'Move: {moves[i]}')
        print(f'State: {states[i+1]}')
    print(f'Total Moves = {len(moves)}')
else:
    print("No solution")
