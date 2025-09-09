import time, random, heapq
from collections import deque
import pandas as pd



#Graph Generation
def generate_weighted_graph(n, extra_edges_factor=2, weight_range=(1, 10)):
    adj = {i: [] for i in range(n)}
    for i in range(1, n):
        j = random.randint(0, i-1)
        w = random.randint(*weight_range)
        adj[i].append((j, w))
        adj[j].append((i, w))
    extra_edges = extra_edges_factor * n
    edges_set = set()
    for u in range(n):
        for v, _ in adj[u]:
            if u < v:
                edges_set.add((u, v))
    added = 0
    while added < extra_edges:
        a, b = random.randrange(n), random.randrange(n)
        if a == b: continue
        u, v = sorted((a, b))
        if (u, v) in edges_set:
            continue
        w = random.randint(*weight_range)
        adj[u].append((v, w))
        adj[v].append((u, w))
        edges_set.add((u, v))
        added += 1
    return adj

def is_connected(adj):
    visited = set()
    q = deque([0])
    visited.add(0)
    while q:
        u = q.popleft()
        for v, _ in adj[u]:
            if v not in visited:
                visited.add(v)
                q.append(v)
    return len(visited) == len(adj)

# Helpers
def reconstruct_path(parents, start, goal):
    if goal not in parents and start != goal:
        return None
    path = []
    node = goal
    while node != start:
        path.append(node)
        node = parents[node]
    path.append(start)
    return path[::-1]

def path_cost(adj, path):
    if not path: return None
    cost = 0
    for i in range(len(path)-1):
        u, v = path[i], path[i+1]
        for nei, w in adj[u]:
            if nei == v:
                cost += w
                break
    return cost

# BFS
def bfs(adj, start, goal):
    start_time = time.perf_counter()
    q = deque([start])
    visited = {start}
    parents = {}
    nodes_expanded = 0
    found = False
    while q:
        u = q.popleft()
        nodes_expanded += 1
        if u == goal:
            found = True
            break
        for v, _ in adj[u]:
            if v not in visited:
                visited.add(v)
                parents[v] = u
                q.append(v)
    return {
        "path": reconstruct_path(parents, start, goal) if found else None,
        "nodes": nodes_expanded,
        "time": time.perf_counter() - start_time
    }

#DFS
def dfs(adj, start, goal):
    start_time = time.perf_counter()
    stack = [start]
    parents = {}
    visited = {start}
    nodes_expanded = 0
    found = False
    while stack:
        u = stack.pop()
        nodes_expanded += 1
        if u == goal:
            found = True
            break
        for v, _ in adj[u]:
            if v not in visited:
                visited.add(v)
                parents[v] = u
                stack.append(v)
    return {
        "path": reconstruct_path(parents, start, goal) if found else None,
        "nodes": nodes_expanded,
        "time": time.perf_counter() - start_time
    }

#UCS
def ucs(adj, start, goal):
    start_time = time.perf_counter()
    dist = {start: 0}
    parents = {}
    pq = [(0, start)]
    visited = set()
    nodes_expanded = 0
    while pq:
        cost, u = heapq.heappop(pq)
        if u in visited:
            continue
        visited.add(u)
        nodes_expanded += 1
        if u == goal:
            break
        for v, w in adj[u]:
            new_cost = cost + w
            if v not in dist or new_cost < dist[v]:
                dist[v] = new_cost
                parents[v] = u
                heapq.heappush(pq, (new_cost, v))
    return {
        "path": reconstruct_path(parents, start, goal) if goal in dist else None,
        "nodes": nodes_expanded,
        "time": time.perf_counter() - start_time,
        "cost": dist.get(goal, None)
    }

#IDS
def depth_limited_dfs(adj, node, goal, limit, visited_path, parents, counter):
    counter['expanded'] += 1
    if node == goal: return True
    if limit == 0: return False
    for v, _ in adj[node]:
        if v in visited_path:
            continue
        parents[v] = node
        visited_path.add(v)
        if depth_limited_dfs(adj, v, goal, limit-1, visited_path, parents, counter):
            return True
        visited_path.remove(v)
    return False

def ids(adj, start, goal, max_depth=None):
    start_time = time.perf_counter()
    if max_depth is None: max_depth = len(adj)
    total_expanded = 0
    parents_final = None
    found = False
    for depth in range(max_depth + 1):
        parents = {}
        counter = {'expanded': 0}
        visited_path = {start}
        if depth_limited_dfs(adj, start, goal, depth, visited_path, parents, counter):
            parents_final = parents
            found = True
            total_expanded += counter['expanded']
            break
        total_expanded += counter['expanded']
    return {
        "path": reconstruct_path(parents_final, start, goal) if found else None,
        "nodes": total_expanded,
        "time": time.perf_counter() - start_time
    }

# Experiment
n = 1000
num_pairs = 5
while True:
    G = generate_weighted_graph(n, extra_edges_factor=2, weight_range=(1, 20))
    if is_connected(G):
        break

pairs = []
for _ in range(num_pairs):
    s, d = random.sample(range(n), 2)
    pairs.append((s, d))

results = []
for s, d in pairs:
    r_bfs = bfs(G, s, d)
    r_dfs = dfs(G, s, d)
    r_ucs = ucs(G, s, d)
    r_ids = ids(G, s, d)
    for name, res in [("BFS", r_bfs), ("DFS", r_dfs), ("UCS", r_ucs), ("IDS", r_ids)]:
        p = res.get("path")
        results.append({
            "start": s,
            "goal": d,
            "algorithm": name,
            "nodes_expanded": res["nodes"],
            "time_sec": res["time"],
            "path_length": len(p)-1 if p else None,
            "path_cost": path_cost(G, p)
        })

df = pd.DataFrame(results)
summary = df.groupby("algorithm").mean(numeric_only=True)
summary=summary.drop(["start", "goal"], axis=1)
pd.set_option("display.max_columns", None)


print("Comparison of Algorithms:\n", summary)
