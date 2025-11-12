import random
import time

class BayesNetSampler:
    """
    A class to perform various types of sampling on a given
    Bayesian Network.
    
    Assumes:
    - All variables are Boolean (True/False).
    - The network is provided in a specific dictionary format.
    - The 'nodes_topo_order' list is a valid topological sort
      of the network graph.
    """

    def __init__(self, network_definition, nodes_topo_order):
        """
        Initializes the sampler.
        
        Args:
            network_definition (dict): The Bayesian network structure.
                Format: {
                    'NodeName': {
                        'parents': ['Parent1', 'Parent2'],
                        'cpt': {
                            # (Parent1_val, Parent2_val): P(NodeName=True | Parents)
                            (True, True): 0.9,
                            (True, False): 0.5,
                            (False, True): 0.3,
                            (False, False): 0.1
                        }
                    },
                    'RootNode': {
                        'parents': [],
                        'cpt': {
                            (): 0.2  # P(RootNode=True)
                        }
                    }
                }
            nodes_topo_order (list): A list of node names (str) in
                                     topological order.
        """
        self.network = network_definition
        self.nodes = nodes_topo_order
        
        # Pre-compute children for each node to speed up Gibbs sampling
        self.children = {node: [] for node in self.nodes}
        for node in self.nodes:
            for parent in self.network[node]['parents']:
                self.children[parent].append(node)
        
        print("Bayesian Network Sampler initialized.")
        print(f"Topological Order: {' -> '.join(self.nodes)}")
        print("-" * 30)

    # --- Internal Helper Methods ---

    def _sample_from_prob(self, prob_true):
        """Samples True/False given a probability of True."""
        return random.random() < prob_true

    def _get_prob_true(self, node, parent_values_tuple):
        """Gets P(node=True | parents) from the CPT."""
        return self.network[node]['cpt'][parent_values_tuple]

    def _generate_prior_sample(self):
        """
        Generates a single, complete sample from the network's
        prior distribution.
        
        Returns:
            dict: A sample {node: value, ...}
        """
        sample = {}
        for node in self.nodes:
            parents = self.network[node]['parents']
            # Get parent values from the sample we are building
            parent_values = tuple(sample[p] for p in parents)
            
            # Get P(Node=True | parents)
            prob_true = self._get_prob_true(node, parent_values)
            
            # Sample the value for the current node
            sample[node] = self._sample_from_prob(prob_true)
            
        return sample

    def _is_consistent(self, sample, evidence):
        """Checks if a sample is consistent with the given evidence."""
        for var, val in evidence.items():
            if sample[var] != val:
                return False
        return True

    def _weighted_sample(self, evidence):
        """
        Generates a single sample using likelihood weighting.
        Fixes evidence variables and weights the sample.
        
        Returns:
            tuple (dict, float): (sample, weight)
        """
        sample = {}
        weight = 1.0
        
        for node in self.nodes:
            parents = self.network[node]['parents']
            parent_values = tuple(sample[p] for p in parents)
            prob_true = self._get_prob_true(node, parent_values)

            if node in evidence:
                # This is an evidence variable
                val = evidence[node]
                sample[node] = val
                
                # Update the weight
                if val == True:
                    weight *= prob_true
                else:
                    weight *= (1.0 - prob_true)
            else:
                # This is not an evidence variable, sample it
                sample[node] = self._sample_from_prob(prob_true)
                
        return sample, weight

    def _prob_given_markov_blanket(self, var, current_state):
        """
        Calculates P(var=True | MarkovBlanket(var))
        
        P(X | MB(X)) ∝ P(X | Parents(X)) * Π_{Y in Children(X)} P(Y | Parents(Y))
        """
        
        # 1. P(var=True | Parents(var))
        parents = self.network[var]['parents']
        parent_values = tuple(current_state[p] for p in parents)
        prob_var_true_given_parents = self._get_prob_true(var, parent_values)
        
        # P(var=False | Parents(var))
        prob_var_false_given_parents = 1.0 - prob_var_true_given_parents

        # 2. Π_{Y in Children(var)} P(Y | Parents(Y))
        prob_children_given_var_true = 1.0
        prob_children_given_var_false = 1.0
        
        for child in self.children[var]:
            child_parents = self.network[child]['parents']
            
            # --- Calculate P(child | parents) when var=True ---
            parent_values_true_state = []
            for p in child_parents:
                if p == var:
                    parent_values_true_state.append(True)
                else:
                    parent_values_true_state.append(current_state[p])
            
            prob_child_true_T = self._get_prob_true(child, tuple(parent_values_true_state))
            
            # P(child=current_state[child] | parents with var=True)
            if current_state[child] == True:
                prob_children_given_var_true *= prob_child_true_T
            else:
                prob_children_given_var_true *= (1.0 - prob_child_true_T)

            # --- Calculate P(child | parents) when var=False ---
            parent_values_false_state = []
            for p in child_parents:
                if p == var:
                    parent_values_false_state.append(False)
                else:
                    parent_values_false_state.append(current_state[p])

            prob_child_true_F = self._get_prob_true(child, tuple(parent_values_false_state))

            # P(child=current_state[child] | parents with var=False)
            if current_state[child] == True:
                prob_children_given_var_false *= prob_child_true_F
            else:
                prob_children_given_var_false *= (1.0 - prob_child_true_F)

        # 3. Calculate unnormalized probabilities
        unnorm_prob_true = prob_var_true_given_parents * prob_children_given_var_true
        unnorm_prob_false = prob_var_false_given_parents * prob_children_given_var_false

        # 4. Normalize and return P(var=True)
        # Add epsilon to prevent division by zero if both are 0
        norm_factor = unnorm_prob_true + unnorm_prob_false + 1e-9
        
        return unnorm_prob_true / norm_factor

    # --- Public Sampling Methods ---

    def prior_sampling(self, query_var, num_samples):
        """
        Estimates P(query_var=True) using prior sampling.
        This method cannot handle evidence.
        """
        print(f"Running Prior Sampling for P({query_var}=T)...")
        start_time = time.time()
        
        true_count = 0
        for _ in range(num_samples):
            sample = self._generate_prior_sample()
            if sample[query_var]:
                true_count += 1
                
        prob = true_count / num_samples
        
        end_time = time.time()
        print(f"  Result: {prob:.4f}")
        print(f"  Time: {end_time - start_time:.4f}s")
        return {'prob': prob, 'total_samples': num_samples}

    def rejection_sampling(self, query_var, evidence, num_samples_to_keep):
        """
        Estimates P(query_var=True | evidence) using rejection sampling.
        
        Args:
            num_samples_to_keep (int): The number of *valid* (non-rejected)
                                       samples to collect.
        """
        print(f"Running Rejection Sampling for P({query_var}=T | {evidence})...")
        start_time = time.time()

        true_count = 0
        valid_samples = 0
        total_samples_drawn = 0
        
        while valid_samples < num_samples_to_keep:
            total_samples_drawn += 1
            sample = self._generate_prior_sample()
            
            if self._is_consistent(sample, evidence):
                valid_samples += 1
                if sample[query_var]:
                    true_count += 1
            
            # Safety break to avoid infinite loops on P(evidence)=0
            if total_samples_drawn > num_samples_to_keep * 1000 and valid_samples == 0:
                print("  WARNING: Extremely rare evidence. Aborting.")
                break

        if valid_samples == 0:
            prob = 0.0
        else:
            prob = true_count / valid_samples
        
        rejection_rate = (total_samples_drawn - valid_samples) / total_samples_drawn if total_samples_drawn > 0 else 0
        
        end_time = time.time()
        print(f"  Result: {prob:.4f}")
        print(f"  Total samples drawn: {total_samples_drawn} (Kept: {valid_samples})")
        print(f"  Rejection Rate: {rejection_rate:.2%}")
        print(f"  Time: {end_time - start_time:.4f}s")
        return {'prob': prob, 'valid_samples': valid_samples, 'total_samples_drawn': total_samples_drawn, 'rejection_rate': rejection_rate}

    def likelihood_weighting(self, query_var, evidence, num_samples):
        """
        Estimates P(query_var=True | evidence) using likelihood weighting.
        """
        print(f"Running Likelihood Weighting for P({query_var}=T | {evidence})...")
        start_time = time.time()

        weighted_true_count = 0.0
        total_weight = 0.0
        
        for _ in range(num_samples):
            sample, weight = self._weighted_sample(evidence)
            total_weight += weight
            
            if sample[query_var]:
                weighted_true_count += weight
        
        if total_weight == 0:
            prob = 0.0
        else:
            prob = weighted_true_count / total_weight
            
        end_time = time.time()
        print(f"  Result: {prob:.4f}")
        print(f"  Total samples generated: {num_samples}")
        print(f"  Time: {end_time - start_time:.4f}s")
        return {'prob': prob, 'total_samples': num_samples}

    def gibbs_sampling(self, query_var, evidence, num_samples_to_collect, burn_in, skip):
        """
        Estimates P(query_var=True | evidence) using Gibbs sampling (MCMC).
        
        Args:
            num_samples_to_collect (int): Number of samples to collect
                                          after burn-in and skipping.
            burn_in (int): Number of initial samples to discard.
            skip (int): Collect one sample every 'skip' iterations.
        """
        print(f"Running Gibbs Sampling for P({query_var}=T | {evidence})...")
        start_time = time.time()

        # Get all variables that are not fixed by evidence
        non_evidence_vars = [node for node in self.nodes if node not in evidence]
        
        # 1. Initialize state
        current_state = {}
        for node in self.nodes:
            if node in evidence:
                current_state[node] = evidence[node]
            else:
                # Randomly initialize non-evidence vars
                current_state[node] = random.choice([True, False])
        
        true_count = 0
        samples_collected = 0
        total_iterations = burn_in + (num_samples_to_collect * skip)

        # 2. Run MCMC chain
        for i in range(total_iterations):
            # Iterate and resample each non-evidence variable
            for var_to_sample in non_evidence_vars:
                # Sample var given its Markov Blanket in the current state
                prob_true = self._prob_given_markov_blanket(var_to_sample, current_state)
                current_state[var_to_sample] = self._sample_from_prob(prob_true)
            
            # 3. Collect samples after burn-in
            if i >= burn_in and (i - burn_in) % skip == 0:
                samples_collected += 1
                if current_state[query_var]:
                    true_count += 1
        
        if samples_collected == 0:
            prob = 0.0
        else:
            prob = true_count / samples_collected
            
        end_time = time.time()
        print(f"  Result: {prob:.4f}")
        print(f"  Total iterations: {total_iterations} (Burn-in: {burn_in}, Skip: {skip})")
        print(f"  Samples collected: {samples_collected}")
        print(f"  Time: {end_time - start_time:.4f}s")
        return {'prob': prob, 'samples_collected': samples_collected, 'total_iterations': total_iterations, 'burn_in': burn_in, 'skip': skip}


