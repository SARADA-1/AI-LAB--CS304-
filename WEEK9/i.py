import copy


def is_variable(expr):
    """A variable is a lowercase string."""
    return isinstance(expr, str) and expr.islower()

def is_term(expr):
    """A term or fact is a tuple."""
    return isinstance(expr, tuple)

# --- 2. Substitution & Unification ---

def apply_substitution(expr, theta):
    """Recursively applies a substitution 'theta' to an expression."""
    if is_variable(expr) and expr in theta:
        # Recursively apply in case of chained substitutions {x: 'y', y: 'John'}
        return apply_substitution(theta[expr], theta)
    elif is_term(expr):
        # Apply to all parts of the tuple
        return tuple(apply_substitution(arg, theta) for arg in expr)
    else:
        # It's a variable not in theta, or a constant (like 'John')
        return expr

def unify(x, y, theta):
    """
    Attempts to unify expressions x and y with substitution theta.
    Returns a new substitution on success, or None on failure.
    """
    theta = theta.copy() # Work on a copy

    if theta is None:
        return None
    elif x == y:
        return theta
    elif is_variable(x):
        return unify_variable(x, y, theta)
    elif is_variable(y):
        return unify_variable(y, x, theta)
    elif is_term(x) and is_term(y):
        # Unify operator and number of arguments
        if len(x) != len(y):
            return None
        # Recursively unify all arguments
        for i in range(len(x)):
            theta = unify(x[i], y[i], theta)
            if theta is None:
                return None
        return theta
    else:
        # e.g., two different constants or a term and a constant
        return None

def unify_variable(var, x, theta):
    """Handles unification when one expression is a variable."""
    if var in theta:
        # 'var' is already bound, unify its value with 'x'
        return unify(theta[var], x, theta)
    elif is_variable(x) and x in theta:
        # 'x' is a variable and is bound, unify 'var' with its value
        return unify(var, theta[x], theta)
    else:
        # Omitting "occurs check" for simplicity
        # Bind the variable
        new_binding = {var: x}
        
        # Apply the new binding to all existing values in theta
        for k, v in theta.items():
            theta[k] = apply_substitution(v, new_binding)
        
        # Add the new binding itself
        theta[var] = x
        return theta

# --- 3. Forward Chaining Step ---

# We need a way to make variables unique for each rule application
# This is a simple global counter.
VAR_COUNT = 0
def standardize_variables(expr):
    """Replaces 'x', 'y', 'z' with unique 'v_1', 'v_2', ..."""
    global VAR_COUNT
    mapping = {}
    
    def _standardize(item):
        global VAR_COUNT
        if is_variable(item):
            if item not in mapping:
                VAR_COUNT += 1
                mapping[item] = f'v_{VAR_COUNT}'
            return mapping[item]
        elif is_term(item):
            return tuple(_standardize(arg) for arg in item)
        else:
            return item
            
    return _standardize(expr)

def canonicalize(fact):
    """Renames variables in a fact back to a standard 'x', 'y' form."""
    mapping = {}
    std_vars = ['x', 'y', 'z', 'w']
    var_index = 0
    
    def _canonicalize(item):
        nonlocal var_index
        if is_variable(item):
            if item not in mapping:
                mapping[item] = std_vars[var_index]
                var_index += 1
            return mapping[item]
        elif is_term(item):
            return tuple(_canonicalize(arg) for arg in item)
        else:
            return item
            
    return _canonicalize(fact)

