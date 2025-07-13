from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from tic_tac_toe_board import TicTacToeBoard

# Initialize FastAPI app
app = FastAPI()

# Define the request body for the /move endpoint
class MoveRequest(BaseModel):
    player: str
    index: int

# Endpoint to get the current board state
@app.get("/state")
async def get_game_state(game_id: str):
    """Returns the current board and game status."""
    try:
        board = TicTacToeBoard.load_from_redis(game_id)
        return board.to_dict()
    except ValueError:
        raise HTTPException(status_code=404, detail="Game not found")

# Endpoint to make a move
@app.post("/move")
async def make_move(game_id: str, move: MoveRequest):
    """Accepts a player and index, updates the board if valid."""
    try:
        board = TicTacToeBoard.load_from_redis(game_id)
        result = board.make_move(move.player, move.index)
        if result["success"]:
            # You can add code here to publish to Redis if needed (for real-time updates)
            return result
        else:
            raise HTTPException(status_code=400, detail=result["message"])
    except ValueError:
        raise HTTPException(status_code=404, detail="Game not found")
    

# Endpoint to reset the board
@app.post("/reset")
async def reset_game(game_id: str):
    """Resets the board and creates a new game."""
    try:
        board = TicTacToeBoard(game_id=game_id)
        result = board.reset()
        return result
    except ValueError:
        raise HTTPException(status_code=400, detail="Error resetting the game")
