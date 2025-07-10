# game_engine.py

import asyncio
import argparse
import json
import redis.asyncio as aioredis
from tic_tac_toe_board import TicTacToeBoard

# Async Redis + Pub/Sub setup
REDIS_HOST = "ai.thewcl.com"
REDIS_PORT = 6379
REDIS_PASSWORD = "atmega328"
redis_client = aioredis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    decode_responses=True
)
CHANNEL = "ttt_game_state_changed:{game_id}"

async def handle_state(game_id: str, player: str):
    """Load state, display it, then if your turn prompt and publish."""
    board = TicTacToeBoard.load_from_redis(game_id)

    # 1) Show structured board JSON
    print(json.dumps(board.to_dict(), indent=2))
    print("Status:", board.state)

    # 2) If game over or not your turn, do nothing further
    if board.state != "is_playing":
        return
    if not board.is_my_turn(player):
        print("⏳ Waiting for opponent…")
        return

    # 3) It's your turn
    idx = input(f"{player}'s move (0-8): ").strip()
    if not idx.isdigit():
        print("Invalid input.")
        return

    result = board.make_move(player, int(idx))
    print(result["message"])

    # 4) If move succeeded, notify opponent
    if result["success"]:
        await redis_client.publish(CHANNEL.format(game_id=game_id), "updated")

async def listen_updates(game_id: str, player: str):
    sub = redis_client.pubsub()
    await sub.subscribe(CHANNEL.format(game_id=game_id))
    print(f"Subscribed as {player!r} to game {game_id!r}")

    # Initial fetch & possible move
    await handle_state(game_id, player)

    # React to pub/sub notifications
    async for msg in sub.listen():
        if msg["type"] == "message":
            print("Update received")
            await handle_state(game_id, player)

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--game-id", required=True, help="Shared game ID")
    parser.add_argument("--player",  required=True, choices=["x","o"], help="Your symbol")
    parser.add_argument("--reset",   action="store_true", help="Reset board and exit")
    args = parser.parse_args()

    if args.reset:
        res = TicTacToeBoard(game_id=args.game_id).reset()
        print(res["message"])
        return

    # Ensure there is a board in Redis
    try:
        TicTacToeBoard.load_from_redis(args.game_id)
    except ValueError:
        TicTacToeBoard(game_id=args.game_id).reset()

    # Start reactive loop
    await listen_updates(args.game_id, args.player)

if __name__ == "__main__":
    asyncio.run(main())
