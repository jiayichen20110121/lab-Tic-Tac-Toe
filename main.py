from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from tic_tac_toe_board import TicTacToeBoard

app = FastAPI()

# Store WebSocket clients per game_id
class MoveRequest(BaseModel):
    player: str
    index: int



@app.get("/state")
async def get_game_state(game_id: str = Query(...)):
    """Return current board state from Redis."""
    try:
        board = TicTacToeBoard.load_from_redis(game_id)
        return JSONResponse(board.to_dict())
    except ValueError:
        raise HTTPException(status_code=404, detail="Game not found")


@app.post("/move")
async def make_move(game_id: str = Query(...), move: MoveRequest = None):
    """Process a move, update state, and broadcast to clients."""
    if move is None:
        raise HTTPException(status_code=400, detail="Missing move payload")

    try:
        board = TicTacToeBoard.load_from_redis(game_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Game not found")

    result = board.make_move(move.player, move.index)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return JSONResponse(result)


@app.post("/reset")
async def reset_game(game_id: str = Query(...)):
    """Reset the board and notify all WebSocket clients."""
    board = TicTacToeBoard(game_id=game_id)
    result = board.reset()
    return JSONResponse(result)
