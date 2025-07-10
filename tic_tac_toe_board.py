# tic_tac_toe_board.py

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
    game_id: str
    state: str = "is_playing"      # "is_playing", "x wins!", "o wins!", or "draw"
    player_turn: str = "x"         # "x" or "o"
    positions: list = field(default_factory=lambda: [""] * 9)

    def to_dict(self) -> dict:
        """
        Structured board state for clients, numbering empty spots 0–8.
        """
        return {
            "game_id":     self.game_id,
            "state":       self.state,
            "player_turn": self.player_turn,
            "positions": [
                pos if pos != "" else str(i)
                for i, pos in enumerate(self.positions)
            ]
        }

    def serialize(self) -> str:
        """
        Persist raw state to Redis: empty slots remain "".
        """
        return json.dumps({
            "game_id":     self.game_id,
            "state":       self.state,
            "player_turn": self.player_turn,
            "positions":   self.positions
        })

    @classmethod
    def load_from_redis(cls, game_id: str):
        """Load raw JSON from Redis and reconstruct the board."""
        key = REDIS_KEY.format(game_id=game_id)
        data_json = r.get(key)
        if data_json is None:
            raise ValueError(f"No game found in Redis for game_id={game_id!r}")
        data = json.loads(data_json)
        return cls(**data)

    def save_to_redis(self):
        """Save raw JSON to Redis."""
        key = REDIS_KEY.format(game_id=self.game_id)
        r.set(key, self.serialize())

    def reset(self) -> dict:
        """Reset to fresh state and persist."""
        self.state = "is_playing"
        self.player_turn = "x"
        self.positions = [""] * 9
        self.save_to_redis()
        return {
            "success": True,
            "message": f"Game {self.game_id!r} reset.",
            "board": self.to_dict()
        }

    def is_my_turn(self, player: str) -> bool:
        return self.state == "is_playing" and self.player_turn == player

    def make_move(self, player: str, index: int) -> dict:
        """
        Place `player` at `index`. Returns structured response.
        """
        if not self.is_my_turn(player):
            return {"success": False, "message": "Not your turn or game over."}

        if not (0 <= index < 9):
            return {"success": False, "message": "Index must be between 0 and 8."}

        if self.positions[index]:
            return {"success": False, "message": f"Position {index} already taken."}

        # Apply move
        self.positions[index] = player

        # Check for win or draw
        if self._check_winner():
            self.state = f"{player} wins!"
        elif self._check_draw():
            self.state = "draw"
        else:
            self.player_turn = "o" if player == "x" else "x"

        # Persist raw state
        self.save_to_redis()

        return {
            "success": True,
            "message": f"Move accepted: {player} → {index}",
            "board": self.to_dict(),
            "state": self.state
        }

    def _check_winner(self) -> bool:
        wins = [
            (0,1,2),(3,4,5),(6,7,8),
            (0,3,6),(1,4,7),(2,5,8),
            (0,4,8),(2,4,6)
        ]
        return any(
            self.positions[a] == self.positions[b] == self.positions[c] != ""
            for a, b, c in wins
        )

    def _check_draw(self) -> bool:
        return all(p != "" for p in self.positions) and self.state == "is_playing"
