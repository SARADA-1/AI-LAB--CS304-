from typing import Any, Set, FrozenSet, Dict, Tuple, Optional, List
from collections import deque


AST = Any
Clause = FrozenSet[str]


#AST BUILDER
def build_tree(formula):
    s = ''.join(formula.split())
    if len(s) == 0:
        raise ValueError("Empty formula")
    if len(s) == 1 and s.isupper():
        return s
    depth = 0
    ops = ["<->", "->", "|", "&"]
    i = len(s) - 1
    while i >= 0:
        ch = s[i]
        if ch == ')':
            depth += 1
        elif ch == '(':
            depth -= 1
        elif depth == 0:
            for op in ops:
                start = i - len(op) + 1
                if start >= 0 and s[start:i+1] == op:
                    left = build_tree(s[:start])
                    right = build_tree(s[i+1:])
                    return (op, left, right)
        i -= 1
    if s.startswith("~"):
        return ('~', build_tree(s[1:]))
    if s.startswith("(") and s.endswith(")"):
        return build_tree(s[1:-1])
    raise ValueError("Formula not well formed: " + formula)


#CNF CONVERSION
def elim_imp(ast):
    if isinstance(ast, str):
        return ast
    op = ast[0]
    if op == '~':
        return ('~', elim_imp(ast[1]))
    if op == '->':
        A = elim_imp(ast[1]); B = elim_imp(ast[2])
        return ('|', ('~', A), B)
    if op == '<->':
        A = elim_imp(ast[1]); B = elim_imp(ast[2])
        # (A <-> B) => (A -> B) & (B -> A)
        return ('&', ('|', ('~', A), B), ('|', ('~', B), A))
    if op in ('|', '&'):
        return (op, elim_imp(ast[1]), elim_imp(ast[2]))
    return ast


def push_not(ast):
    if isinstance(ast, str):
        return ast
    op = ast[0]
    if op == '~':
        sub = ast[1]
        if isinstance(sub, str):
            return ('~', sub)
        if isinstance(sub, tuple):
            sop = sub[0]
            if sop == '~':
                return push_not(sub[1])
            if sop == '&':
                return ('|', push_not(('~', sub[1])), push_not(('~', sub[2])))
            if sop == '|':
                return ('&', push_not(('~', sub[1])), push_not(('~', sub[2])))
            return ('~', push_not(sub))
    if op in ('&', '|'):
        return (op, push_not(ast[1]), push_not(ast[2]))
    return ast


def literal_to_str(node):
    if isinstance(node, str):
        return node
    if isinstance(node, tuple) and node[0] == '~' and isinstance(node[1], str):
        return "~" + node[1]
    raise ValueError("Not a literal: " + repr(node))


def cnf_clauses_from_nnf(ast):
    # returns list of clauses (as sets of literal strings)
    if isinstance(ast, str) or (isinstance(ast, tuple) and ast[0] == '~' and isinstance(ast[1], str)):
        return [{literal_to_str(ast)}]
    if isinstance(ast, tuple):
        op = ast[0]
        if op == '&':
            return cnf_clauses_from_nnf(ast[1]) + cnf_clauses_from_nnf(ast[2])
        if op == '|':
            left = cnf_clauses_from_nnf(ast[1])
            right = cnf_clauses_from_nnf(ast[2])
            res = []
            for a in left:
                for b in right:
                    res.append(set(a).union(b))
            return res
    raise ValueError("Unexpected NNF node")


def cnf_convert(ast):
    step1 = elim_imp(ast)
    step2 = push_not(step1)
    clause_sets = cnf_clauses_from_nnf(step2)
    return {frozenset(c) for c in clause_sets}


#SIMPLIFY HELPERS
def is_tautology(cl):
    for lit in cl:
        comp = lit[1:] if lit.startswith("~") else "~" + lit
        if comp in cl:
            return True
    return False


def simplify_clauses(clauses):
    non_taut = {c for c in clauses if not is_tautology(c)}
    reduced = set(non_taut)
    # remove subsumed clauses
    for c1 in non_taut:
        for c2 in non_taut:
            if c1 != c2 and c1.issubset(c2):
                if c2 in reduced:
                    reduced.discard(c2)
    return reduced


def simplify_active_sets(active_clauses):
    # active-only simplification (tautology removal + subsumption)
    non_taut = {c for c in active_clauses if not is_tautology(c)}
    reduced = set(non_taut)
    for c1 in non_taut:
        for c2 in non_taut:
            if c1 != c2 and c1.issubset(c2):
                if c2 in reduced:
                    reduced.discard(c2)
    return reduced


#RESOLUTION HELPERS
def resolve_pair(c1, c2):
    res = set()
    for lit in c1:
        comp = lit[1:] if lit.startswith("~") else "~" + lit
        if comp in c2:
            new = (set(c1) - {lit}) | (set(c2) - {comp})
            res.add(frozenset(new))
    return res


def clause_to_string(cl):
    if not cl:
        return "NIL"
    lits = sorted(cl, key=lambda x: (x.lstrip('~'), x.startswith('~')))
    return " v ".join(lits)


def print_assignment_style(records,
                           usable_end, sos_end) -> None:
    for i in range(1, usable_end):
        cl, _ = records[i]
        print(f"{i}. {clause_to_string(cl)}")
    print("-" * 20)
    for i in range(usable_end, sos_end):
        cl, _ = records[i]
        print(f"{i}. {clause_to_string(cl)}")
    print("-" * 24)
    for i in sorted(records.keys()):
        cl, parents = records[i]
        if parents is None:
            continue
        print(f"{i}. {clause_to_string(cl)} ({parents[0]}, {parents[1]})")


