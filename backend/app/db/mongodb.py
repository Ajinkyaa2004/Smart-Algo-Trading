from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import os

class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    db_name: str = "smart_algo_trade"

    def connect(self):
        mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        self.client = AsyncIOMotorClient(mongo_uri)
        print(f"✅ Connected to MongoDB at {mongo_uri}")

    def get_database(self):
        if self.client is None:
            self.connect()
        return self.client[self.db_name]

    def close(self):
        if self.client:
            self.client.close()
            self.client = None
            print("MongoDB connection closed")

db = MongoDB()

async def get_database():
    return db.get_database()
