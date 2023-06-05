import chess
import chess.engine
from math import inf
import random
from random import randrange
import pickle

##########################CREATION DE MINIMAX###########################################

transposition_table = {}
MAX_TRANSPOSITION_TABLE_SIZE = 100000

def random_state(max_depth=100) :
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

def evaluation_piece(piece, maximizing_player):
    """fonction prenant en paramètre une chaine de caractère. On vérifie si il s'agit bien d'une pièce puis on retourne sa valeur"""
    try:
        int(piece) #dans ce cas ce n'est pas une pièce
        return 0
    except:
        var = -1 
        if (piece == piece.lower() and not maximizing_player) or (piece==piece.capitalize() and maximizing_player): #si la pièce est a nous (maximizing player)
            var = 1 #on renvoi une valeur positive
        piece = piece.lower()
        if piece =='p':
            return 10*var #pion
        elif piece =='n' or piece=='b':
            return 30*var #cavalier ou fou
        elif piece =='r':
            return 50*var #tour
        elif piece =='q':
            return 90*var #dame
        return 0
        
def is_win(board, tour, maximizing_player): #fonction aussi disponible sur la libraire python-chess
    if board.is_checkmate() and tour!=maximizing_player:
        return True
    return False


def is_lose(board, tour, maximizing_player): #fonction aussi disponible sur la libraire python-chess
    if board.is_checkmate() and tour==maximizing_player:
        return True
    return False


def is_draw(board): #fonction aussi disponible sur la libraire python-chess
    if board.is_stalemate() or board.is_insufficient_material() or board.is_seventyfive_moves() or board.is_fivefold_repetition():
        return True
    return False


def evaluation_plateau(board, tour, maximizing_player, depth): 
    """
    Retourne un score au plateau en fonction du joueur dont c'est le tour (maximizing_player)
    On suppose que les minuscules dans la chaîne renvoyée par board_fen() correspondent aux noirs(False)
    board.turn = tour = True => tour des blancs
    board.turn = tour = False => tour des noirs
    depth correspond au niveau d'exploration de minimax au moment où il appelle cette fonction
    """
    score=0
    if is_lose(board, tour, maximizing_player):
        return -900 * (4-depth) #L'adversaire fait échec et mat. 
    #La multiplication par la soustraction de la (profondeur maximum)-(le niveau actuelle) permet de privilégier des mat en peu de coups
    elif is_win(board, tour, maximizing_player):
        return 900 * (4-depth) #On a fait échec et mat
    elif board.is_stalemate() or board.is_insufficient_material() or board.is_seventyfive_moves() or board.is_fivefold_repetition(): #égalité
        return 0

    for elt in board.board_fen():
        if elt == '/':
            pass
        else:
            score+=evaluation_piece(elt, maximizing_player) #on somme les valeurs des pièces
    return score     

with open("openings_liste.txt", "rb") as fp:   # Unpickling
    openings = pickle.load(fp) #la liste des ouvertures des grands maîtres



def order_moves(board, moves):
    ordered_moves = []

    # 1. Les captures basées sur le MVV-LVA (Most Valuable Victim - Least Valuable Attacker) method
    capture_scores = {}
    for move in moves:
        if board.is_capture(move):
            captured_piece = board.piece_at(move.to_square)
            capturing_piece = board.piece_at(move.from_square)
            score = 10 * piece_value(captured_piece) - piece_value(capturing_piece)
            capture_scores[move] = score
    sorted_captures = sorted(capture_scores, key=capture_scores.get, reverse=True)
    ordered_moves.extend(sorted_captures)

    # 2. Promotions
    promotion_moves = [move for move in moves if move.promotion]
    ordered_moves.extend(promotion_moves)

    # 3. Echecs
    checking_moves = [move for move in moves if board.gives_check(move)]
    ordered_moves.extend(checking_moves)

    # 4. Les autres coups 
    non_capture_moves = [move for move in moves if move not in ordered_moves]
    ordered_moves.extend(non_capture_moves)

    return ordered_moves


def piece_value(piece):
    if piece is None:
        return 0

    piece_type = piece.piece_type
    if piece_type == chess.PAWN:
        return 1
    elif piece_type == chess.KNIGHT:
        return 3
    elif piece_type == chess.BISHOP:
        return 3
    elif piece_type == chess.ROOK:
        return 5
    elif piece_type == chess.QUEEN:
        return 9
    elif piece_type == chess.KING:
        return 0

    return 0






def add_to_transposition_table(board_str, score, move, depth):
    transposition_table[board_str] = (score, move, depth)

    if len(transposition_table) > MAX_TRANSPOSITION_TABLE_SIZE:
        # On enlève l'entrée la moins récente
        oldest_entry = min(transposition_table.keys(), key=lambda k: transposition_table[k][2])
        del transposition_table[oldest_entry]


