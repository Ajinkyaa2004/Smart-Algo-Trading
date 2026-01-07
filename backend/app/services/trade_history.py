"""
Trade History Service
Manages trade history, analytics, and strategy performance tracking
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from app.db.mongodb import db


class TradeHistoryService:
    """
    Service for managing trade history and analytics
    """
    
    def __init__(self):
        self.db = None
        self._initialize_db()
    
    def _initialize_db(self):
        """Initialize database connection"""
        try:
            self.db = db.get_database()
            print("✓ Trade History Service initialized")
        except Exception as e:
            print(f"⚠️  Trade History Service DB initialization failed: {e}")
    
    async def seed_demo_data(self, user_id: str):
        """Generate demo data for a specific user"""
        import random
        from datetime import datetime, timedelta
        
        collection = self.db["trade_history"]
        
        # Check if data already exists
        if await collection.count_documents({"user_id": user_id}) > 0:
            return {"message": "Data already exists"}

        symbols = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "SBIN", "BHARTIARTL"]
        strategies = ["ORB_SCALPING", "EMA_BREAKOUT", "RSI_MEAN_REVERSION", "SUPER_TREND", "SMA_CROSSOVER"]
        
        now = datetime.now()
        
        for i in range(50):
            symbol = random.choice(symbols)
            strategy = random.choice(strategies)
            is_win = random.random() < 0.6
            
            entry_price = random.uniform(500, 3000)
            quantity = random.randint(10, 100)
            
            if is_win:
                pnl_pct = random.uniform(0.5, 3.5)
            else:
                pnl_pct = random.uniform(-0.5, -2.5)
                
            pnl = (entry_price * quantity) * (pnl_pct / 100)
            exit_price = entry_price * (1 + pnl_pct / 100)
            
            days_back = random.randint(0, 30)
            hours_back = random.randint(0, 23)
            trade_time = now - timedelta(days=days_back, hours=hours_back)
            exit_time = trade_time + timedelta(minutes=random.randint(15, 240))
            
            await self.log_trade(
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
                order_id=f"DEMO_{random.getrandbits(32):X}"
            )
            
        return {"message": "Successfully seeded 50 trades"}

    async def log_trade(
        self,
        user_id: str,
        symbol: str,
        strategy: str,
        action: str,
        quantity: int,
        entry_price: float,
        exit_price: Optional[float] = None,
        pnl: Optional[float] = None,
        pnl_percentage: Optional[float] = None,
        entry_time: Optional[datetime] = None,
        exit_time: Optional[datetime] = None,
        status: str = "OPEN",
        order_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Log a trade to the database
        
        Args:
            user_id: User identifier
            symbol: Trading symbol
            strategy: Strategy name used
            action: BUY or SELL
            quantity: Number of shares
            entry_price: Entry price
            exit_price: Exit price (if closed)
            pnl: Profit/Loss amount
            pnl_percentage: P&L percentage
            entry_time: Entry timestamp
            exit_time: Exit timestamp
            status: OPEN or CLOSED
            order_id: Associated order ID
            metadata: Additional metadata
            
        Returns:
            Trade ID
        """
        try:
            trade_data = {
                "user_id": user_id,
                "symbol": symbol,
                "strategy": strategy,
                "action": action,
                "quantity": quantity,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "pnl": pnl or 0.0,
                "pnl_percentage": pnl_percentage or 0.0,
                "entry_time": entry_time or datetime.now(),
                "exit_time": exit_time,
                "status": status,
                "order_id": order_id,
                "duration_minutes": None,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "metadata": metadata or {}
            }
            
            # Calculate duration if both times available
            if entry_time and exit_time:
                duration = (exit_time - entry_time).total_seconds() / 60
                trade_data["duration_minutes"] = duration
            
            # Insert into database
            collection = self.db["trade_history"]
            result = await collection.insert_one(trade_data)
            
            # Update strategy performance if trade is closed
            if status == "CLOSED" and pnl is not None:
                await self._update_strategy_performance(user_id, strategy, pnl, pnl_percentage or 0)
            
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"Error logging trade: {e}")
            return None
    
    async def update_trade(
        self,
        trade_id: str,
        exit_price: Optional[float] = None,
        exit_time: Optional[datetime] = None,
        pnl: Optional[float] = None,
        pnl_percentage: Optional[float] = None,
        status: Optional[str] = None
    ) -> bool:
        """
        Update an existing trade (e.g., when closing a position)
        
        Args:
            trade_id: Trade ID to update
            exit_price: Exit price
            exit_time: Exit timestamp
            pnl: Profit/Loss
            pnl_percentage: P&L percentage
            status: New status
            
        Returns:
            Success boolean
        """
        try:
            from bson.objectid import ObjectId
            
            update_data = {"updated_at": datetime.now()}
            
            if exit_price is not None:
                update_data["exit_price"] = exit_price
            if exit_time is not None:
                update_data["exit_time"] = exit_time
            if pnl is not None:
                update_data["pnl"] = pnl
            if pnl_percentage is not None:
                update_data["pnl_percentage"] = pnl_percentage
            if status is not None:
                update_data["status"] = status
            
            collection = self.db["trade_history"]
            result = await collection.update_one(
                {"_id": ObjectId(trade_id)},
                {"$set": update_data}
            )
            
            # Update strategy performance if closing
            if status == "CLOSED" and pnl is not None:
                trade = await collection.find_one({"_id": ObjectId(trade_id)})
                if trade:
                    await self._update_strategy_performance(
                        trade["user_id"],
                        trade["strategy"],
                        pnl,
                        pnl_percentage or 0
                    )
            
            return result.modified_count > 0
            
        except Exception as e:
            print(f"Error updating trade: {e}")
            return False
    
    async def get_user_trades(
        self,
        user_id: str,
        limit: Optional[int] = None,
        skip: int = 0,
        strategy: Optional[str] = None,
        symbol: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Get trades for a user with optional filters
        
        Args:
            user_id: User identifier
            limit: Maximum number of trades to return
            skip: Number of trades to skip (pagination)
            strategy: Filter by strategy
            symbol: Filter by symbol
            status: Filter by status (OPEN/CLOSED)
            start_date: Filter by start date
            end_date: Filter by end date
            
        Returns:
            List of trades
        """
        try:
            # Build query
            query = {"user_id": user_id}
            
            if strategy:
                query["strategy"] = strategy
            if symbol:
                query["symbol"] = symbol
            if status:
                query["status"] = status
            if start_date or end_date:
                query["entry_time"] = {}
                if start_date:
                    query["entry_time"]["$gte"] = start_date
                if end_date:
                    query["entry_time"]["$lte"] = end_date
            
            # Execute query
            collection = self.db["trade_history"]
            cursor = collection.find(query).sort("entry_time", -1)
            
            if skip:
                cursor = cursor.skip(skip)
            if limit:
                cursor = cursor.limit(limit)
            
            trades = await cursor.to_list(length=None)
            
            # Convert ObjectId to string
            for trade in trades:
                trade["_id"] = str(trade["_id"])
            
            return trades
            
        except Exception as e:
            print(f"Error fetching trades: {e}")
            return []
    
    async def get_trade_statistics(self, user_id: str, days: Optional[int] = None) -> Dict:
        """
        Get comprehensive trade statistics for a user
        
        Args:
            user_id: User identifier
            days: Number of days to look back (None for all time)
            
        Returns:
            Statistics dictionary
        """
        try:
            # Build query
            query = {"user_id": user_id, "status": "CLOSED"}
            
            if days:
                start_date = datetime.now() - timedelta(days=days)
                query["entry_time"] = {"$gte": start_date}
            
            # Fetch all closed trades
            collection = self.db["trade_history"]
            trades = await collection.find(query).to_list(length=None)
            
            if not trades:
                return self._empty_statistics()
            
            # Calculate statistics
            total_trades = len(trades)
            winning_trades = [t for t in trades if t.get("pnl", 0) > 0]
            losing_trades = [t for t in trades if t.get("pnl", 0) < 0]
            
            total_pnl = sum(t.get("pnl", 0) for t in trades)
            total_invested = sum(t.get("entry_price", 0) * t.get("quantity", 0) for t in trades)
            
            win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0
            
            avg_profit = sum(t.get("pnl", 0) for t in winning_trades) / len(winning_trades) if winning_trades else 0
            avg_loss = sum(t.get("pnl", 0) for t in losing_trades) / len(losing_trades) if losing_trades else 0
            
            best_trade = max(trades, key=lambda t: t.get("pnl", 0))
            worst_trade = min(trades, key=lambda t: t.get("pnl", 0))
            
            # Profit factor
            total_profit = sum(t.get("pnl", 0) for t in winning_trades)
            total_loss = abs(sum(t.get("pnl", 0) for t in losing_trades))
            profit_factor = total_profit / total_loss if total_loss > 0 else 0
            
            # Average duration
            durations = [t.get("duration_minutes", 0) for t in trades if t.get("duration_minutes")]
            avg_duration = sum(durations) / len(durations) if durations else 0
            
            return {
                "total_trades": total_trades,
                "winning_trades": len(winning_trades),
                "losing_trades": len(losing_trades),
                "win_rate": round(win_rate, 2),
                "total_pnl": round(total_pnl, 2),
                "total_invested": round(total_invested, 2),
                "avg_profit": round(avg_profit, 2),
                "avg_loss": round(avg_loss, 2),
                "best_trade": {
                    "symbol": best_trade.get("symbol"),
                    "pnl": round(best_trade.get("pnl", 0), 2),
                    "strategy": best_trade.get("strategy")
                },
                "worst_trade": {
                    "symbol": worst_trade.get("symbol"),
                    "pnl": round(worst_trade.get("pnl", 0), 2),
                    "strategy": worst_trade.get("strategy")
                },
                "profit_factor": round(profit_factor, 2),
                "avg_duration_minutes": round(avg_duration, 2)
            }
            
        except Exception as e:
            print(f"Error calculating statistics: {e}")
            return self._empty_statistics()
    
    async def get_strategy_performance(self, user_id: str) -> List[Dict]:
        """
        Get performance breakdown by strategy
        
        Args:
            user_id: User identifier
            
        Returns:
            List of strategy performance data
        """
        try:
            collection = self.db["strategy_performance"]
            strategies = await collection.find({"user_id": user_id}).to_list(length=None)
            
            # Convert ObjectId to string
            for strategy in strategies:
                strategy["_id"] = str(strategy["_id"])
            
            return strategies
            
        except Exception as e:
            print(f"Error fetching strategy performance: {e}")
            return []
    
    async def get_pnl_over_time(
        self,
        user_id: str,
        days: int = 30,
        interval: str = "daily"
    ) -> List[Dict]:
        """
        Get P&L over time for charting
        
        Args:
            user_id: User identifier
            days: Number of days to look back
            interval: 'daily', 'weekly', or 'monthly'
            
        Returns:
            List of {date, pnl, cumulative_pnl} dictionaries
        """
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            collection = self.db["trade_history"]
            trades = await collection.find({
                "user_id": user_id,
                "status": "CLOSED",
                "exit_time": {"$gte": start_date}
            }).sort("exit_time", 1).to_list(length=None)
            
            # Group by date
            pnl_by_date = defaultdict(float)
            
            for trade in trades:
                exit_time = trade.get("exit_time")
                if not exit_time:
                    continue
                
                # Format date based on interval
                if interval == "daily":
                    date_key = exit_time.strftime("%Y-%m-%d")
                elif interval == "weekly":
                    date_key = exit_time.strftime("%Y-W%W")
                else:  # monthly
                    date_key = exit_time.strftime("%Y-%m")
                
                pnl_by_date[date_key] += trade.get("pnl", 0)
            
            # Convert to list with cumulative P&L
            result = []
            cumulative = 0
            
            for date_key in sorted(pnl_by_date.keys()):
                pnl = pnl_by_date[date_key]
                cumulative += pnl
                result.append({
                    "date": date_key,
                    "pnl": round(pnl, 2),
                    "cumulative_pnl": round(cumulative, 2)
                })
            
            return result
            
        except Exception as e:
            print(f"Error calculating P&L over time: {e}")
            return []
    
    async def _update_strategy_performance(
        self,
        user_id: str,
        strategy: str,
        pnl: float,
        pnl_percentage: float
    ):
        """
        Update strategy performance metrics
        
        Args:
            user_id: User identifier
            strategy: Strategy name
            pnl: Trade P&L
            pnl_percentage: Trade P&L percentage
        """
        try:
            collection = self.db["strategy_performance"]
            
            # Check if strategy record exists
            existing = await collection.find_one({
                "user_id": user_id,
                "strategy": strategy
            })
            
            if existing:
                # Update existing record
                total_trades = existing.get("total_trades", 0) + 1
                winning_trades = existing.get("winning_trades", 0) + (1 if pnl > 0 else 0)
                losing_trades = existing.get("losing_trades", 0) + (1 if pnl < 0 else 0)
                total_pnl = existing.get("total_pnl", 0) + pnl
                
                win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
                avg_pnl = total_pnl / total_trades if total_trades > 0 else 0
                
                best_trade = max(existing.get("best_trade", 0), pnl)
                worst_trade = min(existing.get("worst_trade", 0), pnl)
                
                await collection.update_one(
                    {"user_id": user_id, "strategy": strategy},
                    {"$set": {
                        "total_trades": total_trades,
                        "winning_trades": winning_trades,
                        "losing_trades": losing_trades,
                        "total_pnl": round(total_pnl, 2),
                        "win_rate": round(win_rate, 2),
                        "avg_pnl": round(avg_pnl, 2),
                        "best_trade": round(best_trade, 2),
                        "worst_trade": round(worst_trade, 2),
                        "last_updated": datetime.now()
                    }}
                )
            else:
                # Create new record
                await collection.insert_one({
                    "user_id": user_id,
                    "strategy": strategy,
                    "total_trades": 1,
                    "winning_trades": 1 if pnl > 0 else 0,
                    "losing_trades": 1 if pnl < 0 else 0,
                    "total_pnl": round(pnl, 2),
                    "win_rate": 100.0 if pnl > 0 else 0.0,
                    "avg_pnl": round(pnl, 2),
                    "best_trade": round(pnl, 2),
                    "worst_trade": round(pnl, 2),
                    "created_at": datetime.now(),
                    "last_updated": datetime.now()
                })
                
        except Exception as e:
            print(f"Error updating strategy performance: {e}")
    
    def _empty_statistics(self) -> Dict:
        """Return empty statistics structure"""
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0,
            "total_pnl": 0,
            "total_invested": 0,
            "avg_profit": 0,
            "avg_loss": 0,
            "best_trade": {"symbol": None, "pnl": 0, "strategy": None},
            "worst_trade": {"symbol": None, "pnl": 0, "strategy": None},
            "profit_factor": 0,
            "avg_duration_minutes": 0
        }


# Global instance
trade_history_service = TradeHistoryService()
