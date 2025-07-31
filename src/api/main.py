from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional
import uvicorn
from contextlib import asynccontextmanager

from ..data.data_service import DataService

# Initialize data service
data_service = DataService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    data_service.seed_sample_data()
    yield
    # Shutdown
    data_service.close()

app = FastAPI(
    title="NBA Betting Research API",
    description="API for NBA betting research and analytics",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "NBA Betting Research API", "status": "active"}

@app.get("/api/teams")
async def get_teams():
    """Get all NBA teams"""
    try:
        teams = data_service.get_teams()
        return {"teams": teams}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/players")
async def get_players(team_id: Optional[int] = None):
    """Get players, optionally filtered by team"""
    try:
        players = data_service.get_players(team_id)
        return {"players": players}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/games/recent")
async def get_recent_games(limit: int = 10):
    """Get recent games"""
    try:
        games = data_service.get_recent_games(limit)
        return {"games": games}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/players/{player_id}/stats")
async def get_player_stats(player_id: int):
    """Get player statistics"""
    try:
        stats = data_service.get_player_stats(player_id)
        if not stats:
            raise HTTPException(status_code=404, detail="Player not found")
        return {"stats": stats}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/games/{game_id}/odds")
async def get_odds_comparison(game_id: int):
    """Get odds comparison for a specific game"""
    try:
        odds = data_service.get_odds_comparison(game_id)
        return {"odds": odds}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/players/{player_id}/insights")
async def get_betting_insights(player_id: int):
    """Get betting insights for a player"""
    try:
        insights = data_service.get_betting_insights(player_id)
        return {"insights": insights}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "NBA Betting Research API"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