def forward_chain_step(kb_facts, rule):
    """
    Runs one step of forward chaining and returns any new facts found.
    This logic is specific to the 2-antecedent rule in the problem.
    """
    new_facts_found = set()
    
    # Get the rule components
    (ant1, ant2), consequent = rule

    # Try to match the rule against every *pair* of facts in the KB
    for fact1 in kb_facts:
        for fact2 in kb_facts:
            
            # --- Standardization ---
            # We must use unique variables for each attempt
            std_ant1 = standardize_variables(ant1)
            std_ant2 = standardize_variables(ant2)
            std_consequent = standardize_variables(consequent)
            std_fact1 = standardize_variables(fact1) # Standardize facts too
            std_fact2 = standardize_variables(fact2) # to avoid clashes
            
            # 1. Try to unify the first antecedent with fact1
            theta1 = unify(std_ant1, std_fact1, {})
            
            if theta1 is not None:
                # 2. If success, apply substitution to the second antecedent
                ant2_substituted = apply_substitution(std_ant2, theta1)
                
                # 3. Try to unify the *substituted* second antecedent with fact2
                theta2 = unify(ant2_substituted, std_fact2, {})

                if theta2 is not None:
                    # 4. Compose the substitutions
                    # (Apply theta2 to values of theta1, then add theta2)
                    final_theta = theta2.copy()
                    for k, v in theta1.items():
                        final_theta[k] = apply_substitution(v, theta2)
                    
                    # 5. Apply the final substitution to the rule's consequent
                    new_fact = apply_substitution(std_consequent, final_theta)
                    
                    # 6. Canonicalize to a standard variable name (e.g., 'x')
                    new_fact_canonical = canonicalize(new_fact)
                    
                    # 7. Add to our set of new facts (if not already in KB)
                    if new_fact_canonical not in kb_facts:
                        new_facts_found.add(new_fact_canonical)
                            
    return new_facts_found

# --- 4. Main Execution ---

if __name__ == "__main__":
    
    # --- Create the initial Knowledge Base ---
    # F1: Ancestor(Mother(x), x)
    f1 = ('Ancestor', ('Mother', 'x'), 'x')
    kb_facts = {f1}
    
    # R1: Ancestor(x, y) ∧ Ancestor(y, z) ⇒ Ancestor(x, z)
    rule = (
        (('Ancestor', 'x', 'y'), ('Ancestor', 'y', 'z')),  # Antecedents
        ('Ancestor', 'x', 'z')                             # Consequent
    )
    
    # --- Show the KB *before* ---
    print("=" * 30)
    print("Knowledge Base BEFORE Inference:")
    print("=" * 30)
    for fact in kb_facts:
        print(f"  {fact}")
    
    # --- Run one step of Forward Chaining ---
    print("\nRunning forward chaining step...")
    new_inferences = forward_chain_step(kb_facts, rule)
    
    if not new_inferences:
        print("No new inferences found.")
    else:
        print("\nNew Inferences Found:")
        for fact in new_inferences:
            print(f"  > {fact}")
            kb_facts.add(fact) # Add new facts to the KB
    
    # --- Show the KB *after* ---
    print("\n" + "=" * 30)
    print("Knowledge Base AFTER Inference:")
    print("=" * 30)
    for fact in kb_facts:
        print(f"  {fact}")

    # --- NEW: Test Query from Exercise 9.19 (a.i) ---
    print("\n" + "=" * 30)
    print("Testing Query from Image:")
    print("=" * 30)
    
    # Query: Ancestor(Mother(y), John)
    # Note: 'John' is a constant, so we use an uppercase string.
    query = ('Ancestor', ('Mother', 'y'), 'John')
    
    print(f"Query: {query}\n")
    
    found_answer = False
    for fact in kb_facts:
        print(f"  Trying to unify with fact: {fact}")
        
        # We must standardize the query variables for each attempt
        std_query = standardize_variables(query)
        std_fact = standardize_variables(fact)
        
        substitution = unify(std_query, std_fact, {})
        
        if substitution is not None:
            print(f"    SUCCESS: Unification found.")
            # We can print a cleaner substitution, but this shows the internal state
            print(f"    Substitution: {substitution}")
            found_answer = True
            break # Stop after first match
        else:
            print("    FAILURE: No unification.")
            
    if not found_answer:
        print("\nNo answer found for query in the current KB.")

