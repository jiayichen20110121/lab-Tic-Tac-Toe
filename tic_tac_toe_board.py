import json
import redis
from dataclasses import dataclass, field

# Redis configuration
REDIS_HOST = "ai.thewcl.com"
REDIS_PORT = 6379
REDIS_PASSWORD = "atmega328"
r = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    decode_responses=True
)

# Redis key template
REDIS_KEY = "tic_tac_toe:game_state:{game_id}"

@dataclass
class TicTacToeBoard:
    game_id: str                   # Unique identifier for this game in Redis
    state: str = "is_playing"      # "is_playing", "x wins!", "o wins!", or "draw"
    player_turn: str = "x"         # Whose turn it is: "x" or "o"
    positions: list = field(default_factory=lambda: [""] * 9)

    def serialize(self) -> str:
        """Convert the board to a JSON string."""
        return json.dumps({
            "game_id": self.game_id,
            "state": self.state,
            "player_turn": self.player_turn,
            "positions": self.positions
        })

    def save_to_redis(self):
        """Save current board state to Redis."""
        key = REDIS_KEY.format(game_id=self.game_id)
        r.set(key, self.serialize())

    @classmethod
    def load_from_redis(cls, game_id: str):
        """Load board JSON from Redis and return a TicTacToeBoard."""
        key = REDIS_KEY.format(game_id=game_id)
        data_json = r.get(key)
        if data_json is None:
            raise ValueError(f"No game found in Redis for game_id={game_id!r}")
        data = json.loads(data_json)
        return cls(**data)

    def reset(self):
        """Reset the board to initial state and save to Redis."""
        self.state = "is_playing"
        self.player_turn = "x"
        self.positions = [""] * 9
        self.save_to_redis()

    def is_my_turn(self, i_am: str) -> bool:
        """Return True only if game is still playing and it's this player's turn."""
        return self.state == "is_playing" and self.player_turn == i_am

    def make_move(self, index: int, i_am: str):
        """Attempt a move for player `i_am` at position `index`."""
        if not self.is_my_turn(i_am):
            print(f"Not your turn ({i_am}), or game is over.")
            return

        if not (0 <= index < 9):
            print("Invalid index. Choose a number between 0 and 8.")
            return

        if self.positions[index]:
            print(f"Position {index} already taken.")
            return

        # Place the move
        self.positions[index] = i_am

        # Check for win
        if self.check_winner():
            self.state = f"{i_am} wins!"
        # Check for draw
        elif self.check_draw():
            self.state = "draw"
        else:
            # Switch turn
            self.player_turn = "o" if i_am == "x" else "x"

        # Persist and display
        self.save_to_redis()
        self.print_board()
        print("→", self.state)

    def check_winner(self) -> bool:
        """Check all win conditions."""
        wins = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8),  # columns
            (0, 4, 8), (2, 4, 6)              # diagonals
        ]
        for a, b, c in wins:
            if self.positions[a] == self.positions[b] == self.positions[c] != "":
                return True
        return False

    def check_draw(self) -> bool:
        """Return True if board is full and no winner."""
        return all(pos != "" for pos in self.positions) and self.state == "is_playing"

    def print_board(self):
        """Print the board, showing indexes for empty spots."""
        for i in range(0, 9, 3):
            row = ""
            for j in range(3):
                pos = self.positions[i + j] or str(i + j)
                row += f" {pos} " + ("|" if j < 2 else "")
            print(row)
            if i < 6:
                print("---------")
