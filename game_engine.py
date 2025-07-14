# game_engine.py

import asyncio
import argparse
import json

import httpx
import redis.asyncio as aioredis

# Redis Pub/Sub setup (only for notifications)
REDIS_HOST = "ai.thewcl.com"
REDIS_PORT = 6379
REDIS_PASSWORD = "atmega328"
CHANNEL = "ttt_game_state_changed:{game_id}"

redis_client = aioredis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    decode_responses=True
)

# HTTP API base
API_BASE_URL = "http://localhost:8000"

async def get_state(game_id: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{API_BASE_URL}/state", params={"game_id": game_id})
        resp.raise_for_status()
        return resp.json()

async def post_move(game_id: str, player: str, index: int) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{API_BASE_URL}/move",
            params={"game_id": game_id},
            json={"player": player, "index": index}
        )
        if resp.status_code == 200:
            return resp.json()
        else:
            # FastAPI returns {"detail": "..."} on error
            detail = resp.json().get("detail", resp.text)
            return {"success": False, "message": detail}

async def post_reset(game_id: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{API_BASE_URL}/reset", params={"game_id": game_id})
        resp.raise_for_status()
        return resp.json()

async def handle_state(game_id: str, player: str):
    # 1) Fetch current state
    state = await get_state(game_id)
    print(json.dumps(state, indent=2))
    print("Status:", state["state"])

    # 2) If game over or not your turn, skip move prompt
    if state["state"] != "is_playing":
        return
    if state["player_turn"] != player:
        print("⏳ Waiting for opponent…")
        return

    # 3) It's your turn: prompt and POST /move
    idx = input(f"{player}'s move (0-8): ").strip()
    if not idx.isdigit():
        print("Invalid input.")
        return

    result = await post_move(game_id, player, int(idx))
    print(result.get("message", ""))

    # 4) On success, publish notification so opponent wakes up
    if result.get("success"):
        await redis_client.publish(CHANNEL.format(game_id=game_id), "updated")

async def listen_updates(game_id: str, player: str):
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(CHANNEL.format(game_id=game_id))
    print(f"Subscribed as {player!r} to game {game_id!r}\n")

    # Initial display/prompt
    await handle_state(game_id, player)

    # React to any pub/sub messages
    async for msg in pubsub.listen():
        if msg["type"] == "message":
            print("\nUpdate received")
            await handle_state(game_id, player)

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--game-id", required=True, help="Shared game ID")
    parser.add_argument("--player", required=True, choices=["x", "o"], help="Your symbol")
    parser.add_argument("--reset", action="store_true", help="Reset board and exit")
    args = parser.parse_args()

    if args.reset:
        result = await post_reset(args.game_id)
        print(result.get("message"))
        return

    # Ensure game exists on server
    try:
        await get_state(args.game_id)
    except httpx.HTTPStatusError:
        result = await post_reset(args.game_id)
        print(result.get("message"))

    # Enter Pub/Sub-driven loop
    await listen_updates(args.game_id, args.player)

if __name__ == "__main__":
    asyncio.run(main())
