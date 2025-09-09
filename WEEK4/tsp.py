import random

def generate_distance_matrix(n, max_dist=10):
    dist = [[0]*n for _ in range(n)]
    for i in range(n):
        for j in range(i+1, n):
            d = random.randint(1, max_dist)
            dist[i][j] = dist[j][i] = d
    return dist

def tour_cost(tour, dist):
    cost = 0
    for i in range(len(tour)):
        cost += dist[tour[i]][tour[(i + 1) % len(tour)]]
    return cost

def get_neighbors(tour):
    neighbors = []
    for i in range(1, len(tour)):
        for j in range(i+1, len(tour)):
            neighbor = tour[:]
            neighbor[i], neighbor[j] = neighbor[j], neighbor[i]
            neighbors.append(neighbor)
    return neighbors

def hill_climb(tour, dist):
    current = tour
    current_cost = tour_cost(current, dist)

    while True:
        neighbors = get_neighbors(current)
        best_neighbor = min(neighbors, key=lambda t: tour_cost(t, dist))
        best_cost = tour_cost(best_neighbor, dist)

        if best_cost < current_cost:
            current, current_cost = best_neighbor, best_cost
        else:
            break
    return current, current_cost

def random_restart_hill_climb(dist, num_restarts=50):
    n = len(dist)
    best_overall, best_cost = None, float("inf")

    for _ in range(num_restarts):
        random_tour = list(range(n))
        random.shuffle(random_tour)
        tour, cost = hill_climb(random_tour, dist)
        if cost < best_cost:
            best_overall, best_cost = tour, cost
    return best_overall, best_cost


n = 6  
dist_matrix = generate_distance_matrix(n, max_dist=20)

best_tour, best_cost = random_restart_hill_climb(dist_matrix, num_restarts=100)

print("Distance Matrix:")
for row in dist_matrix:
    print(row)

print("\nBest tour found:", best_tour + [best_tour[0]])
print("Tour cost:", best_cost)