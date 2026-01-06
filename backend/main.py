from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from app.api.strategies import router as strategies_router
from app.api.auth import router as auth_router
from app.api.market_data import router as market_data_router
from app.api.orders import router as orders_router
from app.api.indicators import router as indicators_router
from app.api.price_action import router as price_action_router
from app.api.live_data import router as live_data_router
from app.api.portfolio import router as portfolio_router
from app.api.trading_bot import router as trading_bot_router
from app.api.paper_trading import router as paper_trading_router
from app.api.backtesting import router as backtesting_router
from app.services.market_hours import market_hours
from app.services.tick_processor import tick_processor
from app.services.kite_auth import kite_auth_service
import asyncio
import os

load_dotenv()


# ==================== LIFESPAN EVENTS ====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler - runs on startup and shutdown
    Auto-starts tick streaming when markets are open
    """
    print("\n" + "="*60)
    print("🚀 SMART ALGO TRADE - BACKEND STARTING")
    print("="*60)
    
    # Startup
    market_status = market_hours.get_market_status()
    print(f"\n📊 Market Status: {market_status['status']} ({market_status['session']})")
    print(f"⏰ Current Time (IST): {market_status['current_time']}")
    
    # Auto-start tick streaming if authenticated and market is open/pre-open
    if kite_auth_service.is_authenticated() and market_hours.should_stream_data():
        print(f"\n✅ Markets are {market_status['status']} - Auto-starting tick streaming...")
        
        # Key indexes to monitor
        default_symbols = [
            "NIFTY 50",
            "NIFTY BANK", 
            "NIFTY IT",
            "NIFTY MIDCAP 50",
            "SENSEX"
        ]
        
        try:
            # Start tick processor in background task
            asyncio.create_task(start_tick_streaming(default_symbols))
            print("✓ Tick streaming scheduled to start")
        except Exception as e:
            print(f"⚠️  Failed to auto-start tick streaming: {e}")
    else:
        if not kite_auth_service.is_authenticated():
            print("\n⚠️  Not authenticated - Tick streaming will start after login")
        else:
            print(f"\n💤 Markets are {market_status['status']} - Tick streaming on standby")
            if "next_open" in market_status:
                print(f"   Next market open: {market_status['next_open']}")
    
    print("\n" + "="*60)
    print("✅ BACKEND READY")
    print("="*60 + "\n")
    
    yield  # Server is running
    
    # Shutdown
    print("\n🛑 Shutting down...")
    if tick_processor.is_running:
        tick_processor.stop()
    print("✅ Shutdown complete\n")


async def start_tick_streaming(symbols: list):
    """Background task to start tick streaming"""
    await asyncio.sleep(2)  # Give server time to fully start
    try:
        tick_processor.start(symbols=symbols, exchange="NSE", mode="full")
    except Exception as e:
        print(f"❌ Tick streaming error: {e}")


app = FastAPI(
    title="Smart Algo Trade",
    version="2.0.0",
    description="Production-ready algorithmic trading system using Kite Connect API",
    lifespan=lifespan
)

# CORS Setup
origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Configure via environment variable
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "status": "ok",
        "message": "Smart Algo Trade Backend Running",
        "version": "2.0.0",
        "modules": ["auth", "market_data", "orders", "indicators", "price_action", "live_data", "strategies", "portfolio"]
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Register routers
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(market_data_router, prefix="/api/market", tags=["Market Data"])
app.include_router(orders_router, prefix="/api/orders", tags=["Orders"])
app.include_router(indicators_router, prefix="/api/indicators", tags=["Technical Indicators"])
app.include_router(price_action_router, prefix="/api/price-action", tags=["Price Action & Patterns"])
app.include_router(live_data_router, prefix="/api/live", tags=["Live Data & WebSocket"])
app.include_router(strategies_router, prefix="/api/strategies", tags=["Strategies"])
app.include_router(portfolio_router, prefix="/api/portfolio", tags=["Portfolio & Account"])
app.include_router(trading_bot_router, prefix="/api/bot", tags=["Trading Bot"])
app.include_router(paper_trading_router, prefix="/api/paper-trading", tags=["Paper Trading"])
app.include_router(backtesting_router, tags=["Backtesting"])

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "False").lower() == "true"
    workers = int(os.getenv("WORKERS", "1"))
    
    uvicorn.run(
        "main:app", 
        host=host, 
        port=port, 
        reload=reload,
        workers=workers if not reload else 1
    )

