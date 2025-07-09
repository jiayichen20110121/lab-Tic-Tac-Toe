from tic_tac_toe_board import TicTacToeBoard

def main():
    board = TicTacToeBoard()
    print("Welcome to Tic-Tac-Toe!")
    player = input("Which player are you? ('x' or 'o'): ").strip().lower()


    print("\nInitial board:")
    board.print_board()

    while board.state == "is_playing":
        print(f"\n{board.player_turn}'s turn")
        index = input("Enter a position (0-8): ")
        
        if not index.isdigit() or not (0 <= int(index) <= 8):
            print("Invalid input. Please choose a number between 0 and 8.")
            continue

        board.make_move(int(index))

    print(f"Game over! {board.state}")

if __name__ == "__main__":
    main()