#PL-resolution with SOS
def pl_resolution(premises, goal,
                  strategy= 0,
                  max_steps= 200000, max_clauses=200000):
    # Convert premises to CNF clauses
    usable_clauses: Set[Clause] = set()
    for f in premises:
        usable_clauses |= cnf_convert(build_tree(f))
    usable_clauses = simplify_clauses(usable_clauses)

    # Negated goal (S.O.S)
    neg_ast = ('~', build_tree(goal))
    sos_clauses: Set[Clause] = cnf_convert(neg_ast)
    sos_clauses = simplify_clauses(sos_clauses)

    clause_idx: Dict[Clause, int] = {}
    records: Dict[int, Tuple[Clause, Optional[Tuple[int, int]]]] = {}
    next_idx = 1

    # register usable clauses
    for c in sorted(usable_clauses, key=lambda c: (len(c), sorted(c))):
        clause_idx[c] = next_idx
        records[next_idx] = (c, None)
        next_idx += 1
    usable_end = next_idx

    # register sos clauses
    for c in sorted(sos_clauses, key=lambda c: (len(c), sorted(c))):
        if c not in clause_idx:
            clause_idx[c] = next_idx
            records[next_idx] = (c, None)
            next_idx += 1
    sos_end = next_idx

    usable_set = {c for c in clause_idx if clause_idx[c] < usable_end}
    sos_set = {c for c in clause_idx if usable_end <= clause_idx[c] < sos_end}
    for c in sos_clauses:
        if c in clause_idx and clause_idx[c] < usable_end:
            sos_set.add(c)

    # initial active simplification if strategy == 1
    if strategy == 1:
        usable_set = simplify_active_sets(usable_set)
        sos_set = simplify_active_sets(sos_set)

    sos_queue = deque(sorted(sos_set, key=lambda c: (len(c), sorted(c))))
    resolved_pairs: Set[FrozenSet[int]] = set()

    steps = 0
    max_seen = len(clause_idx)

    def add_new_clause(new_c, parents):
        nonlocal next_idx, max_seen
        if is_tautology(new_c):
            return None
        if new_c in clause_idx:
            return None
        if new_c in usable_set or new_c in sos_set:
            return None
        clause_idx[new_c] = next_idx
        records[next_idx] = (new_c, parents)
        sos_set.add(new_c)
        sos_queue.append(new_c)
        idx_assigned = next_idx
        next_idx += 1
        max_seen = max(max_seen, len(clause_idx))
        return idx_assigned

    while sos_queue:
        c = sos_queue.popleft()
        if c not in sos_set:
            continue
        targets = list(usable_set | sos_set)
        for d in targets:
            if c == d:
                continue
            i = clause_idx.get(c)
            j = clause_idx.get(d)
            if i is None or j is None:
                continue
            if frozenset({i, j}) in resolved_pairs:
                continue
            resolved_pairs.add(frozenset({i, j}))
            for r in resolve_pair(c, d):
                steps += 1
                if not r:
                    # empty clause found -> proven
                    records[next_idx] = (frozenset(), (i, j))
                    clause_idx[frozenset()] = next_idx
                    return True, steps, max_seen, records, usable_end, sos_end
                add_new_clause(r, (i, j))
                # active simplification each step if strategy==1
                if strategy == 1:
                    usable_set = simplify_active_sets(usable_set)
                    sos_set = simplify_active_sets(sos_set)
    return False, steps, max_seen, records, usable_end, sos_end


#Input parsing (from a string)
def read_input_from_string(s):
    raw = s
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip() != ""]
    if not lines:
        raise ValueError("Empty input. Expect premises, goal and optional strategy.")
    leading_strategy = None
    trailing_strategy = None
    if lines[0] in ("0", "1"):
        leading_strategy = int(lines[0])
    if lines[-1] in ("0", "1"):
        trailing_strategy = int(lines[-1])

    if trailing_strategy is not None:
        strategy = trailing_strategy
        body = lines[:-1]
    elif leading_strategy is not None:
        strategy = leading_strategy
        body = lines[1:]
    else:
        strategy = 0
        body = lines[:]

    if not body:
        raise ValueError("No formulas found after removing strategy flags. Need premises and goal.")
    goal = body[-1]
    premises = body[:-1]
    return premises, goal, strategy


def solve_from_string(input_str):
    """
    Run the solver on an input string (same format as SAMPLE_INPUT).
    Prints the solver output and returns the resolution tuple:
    (proven: bool, steps: int, max_seen: int, records: dict, usable_end: int, sos_end: int)
    """
    premises, goal, strategy = read_input_from_string(input_str)
    proven, steps, max_seen, records, usable_end, sos_end = pl_resolution(premises, goal, strategy=strategy)
    print("Proven" if proven else "Not proven")
    print("\nNumber of steps:", steps)
    print("Maximum number of clauses:", max_seen)
    print()
    print_assignment_style(records, usable_end, sos_end)
    return proven, steps, max_seen, records, usable_end, sos_end



SAMPLE_INPUT = """
1
((~P & Q) <-> (R|S)) | (~P-> S)
((~S&R)->(Q&P))|((P&R)|Q)
"""
print("Running embedded SAMPLE_INPUT:\n" + SAMPLE_INPUT)
solve_from_string(SAMPLE_INPUT)
