from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import asyncio

router = APIRouter()

class DeployRequest(BaseModel):
    strategy: str
    riskProfile: str
    capital: float
    asset: str
    customSL: str | None = None
    customTP: str | None = None

# Mock storage for active bots
active_bots = [
    {
        "id": 1,
        "strategy": "trend",
        "risk": "medium",
        "capital": 100000,
        "asset": "NIFTY 50",
        "status": "RUNNING",
        "pnl": 1250.0
    },
    {
        "id": 2,
        "strategy": "reversion",
        "risk": "low",
        "capital": 50000,
        "asset": "BANKNIFTY",
        "status": "PAUSED",
        "pnl": -450.0
    }
]

@router.post("/deploy")
async def deploy_strategy(request: DeployRequest):
    """
    Deploys a new trading bot with the specified configuration.
    """
    bot_id = len(active_bots) + 1
    
    bot_config = {
        "id": bot_id,
        "strategy": request.strategy,
        "risk": request.riskProfile,
        "capital": request.capital,
        "asset": request.asset,
        "sl": request.customSL,
        "tp": request.customTP,
        "status": "RUNNING",
        "pnl": 0.0
    }
    
    active_bots.append(bot_config)
    
    # In a real app, we would start a background task here
    # asyncio.create_task(run_bot(bot_config))
    
    return {"status": "success", "message": "Bot deployed successfully", "bot_id": bot_id}

@router.get("/")
def get_active_strategies():
    return active_bots
