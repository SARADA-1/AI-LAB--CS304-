import time, tracemalloc, copy

def is_variable(x):
    return isinstance(x, str) and x[0].islower()

def occurs_check(v, x, t):
    if v == x:
        return True
    elif is_variable(x) and x in t:
        return occurs_check(v, t[x], t)
    elif isinstance(x, list):
        return any(occurs_check(v, i, t) for i in x)
    else:
        return False

def unify_var(v, x, t):
    if v in t:
        return unify(t[v], x, t)
    elif x in t:
        return unify(v, t[x], t)
    elif occurs_check(v, x, t):
        return "FAIL"
    else:
        nt = copy.deepcopy(t)
        nt[v] = x
        return nt

def unify(x, y, t=None):
    if t is None:
        t = {}
    if t == "FAIL":
        return "FAIL"
    elif x == y:
        return t
    elif is_variable(x):
        return unify_var(x, y, t)
    elif is_variable(y):
        return unify_var(y, x, t)
    elif isinstance(x, list) and isinstance(y, list) and len(x) == len(y):
        return unify(x[1:], y[1:], unify(x[0], y[0], t))
    else:
        return "FAIL"

def forward_chain(KB, query):
    inferred = set()
    added = True
    while added:
        added = False
        for head, body in KB:
            if all(p in inferred or p in [b[0] for b in KB if not b[1]] for p in body):
                if head not in inferred:
                    inferred.add(head)
                    added = True
                    if head == query:
                        return True
    return query in inferred

KB = [
    ('Ancestor(Mother(x), x)', []),
    ('Ancestor(x, z)', ['Ancestor(x, y)', 'Ancestor(y, z)'])
]

queries = [
    'Ancestor(Mother(y), John)',
    'Ancestor(Mother(Mother(y)), John)',
    'Ancestor(Mother(Mother(Mother(y))), Mother(y))',
    'Ancestor(Mother(John), Mother(Mother(John)))'
]

tracemalloc.start()
start = time.time()

for q in queries:
    r = forward_chain(KB, q)
    print(f"{q} -> {r}")

end = time.time()
current, peak = tracemalloc.get_traced_memory()
print(f"Time: {end - start:.6f}s")
print(f"Space: {peak / 1024:.2f} KB")
tracemalloc.stop()