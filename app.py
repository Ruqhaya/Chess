from flask import Flask, render_template, request, jsonify
import copy
app = Flask(__name__)

# Store ongoing games
games = {}

class ChessGame:
    def __init__(self):
        self.board = self.initialize_board()
        self.turn = 'white'
        self.move_history = []
        self.en_passant_target = None  # Track en passant target square
        self.castling_rights = {'white': {'king_side': True, 'queen_side': True}, 
                                'black': {'king_side': True, 'queen_side': True}}
        self.captured_pieces = {'white': [], 'black': []}  # Store captured pieces
        self.game_over = False  # Track whether the game is over
        self.winner = None 
        self.move_history.append((copy.deepcopy(self.board), self.turn))
    
    def initialize_board(self):
        board = [
            ['black rook', 'black knight', 'black bishop', 'black queen', 'black king', 'black bishop', 'black knight', 'black rook'],
            ['black pawn', 'black pawn', 'black pawn', 'black pawn', 'black pawn', 'black pawn', 'black pawn', 'black pawn'],
            ['', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', ''],
            ['white pawn', 'white pawn', 'white pawn', 'white pawn', 'white pawn', 'white pawn', 'white pawn', 'white pawn'],
            ['white rook', 'white knight', 'white bishop', 'white queen', 'white king', 'white bishop', 'white knight', 'white rook']
        ]
        return board

    def get_board(self):
        return self.board

    def validate_move(self, start_pos, end_pos):
        if self.game_over:
            return False  # No moves allowed if the game is over

        piece = self.board[start_pos[0]][start_pos[1]]
        legal_moves = self.get_legal_moves(start_pos[0], start_pos[1])
        if end_pos not in legal_moves:
            return False
        
        # Make the move temporarily
        temp_board = copy.deepcopy(self.board)
        temp_board[end_pos[0]][end_pos[1]] = piece
        temp_board[start_pos[0]][start_pos[1]] = ''

        # Check if the king is still in check after the move
        if self.is_in_check(self.turn, temp_board):
            return False

        return True

    def make_move(self, start_pos, end_pos):
        start_pos = [int(start_pos[0]), int(start_pos[1])]
        end_pos = [int(end_pos[0]), int(end_pos[1])]

        if self.validate_move(start_pos, end_pos):
            piece = self.board[start_pos[0]][start_pos[1]]
            target_piece = self.board[end_pos[0]][end_pos[1]]

            # Capture the target piece
            if target_piece:
                captured_color = 'black' if 'white' in target_piece else 'white'
                self.captured_pieces[captured_color].append(target_piece)

            self.board[end_pos[0]][end_pos[1]] = piece
            self.board[start_pos[0]][start_pos[1]] = ''

            # Handle pawn promotion
            if 'pawn' in piece and (end_pos[0] == 0 or end_pos[0] == 7):
                self.board[end_pos[0]][end_pos[1]] = piece.replace('pawn', 'queen')  # Auto-promote to queen for now

            # Handle en passant
            if 'pawn' in piece:
                if abs(start_pos[0] - end_pos[0]) == 2:
                    self.en_passant_target = [(start_pos[0] + end_pos[0]) // 2, start_pos[1]]
                elif end_pos == self.en_passant_target:
                    captured_pawn_row = start_pos[0]
                    captured_pawn_col = end_pos[1]
                    self.board[captured_pawn_row][captured_pawn_col] = ''
                else:
                    self.en_passant_target = None
            else:
                self.en_passant_target = None

            # Handle castling
            if piece == 'white king' and start_pos == [7, 4]:
                if end_pos == [7, 6]:  # King-side castling
                    if self.castling_rights['white']['king_side']:
                        self.board[7][7] = ''
                        self.board[7][5] = 'white rook'
                        self.castling_rights['white']['king_side'] = False
                        self.castling_rights['white']['queen_side'] = False
                elif end_pos == [7, 2]:  # Queen-side castling
                    if self.castling_rights['white']['queen_side']:
                        self.board[7][0] = ''
                        self.board[7][3] = 'white rook'
                        self.castling_rights['white']['king_side'] = False
                        self.castling_rights['white']['queen_side'] = False
            elif piece == 'black king' and start_pos == [0, 4]:
                if end_pos == [0, 6]:  # King-side castling
                    if self.castling_rights['black']['king_side']:
                        self.board[0][7] = ''
                        self.board[0][5] = 'black rook'
                        self.castling_rights['black']['king_side'] = False
                        self.castling_rights['black']['queen_side'] = False
                elif end_pos == [0, 2]:  # Queen-side castling
                    if self.castling_rights['black']['queen_side']:
                        self.board[0][0] = ''
                        self.board[0][3] = 'black rook'
                        self.castling_rights['black']['king_side'] = False
                        self.castling_rights['black']['queen_side'] = False

            # Update turn
            self.turn = 'black' if self.turn == 'white' else 'white'
            self.move_history.append((copy.deepcopy(self.board), self.turn))
            
            # Check for endgame conditions
            if self.is_checkmate():
                return True
            if self.is_stalemate():
                return True

            return True
        return False

    def get_legal_moves(self, row, col):
        piece = self.board[row][col]
        all_moves = self.get_possible_moves_without_check(row, col)
        print(all_moves)
        valid_moves = []
        for move in all_moves:
            temp_board = copy.deepcopy(self.board)  # Deep copy only here
            temp_board[move[0]][move[1]] = piece
            temp_board[row][col] = ''
            if not self.is_in_check(self.turn, temp_board):
                valid_moves.append(move)
    
        return valid_moves
    
    def get_pawn_moves(self, row, col, piece):
        moves = []
        direction = -1 if 'white' in piece else 1
        start_row = 6 if 'white' in piece else 1

        # Move forward
        if self.board[row + direction][col] == '':
            moves.append([row + direction, col])
            if row == start_row and self.board[row + 2 * direction][col] == '':
                moves.append([row + 2 * direction, col])

        # Capture diagonally
        for offset in [-1, 1]:
            new_col = col + offset
            if 0 <= new_col < 8 and self.board[row + direction][new_col]:
                if 'white' not in self.board[row + direction][new_col] if 'white' in piece else 'white' in self.board[row + direction][new_col]:
                    moves.append([row + direction, new_col])

        # Handle en passant
        if self.en_passant_target:
            if [row + direction, col + 1] == self.en_passant_target or [row + direction, col - 1] == self.en_passant_target:
                moves.append(self.en_passant_target)

        return moves

    def get_rook_moves(self, row, col):
        return self.get_straight_line_moves(row, col, directions=[(1, 0), (-1, 0), (0, 1), (0, -1)])

    def get_bishop_moves(self, row, col):
        return self.get_straight_line_moves(row, col, directions=[(1, 1), (-1, -1), (1, -1), (-1, 1)])

    def get_queen_moves(self, row, col):
        return self.get_rook_moves(row, col) + self.get_bishop_moves(row, col)

    def get_knight_moves(self, row, col):
        moves = []
        possible_moves = [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]
        for dx, dy in possible_moves:
            new_row = row + dx
            new_col = col + dy
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                if not self.board[new_row][new_col] or ('white' not in self.board[new_row][new_col] if 'white' in self.board[row][col] else 'white' in self.board[new_row][new_col]):
                    moves.append([new_row, new_col])
        return moves

    def get_king_moves(self, row, col, piece):
        moves = []
        king_moves = [(1, 0), (1, 1), (1, -1), (0, 1), (0, -1), (-1, 0), (-1, 1), (-1, -1)]
        for move in king_moves:
            new_row = row + move[0]
            new_col = col + move[1]
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                if not self.board[new_row][new_col] or 'white' not in self.board[new_row][new_col] if 'white' in piece else 'white' in self.board[new_row][new_col]:
                    moves.append([new_row, new_col])

        # Handle castling
        if piece == 'white king' and row == 7 and col == 4:
            if self.castling_rights['white']['king_side'] and self.board[7][5] == '' and self.board[7][6] == '':
                moves.append([7, 6])
            if self.castling_rights['white']['queen_side'] and self.board[7][3] == '' and self.board[7][2] == '' and self.board[7][1] == '':
                moves.append([7, 2])
        elif piece == 'black king' and row == 0 and col == 4:
            if self.castling_rights['black']['king_side'] and self.board[0][5] == '' and self.board[0][6] == '':
                moves.append([0, 6])
            if self.castling_rights['black']['queen_side'] and self.board[0][3] == '' and self.board[0][2] == '' and self.board[0][1] == '':
                moves.append([0, 2])

        return moves

    def get_straight_line_moves(self, row, col, directions):
        moves = []
        for direction in directions:
            for i in range(1, 8):
                new_row = row + direction[0] * i
                new_col = col + direction[1] * i
                if 0 <= new_row < 8 and 0 <= new_col < 8:
                    if self.board[new_row][new_col]:
                        if 'white' not in self.board[new_row][new_col] if 'white' in self.board[row][col] else 'white' in self.board[new_row][new_col]:
                            moves.append([new_row, new_col])
                        break
                    moves.append([new_row, new_col])
                else:
                    break
        return moves

    def is_in_check(self, color, board):
        king_pos = self.find_king(color, board)

        if king_pos:
            opponent_color = 'white' if color == 'black' else 'black'
            for row in range(8):
                for col in range(8):
                    if opponent_color in board[row][col]:
                    # Check if the king is in the possible moves of an opponent's piece
                        if king_pos in self.get_possible_moves_without_check(row, col):
                            print(color,'king is in check')
                            return True
        return False
    
    def find_king(self, color, board):
        king = color + ' king'
        for row in range(8):
            for col in range(8):
                if board[row][col] == king:
                    return [row, col]
        return None

    def is_checkmate(self):
        if not self.is_in_check(self.turn, self.board):
            return False

        for row in range(8):
            for col in range(8):
                if self.turn in self.board[row][col]:
                    legal_moves = self.get_legal_moves(row, col)
                    print('checking checkmate and it should above it []')
                    if len(legal_moves)!=0:
                        for move in legal_moves:
                            temp_board = copy.deepcopy(self.board)
                            temp_board[move[0]][move[1]] = self.board[row][col]
                            temp_board[row][col] = ''
                            if not self.is_in_check(self.turn, temp_board):
                                return False
                    else:
                        self.game_over = True
                        self.winner = 'black' if self.turn == 'white' else 'white'
                        return True

    def is_stalemate(self):
        if self.is_in_check(self.turn, self.board):
            return False

        for row in range(8):
            for col in range(8):
                if self.turn in self.board[row][col]:
                    legal_moves = self.get_legal_moves(row, col)
                    if legal_moves:
                        return False

        self.game_over = True
        self.winner = 'draw'
        return True

    def get_possible_moves_without_check(self, row, col):
        piece = self.board[row][col]
        legal_moves = []

        if 'pawn' in piece:
            legal_moves = self.get_pawn_moves(row, col, piece)
        elif 'rook' in piece:
            legal_moves = self.get_rook_moves(row, col)
        elif 'knight' in piece:
            legal_moves = self.get_knight_moves(row, col)
        elif 'bishop' in piece:
            legal_moves = self.get_bishop_moves(row, col)
        elif 'queen' in piece:
            legal_moves = self.get_rook_moves(row, col) + self.get_bishop_moves(row, col)
        elif 'king' in piece:
            legal_moves = self.get_king_moves(row, col, piece)

        return legal_moves
    
    def undo_move(self):
        if not self.move_history:
            return False  # No move to undo

        # Remove the last move and revert to the previous state
        self.move_history.pop()
        last_board_state, last_turn = self.move_history[-1] if self.move_history else (self.initialize_board(), 'white')
        self.board = last_board_state
        # self.current_turn = last_turn
        self.turn=last_turn
        return True
    
    def restart_game(self):
        self.board = self.initialize_board()
        self.turn = 'white'
        self.move_history = []
        self.en_passant_target = None
        self.castling_rights = {'white': {'king_side': True, 'queen_side': True}, 
                            'black': {'king_side': True, 'queen_side': True}}
        self.captured_pieces = {'white': [], 'black': []}
        self.game_over = False
        self.winner = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/1vs1')
def vs1():
    return render_template('1vs1.html')

@app.route('/1vsbot')
def vsbot():
    return render_template('1vsbot.html')

@app.route('/start_game', methods=['POST'])
def start_game():
    game_id = request.json.get('game_id')
    games[game_id] = ChessGame()
    return jsonify({'status': 'game started', 'game_id': game_id})

@app.route('/move', methods=['POST'])
def move():
    data = request.json
    game_id = data['game_id']
    start_pos = data['start']
    end_pos = data['end']

    game = games.get(game_id)
    if not game:
        return jsonify({'error': 'Game not found'}), 404

    if game.game_over:
        return jsonify({
            'status': 'game over',
            'board': game.get_board(),
            'turn': game.turn,
            'game_over': game.game_over,
            'winner': game.winner,
            'captured':game.captured_pieces
        })

    move_result = game.make_move(start_pos, end_pos)

    if move_result:
        return jsonify({
            'status': 'move made',
            'board': game.get_board(),
            'turn': game.turn,
            'game_over': game.game_over,
            'winner': game.winner,
            'captured':game.captured_pieces
        })
    else:
        # Add debugging information
        return jsonify({
            'status': 'invalid move',
            'board': game.get_board(),
            'turn': game.turn
        })

@app.route('/board/<game_id>', methods=['GET'])
def get_board(game_id):
    game = games.get(game_id)
    if not game:
        return jsonify({'error': 'Game not found'}), 404

    return jsonify({
        'board': game.get_board(),
        'turn': game.turn,
        'game_over': game.game_over,
        'winner': game.winner
    })

@app.route('/legal_moves', methods=['POST'])
def legal_moves():
    data = request.json
    game_id = data['game_id']
    row = int(data['row'])
    col = int(data['col'])

    game = games.get(game_id)
    if not game:
        return jsonify({'error': 'Game not found'}), 404

    legal_moves = game.get_legal_moves(row, col)
    return jsonify({'legal_moves':legal_moves})

@app.route('/captured_pieces/<game_id>', methods=['GET'])
def get_captured_pieces(game_id):
    game = games.get(game_id)
    if not game:
        return jsonify({'error': 'Game not found'}), 404

    return jsonify({'captured': game.captured_pieces})

@app.route('/restart', methods=['POST'])
def restart():
    data = request.json
    game_id = data.get('game_id')
    game = games.get(game_id)
    if not game:
        return jsonify({'error': 'Game not found'}), 404

    game.restart_game()
    return jsonify({'status': 'success', 'message': 'Game restarted'})

@app.route('/undo', methods=['POST'])
def undo():
    data = request.json
    game_id = data.get('game_id')
    game = games.get(game_id)
    if not game:
        return jsonify({'error': 'Game not found'}), 404
    # print(game.board)
    success = game.undo_move()
    # print(game.board)
    if success:
        return jsonify({'status': 'success', 'message': 'Move undone', 'board': game.board, 'turn': game.turn})
    else:
        return jsonify({'status': 'error', 'message': 'No moves to undo'})

@app.route('/bot_move', methods=['POST'])
def bot_move():
    data = request.json
    game_id = data['game_id']

    game = games.get(game_id)
    if not game:
        return jsonify({'error': 'Game not found'}), 404

    if game.game_over:
        return jsonify({
            'status': 'game over',
            'board': game.get_board(),
            'turn': game.turn,
            'game_over': game.game_over,
            'winner': game.winner,
            'captured':game.captured_pieces
        })

    # Simulate bot move (implement bot logic here)
    move= get_bot_move(game)  # You need to define this method
    bot_start, bot_end =move['start'],move['end']
    move_result = game.make_move(bot_start, bot_end)

    if move_result:
        return jsonify({
            'status': 'move made',
            'board': game.get_board(),
            'turn': game.turn,
            'game_over': game.game_over,
            'winner': game.winner,
            'captured':game.captured_pieces
        })
    else:
        return jsonify({
            'status': 'bot move invalid',
            'board': game.get_board(),
            'turn': game.turn
        })

# def get_bot_move(game):
#     """
#     Generate a move for the bot.
#     This simple implementation randomly selects a legal move.
#     """

#     all_legal_moves = []

#     for row in range(8):
#         for col in range(8):
#             piece = game.board[row][col]
#             if piece and piece.startswith(game.turn):  # Check if the piece belongs to the current player (bot)
#                 legal_moves = game.get_legal_moves(row, col)
#                 if legal_moves:
#                     for move in legal_moves:
#                         all_legal_moves.append(((row, col), move))

#     if not all_legal_moves:
#         return None, None  # No legal moves available, should not happen in a valid game state

#     selected_move = random.choice(all_legal_moves)
#     start_pos, end_pos = selected_move

#     return start_pos, end_pos
def evaluate_board(board, color):
    # Basic evaluation function based on piece values
    piece_values = {'pawn': 1, 'knight': 3, 'bishop': 3, 'rook': 5, 'queen': 9, 'king': 0}
    value = 0
    for row in board:
        for cell in row:
            if color in cell:
                piece_type = cell.split(' ')[1]
                value += piece_values.get(piece_type, 0)
            elif cell and color not in cell:
                piece_type = cell.split(' ')[1]
                value -= piece_values.get(piece_type, 0)
    return value

def minimax(game, depth, is_maximizing, alpha, beta):
    if depth == 0 or game.game_over:
        return evaluate_board(game.get_board(), game.turn)

    if is_maximizing:
        max_eval = float('-inf')
        for move in get_all_possible_moves(game, game.turn):
            game_copy = copy.deepcopy(game)
            game_copy.make_move(move['start'], move['end'])
            eval = minimax(game_copy, depth - 1, False, alpha, beta)
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for move in get_all_possible_moves(game, 'black' if game.turn == 'white' else 'white'):
            game_copy = copy.deepcopy(game)
            game_copy.make_move(move['start'], move['end'])
            eval = minimax(game_copy, depth - 1, True, alpha, beta)
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval

def get_best_move(game, depth):
    best_move = None
    best_value = float('-inf')
    for move in get_all_possible_moves(game, game.turn):
        game_copy = copy.deepcopy(game)
        game_copy.make_move(move['start'], move['end'])
        move_value = minimax(game_copy, depth - 1, False, float('-inf'), float('inf'))
        if move_value > best_value:
            best_value = move_value
            best_move = move
    return best_move

def get_all_possible_moves(game, color):
    moves = []
    for row in range(8):
        for col in range(8):
            if color in game.get_board()[row][col]:
                legal_moves = game.get_legal_moves(row, col)
                for move in legal_moves:
                    moves.append({'start': [row, col], 'end': move})
    return moves

def get_bot_move(game):
    # Use a depth of 3 for the minimax algorithm
    best_move = get_best_move(game, depth=3)
    return best_move


if __name__ == '__main__':
    app.run(debug=True)

