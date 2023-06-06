# Importation de bibliothèques
from math import log, inf, sqrt
import random
import chess
import chess.engine
import os

#Stockfish
engine = chess.engine.SimpleEngine.popen_uci(r"stockfish-windows-2022-x86-64-avx2.exe")



# Définition de la classe Node
class Node:
    def __init__(self, state, parent=None):
        # État actuel du noeud
        self.state = state
        # Parent du noeud
        self.parent = parent
        # Liste des coups possibles à partir de ce noeud
        self.children = []
        # Nombre de victoires du noeud
        self.wins = 0
        # Nombre de visites du noeud
        self.visits = 0
        
    # Ajout d'un child à un noeud
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
            # Si le noeud enfant n'a pas encore été visité
            exploitation_term = inf
            exploration_term = inf
        else: 
            # Calcul du terme d'exploitation et du terme d'exploration
            exploitation_term = child.wins / child.visits
            exploration_term = c_param * sqrt(log_total_visits / child.visits) * (1 / len(node.children))
        
        # Calcul du score pour chaque noeud enfant
        score = exploitation_term + exploration_term
        
        # Mise à jour du meilleur score et de le noeud enfant correspondant
        if score > best_score:
            best_score = score
            best_child = child
    # Retourne le noeud enfant ayant le meilleur score
    return best_child
    
    
    
def evaluate(state, player):
    """
    Vérifie qu'on soit en fin de partie et retourne 1 si gagnant, -1 si perdant et 0 en cas d'égalité
    """
    piece_values = {'P': 1,'N': 3,'B': 3,'R': 5,'Q': 9,'K': 100,'p': 1,'n': 3,'b': 3,'r': 5,'q': 9,'k': 100}  # Associer les lettres (pièces) à leur valeur
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
        # Calcul du score en sommant les valeurs de chaque pièce dans le cas où l'on soit pas en fin de partie (cas de secours)
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


# Sélection d'un noeud fils avec la plus grande valeur UCB ou PUCT
def select_node(node,state, player):
    """
    Sélection en se basant sur le UCB ou PUCT
    """
    #UCB
    #max_score = -inf
    #best_child = None
    #for child in node.children:
    #    score = ucb(child)
    #    if score > max_score:
    #        max_score = score
    #        best_child = child
    #return best_child
    
    #PUCT
    return puct(node, 5.0)


def expand_node(node, state, player):
    """
    Expansion d'un noeud avec un mouvement aléatoire si c'est l'algo (en rajoutant tous ses nœuds enfants possibles) et le meilleur coup si c'est le joueur
    """
    # Si c'est à l'adversaire de jouer
    if " " + player + " " in state.fen():
        try:
            # Essaye de trouver le meilleur coup possible en utilisant Stockfish
            best_possible_move = engine.play(state, chess.engine.Limit(time=0.1, depth=18))
        except:
            # Si Stockfish ne peut pas trouver de coup, choisis un coup aléatoire parmi les coups légaux
            best_possible_move = random.choice(list(state.legal_moves))
            
        # Crée un nouvel état en appliquant le meilleur coup possible et ajoute le nouvel état comme enfant du nœud actuel
        new_state = state.copy()
        new_state.push(best_possible_move.move)
        if new_state not in [child.state for child in node.children]:
            node.add_child(new_state)
            
        # Le coup choisi est le dernier enfant du nœud actuel
        chosen_move = node.children[-1]
        return chosen_move
    else:
        # Si c'est au MCTS de joeur
        for move in state.legal_moves:
            new_state = state.copy()
            new_state.push(move)
            
            # Vérifie si le nouvel état n'est pas déjà un enfant du nœud actuel et ajoute le nouvel état comme enfant du nœud actuel
            if new_state not in [child.state for child in node.children]:
                node.add_child(new_state)
                
        # Choisi un coup aléatoire parmi les enfants du nœud actuel
        random_move = random.choice(node.children)
        return random_move


def simulate(state, player):
    """
    Simulation d'une partie jusqu'à la fin
    """
    while not state.is_game_over():
        # Effectue un mouvement aléatoire parmi les coups légaux disponibles
        state.push(random.choice(list(state.legal_moves)))
        
        # Si utilisation de Stockfish
        # best_possible_move = engine.play(state, chess.engine.Limit(time=0.1, depth=18))
        # if state.is_game_over():
        #     return evaluate(state)
        # else:
        #     state.push(best_possible_move.move)
    
    # Une fois que la partie est terminée, évalue l'état final du jeu
    return evaluate(state, player)


def backpropagate(node, reward, player):
    """
    Mise à jour de la valeur de tous les noeuds
    """
    while node is not None:
        node.update(reward)
        node = node.parent
        


def analyze_position(board, num_moves_to_return=1, depth_limit=10, time_limit=0.1):
    """
    Effectue l'analyse de la position avec Stockfish
    """
    search_limit = chess.engine.Limit(depth=depth_limit, time=time_limit)
    infos = engine.analyse(board, search_limit, multipv=num_moves_to_return)
    return [format_info(info) for info in infos]


def format_info(info):
    """
    Extrait le score et le convertit en différents formats
    """
    score = info["score"].white()
    mate_score = score.mate()
    centipawn_score = score.score()
    
    # Retourne les informations formatées sous forme de dictionnaire
    return {
        "mate_score": mate_score,
        "centipawn_score": centipawn_score,
        "pv": format_moves(info["pv"]),
    }


