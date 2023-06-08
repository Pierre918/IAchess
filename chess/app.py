from flask import Flask, request, jsonify
from flask_cors import CORS
from minimax import *
from mcts import *
import chess
import json
import ast

app = Flask(__name__)
CORS(app)

iterations = 800

# Route pour jouer un coup
@app.route('/play', methods=['POST'])
def play_move():
    move = request.form.get('move')
    datas = request.form.get('coups')
    if datas is None:
        return jsonify({'error': 'Invalid data format'})

    try:
        coups = ast.literal_eval(datas)
    except (SyntaxError, ValueError) as e:
        return jsonify({'error': 'Invalid data format'})
    ai = request.form.get('ai')

    print(move)
    try:
        print(coups)
    except:
        print("pas de coups")
    
    # Crée un objet d'échiquier
    board = chess.Board(move)
    coups1 = []
    for coup in coups:
        coups1.append(chess.Move.from_uci(coup))
    
    # Utilisez une des IA en Python pour calculer le mouvement de l'IA
    
    if ai == "minimax":
        # Utilise l'algorithme Minimax pour trouver le meilleur mouvement
        move_minimax = minimax(board, board.turn, board.turn, coups1)[1]
        print(move_minimax)
        # Applique le mouvement sur l'échiquier
        board.push(move_minimax)
        ai_move =  str(move_minimax)
    elif ai == "mcts":
        # Utilise l'algorithme MCTS pour trouver le meilleur mouvement
        root = Node(board)
        if len(coups)%2 !=0:
            player = "w"
        else:
            player = "b"
        print(player)
        best_move = mcts(root, board, iterations, player)
        print(best_move)
        # Applique le mouvement sur l'échiquier
        board.push_san(str(best_move))
        ai_move =  str(best_move)
    elif ai == "vs":
        if len(coups1)%2==0 or len(coups1)<= 10:
            # Utilise l'algorithme Minimax pour trouver le meilleur mouvement si le nombre de coups est pair ou inférieur à 10
            move_minimax = minimax(board, board.turn, board.turn, coups1)[1]
            print(move_minimax)
            # Applique le mouvement sur l'échiquier
            board.push(move_minimax)
            ai_move =  str(move_minimax)
        else:
            # Utilise l'algorithme MCTS pour trouver le meilleur mouvement si le nombre de coups est impair et supérieur à 10
            root = Node(board)
            player = "b"
            print(player)
            best_move = mcts(root, board, iterations, player)
            print(best_move)
            # Applique le mouvement sur l'échiquier
            board.push_san(str(best_move))
            ai_move =  str(best_move)

    #ai_move =  str(board.fen()) 

    response = {'ai_move': ai_move}
    print("response :",response)
    return jsonify(response)

if __name__ == '__main__':
    app.run(port=5000)