def lookup_transposition_table(board_str):
    if board_str in transposition_table:
        return transposition_table[board_str]
    return None


def minimax(board, tour, maximizing_player, alpha=-inf, beta=inf, depth=5):
    """
    Renvoi le meilleur coup à jouer et le score au plateau après que ce coup soit joué
    """
    
    #On vérifie si on est dans une ouverture
    if len(board.move_stack) <= 10 :
        nb_coups_joues = len(board.move_stack)
        #Si on est au premier coup, on joue une ouverture aléatoire
        if nb_coups_joues==0 and tour == True:
            return (None, openings[randrange(0,len(openings))][0])
        #On cherche la même configuration dans la liste des ouvertures
        r = randrange(1,10)
        rd = 1
        for i in range(len(openings)):
            if board.move_stack==openings[i][:nb_coups_joues]:
                coup_secours = (None, openings[i][nb_coups_joues])
                print(coup_secours)
                if r==rd:
                    coup = (None, openings[i][nb_coups_joues])
                    return coup
                rd += 1
        try:
            return coup_secours
        except:
            pass
    
    board_str = board.fen()
    transposition_entry = lookup_transposition_table(board_str)
    if transposition_entry and transposition_entry[2] >= depth:
        return transposition_entry[0], transposition_entry[1]

    moves = [move for move in board.legal_moves]
    ordered_moves = order_moves(board, moves)

    #condition d'arret (fin de partie ou profondeur max atteinte)
    if board.legal_moves.count()==0 or depth==0 or is_win(board,tour,maximizing_player) or is_lose(board, tour, maximizing_player) or is_draw(board):
        score = evaluation_plateau(board, tour, maximizing_player, depth)
        add_to_transposition_table(board_str, score, None, depth)
        return score, None
    board.push(moves[0]) #on effectue le tout premier coup avant de rentrer dans la boucle pour obtenir une valeur de score et pouvoir la comparé ensuite
    score = minimax(board,not tour, maximizing_player, alpha,beta, depth-1)[0] #variable qui contient le meilleur score
    best_move=board.pop()
    if tour==maximizing_player: #On cherche le Max
        for move in ordered_moves[1:]: #on explore les branches
            board.push(move)
            
            val_board = minimax(board,not tour, maximizing_player, alpha,beta, depth-1)[0]
        
            if val_board>score: #on met à jour
                score= val_board
                best_move = board.pop()
            else:
                board.pop()
            alpha = max(alpha, score) #optimisation alpha beta 
            if beta<=alpha:
                break #on arrête l'exploration de la branche 
            
    else: #On cherche le Min
        for move in moves: #même principe que pour le max
            board.push(move)
            val_board = minimax(board,not tour, maximizing_player, alpha,beta, depth-1)[0]

            if val_board<score:
                score = val_board
                best_move = board.pop()
            else:
                board.pop()
            beta = min(beta, score)
            if beta<=alpha:
                break
    return (score, best_move) 

####### PARTIE ENDGAME (pas fonctionnelle) #############################

from math import sqrt
def endgameweight(board, maximizing_player):
    """
    Fonction qui compte le nombre de piece et renvoi son inverse
    """
    endgame_weight = 1
    fen = board.fen()
    piece = 0
    for i in range(0,len(fen)):
        try:
            int(fen[i])
        except:
            piece +=1
    endgame_weight /= piece
    return endgame_weight
def dist_to_corner(board, maximizing_player):
    """retourne la distance du roi adverse au coin le plus proche"""
    if maximizing_player: #si on est les blancs
        black_king_square = board.king(chess.BLACK) #on cherche la distance entre le roi noir et un coin
        return min(chess.square_distance(0,black_king_square),chess.square_distance(7,black_king_square),chess.square_distance(56,black_king_square),chess.square_distance(63,black_king_square))
        #on veut le coin le plus proche on prend donc le minimum de la distance entre ce roi et chacun des points                 
    else:
        white_king_square = board.king(chess.WHITE) #sinon le roi adverse est celui des blancs
        return min(chess.square_distance(0,white_king_square),chess.square_distance(7,white_king_square),chess.square_distance(56,white_king_square),chess.square_distance(63,white_king_square))


def dist_btw_king(board):
    """Retourne la distance entre les deux rois"""
    black_king_square = board.king(chess.BLACK)
    white_king_square = board.king(chess.WHITE)
    return chess.square_distance(black_king_square,white_king_square)

