import time, tracemalloc, pandas as pd, sys
sys.setrecursionlimit(100000)


def planar_graph(n):
    adj = {i: set() for i in range(n)}

    for i in range(n-1):
        adj[i].add(i+1)
        adj[i+1].add(i)
    adj[0].add(n-1)
    adj[n-1].add(0)


    for start in range(0, min(n, 20), 4): 
        if start + 3 < n:
            nodes = [start, start+1, start+2, start+3]
            for i in range(4):
                for j in range(i+1, 4):
                    adj[nodes[i]].add(nodes[j])
                    adj[nodes[j]].add(nodes[i])
    for i in range(0, n-2, 2):
        adj[i].add(i+2)
        adj[i+2].add(i)

    edges = sum(len(v) for v in adj.values()) // 2
    return adj, n, edges



class CSP:
    def __init__(self, variables, domains, neighbors):
        self.variables = list(variables)
        self.domains = {v:set(domains[v]) for v in variables}
        self.neighbors = {v:set(neighbors[v]) for v in variables}
        self.nodes_explored = 0

def is_consistent(var, val, assignment, csp):
    for nb in csp.neighbors[var]:
        if nb in assignment and assignment[nb]==val:
            return False
    return True

def select_unassigned_var(assignment, csp):
    unassigned = [v for v in csp.variables if v not in assignment]
    best=None; best_key=None
    for v in unassigned:
        ds=len(csp.domains[v]); deg=len(csp.neighbors[v])
        key=(ds, -deg)
        if best is None or key < best_key:
            best=v; best_key=key
    return best

def forward_check(var, val, csp, assignment):
    removed=[]
    for nb in csp.neighbors[var]:
        if nb not in assignment and val in csp.domains[nb]:
            csp.domains[nb].remove(val)
            removed.append((nb,val))
            if len(csp.domains[nb])==0:
                return False, removed
    return True, removed

def restore(csp, removed):
    for v,val in removed:
        csp.domains[v].add(val)


def backtracking_search(csp):
    start=time.perf_counter()
    assignment={}
    csp.nodes_explored=0
    tracemalloc.start()

    def backtrack():
        if len(assignment)==len(csp.variables):
            return dict(assignment)
        var = select_unassigned_var(assignment, csp)
        csp.nodes_explored += 1
        for val in sorted(list(csp.domains[var])):
            if is_consistent(var, val, assignment, csp):
                assignment[var]=val
                ok, removed = forward_check(var, val, csp, assignment)
                if ok:
                    sol = backtrack()
                    if sol is not None:
                        return sol      
                restore(csp, removed)
                del assignment[var]
        return None

    sol = backtrack()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {
        "solution": sol,
        "time": time.perf_counter()-start,
        "memory_peak_kb": peak/1024.0,
        "nodes_explored": csp.nodes_explored,
    }

def validate_coloring(adj, coloring):
    if coloring is None: return False
    for v,neis in adj.items():
        for nb in neis:
            if coloring[v]==coloring[nb]:
                return False
    return True


sizes = [100, 200, 500, 1000, 5000]   
results=[]

for n in sizes:
    adj, nodes, edges = planar_graph(n)
    domains = {v:set(range(5)) for v in adj}  
    csp = CSP(list(adj.keys()), domains, adj)
    res = backtracking_search(csp)
    sol = res["solution"]
    success = validate_coloring(adj, sol)
    colors_used = len(set(sol.values())) if sol else None
    results.append({
        "n": n, "nodes": nodes, "edges": edges, "colors_used": colors_used,
        "time_s": round(res["time"],4), "memory_peak_kb": round(res["memory_peak_kb"],2),
        "nodes_explored": res["nodes_explored"],
        "success": success
    })

df = pd.DataFrame(results)
print(df.to_string(index=False))

