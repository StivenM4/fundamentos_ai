"""Práctica de referencia de Minimax sobre tres en línea."""

WIN_LINES = (
    (0, 1, 2),
    (3, 4, 5),
    (6, 7, 8),
    (0, 3, 6),
    (1, 4, 7),
    (2, 5, 8),
    (0, 4, 8),
    (2, 4, 6),
)

REFERENCE_BOARD = ["X", "O", "X", "O", "X", " ", " ", " ", "O"]
BLOCKING_BOARD = ["X", " ", " ", "O", "O", " ", " ", " ", "X"]


def winner(board):
    for a, b, c in WIN_LINES:
        if board[a] == board[b] == board[c] and board[a] != " ":
            return board[a]
    return None


def minimax(board, maximizing, counter=None):
    if counter is not None:
        counter["states"] += 1
    result = winner(board)
    if result == "X":
        return 1
    if result == "O":
        return -1
    if " " not in board:
        return 0

    scores = []
    mark = "X" if maximizing else "O"
    for index, cell in enumerate(board):
        if cell == " ":
            nxt = board.copy()
            nxt[index] = mark
            scores.append(minimax(nxt, not maximizing, counter))
    return max(scores) if maximizing else min(scores)


def move_scores(board, counter=None):
    """Calcula la utilidad que Minimax asigna a cada jugada de X."""

    choices = {}
    for index, cell in enumerate(board):
        if cell == " ":
            nxt = board.copy()
            nxt[index] = "X"
            choices[index] = minimax(nxt, False, counter)
    return choices


def best_move(board):
    choices = [(score, index) for index, score in move_scores(board).items()]
    return max(choices)[1]


def run_case(name, board):
    """Muestra utilidades, decisión y estados evaluados para un tablero."""

    counter = {"states": 0}
    scores = move_scores(board, counter)
    move = max((score, index) for index, score in scores.items())[1]
    print(name)
    print("Tablero:", board)
    print("Utilidad por posición:", scores)
    print("Mejor posición para X:", move)
    print("Estados evaluados:", counter["states"])
    print()
    return move, scores, counter["states"]


if __name__ == "__main__":
    run_case("Caso 1 - jugada ganadora", REFERENCE_BOARD)
    run_case("Caso 2 - bloqueo obligatorio", BLOCKING_BOARD)
