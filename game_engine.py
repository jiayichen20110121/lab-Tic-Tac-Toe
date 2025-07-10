# game_engine.py

import asyncio
import argparse
import redis.asyncio as aioredis
from tic_tac_toe_board import TicTacToeBoard

# Async Redis client + Pub/Sub channel
REDIS_HOST = "ai.thewcl.com"
REDIS_PORT = 6379
REDIS_PASSWORD = "atmega328"
pubsub_client = aioredis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    decode_responses=True
)
CHANNEL = "ttt_game_state_changed:{game_id}"

async def handle_board_state(game_id: str, player: str):
    """Load board, prompt if it's your turn, make move + publish."""
    board = TicTacToeBoard.load_from_redis(game_id)
    print("\nCurrent board:")
    board.print_board()
    print("Status:", board.state)

    if board.state != "is_playing":
        return  # game over

    if not board.is_my_turn(player):
        print("⏳ Waiting for opponent...")
        return

    idx = input(f"{player}'s move (0-8): ").strip()
    if not idx.isdigit():
        print("Invalid input.")
        return

    board.make_move(int(idx), player)
    # Publish an update so the other subscriber wakes up:
    await pubsub_client.publish(CHANNEL.format(game_id=game_id), "updated")

async def listen_for_updates(game_id: str, player: str):
    """Subscribe to the channel and react to updates."""
    sub = pubsub_client.pubsub()
    await sub.subscribe(CHANNEL.format(game_id=game_id))
    print(f"Subscribed to game {game_id!r} as player {player!r}.\n")

    # Fire once immediately to show the initial state / maybe move
    await handle_board_state(game_id, player)

    async for msg in sub.listen():
        if msg["type"] == "message":
            # Another player moved
            await handle_board_state(game_id, player)

async def main():
    p = argparse.ArgumentParser()
    p.add_argument("--game-id", required=True, help="Shared game ID")
    p.add_argument("--player",  required=True, choices=["x","o"], help="Your symbol")
    p.add_argument("--reset",   action="store_true", help="Reset board then exit")
    args = p.parse_args()

    if args.reset:
        board = TicTacToeBoard(game_id=args.game_id)
        board.reset()
        print(f"Game {args.game_id!r} reset.")
        return

    # Ensure there's a board in Redis
    try:
        TicTacToeBoard.load_from_redis(args.game_id)
    except ValueError:
        print("No existing game; initializing a fresh board.")
        TicTacToeBoard(game_id=args.game_id).reset()

    # Start Pub/Sub loop
    await listen_for_updates(args.game_id, args.player)

if __name__ == "__main__":
    asyncio.run(main())