def format_moves(pv):
    """
    Formate les mouvements principaux en notation UCI (pour pouvoir être exploités)
    """
    return [move.uci() for move in pv]





def mcts(root, state, itermax, player):
    """
    Algorithme principal de Monte-Carlo
    """
    # Analyse la position pour vérifier s'il y a un échec et mat forcé
    distance_checkmate = analyze_position(state)
    if distance_checkmate[0]["mate_score"] is not None:
        # S'il y a, retourne le premier coup de la meilleure variation
        return distance_checkmate[0]["pv"][0]
    
    first_expansion = True
    for i in range(itermax):        # Nombre d'itérations de l'algoritmhe
        node = root
        current_state = state.copy()     # Pour ne pas .pop() à chaque coup fait
        
        if first_expansion:
            # Effectue la première expansion en ajoutant tous les coups légaux comme enfants du nœud racine
            for move in state.legal_moves:
                new_state = state.copy()
                new_state.push(move)
                if new_state not in [child.state for child in node.children]:
                    node.add_child(new_state)
            first_expansion = False
        
        while node.children:
            # Sélectionne le nœud fils à explorer en utilisant une stratégie de sélection
            node = select_node(node, current_state, player)
            current_state.push(node.state.peek())

        if not current_state.is_game_over():
            # Effectue l'expansion du nœud sélectionné
            node = expand_node(node, current_state, player)
            # Effectue une simulation de la partie à partir du nœud étendu
            reward = simulate(current_state, player)
            # Rétropropagation à partir du nœud étendu jusqu'au nœud racine
            backpropagate(node, reward, player)
        else:
            # Si la partie est terminée à partir du nœud sélectionné, évalue l'état final et rétropropage la récompense
            reward = evaluate(current_state, player)
            backpropagate(node, reward, player)
    
    # Dictionnaire avec les statistiques de tous les coups
    moves = {}
    for move in root.children:
        moves[str(move.state.peek())] = (move.wins, move.visits)
    best_moves = dict(sorted(moves.items(), key=lambda item: item[1], reverse=True))
    for (cle, valeur) in enumerate(best_moves.items()):
        print(f"{cle}: {valeur}")
    
    # Retourne le coup avec le plus grand nombre de visites parmi les nœuds enfants du nœud racine
    return max(root.children, key=lambda x: x.visits).state.peek()


# Dans le cas d'une recherche de meilleur coup à une position précise
"""
if __name__ == "__main__":
    fen ="r2q2nr/pppk3p/5ppB/2P5/2BN4/2N4P/PPP1QP1P/R3K2R w KQ - 4 14"
    board = chess.Board(fen)
    #board = random_board()
    root = Node(board)
    best_move = mcts(root, board, 1000)
    #print(board.fen())
    print(best_move)
    print(board)
"""


import matplotlib.pyplot as plt

# Crée une figure et un axe pour le tracé
fig, ax = plt.subplots(figsize=(20, 10), dpi=40)
ax.set_xlim(0, 10)  # Définit les limites de l'axe des x
ax.set_ylim(0, 10)  # Définit les limites de l'axe des y

def plot_node(node, x, y, dx, dy):
    """
    Permet de tracer l'arbre de recherche
    """
    # Trace le nœud
    ax.annotate(node.state, xy=(x, y), xytext=(x, y + 0.5), ha='center', va='center',
                bbox=dict(boxstyle='square', facecolor='w', edgecolor='black'))

    # Trace les arêtes vers les enfants
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
            plot_node(child, x_child, y_child, dx / 2, dy)









def move_player():
    """
    Pemet de jouer contre l'algorithme
    """
    try :
        player_move = str(input("Move: "))
        # Si flemme de réfléchir taper 's' permet de faire jouer Stockfish à sa place
        if player_move == "s":
            best_possible_move = engine.play(board, chess.engine.Limit(time=2,depth = 18))
            board.push(best_possible_move.move)
        else:
            board.push_san(player_move)
    except:
        print("Invalid move")
        move_player()



def play():
    """
    Fonction de jeu de parties contre le MCTS
    """
    global player
    iterations = 800
    
    # Demande à l'utilisateur de choisir de quelle couleur il veut jouer
    first = input("White or Black ? (w/b) ")
    
    if str(first) == "w" or str(first).lower() == "white" or str(first).lower() == "White":
        # Partie en tant que joueur blanc
        while not board.is_game_over():
            root = Node(board)
                
            print(board.fen())
            print(board)
            player = "w"
            # Le joueur joue
            move_player()
            
            # Vérifie si la partie n'est pas fini (parfois le while ne suffit pas)
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
            
            # Effectue la recherche Monte-Carlo
            best_move = mcts(root, board, iterations, player)
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
        
            # Trace le graphique du nœud racine actuel
            """plot_node(root, 0, 0, 10, 5)
            plt.axis('off')
            plt.show()"""

    elif str(first) == "b" or str(first).lower() == "black" or str(first).lower() == "Black":
        # Partie en tant que joueur noir
        while not board.is_game_over():
            root = Node(board)
                    
            print(board.fen())
            print(board)
            player = "b"
            
            print("L'IA réfléchit...")
            
            # Effectue la recherche Monte-Carlo
            best_move = mcts(root, board, iterations, player)
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
            
            # Trace le graphique du nœud racine actuel
            """plot_node(root, 0, 0, 10, 5)
            plt.axis('off')
            plt.show()"""
    else:
        # La syntaxe du coup n'est pas bonne
        print("Invalid input")
        play()
    



board=chess.Board()
play()

