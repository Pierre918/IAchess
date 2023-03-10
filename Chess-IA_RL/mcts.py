# Importation de bibliothèques mathématiques
from math import log, inf, sqrt
import random
import chess
import chess.engine

# Définition de la classe Node
class Node:
    def __init__(self, state, parent=None):
        # État actuel du noeud
        self.state = state
        # Parent du noeud
        self.parent = parent
        # Liste des enfants du noeud
        self.children = []
        # Nombre de victoires du noeud
        self.wins = 0
        # Nombre de visites du noeud
        self.visits = 0
        
    # Ajout d'un enfant à un noeud
    def add_child(self, child_state):
        child = Node(child_state, self)
        self.children.append(child)
        return child
        
    # Mise à jour du nombre de victoires et de visites du noeud
    def update(self, reward):
        self.visits += 1
        self.wins += reward


def random_board(max_depth=100) :
    #créé un plateau avec des pièces positionées aléatoirement
    board = chess.Board()
    depth = random.randrange(0, max_depth)
    
    for _ in range(depth):
        all_moves = list(board.legal_moves)
        random_move = random.choice(all_moves)
        board.push(random_move)
        if board.is_game_over():
            break
    return board


# Calcul de la valeur UCB (à faire)
def ucb(node, c_param=sqrt(2)):
    if node.visits==0:
        return inf
    return node.wins / (node.visits) + c_param * sqrt(2 * log(node.parent.visits) / node.visits)
    

# Évaluation de l'état de jeu
def evaluate(board):
    if board.is_checkmate():
        if board.turn:
            return -1
        else:
            return 1
    elif board.is_stalemate():
        return 0
    elif board.is_insufficient_material():
        return 0
    elif board.is_seventyfive_moves():
        return 0
    elif board.is_fivefold_repetition():
        return 0
    else:
        return None


# Sélection d'un noeud fils avec la plus grande valeur UCB
def select_node(node):
        max_score = -inf
        best_child = None
        for child in node.children:
            score = ucb(child)
            if score > max_score:
                max_score = score
                best_child = child
        return best_child

# Expansion d'un noeud avec un mouvement aléatoire
def expand_node(node, state):
    possible_moves = list(state.legal_moves)
    random_move = random.choice(possible_moves)
    new_state = state.copy()
    new_state.push(random_move)
    return node.add_child(new_state)

# Simulation d'un jeu jusqu'à la fin
def simulate(state):
    while not state.is_game_over():
        state.push(random.choice(list(state.legal_moves))) # Avec des mouvements aléatoires

    return evaluate(state)

def backpropagate(node, reward):
    while node is not None:
        node.update(reward)
        node = node.parent
        


