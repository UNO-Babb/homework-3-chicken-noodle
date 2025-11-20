import random
from flask import Flask, session, redirect, url_for, request, render_template

app = Flask(__name__)
app.secret_key = "change_this_to_a_random_secret_key"

BOARD_SIZE = 9
TARGET_SCORE = 45
MAX_GUESSES = 25


def new_game():
    home_row = random.randint(1, BOARD_SIZE - 2)
    home_col = random.randint(1, BOARD_SIZE - 2)
    home = (home_row, home_col)

    fence = set()
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            fence.add((home_row + dr, home_col + dc))

    def not_adjacent_to_home(r, c):
        return abs(r - home_row) > 1 or abs(c - home_col) > 1

    all_coords = [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE)]
    stronghold_candidates = [
        (r, c)
        for (r, c) in all_coords
        if (r, c) != home and (r, c) not in fence and not_adjacent_to_home(r, c)
    ]
    strongholds = set(random.sample(stronghold_candidates, 3))

    trap_candidates = [
        (r, c)
        for (r, c) in all_coords
        if (r, c) != home
        and (r, c) not in fence
        and (r, c) not in strongholds
        and not_adjacent_to_home(r, c)
    ]
    trap = random.choice(trap_candidates)

    board = []
    for r in range(BOARD_SIZE):
        row = []
        for c in range(BOARD_SIZE):
            if (r, c) == home:
                row.append("H")
            elif (r, c) in fence:
                row.append("F")
            elif (r, c) in strongholds:
                row.append("S")
            elif (r, c) == trap:
                row.append("T")
            else:
                row.append("L")
        board.append(row)

    session["board"] = board
    session["revealed"] = []
    session["score"] = 0
    session["remaining"] = MAX_GUESSES
    session["game_over"] = False
    session["result"] = None


def get_game_state():
    if "board" not in session:
        new_game()
    return (
        session["board"],
        set(session.get("revealed", [])),
        session["score"],
        session["remaining"],
        session.get("game_over", False),
        session.get("result", None),
    )


def handle_click(row, col):
    board, revealed, score, remaining, game_over, result = get_game_state()

    if game_over or remaining <= 0:
        return

    key = f"{row},{col}"
    if key in revealed:
        return

    revealed.add(key)
    tile_type = board[row][col]
    remaining -= 1

    if tile_type == "H":
        score += 45
        game_over = True
        result = "win"
    elif tile_type == "F":
        score += 3
    elif tile_type == "S":
        score += 12
    elif tile_type == "T":
        game_over = True
        result = "lose"

    if not game_over:
        if score >= TARGET_SCORE:
            game_over = True
            result = "win"
        elif remaining <= 0:
            game_over = True
            result = "lose"

    session["revealed"] = list(revealed)
    session["score"] = score
    session["remaining"] = remaining
    session["game_over"] = game_over
    session["result"] = result


@app.route("/", methods=["GET"])
def index():
    board, revealed, score, remaining, game_over, result = get_game_state()
    return render_template(
        "template.html",
        board=board,
        revealed=revealed,
        score=score,
        remaining=remaining,
        game_over=game_over,
        result=result,
        board_size=BOARD_SIZE,
        target_score=TARGET_SCORE,
        max_guesses=MAX_GUESSES,
    )


@app.route("/click", methods=["POST"])
def click():
    cell = request.form.get("cell")
    if cell:
        try:
            r_str, c_str = cell.split(",")
            row = int(r_str)
            col = int(c_str)
            if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
                handle_click(row, col)
        except ValueError:
            pass
    return redirect(url_for("index"))


@app.route("/reset", methods=["POST"])
def reset():
    session.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
