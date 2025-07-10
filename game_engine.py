import argparse
from tic_tac_toe_board import TicTacToeBoard

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--game-id",   required=True, help="Unique ID for the shared game")
    parser.add_argument("--player",    required=True, choices=["x","o"], help="Your player symbol")
    parser.add_argument("--reset",     action="store_true", help="Reset board to fresh state and exit")
    args = parser.parse_args()

    # Part A: Reset if requested
    board = TicTacToeBoard(game_id=args.game_id)
    if args.reset:
        board.reset()
        print(f"Game {args.game_id!r} has been reset.")
        return

    # Part B: Load existing state
    try:
        board = TicTacToeBoard.load_from_redis(args.game_id)
    except ValueError:
        print("No existing game; resetting.")
        board.reset()

    # Show current board
    print("\nCurrent board:")
    board.print_board()
    print(f"Status: {board.state}\n")

    # If game still in play, let this player make one move
    if board.state == "is_playing":
        if not board.is_my_turn(args.player):
            print("→ It's not your turn yet.")
            return

        idx = input(f"{args.player}'s move (0-8): ").strip()
        if not idx.isdigit():
            print("Invalid input.")
            return

        board.make_move(int(idx), args.player)
    else:
        print("→ Game already finished.")

if __name__=="__main__":
    main()