def endgame_evaluation(board, maximizing_player):
    """fonction qui évalue la position en fin de partie. On se sert des fonctions précédentes pour attribuer une récompense lors de situations favorables en fin de partie.
    Elément augmentant le socre : 
    roi proche entre eux
    roi proche du coin 
    
    retourne un coefficient multiplicateur qui doit être appliqué à la fonction d'évaluation
    """
    weight=endgameweight(board, maximizing_player)
    if len(board.move_stack)>=40 and weight>=0.2: #engame_weight = 1/nb_piece_adverse => on veut ici qu'il reste au max 5 pièces adverses pour que le mode "endgame" se mette en place
        
        dist_corner = dist_to_corner(board, maximizing_player)
        square_distance = dist_btw_king(board)
        return weight*(1/square_distance)*(1/(dist_corner+1))*10000 #ce calcul ne permet pas d'obtenir un poids exploitable
    
################################## UTILISATION DE L'ALGORITHME #############################################

import time
class JoueurMinimax():
    """définition d'une classe qui nous a été utile lors de tests de l'algorithme"""
    def __init__(self,board, ma_couleur):
        self.board = board
        self.color = ma_couleur=="white" or ma_couleur=="blanc"
        self.score = evaluation_plateau(board, board.turn, board.turn)
        
    def is_my_turn(self,new_board):
        """"renvoi True ou False selon si c'est notre tour de jouer"""
        if new_board.turn == self.color:
            self.board=new_board
            self.score = evaluation_plateau(board, board.turn, board.turn)
            return True
        return False
    def is_win(self):
        if self.score==inf:
            print('Victoire des: ', self.color)
            time.sleep(5)
            return True
            
        return False
    def is_lose(self):
        if self.score==-inf:
            print('Victoire des: ', not self.color)
            time.sleep(5)
            return True
        return False
    def jouer(self, new_board):
        """renvoie le plateau modifié du coup que l'on joue"""
        print(self.is_my_turn(new_board), new_board.turn, self.color)
        if self.is_my_turn(new_board) and not is_lose(new_board, board.turn, self.color) and not is_draw(board):
            print("je joue")
            self.board.push(minimax(self.board)[1])
            return self.board
        return new_board
    

class JoueurAleatoire:
    """on définit un joueur qui joue de manière aléatoire""""
    def __init__(self, board, ma_couleur):
        self.board = board
        self.color = ma_couleur=="white" or ma_couleur=="blanc"
        
    def is_my_turn(self,new_board):
        if new_board.turn == self.color:
            self.board=new_board
            return True
        return False
    def is_win(self):
        if self.score==inf:
            print('Victoire des: ', self.color)
            time.sleep(5)
            return True
            
        return False
    def is_lose(self):
        if self.score==-inf:
            print('Victoire des: ', not self.color)
            time.sleep(5)
            return True
        return False
    def jouer(self, new_board):
        """"fonction qui renvoi un coup au hasard parmi tous les coups possibles"""
        print(self.is_my_turn(new_board), new_board.turn, self.color)
        if self.is_my_turn(new_board) and not is_lose(new_board, board.turn, self.color) and not is_draw(board):
            moves = [move for move in board.legal_moves]
            print("je joue")
            self.board.push(random.choice(moves))
            return self.board
        return new_board
    



def move_player():
    """permet de jouer contre l'IA"""
    try :
        player_move = str(input("Move Player: "))
        board.push_san(player_move)
    except:
        print("Invalid move")
        move_player()



###### QUELQUES TESTS DE MAT #######
#board = chess.Board()
#mat en 2 (le programme y arrive)
#board=chess.Board("5Q2/8/4r1p1/6kp/qP6/3B1P2/3K2PP/8")
#mat en 3 : (le programme y arrive)
#board=chess.Board("4R2B/5N1k/6pP/6P1/8/1p6/1p6/QK6")
board = chess.Board()
print(board)
print("\n")
print(board.turn)
print("\n")
print(board.legal_moves)
print(board.fen)
transposition_table.clear()
while not board.is_checkmate():
    move_player()
    move_minimax = minimax(board, board.turn, board.turn)[1]
    print('Move AI : ', move_minimax)
    print("\n")
    board.push(move_minimax)
    
    print(board)
    print("\n")
    
    """
    board.push(minimax(board, board.turn, board.turn)[1])
    print(board, board.turn)
    print("checkmate : ",board.is_checkmate())
    print("\n")
    print(board.move_stack,"\n", type(board.move_stack), type(board.move_stack[0]))
    if len(board.move_stack)>10:
        break
    """
transposition_table.clear()
if board.turn:
    print("Winner : Player")
else :
    print("Winner : AI")
