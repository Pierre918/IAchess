# Importation de bibliothèques mathématiques
from math import log, inf, sqrt
import random
import chess
import chess.engine
import matplotlib.pyplot as plt


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
    

#Calcul de la valeur PUCT   
def puct(node, c_param):
    total_visits = sum(child.visits for child in node.children)
    # Calcul du logarithme naturel du nombre total de visites
    if total_visits == 0:
        log_total_visits = 0
    else :
        log_total_visits = log(total_visits)
        
    best_score = -inf
    best_child = None

    for child in node.children:
        if child.visits == 0:
            # Si l'enfant n'a pas encore été visité
            exploitation_term = inf
            exploration_term = inf
        else: 
            # Calcul du terme d'exploitation et du terme d'exploration
            exploitation_term = child.wins / child.visits
            exploration_term = c_param * sqrt(log_total_visits / child.visits) * (1 / len(node.children))
        
        # Calcul du score pour chaque enfant
        score = exploitation_term + exploration_term
        
        # Mise à jour du meilleur score et de l'enfant correspondant
        if score > best_score:
            best_score = score
            best_child = child

    # Retourne l'enfant ayant le meilleur score
    return best_child  
    
    
    
    
# Évaluation de l'état de jeu
def evaluate(state):
    piece_values = {'P': 1,'N': 3,'B': 3,'R': 5,'Q': 9,'K': 100,'p': 1,'n': 3,'b': 3,'r': 5,'q': 9,'k': 100}
    if state.is_checkmate():
        if " "+player+" " in str(state.fen()):
            return 1
        else:
            return -1
    elif state.is_stalemate():
        return 0
    elif state.is_insufficient_material():
        return 0
    elif state.is_seventyfive_moves():
        return 0
    elif state.is_fivefold_repetition():
        return 0
    else:
        score = 0
        # Calcul du score en sommant les valeurs de chaque pièce
        for piece in state.piece_map().values():
            if piece.color == chess.WHITE:
                score += piece_values[str(piece)]
            else:
                score -= piece_values[str(piece)]

        # Si c'est au tour du joueur courant, retourne l'inverse du score divisé par 100
        if state.turn == player:
            return -score / 100.0
        # Sinon, retourne le score divisé par 100
        else:
            return score / 100.0


# Sélection d'un noeud fils avec la plus grande valeur UCB/PUCT
def select_node(node):
       """max_score = -inf
        best_child = None
        for child in node.children:
            score = ucb(child)
            if score > max_score:
                max_score = score
                best_child = child
        return best_child"""
        return puct(node, 5.0)

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
        #distance_checkmate = analyze_position(state) #Avec Stockfish
        #state.push_san(distance_checkmate[0]["pv"][0])
        state.push(random.choice(list(state.legal_moves))) # Avec des mouvements aléatoires

    return evaluate(state)

#Mise à jour de la valeur de tous les Noeuds
def backpropagate(node, reward):
    while node is not None:
        node.update(reward)
        node = node.parent
        

        
def analyze_position(board, num_moves_to_return=1, depth_limit=10, time_limit=0.1):
    search_limit = chess.engine.Limit(depth=depth_limit, time=time_limit)
    infos = engine.analyse(board, search_limit, multipv=num_moves_to_return)
    return [format_info(info) for info in infos]

def format_info(info):
    score = info["score"].white()
    mate_score = score.mate()
    centipawn_score = score.score()
    return {
        "mate_score": mate_score,
        "centipawn_score": centipawn_score,
        "pv": format_moves(info["pv"]),
    }
    
def format_moves(pv):
    return [move.uci() for move in pv]





def mcts(root, state, itermax):
    """Monte Carlo Tree Search algorithme"""
    distance_checkmate = analyze_position(state)
    if distance_checkmate[0]["mate_score"]!=None:
        return distance_checkmate[0]["pv"][0]
    first_expansion = True
    for i in range(itermax):
        node = root
        current_state = state.copy()
        if first_expansion:
            for move in state.legal_moves:
                new_state = state.copy()
                new_state.push(move)
                if new_state not in [child.state for child in node.children]:
                    node.add_child(new_state)
            first_expansion = False
            
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
    moves = {}
    for move in root.children:
        moves[move.state.peek()] = (move.wins,move.visits)
    best_moves = dict(sorted(moves.items(), key=lambda item:item[1],reverse=True))
    for (cle, valeur) in enumerate(best_moves.items()):
        print(f"{cle}: {valeur}")
   
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




fig, ax = plt.subplots(figsize=(20, 10), dpi = 40)
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)

def plot_node(node, x, y, dx, dy):
    """Dessiner l'arbre des coups"""
    ax.annotate(node.state, xy=(x, y), xytext=(x, y+0.5), ha='center', va='center', bbox=dict(boxstyle='square', facecolor='w', edgecolor='black'))

    if node.children:
        if len(node.children) == 1:
            x_spacing = 0
        else:
            x_spacing = dx / (len(node.children) - 1)
        x_start = x - dx / 2
        y_start = y - dy
        for i, child in enumerate(node.children):
            x_child = x_start + i * x_spacing
            y_child = y_start
            ax.plot([x, x_child], [y, y_child], 'k-', lw=1)
            plot_node(child, x_child, y_child, dx/2, dy)
            
            
            
    
def move_player():
    try :
        player_move = input("Move: ")
        board.push_san(str(player_move))
    except:
        print("Invalid move")
        move_player()



def play():
    global player
    iterations = 1000
    first = input("White or Black ? (w/b) ")

        
    if str(first)=="w" or str(first).lower=="white" or str(first).lower=="White":
        while not board.is_game_over():
            root = Node(board) 
            print(board.fen())
            print(board)
            player = "w"
            move_player()
            if board.is_checkmate():
                print("Vous gagnez")
                print(board)
                break
            elif board.is_stalemate() or board.is_fivefold_repetition() or board.is_seventyfive_moves() or board.is_insufficient_material():
                print("Egalité") 
                print(board)
                break
            print(board)
            print("L'IA réfléchit...")
            best_move = mcts(root, board, iterations)
            board.push_san(str(best_move))
            print("L'IA joue : " + str(best_move))
            if board.is_checkmate():
                print("IA gagne")
                print(board)
                break
            elif board.is_stalemate() or board.is_fivefold_repetition() or board.is_seventyfive_moves() or board.is_insufficient_material():
                print("Egalité") 
                print(board)
                break
            """plot_node(root, 0, 0, 10, 5)
            plt.axis('off')
            plt.show()"""

    elif str(first)=="b" or str(first).lower=="black" or str(first).lower=="Black":
        while not board.is_game_over():
            root = Node(board) 
            print(board.fen())
            print(board)
            player = "b"
            print("L'IA réfléchit...")
            best_move = mcts(root, board, iterations)
            board.push_san(str(best_move))
            print("L'IA joue : " + str(best_move))
            
            if board.is_checkmate():
                print("IA gagne")
                print(board)
                break
            elif board.is_stalemate() or board.is_fivefold_repetition() or board.is_seventyfive_moves() or board.is_insufficient_material():
                print("Egalité") 
                print(board)
                break
            print(board.fen())
            print(board)
            move_player()
            if board.is_checkmate():
                print("Vous gagnez")
                print(board)
                break
            elif board.is_stalemate() or board.is_fivefold_repetition() or board.is_seventyfive_moves() or board.is_insufficient_material():
                print("Egalité") 
                print(board)
                break
            """plot_node(root, 0, 0, 10, 5)
            plt.axis('off')
            plt.show()"""
    else :
        print("Invalid input")
        play()
    



board=chess.Board()
play()
