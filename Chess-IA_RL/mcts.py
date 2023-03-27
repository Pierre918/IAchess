# Importation de bibliothèques mathématiques
from math import log, inf, sqrt
import random
import chess
import chess.engine


#Stockfish
engine = chess.engine.SimpleEngine.popen_uci(r"stockfish-windows-2022-x86-64-avx2.exe")


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


# Calcul de la valeur UCB
def ucb(node, c_param=sqrt(2)):
    if node.visits==0:
        return inf
    return node.wins / (node.visits) + c_param * sqrt(log(node.parent.visits) / node.visits)
    

#Calcul de la valeur PUCT (à faire)    
    
    
    
    
# Évaluation de l'état de jeu
def evaluate(board):
    #piece_values = {'P': 1,'N': 3,'B': 3,'R': 5,'Q': 9,'K': 100,'p': 1,'n': 3,'b': 3,'r': 5,'q': 9,'k': 100}
    if board.is_checkmate():
        if board.turn==player:
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
    for move in state.legal_moves:
        new_state = state.copy()
        new_state.push(move)
        if new_state not in [child.state for child in node.children]:
            node.add_child(new_state)
    random_move = random.choice(node.children)
    return random_move

# Simulation d'un jeu jusqu'à la fin
def simulate(state):
    while not state.is_game_over():
        state.push(random.choice(list(state.legal_moves))) # Avec des mouvements aléatoires

    return evaluate(state)

#Mise à jour de la valeur de tous les Noeuds
def backpropagate(node, reward):
    while node is not None:
        node.update(reward)
        node = node.parent
        


def mcts(root, state, itermax):
    """Monte Carlo Tree Search algorithme"""
    for i in range(itermax):
        node = root
        current_state = state.copy()
            
        while node.children:
            node = select_node(node)
            current_state.push(node.state.peek())
                
        if not current_state.is_game_over():
            node = expand_node(node, current_state)
    
            reward = simulate(current_state)
            backpropagate(node, reward)
        else:
            reward = evaluate(current_state)
            backpropagate(node, reward)

   
     return max(root.children, key=lambda x: x.wins / x.visits).state.peek()


"""
if __name__ == "__main__":
    fen ="r2q2nr/pppk3p/5ppB/2P5/2BN4/2N4P/PPP1QP1P/R3K2R w KQ - 4 14"
    board = chess.Board(fen)
    #board = random_board()
    root = Node(board)
    best_move = mcts(root, board, 1000)
    #print(board.fen())
    print(best_move)
    print(board)"""

    
def move_player():
    global player
    if board.turn: 
        player = True
    else: 
        player = False
    try :
        player_move = input("Move: ")
        board.push_san(str(player_move))
    except:
        print("Invalid move")
        move_player()

board=chess.Board()

while not board.is_game_over():
    root = Node(board) 
    print(board.fen())
    print(board)
    move_player()
    if board.is_game_over():
        print("You win")
        break
    best_move = mcts(root, board, 100)
    print(best_move)
    board.push_san(str(best_move))
