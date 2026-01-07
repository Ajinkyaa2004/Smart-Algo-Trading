"""
Seed Trading History Mock Data
Populates MongoDB with sample trades to demonstrate the Trading History feature
"""
import asyncio
import random
from datetime import datetime, timedelta
import os
import sys

# Add the project root to sys.path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.trade_history import trade_history_service
from app.db.mongodb import db

async def seed_data():
    print("🚀 Seeding Mock Trading History Data...")
    
    # Target User ID (should match yours)
    user_id = "PVA995" 
    
    # Connect to DB
    database = db.get_database()
    
    # Clear existing history for clean demo
    await database["trade_history"].delete_many({"user_id": user_id})
    await database["strategy_performance"].delete_many({"user_id": user_id})
    
    symbols = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "SBIN", "BHARTIARTL"]
    strategies = ["ORB_SCALPING", "EMA_BREAKOUT", "RSI_MEAN_REVERSION", "SUPER_TREND", "SMA_CROSSOVER"]
    
    now = datetime.now()
    
    trades_count = 50
    print(f"📈 Generating {trades_count} sample trades...")
    
    for i in range(trades_count):
        # Generate random trade data
        symbol = random.choice(symbols)
        strategy = random.choice(strategies)
        # 60% win rate for demo
        is_win = random.random() < 0.6
        
        entry_price = random.uniform(500, 3000)
        quantity = random.randint(10, 100)
        
        if is_win:
            pnl_pct = random.uniform(0.5, 3.5)
        else:
            pnl_pct = random.uniform(-0.5, -2.5)
            
        pnl = (entry_price * quantity) * (pnl_pct / 100)
        exit_price = entry_price * (1 + pnl_pct / 100)
        
        # Staggered dates back 30 days
        days_back = random.randint(0, 30)
        hours_back = random.randint(0, 23)
        trade_time = now - timedelta(days=days_back, hours=hours_back)
        exit_time = trade_time + timedelta(minutes=random.randint(15, 240))
        
        # Log the trade
        await trade_history_service.log_trade(
            user_id=user_id,
            symbol=symbol,
            strategy=strategy,
            action="BUY",
            quantity=quantity,
            entry_price=entry_price,
            exit_price=exit_price,
            pnl=pnl,
            pnl_percentage=pnl_pct,
            entry_time=trade_time,
            exit_time=exit_time,
            status="CLOSED",
            order_id=f"MOCK_{random.getrandbits(32):X}"
        )
        
    print("✅ Successfully seeded 50 trades!")
    print("📊 Strategy performance metrics automatically updated.")
    
if __name__ == "__main__":
    asyncio.run(seed_data())
