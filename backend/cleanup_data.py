
import os
import asyncio
from pymongo import MongoClient

async def cleanup():
    uri = os.getenv("MONGO_URI")
    if not uri:
        print("❌ MONGO_URI not found")
        return

    print(f"Connecting to: {uri.split('@')[1]}")
    client = MongoClient(uri)
    db = client["smart_algo_trade"]
    collection = db["trade_history"]
    
    # Define query for mock data
    query = {"order_id": {"$regex": "^(MOCK|DEMO)_"}}
    
    # Count before deletion
    count = collection.count_documents(query)
    print(f"🔍 Found {count} simulated trades to clean up.")
    
    if count > 0:
        result = collection.delete_many(query)
        print(f"✅ Deleted {result.deleted_count} simulated trades.")
    else:
        print("✓ No simulated data found.")
        
    # Verify remaining
    remaining = collection.count_documents({})
    print(f"📉 Remaining Trades in DB: {remaining}")

if __name__ == "__main__":
    asyncio.run(cleanup())
