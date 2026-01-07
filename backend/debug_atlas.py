
import os
import asyncio
from pymongo import MongoClient
import sys

# Load env vars potentially? No, we will export again.

async def check_data():
    uri = os.getenv("MONGO_URI")
    if not uri:
        print("❌ MONGO_URI not found")
        return

    print(f"Connecting to: {uri.split('@')[1]}") # Print host part for verification
    client = MongoClient(uri)
    db = client["smart_algo_trade"]
    
    # Check trade_history
    collection = db["trade_history"]
    count = collection.count_documents({})
    print(f"📉 Total Trades in DB: {count}")

    if count > 0:
        real_trades = collection.count_documents({"order_id": {"$regex": "^ORD_"}})
        mock_trades = collection.count_documents({"order_id": {"$regex": "^(MOCK|DEMO)_"}})
        
        print(f"📊 Data Analysis:")
        print(f"   • Real Bot Trades: {real_trades}")
        print(f"   • Simulated/Mock:  {mock_trades}")
        
        sample = collection.find_one({"order_id": {"$regex": "^ORD_"}})
        if sample:
            print(f"   • Sample Real Trade: {sample.get('symbol')} | {sample.get('pnl')}")
        else:
            print(f"   • No real trades found yet.")
            
    # Check Orders Collection
    order_count = db["orders"].count_documents({})
    print(f"📦 Total Orders in DB: {order_count}")

if __name__ == "__main__":
    asyncio.run(check_data())
