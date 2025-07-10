# tic_tac_toe_board.py

import json
import redis
from dataclasses import dataclass, field

# Redis configuration (unchanged, sync client)
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
    state: str = "is_playing"
    player_turn: str = "x"
    positions: list = field(default_factory=lambda: [""] * 9)

    def serialize(self) -> str:
        return json.dumps({
            "game_id": self.game_id,
            "state": self.state,
            "player_turn": self.player_turn,
            "positions": self.positions
        })

    def save_to_redis(self):
        key = REDIS_KEY.format(game_id=self.game_id)
        r.set(key, self.serialize())

    @classmethod
    def load_from_redis(cls, game_id: str):
        key = REDIS_KEY.format(game_id=game_id)
        data_json = r.get(key)
        if data_json is None:
            raise ValueError(f"No game found for {game_id!r}")
        data = json.loads(data_json)
        return cls(**data)

    def reset(self):
        self.state = "is_playing"
        self.player_turn = "x"
        self.positions = [""] * 9
        self.save_to_redis()

    def is_my_turn(self, i_am: str) -> bool:
        return self.state == "is_playing" and self.player_turn == i_am

    def make_move(self, index: int, i_am: str):
        if not self.is_my_turn(i_am):
            print(f"Not your turn ({i_am}), or game over.")
            return

        if not (0 <= index < 9):
            print("Invalid index. Choose 0–8.")
            return

        if self.positions[index]:
            print(f"Position {index} already taken.")
            return

        self.positions[index] = i_am
        if self.check_winner():
            self.state = f"{i_am} wins!"
        elif self.check_draw():
            self.state = "draw"
        else:
            self.player_turn = "o" if i_am == "x" else "x"

        self.save_to_redis()
        self.print_board()
        print("→", self.state)

    def check_winner(self) -> bool:
        wins = [
            (0,1,2),(3,4,5),(6,7,8),
            (0,3,6),(1,4,7),(2,5,8),
            (0,4,8),(2,4,6)
        ]
        return any(self.positions[a]==self.positions[b]==self.positions[c]!="" 
                   for a,b,c in wins)

    def check_draw(self) -> bool:
        return all(p!="" for p in self.positions) and self.state=="is_playing"

    def print_board(self):
        for i in range(0,9,3):
            row = " | ".join(self.positions[i+j] or str(i+j) for j in range(3))
            print(f" {row} ")
            if i<6:
                print("-----------")
