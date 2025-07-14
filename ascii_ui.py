#!/usr/bin/env python3
import argparse
import asyncio
import json
import os
import sys

import websockets

# Replace xx with your student number (00–15)
WEBSOCKET_URL = "ws://ai.thewcl.com:8709"


def clear_screen():
    """Clear the terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


def render_board(positions):
    """
    Draw the 3×3 board.
    positions: list of length 9, each "" or "x"/"o" (any case).
    Empty slots show their index; occupied show X or O.
    """
    # Normalize to uppercase or index string
    cells = [
        (pos.upper() if isinstance(pos, str) and pos.lower() in ("x", "o") else str(i))
        for i, pos in enumerate(positions)
    ]

    # Build rows
    lines = []
    for row in range(3):
        start = row * 3
        lines.append(f" {cells[start]} | {cells[start+1]} | {cells[start+2]} ")
        if row < 2:
            lines.append("---+---+---")

    # Print
    clear_screen()
    print("\n".join(lines))


async def listen_for_updates(game_id: str):
    """Connect via WebSocket and redraw on each message."""
    try:
        async with websockets.connect(WEBSOCKET_URL) as ws:
            print(f"Connected to {WEBSOCKET_URL}. Waiting for game updates...")
            async for raw in ws:
                try:
                    data = json.loads(raw)
                    positions = data["board"]["positions"]
                    if not isinstance(positions, list) or len(positions) != 9:
                        print("⚠️  Received invalid board data:", data)
                        continue
                    render_board(positions)
                except json.JSONDecodeError:
                    print("⚠️  Received non-JSON message:", raw)
    except Exception as e:
        print(f"Connection error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--game-id", required=True, help="Shared game ID to subscribe to")
    args = parser.parse_args()
    try:
        asyncio.run(listen_for_updates(args.game_id))
    except KeyboardInterrupt:
        print("\nExiting.")
