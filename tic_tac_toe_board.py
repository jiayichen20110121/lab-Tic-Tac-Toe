from dataclasses import dataclass, field


@dataclass
class TicTacToeBoard:
    state: str = "is_playing" 
    player_turn: str = "x"
    positions: list = field(default_factory=lambda: [""] * 9)

    def is_my_turn(self, i_am: str) -> bool:

        return self.player_turn == i_am

    def make_move(self, index: int):

        if self.state != "is_playing":
            print("Game over. Cannot make a move.")
            return

        if index < 0 or index > 8:
            print("Invalid index. Choose a number between 0 and 8.")
            return

        if self.positions[index] != "":
            print(f"Position {index} is already taken. Choose another.")
            return

        self.positions[index] = self.player_turn 
        self.print_board()
    
        if self.check_winner():
            self.state = f"{self.player_turn} wins!"
            print(self.state)
        elif self.check_draw():
            self.state = "It's a draw!"
            print(self.state)
        else:
            self.switch_turn()

    def check_winner(self) -> bool:
     
        win_conditions = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),  # Rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8),  # Columns
            (0, 4, 8), (2, 4, 6)               # Diagonals
        ]
        for a, b, c in win_conditions:
            if self.positions[a] == self.positions[b] == self.positions[c] != "":
                return True
        return False

    def check_draw(self) -> bool:

        return all(position != "" for position in self.positions) and self.state == "is_playing"

    def switch_turn(self):
        
        self.player_turn = "o" if self.player_turn == "x" else "x"

    def print_board(self):

        for i in range(0, 9, 3):
            row = ""
            for j in range(3):
                position = self.positions[i + j] if self.positions[i + j] != "" else str(i + j)
                row += f" {position} "
                if j < 2:
                    row += "|"
            print(row)
            if i < 6:
                print("---------")

