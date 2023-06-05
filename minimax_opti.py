import chess
import chess.engine
from math import inf
import random
from random import randrange
import pickle


transposition_table = {}
MAX_TRANSPOSITION_TABLE_SIZE = 1000000

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
    try:
        int(piece)
        return 0
    except:
        var = -1
        if (piece == piece.lower() and not maximizing_player) or (piece==piece.capitalize() and maximizing_player):
            var = 1
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
        
def is_win(board, tour, maximizing_player):
    if board.is_checkmate() and tour!=maximizing_player:
        return True
    return False


def is_lose(board, tour, maximizing_player):
    if board.is_checkmate() and tour==maximizing_player:
        return True
    return False


def is_draw(board):
    if board.is_stalemate() or board.is_insufficient_material() or board.is_seventyfive_moves() or board.is_fivefold_repetition():
        return True
    return False


def evaluation_plateau(board, tour, maximizing_player, depth): 
    """
    Retourne un score au plateau en fonction du joueur dont c'est le tour (maximizing_player)
    On suppose que les minuscules dans la chaîne renvoyée par board_fen() correspondent aux noirs(False)
    board.turn = tour = True => tour des blancs
    board.turn = tour = False => tour des noirs
    """
    score=0
    if is_lose(board, tour, maximizing_player):
        return -900 * (4-depth) #L'adversaire fait échec et mat
    elif is_win(board, tour, maximizing_player):
        return 900 * (4-depth) #On a fait échec et mat
    elif board.is_stalemate() or board.is_insufficient_material() or board.is_seventyfive_moves() or board.is_fivefold_repetition():
        return 0

    for elt in board.board_fen():
        if elt == '/':
            pass
        else:
            score+=evaluation_piece(elt, maximizing_player)
    return score     

with open("openings_liste.txt", "rb") as fp:   # Unpickling
    openings = pickle.load(fp)



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


    if board.legal_moves.count()==0 or depth==0 or is_win(board,tour,maximizing_player) or is_lose(board, tour, maximizing_player) or is_draw(board):
        score = evaluation_plateau(board, tour, maximizing_player, depth)
        add_to_transposition_table(board_str, score, None, depth)
        return score, None
    board.push(moves[0])
    score = minimax(board,not tour, maximizing_player, alpha,beta, depth-1)[0]
    best_move=board.pop()
    if tour==maximizing_player: #On cherche le Max
        for move in ordered_moves[1:]:
            board.push(move)
            
            val_board = minimax(board,not tour, maximizing_player, alpha,beta, depth-1)[0]
        
            if val_board>score:
                score= val_board
                best_move = board.pop()
            else:
                board.pop()
            alpha = max(alpha, score)
            if beta<=alpha:
                break
            
    else: #On cherche le Min
        for move in moves:
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

import time
class JoueurMinimax():
    def __init__(self,board, ma_couleur):
        self.board = board
        self.color = ma_couleur=="white" or ma_couleur=="blanc"
        self.score = evaluation_plateau(board, board.turn, board.turn)
        
    def is_my_turn(self,new_board):
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
        print(self.is_my_turn(new_board), new_board.turn, self.color)
        if self.is_my_turn(new_board) and not is_lose(new_board, board.turn, self.color) and not is_draw(board):
            print("je joue")
            self.board.push(minimax(self.board)[1])
            return self.board
        return new_board
    

class JoueurAleatoire:
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
        print(self.is_my_turn(new_board), new_board.turn, self.color)
        if self.is_my_turn(new_board) and not is_lose(new_board, board.turn, self.color) and not is_draw(board):
            moves = [move for move in board.legal_moves]
            print("je joue")
            self.board.push(random.choice(moves))
            return self.board
        return new_board
    



def move_player():
    try :
        player_move = str(input("Move Player: "))
        board.push_san(player_move)
    except:
        print("Invalid move")
        move_player()




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