# --- Main execution ---
if __name__ == "__main__":

    # Define the "Cloudy" -> "Sprinkler" / "Rain" -> "WetGrass" network
    # This is a classic simple Bayesian network.
    cloudy_network = {
        'Cloudy': {
            'parents': [],
            'cpt': {(): 0.5}  # P(Cloudy=T) = 0.5
        },
        'Sprinkler': {
            'parents': ['Cloudy'],
            'cpt': {
                (True,): 0.1,   # P(S=T | C=T)
                (False,): 0.5   # P(S=T | C=F)
            }
        },
        'Rain': {
            'parents': ['Cloudy'],
            'cpt': {
                (True,): 0.8,   # P(R=T | C=T)
                (False,): 0.2   # P(R=T | C=F)
            }
        },
        'WetGrass': {
            'parents': ['Sprinkler', 'Rain'],
            'cpt': {
                (True, True): 0.99, # P(W=T | S=T, R=T)
                (True, False): 0.9, # P(W=T | S=T, R=F)
                (False, True): 0.9, # P(W=T | S=F, R=T)
                (False, False): 0.0 # P(W=T | S=F, R=F)
            }
        }
    }
    
    # The topological order MUST be provided
    topo_order = ['Cloudy', 'Sprinkler', 'Rain', 'WetGrass']

    # Initialize the sampler
    sampler = BayesNetSampler(cloudy_network, topo_order)
    
    # --- Define Queries ---
    
    # Query 1: Diagnostic reasoning (late evidence)
    # P(CloudT | WetGrass=True)
    # 'WetGrass' is "late" in the topological sort.
    # We expect this to be very inefficient for Rejection Sampling.
    query_1_var = 'Cloudy'
    query_1_evidence = {'WetGrass': True}
    
    # Query 2: Predictive reasoning (early evidence)
    # P(WetGrass | Cloudy=True)
    # 'Cloudy' is "early" in the topological sort.
    # We expect this to be efficient for Rejection Sampling.
    query_2_var = 'WetGrass'
    query_2_evidence = {'Cloudy': True}

    # Query 3: Marginal probability (no evidence)
    # P(WetGrass)
    query_3_var = 'WetGrass'
    query_3_evidence = {}

    # List to store all results for summary table
    all_results_log = []

    # --- Set Sampling Parameters ---
    N_SAMPLES_REJECTION = 20000  # Number of *valid* samples for Rejection
    N_SAMPLES_LIKELIHOOD = 100000 # Total samples for Likelihood
    N_SAMPLES_PRIOR = 100000      # Total samples for Prior
    
    # Gibbs parameters
    N_SAMPLES_GIBBS = 20000      # Samples to collect
    BURN_IN = 5000               # Iterations to discard
    SKIP = 5                     # Collect 1 sample every 5 iterations

    # --- Run Query 1: P(Cloudy | WetGrass=T) ---
    # (Late evidence)
    print("\n--- Query 1: P(Cloudy=T | {'WetGrass': True}) [Late Evidence] ---")
    query_1_log = {
        'query_name': "Query 1: P(Cloudy=T | {'WetGrass': True}) [Late Evidence]",
        'true_answer': '~0.3577',
        'results': []
    }
    # (Prior sampling cannot be used)
    res_rej1 = sampler.rejection_sampling(query_1_var, query_1_evidence, N_SAMPLES_REJECTION)
    query_1_log['results'].append({'method': 'Rejection Sampling', **res_rej1})
    
    res_lik1 = sampler.likelihood_weighting(query_1_var, query_1_evidence, N_SAMPLES_LIKELIHOOD)
    query_1_log['results'].append({'method': 'Likelihood Weighting', **res_lik1})

    res_gib1 = sampler.gibbs_sampling(query_1_var, query_1_evidence, N_SAMPLES_GIBBS, BURN_IN, SKIP)
    query_1_log['results'].append({'method': 'Gibbs Sampling', **res_gib1})
    
    all_results_log.append(query_1_log)
    # True answer is approx 0.3577

    # --- Run Query 2: P(WetGrass=T | Cloudy=T) ---
    # (Early evidence)
    print("\n--- Query 2: P(WetGrass=T | {'Cloudy': True}) [Early Evidence] ---")
    query_2_log = {
        'query_name': "Query 2: P(WetGrass=T | {'Cloudy': True}) [Early Evidence]",
        'true_answer': '~0.7576',
        'results': []
    }
    
    res_rej2 = sampler.rejection_sampling(query_2_var, query_2_evidence, N_SAMPLES_REJECTION)
    query_2_log['results'].append({'method': 'Rejection Sampling', **res_rej2})

    res_lik2 = sampler.likelihood_weighting(query_2_var, query_2_evidence, N_SAMPLES_LIKELIHOOD)
    query_2_log['results'].append({'method': 'Likelihood Weighting', **res_lik2})

    res_gib2 = sampler.gibbs_sampling(query_2_var, query_2_evidence, N_SAMPLES_GIBBS, BURN_IN, SKIP)
    query_2_log['results'].append({'method': 'Gibbs Sampling', **res_gib2})
    
    all_results_log.append(query_2_log)
    # True answer is 0.7576
    
    # --- Run Query 3: P(WetGrass=T) ---
    # (Marginal / No evidence)
    print(f"\n--- Query 3: P({query_3_var}=T) [Marginal] ---")
    query_3_log = {
        'query_name': f"Query 3: P({query_3_var}=T) [Marginal]",
        'true_answer': '~0.4588',
        'results': []
    }

    res_pri3 = sampler.prior_sampling(query_3_var, N_SAMPLES_PRIOR)
    query_3_log['results'].append({'method': 'Prior Sampling', **res_pri3})
    
    # We can also use the other methods with empty evidence
    res_rej3 = sampler.rejection_sampling(query_3_var, query_3_evidence, N_SAMPLES_REJECTION)
    query_3_log['results'].append({'method': 'Rejection Sampling', **res_rej3})
    
    res_lik3 = sampler.likelihood_weighting(query_3_var, query_3_evidence, N_SAMPLES_LIKELIHOOD)
    query_3_log['results'].append({'method': 'Likelihood Weighting', **res_lik3})
    
    res_gib3 = sampler.gibbs_sampling(query_3_var, query_3_evidence, N_SAMPLES_GIBBS, BURN_IN, SKIP)
    query_3_log['results'].append({'method': 'Gibbs Sampling', **res_gib3})
    
    all_results_log.append(query_3_log)
    # True answer is 0.4588

    # --- Print Summary Table ---
    
    def print_summary_tables(all_results):
        """
        Prints a final summary table of all query results
        in markdown format.
        """
        print("\n" + "="*70)
        print(" " * 20 + "FINAL SUMMARY OF SAMPLING RUNS")
        print("="*70 + "\n")
        
        for query in all_results:
            print(f"### {query['query_name']}")
            if query['true_answer']:
                print(f"**True Answer: {query['true_answer']}**\n")
            
            print("| Sampling Method      | Estimated Probability | Key Statistic |")
            print("| :--- | :--- | :--- |")
            
            for res in query['results']:
                prob = f"{res['prob']:.4f}"
                stat = ""
                if res['method'] == 'Prior Sampling':
                    stat = f"Total samples generated: {res['total_samples']}"
                elif res['method'] == 'Rejection Sampling':
                    stat = f"Total drawn: {res['total_samples_drawn']} (Kept: {res['valid_samples']}) / Rejection Rate: {res['rejection_rate']:.2%}"
                elif res['method'] == 'Likelihood Weighting':
                    stat = f"Total samples generated: {res['total_samples']}"
                elif res['method'] == 'Gibbs Sampling':
                    stat = f"Samples collected: {res['samples_collected']} (Total iterations: {res['total_iterations']})"
                
                print(f"| {res['method']:<20} | {prob:<21} | {stat} |")
            print("\n")

    print_summary_tables(all_results_log)