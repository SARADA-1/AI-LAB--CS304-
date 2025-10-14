import math
import time
import pandas as pd

PLAYER_HUMAN = 'O'
PLAYER_AI = 'X'


minimax_nodes_evaluated = 0
alphabeta_nodes_evaluated = 0

def print_board(board):
    print("\n")
    for i in range(3):
        print(f" {board[i*3]} | {board[i*3+1]} | {board[i*3+2]} ")
        if i < 2:
            print("---|---|---")
    print("\n")

def get_available_moves(board):
    return [i for i, spot in enumerate(board) if spot == ' ']

def is_winner(board, player):
    # Check rows
    for i in range(0, 9, 3):
        if all(board[j] == player for j in range(i, i + 3)):
            return True
    # Check columns
    for i in range(3):
        if all(board[j] == player for j in range(i, 9, 3)):
            return True
    # Check diagonals
    if all(board[i] == player for i in [0, 4, 8]):
        return True
    if all(board[i] == player for i in [2, 4, 6]):
        return True
    return False

def is_board_full(board):
    return ' ' not in board

def evaluate(board):
    if is_winner(board, PLAYER_AI):
        return 1
    elif is_winner(board, PLAYER_HUMAN):
        return -1
    else:
        return 0


def minimax(board, depth, is_maximizing):
    global minimax_nodes_evaluated
    minimax_nodes_evaluated += 1

    score = evaluate(board)

    if score == 1 or score == -1 or is_board_full(board):
        return score

    if is_maximizing:
        best_score = -math.inf
        for move in get_available_moves(board):
            board[move] = PLAYER_AI
            best_score = max(best_score, minimax(board, depth + 1, False))
            board[move] = ' ' 
        return best_score
    else: 
        best_score = math.inf
        for move in get_available_moves(board):
            board[move] = PLAYER_HUMAN
            best_score = min(best_score, minimax(board, depth + 1, True))
            board[move] = ' ' 
        return best_score

def find_best_move_minimax(board):
    best_score = -math.inf
    best_move = -1
    for move in get_available_moves(board):
        board[move] = PLAYER_AI
        move_score = minimax(board, 0, False)
        board[move] = ' ' 
        if move_score > best_score:
            best_score = move_score
            best_move = move
    return best_move


def minimax_alpha_beta(board, depth, alpha, beta, is_maximizing):
    global alphabeta_nodes_evaluated
    alphabeta_nodes_evaluated += 1

    score = evaluate(board)

    if score == 1 or score == -1 or is_board_full(board):
        return score

    if is_maximizing:
        best_score = -math.inf
        for move in get_available_moves(board):
            board[move] = PLAYER_AI
            best_score = max(best_score, minimax_alpha_beta(board, depth + 1, alpha, beta, False))
            board[move] = ' '
            alpha = max(alpha, best_score)
            if beta <= alpha:
                break 
        return best_score
    else:
        best_score = math.inf
        for move in get_available_moves(board):
            board[move] = PLAYER_HUMAN
            best_score = min(best_score, minimax_alpha_beta(board, depth + 1, alpha, beta, True))
            board[move] = ' '
            beta = min(beta, best_score)
            if beta <= alpha:
                break 
        return best_score

def find_best_move_alpha_beta(board):
    best_score = -math.inf
    best_move = -1
    for move in get_available_moves(board):
        board[move] = PLAYER_AI
        move_score = minimax_alpha_beta(board, 0, -math.inf, math.inf, False)
        board[move] = ' '
        if move_score > best_score:
            best_score = move_score
            best_move = move
    return best_move

results = []
def play_game(choice):
    
    
    board = [' '] * 9
    current_player = PLAYER_AI
    
    total_start_time = time.perf_counter()
    ai_total_time = 0

    while True:
        print_board(board)
        if current_player == PLAYER_AI:
            print("Computer's turn (X)...")
            ai_start_time = time.perf_counter()
            if choice == 1:
                move = find_best_move_minimax(board)
            else:
                move = find_best_move_alpha_beta(board)
            ai_end_time = time.perf_counter()
            ai_total_time += (ai_end_time - ai_start_time)
            
            if move != -1:
                board[move] = PLAYER_AI
            
            if is_winner(board, PLAYER_AI):
                print_board(board)
                print("Computer (X) wins!")
                break
            current_player = PLAYER_HUMAN
        else: 
            try:
                move = int(input("Your turn (O). Enter move (0-8): "))
                if 0 <= move <= 8 and board[move] == ' ':
                    board[move] = PLAYER_HUMAN
                    if is_winner(board, PLAYER_HUMAN):
                        print_board(board)
                        print("You (O) win!")
                        break
                    current_player = PLAYER_AI
                else:
                    print("Invalid move. Try again.")
            except ValueError:
                print("Invalid input. Please enter a number between 0 and 8.")

        if is_board_full(board):
            print_board(board)
            print("It's a draw! Result: -1")
            break
            
    total_end_time = time.perf_counter()
    
    print("\n--- Game Over ---")
    print(f"Total game time: {total_end_time - total_start_time:.6f} seconds")
    print(f"Total AI thinking time: {ai_total_time:.6f} seconds")
    if choice == 1:
        print(f"Nodes evaluated by Minimax: {minimax_nodes_evaluated}")
        results.append({"Algorithm": "MINMAX",
                        "AI THINKING TIME": round((total_end_time-total_start_time),6),
                        "Nodes Evaluated": minimax_nodes_evaluated})
    else:
        print(f"Nodes evaluated by Alpha-Beta Pruning: {alphabeta_nodes_evaluated}")
        results.append({"Algorithm": "ALPHA-BETA",
                        "AI THINKING TIME": round((total_end_time-total_start_time),6),
                        "Nodes Evaluated": alphabeta_nodes_evaluated})


print("---MINMAX Algorithm---")
play_game(1)
print("---ALPHA-BETA Algorithm---")
play_game(2)

df = pd.DataFrame(results)

print(df)


