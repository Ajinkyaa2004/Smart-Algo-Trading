"""
Paper Trading Engine
Simulates order execution for safe testing without real money

CRITICAL: This module ensures NO REAL ORDERS are ever placed on Zerodha
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid
import threading
import os
import json

# Import pymongo for persistence
try:
    from pymongo import MongoClient
    MONGO_AVAILABLE = True
except ImportError:
    MONGO_AVAILABLE = False
    print("⚠️  pymongo not installed, paper trading persistence disabled")

# Import market data service for fetching real-time prices
try:
    from app.services.market_data import market_data_service
    MARKET_DATA_AVAILABLE = True
except ImportError:
    MARKET_DATA_AVAILABLE = False
    print("⚠️  Market data service not available for paper trading")

# Import configuration
try:
    from app.config import (
        PAPER_TRADING,
        MAX_LOSS_PER_DAY,
        MAX_POSITIONS,
        RISK_PER_TRADE,
        MAX_TRADES_PER_DAY
    )
    PAPER_TRADING_MODE = PAPER_TRADING
except ImportError:
    # Fallback to safe default
    PAPER_TRADING_MODE = True
    MAX_LOSS_PER_DAY = 5000.0
    MAX_POSITIONS = 3
    RISK_PER_TRADE = 0.01
    MAX_TRADES_PER_DAY = 10


# ==================== GLOBAL PAPER TRADING FLAG ====================
# CRITICAL: This flag controls whether orders are real or simulated

# Safety guard: Prevent accidental live trading
if not PAPER_TRADING_MODE:
    print("\n" + "="*60)
    print("⚠️  WARNING: PAPER TRADING MODE IS DISABLED!")
    print("⚠️  REAL ORDERS WILL BE PLACED ON ZERODHA!")
    print("⚠️  YOU ARE TRADING WITH REAL MONEY!")
    print("="*60 + "\n")
else:
    print("\n" + "="*60)
    print("✓ PAPER TRADING MODE: ENABLED")
    print("✓ No real orders will be placed")
    print("✓ Safe for zero-balance accounts")
    print("="*60 + "\n")


class OrderStatus(Enum):
    """Simulated order status"""
    PENDING = "PENDING"
    OPEN = "OPEN"
    COMPLETE = "COMPLETE"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class TransactionType(Enum):
    """Transaction types"""
    BUY = "BUY"
    SELL = "SELL"


@dataclass
class PaperOrder:
    """Simulated order"""
    order_id: str
    timestamp: datetime
    tradingsymbol: str
    exchange: str
    transaction_type: str
    quantity: int
    order_type: str  # MARKET, LIMIT, SL, SL-M
    product: str  # MIS, CNC, NRML
    status: OrderStatus
    
    # Prices
    price: Optional[float] = None
    trigger_price: Optional[float] = None
    average_price: Optional[float] = None
    
    # Execution details
    filled_quantity: int = 0
    pending_quantity: int = 0
    cancelled_quantity: int = 0
    
    # Metadata
    tag: Optional[str] = None
    placed_by: str = "PAPER_TRADING"
    
    # Timestamps
    order_timestamp: datetime = field(default_factory=datetime.now)
    exchange_timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        self.pending_quantity = self.quantity


@dataclass
class PaperPosition:
    """Simulated position"""
    symbol: str
    exchange: str
    product: str
    quantity: int  # Positive for long, negative for short
    average_price: float
    last_price: float
    
    # P&L
    unrealised_pnl: float = 0.0
    realised_pnl: float = 0.0
    
    # Trade tracking
    buy_quantity: int = 0
    sell_quantity: int = 0
    buy_value: float = 0.0
    sell_value: float = 0.0
    
    # Timestamps
    opened_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class PaperTradingEngine:
    """
    Paper Trading Engine
    
    Simulates order execution without placing real orders on Zerodha.
    Uses real market data but fake order fills.
    PERSISTENCE: Uses MongoDB to save state across restarts.
    """
    
    def __init__(self):
        self.orders: Dict[str, PaperOrder] = {}
        self.positions: Dict[str, PaperPosition] = {}  # key: symbol_exchange_product
        self.trades: List[Dict] = []
        self.daily_pnl = 0.0
        self.total_pnl = 0.0
        self.lock = threading.Lock()
        
        # ==================== VIRTUAL CAPITAL ====================
        # Starting virtual capital for paper trading
        self.VIRTUAL_CAPITAL = 100000.0  # ₹1,00,000
        self.available_funds = 100000.0  # Available for new trades
        self.invested_funds = 0.0        # Currently invested in positions
        self.reserved_funds = 0.0        # Allocated to running bots (but not yet in positions)
        self.realized_pnl = 0.0          # Realized P&L from closed trades
        
        # Risk management (from config)
        self.max_loss_per_day = MAX_LOSS_PER_DAY
        self.max_positions = MAX_POSITIONS
        self.risk_per_trade = RISK_PER_TRADE
        self.trades_today = 0
        self.max_trades_per_day = MAX_TRADES_PER_DAY
        
        # Market data cache (for fills)
        self.ltp_cache: Dict[str, float] = {}

        # ==================== PERSISTENCE ====================
        self.db = None
        self.collection_orders = None
        self.collection_positions = None
        self.collection_trades = None
        self.collection_meta = None
        
        if MONGO_AVAILABLE:
            try:
                # Use env variable or default localhost. Use sync client.
                mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
                self.client = MongoClient(mongo_uri)
                self.db = self.client["smart_algo_trade"]
                self.collection_orders = self.db["paper_orders"]
                self.collection_positions = self.db["paper_positions"]
                self.collection_trades = self.db["paper_trades"]
                self.collection_meta = self.db["paper_meta"]
                print("✓ Connected to MongoDB for persistence")
                
                # Load state immediately
                self._load_state()
            except Exception as e:
                print(f"⚠️  MongoDB Connection Error: {e}")
        
        print("="*60)
        print("🛡️  PAPER TRADING ENGINE INITIALIZED")
        print("="*60)
        print("✓ No real orders will be placed")
        print("✓ All trades are simulated")
        print("✓ Real market data used for fills")
        print(f"✓ Virtual Capital: ₹{self.VIRTUAL_CAPITAL:,.2f}")
        print(f"✓ Available Funds: ₹{self.available_funds:,.2f}")
        print(f"✓ Reserved Funds:  ₹{self.reserved_funds:,.2f}")
        print("="*60)

    # ==================== FUND ALLOCATION ====================
    
    def allocate_funds(self, amount: float) -> bool:
        """
        Allocate funds to a running bot/strategy.
        Moves funds from 'available' to 'reserved'.
        
        Args:
            amount: Amount to reserve
            
        Returns:
            True if successful
        """
        with self.lock:
            if amount > self.available_funds:
                print(f"❌ Cannot allocate ₹{amount:.2f}: Only ₹{self.available_funds:.2f} available")
                return False
            
            self.available_funds -= amount
            self.reserved_funds += amount
            self._save_meta()
            print(f"💰 Allocated ₹{amount:.2f} to reserved funds")
            print(f"   Available: ₹{self.available_funds:.2f} | Reserved: ₹{self.reserved_funds:.2f}")
            return True
    
    def reclaim_reserved_funds(self):
        """
        Reclaim all reserved funds back to available.
        Called when bots are stopped.
        """
        with self.lock:
            if self.reserved_funds > 0:
                amount = self.reserved_funds
                self.available_funds += amount
                self.reserved_funds = 0.0
                self._save_meta()
                print(f"💰 Reclaimed ₹{amount:.2f} from reserved funds")
                print(f"   Available: ₹{self.available_funds:.2f}")

    # ==================== PERSISTENCE METHODS ====================

    def _load_state(self):
        """Load state from MongoDB on startup"""
        if not self.db:
            return
            
        try:
            # 1. Load Meta (Funds)
            meta = self.collection_meta.find_one({"_id": "global_state"})
            if meta:
                self.VIRTUAL_CAPITAL = meta.get("virtual_capital", 100000.0)
                self.available_funds = meta.get("available_funds", 100000.0)
                self.invested_funds = meta.get("invested_funds", 0.0)
                self.reserved_funds = meta.get("reserved_funds", 0.0)
                self.realized_pnl = meta.get("realized_pnl", 0.0)
                self.total_pnl = meta.get("total_pnl", 0.0)
                # We typically reset daily PnL, but for continuity in dev let's load it
                # In prod, check date vs today
                self.daily_pnl = meta.get("daily_pnl", 0.0)
                print("✓ Loaded funds from MongoDB")
            
            # 2. Load Orders
            for doc in self.collection_orders.find():
                try:
                    # Map back to objects
                    order = PaperOrder(
                        order_id=doc['order_id'],
                        timestamp=doc.get('timestamp', datetime.now()),
                        tradingsymbol=doc['tradingsymbol'],
                        exchange=doc['exchange'],
                        transaction_type=doc['transaction_type'],
                        quantity=doc['quantity'],
                        order_type=doc['order_type'],
                        product=doc['product'],
                        status=OrderStatus(doc['status']), # Enum conversion
                        price=doc.get('price'),
                        trigger_price=doc.get('trigger_price'),
                        average_price=doc.get('average_price'),
                        filled_quantity=doc.get('filled_quantity', 0),
                        pending_quantity=doc.get('pending_quantity', 0),
                        cancelled_quantity=doc.get('cancelled_quantity', 0),
                        tag=doc.get('tag'),
                        placed_by=doc.get('placed_by', 'PAPER_TRADING'),
                        order_timestamp=doc.get('order_timestamp', datetime.now()),
                        exchange_timestamp=doc.get('exchange_timestamp')
                    )
                    self.orders[order.order_id] = order
                except Exception as e:
                    print(f"Error loading order {doc.get('order_id')}: {e}")
            
            # 3. Load Positions
            for doc in self.collection_positions.find():
                try:
                    key = f"{doc['symbol']}_{doc['exchange']}_{doc['product']}"
                    pos = PaperPosition(
                        symbol=doc['symbol'],
                        exchange=doc['exchange'],
                        product=doc['product'],
                        quantity=doc['quantity'],
                        average_price=doc['average_price'],
                        last_price=doc['last_price'],
                        unrealised_pnl=doc.get('unrealised_pnl', 0.0),
                        realised_pnl=doc.get('realised_pnl', 0.0),
                        buy_quantity=doc.get('buy_quantity', 0),
                        sell_quantity=doc.get('sell_quantity', 0),
                        buy_value=doc.get('buy_value', 0.0),
                        sell_value=doc.get('sell_value', 0.0),
                        opened_at=doc.get('opened_at', datetime.now()),
                        updated_at=doc.get('updated_at', datetime.now())
                    )
                    self.positions[key] = pos
                except Exception as e:
                    print(f"Error loading position {doc.get('symbol')}: {e}")
            
            # 4. Load Trades history
            self.trades = list(self.collection_trades.find({}, {"_id": 0}))
            self.trades_today = len(self.trades) # Simplification
            
            print(f"✓ State Loaded: {len(self.orders)} orders, {len(self.positions)} positions, {len(self.trades)} trades")
            
        except Exception as e:
            print(f"✗ Failed to load state from DB: {e}")

    def _save_meta(self):
        """Save funds and global state"""
        if not self.db: return
        try:
            self.collection_meta.update_one(
                {"_id": "global_state"},
                {"$set": {
                    "virtual_capital": self.VIRTUAL_CAPITAL,
                    "available_funds": self.available_funds,
                    "invested_funds": self.invested_funds,
                    "reserved_funds": self.reserved_funds,
                    "realized_pnl": self.realized_pnl,
                    "total_pnl": self.total_pnl,
                    "daily_pnl": self.daily_pnl,
                    "updated_at": datetime.now()
                }},
                upsert=True
            )
        except Exception as e:
            print(f"DB Error saving meta: {e}")

    def _save_order(self, order: PaperOrder):
        """Save or update order"""
        if not self.db: return
        try:
            data = asdict(order)
            data["status"] = order.status.value # Convert Enum
            # _id not needed in update filter usually, but good to preserve
            self.collection_orders.update_one(
                {"order_id": order.order_id},
                {"$set": data},
                upsert=True
            )
        except Exception as e:
            print(f"DB Error saving order: {e}")

    def _save_position(self, position: PaperPosition):
        """Save or update position"""
        if not self.db: return
        try:
            data = asdict(position)
            self.collection_positions.update_one(
                {"symbol": position.symbol, "exchange": position.exchange, "product": position.product},
                {"$set": data},
                upsert=True
            )
        except Exception as e:
            print(f"DB Error saving position: {e}")

    def _delete_position(self, position: PaperPosition):
        """Remove closed position from DB"""
        if not self.db: return
        try:
            self.collection_positions.delete_one(
                {"symbol": position.symbol, "exchange": position.exchange, "product": position.product}
            )
        except Exception as e:
            print(f"DB Error deleting position: {e}")

    def _save_trade(self, trade: Dict):
        """Save completed trade log"""
        if not self.db: return
        try:
            self.collection_trades.insert_one(trade)
        except Exception as e:
            print(f"DB Error saving trade: {e}")

    # ==================== SAFETY GUARD ====================
    
    def _safety_check(self):
        """
        CRITICAL: Ensure paper trading mode is enabled
        Throws exception if someone tries to bypass it
        """
        if not PAPER_TRADING_MODE:
            raise Exception(
                "❌ CRITICAL ERROR: Attempted to place REAL order!\n"
                "Paper trading mode is DISABLED. This will place REAL orders on Zerodha!\n"
                "Set PAPER_TRADING_MODE = True to enable paper trading."
            )
    
    # ==================== RISK MANAGEMENT ====================
    
    def can_place_trade(self, required_funds: float = 0, is_bot_trade: bool = False) -> Tuple[bool, str]:
        """
        Check if new trade is allowed based on risk rules
        """
        # Check available funds
        # If it's a bot trade, we can use reserved funds + available
        limit = self.available_funds
        if is_bot_trade:
            limit += self.reserved_funds
            
        if required_funds > 0 and required_funds > limit:
            return False, f"Insufficient funds: Need ₹{required_funds:.2f}, Limit ₹{limit:.2f}"
        
        # Check daily loss limit
        if abs(self.daily_pnl) >= self.max_loss_per_day:
            return False, f"Daily loss limit reached: ₹{abs(self.daily_pnl):.2f}"
        
        # Check max positions
        if len(self.positions) >= self.max_positions:
            return False, f"Max positions limit reached: {len(self.positions)}"
        
        # Check max trades per day
        if self.trades_today >= self.max_trades_per_day:
            return False, f"Max trades per day reached: {self.trades_today}"
        
        return True, "OK"
    
    # ==================== ORDER PLACEMENT ====================
    
    def place_order(
        self,
        tradingsymbol: str,
        exchange: str,
        transaction_type: str,
        quantity: int,
        order_type: str = "MARKET",
        product: str = "MIS",
        price: Optional[float] = None,
        trigger_price: Optional[float] = None,
        tag: Optional[str] = None
    ) -> str:
        """
        Simulate order placement
        """
        self._safety_check()
        
        with self.lock:
            # Check if this is a bot trade
            is_bot_trade = tag is not None and tag.startswith("BOT_")
            
            # Calculate required funds for BUY orders
            required_funds = 0
            if transaction_type == "BUY":
                # Estimate required funds using provided price or cached LTP
                symbol_key = f"{exchange}:{tradingsymbol}"
                estimated_price = price or self.ltp_cache.get(symbol_key, 100.0)
                required_funds = quantity * estimated_price
                print(f"💰 BUY Order Check: {tradingsymbol} @ ₹{estimated_price:.2f} × {quantity} = ₹{required_funds:.2f}")
                print(f"   Available: ₹{self.available_funds:.2f} | Reserved: ₹{self.reserved_funds:.2f}")
            
            # Check risk rules
            allowed, reason = self.can_place_trade(required_funds, is_bot_trade)
            if not allowed:
                print(f"❌ [PAPER TRADE BLOCKED] {reason}")
                raise Exception(f"Risk rule violation: {reason}")
            
            # Generate order ID
            order_id = f"PAPER_{uuid.uuid4().hex[:8].upper()}"
            
            # Create paper order
            order = PaperOrder(
                order_id=order_id,
                timestamp=datetime.now(),
                tradingsymbol=tradingsymbol,
                exchange=exchange,
                transaction_type=transaction_type,
                quantity=quantity,
                order_type=order_type,
                product=product,
                status=OrderStatus.PENDING,
                price=price,
                trigger_price=trigger_price,
                tag=tag
            )
            
            # Store order
            self.orders[order_id] = order
            self._save_order(order)  # PERSISTENCE
            
            # Log paper trade
            self._log_order(order, "PLACED")
            
            # Simulate immediate execution for market orders
            if order_type == "MARKET":
                self._simulate_fill(order_id)
            
            return order_id
    
    def _simulate_fill(self, order_id: str):
        """
        Simulate order fill at market price
        """
        order = self.orders.get(order_id)
        if not order:
            return
        
        # Get fill price
        if order.order_type == "MARKET":
            # Use cached LTP or fetch from market data service
            symbol_key = f"{order.exchange}:{order.tradingsymbol}"
            fill_price = self.ltp_cache.get(symbol_key)
            
            # If not in cache, try to fetch real-time LTP
            if fill_price is None and MARKET_DATA_AVAILABLE:
                try:
                    print(f"📡 Fetching real-time LTP for {symbol_key}...")
                    ltp_data = market_data_service.get_ltp([symbol_key])
                    if ltp_data and symbol_key in ltp_data:
                        fill_price = ltp_data[symbol_key]['last_price']
                        # Cache it for future use
                        self.ltp_cache[symbol_key] = fill_price
                        print(f"✓ Fetched LTP: ₹{fill_price:.2f}")
                except Exception as e:
                    print(f"⚠️  Could not fetch LTP: {str(e)}")
            
            # Fallback to provided price or default estimate
            if fill_price is None:
                fill_price = order.price or 100.0
                print(f"⚠️  Using fallback price: ₹{fill_price:.2f}")
        else:
            # Use limit price
            fill_price = order.price
        
        # Update order
        order.status = OrderStatus.COMPLETE
        order.filled_quantity = order.quantity
        order.pending_quantity = 0
        order.average_price = fill_price
        order.exchange_timestamp = datetime.now()
        
        # PERSISTENCE: Save updated order
        self._save_order(order)
        
        # Update position
        self._update_position(order, fill_price)
        
        # Log fill
        self._log_order(order, "FILLED")
        
        # Track trade
        self.trades_today += 1
        trade_record = {
            "timestamp": datetime.now(),
            "order_id": order_id,
            "symbol": order.tradingsymbol,
            "action": order.transaction_type,
            "quantity": order.quantity,
            "price": fill_price,
            "tag": order.tag
        }
        self.trades.append(trade_record)
        self._save_trade(trade_record) # PERSISTENCE
    
    def _update_position(self, order: PaperOrder, fill_price: float):
        """Update position after order fill AND manage virtual funds"""
        position_key = f"{order.tradingsymbol}_{order.exchange}_{order.product}"
        
        # Check if trade is from a bot
        is_bot_trade = order.tag and order.tag.startswith("BOT_")
        
        if position_key not in self.positions:
            # New position
            self.positions[position_key] = PaperPosition(
                symbol=order.tradingsymbol,
                exchange=order.exchange,
                product=order.product,
                quantity=0,
                average_price=0.0,
                last_price=fill_price
            )
        
        position = self.positions[position_key]
        
        # ==================== FUND MANAGEMENT ====================
        trade_value = order.quantity * fill_price
        
        if order.transaction_type == "BUY":
            # DEDUCT funds on BUY
            
            # Logic: If it's a bot trade, use RESERVED funds first
            if is_bot_trade and self.reserved_funds > 0:
                # Deduct from reserved as much as possible
                deduct_from_reserved = min(self.reserved_funds, trade_value)
                deduct_from_available = trade_value - deduct_from_reserved
                
                self.reserved_funds -= deduct_from_reserved
                self.available_funds -= deduct_from_available
                print(f"💰 [PAPER FUNDS] BUY uses Reserved: ₹{deduct_from_reserved:.2f}, Available: ₹{deduct_from_available:.2f}")
            else:
                # Manual trade or no reserved funds
                self.available_funds -= trade_value
                
            self.invested_funds += trade_value
            
            position.buy_quantity += order.quantity
            position.buy_value += trade_value
            position.quantity += order.quantity
            
            print(f"💰 [PAPER FUNDS] BUY ₹{trade_value:.2f} deducted")
            print(f"   Available: ₹{self.available_funds:.2f} | Reserved: ₹{self.reserved_funds:.2f} | Invested: ₹{self.invested_funds:.2f}")
            
        else:  # SELL
            position.sell_quantity += order.quantity
            position.sell_value += trade_value
            position.quantity -= order.quantity
            
            # Calculate realized P&L for this SELL
            if position.quantity == 0:
                # Position fully closed - calculate total realized P&L
                realized_pnl = position.sell_value - position.buy_value
                position.realised_pnl = realized_pnl
                
                # CREDIT funds on SELL (invested amount + P&L)
                # If bot trade, return principal + profit to RESERVED funds?
                # User wants "allocation deducted". If we sell, does it go back to allocation?
                # Usually yes, for continuous trading.
                
                self.invested_funds -= position.buy_value
                
                total_credit = trade_value 
                # (principal + profit)
                
                if is_bot_trade:
                    # Return to reserved so bot can use it again
                    self.reserved_funds += total_credit
                    # Warning: realized P&L is still tracked globally, but the cash moves to reserved
                else:
                    self.available_funds += total_credit
                
                self.realized_pnl += realized_pnl
                self.daily_pnl += realized_pnl
                self.total_pnl += realized_pnl
                
                print(f"💰 [PAPER FUNDS] SELL ₹{trade_value:.2f} credited ({'Reserved' if is_bot_trade else 'Available'})")
                print(f"   P&L: ₹{realized_pnl:.2f} | Total P&L: ₹{self.total_pnl:.2f}")
                print(f"   Available: ₹{self.available_funds:.2f} | Reserved: ₹{self.reserved_funds:.2f} | Invested: ₹{self.invested_funds:.2f}")
            else:
                # Partial sell - reduce invested amount proportionally
                avg_cost = position.buy_value / position.buy_quantity if position.buy_quantity > 0 else 0
                cost_of_sold = order.quantity * avg_cost
                partial_pnl = trade_value - cost_of_sold
                
                self.invested_funds -= cost_of_sold
                
                if is_bot_trade:
                    self.reserved_funds += trade_value
                else:
                    self.available_funds += trade_value
                    
                self.realized_pnl += partial_pnl
                self.daily_pnl += partial_pnl
                self.total_pnl += partial_pnl
                
                print(f"💰 [PAPER FUNDS] PARTIAL SELL ₹{trade_value:.2f} credited")
                print(f"   P&L: ₹{partial_pnl:.2f} | Total P&L: ₹{self.total_pnl:.2f}")
                print(f"   Available: ₹{self.available_funds:.2f} | Reserved: ₹{self.reserved_funds:.2f} | Invested: ₹{self.invested_funds:.2f}")
        
        # Recalculate average price
        if position.quantity != 0:
            net_value = position.buy_value - position.sell_value
            position.average_price = abs(net_value / position.quantity)
        
        position.last_price = fill_price
        position.updated_at = datetime.now()
        
        # Calculate P&L
        self._calculate_pnl(position)
        
        # PERSISTENCE: Save Funds State
        self._save_meta()
        
        # Remove position if closed
        if position.quantity == 0:
            del self.positions[position_key]
            self._delete_position(position) # PERSISTENCE
        else:
            self._save_position(position) # PERSISTENCE
    
    def _calculate_pnl(self, position: PaperPosition):
        """Calculate position P&L"""
        if position.quantity > 0:
            # Long position
            position.unrealised_pnl = (position.last_price - position.average_price) * position.quantity
        elif position.quantity < 0:
            # Short position
            position.unrealised_pnl = (position.average_price - position.last_price) * abs(position.quantity)
        else:
            # Closed position
            position.realised_pnl = position.sell_value - position.buy_value
            position.unrealised_pnl = 0.0
    
    # ==================== ORDER MANAGEMENT ====================
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel a pending order"""
        self._safety_check()
        
        with self.lock:
            order = self.orders.get(order_id)
            if not order:
                return False
            
            if order.status not in [OrderStatus.PENDING, OrderStatus.OPEN]:
                return False
            
            order.status = OrderStatus.CANCELLED
            order.cancelled_quantity = order.pending_quantity
            order.pending_quantity = 0
            
            self._log_order(order, "CANCELLED")
            
            # PERSISTENCE
            self._save_order(order)
            
            return True
    
    def modify_order(
        self,
        order_id: str,
        quantity: Optional[int] = None,
        price: Optional[float] = None,
        trigger_price: Optional[float] = None
    ) -> bool:
        """Modify a pending order"""
        self._safety_check()
        
        with self.lock:
            order = self.orders.get(order_id)
            if not order:
                return False
            
            if order.status not in [OrderStatus.PENDING, OrderStatus.OPEN]:
                return False
            
            if quantity:
                order.quantity = quantity
                order.pending_quantity = quantity - order.filled_quantity
            if price:
                order.price = price
            if trigger_price:
                order.trigger_price = trigger_price
            
            self._log_order(order, "MODIFIED")
            
            # PERSISTENCE
            self._save_order(order)
            
            return True
    
    # ==================== MARKET DATA ====================
    
    def update_ltp(self, symbol: str, exchange: str, ltp: float):
        """
        Update last traded price for simulation and recalculate unrealized P&L
        
        This is called when live market data is received to update holdings in real-time
        """
        symbol_key = f"{exchange}:{symbol}"
        self.ltp_cache[symbol_key] = ltp
        
        # Update position P&L with new price
        updated = False
        for position_key, position in self.positions.items():
            if position.symbol == symbol and position.exchange == exchange:
                position.last_price = ltp
                self._calculate_pnl(position)
                self._save_position(position) # PERSISTENCE
                updated = True
        
        # Update daily P&L
        self._update_daily_pnl()
        if updated:
            self._save_meta() # PERSISTENCE
    
    def _update_daily_pnl(self):
        """Update daily P&L from all positions"""
        total_unrealised = sum(p.unrealised_pnl for p in self.positions.values())
        total_realised = sum(p.realised_pnl for p in self.positions.values())
        self.daily_pnl = total_unrealised + total_realised
        self.total_pnl += total_realised
    
    # ==================== QUERIES ====================
    
    def get_orders(self) -> List[Dict]:
        """Get all orders"""
        return [
            {
                "order_id": order.order_id,
                "tradingsymbol": order.tradingsymbol,
                "exchange": order.exchange,
                "transaction_type": order.transaction_type,
                "quantity": order.quantity,
                "status": order.status.value,
                "average_price": order.average_price,
                "order_type": order.order_type,
                "product": order.product,
                "tag": order.tag,
                "timestamp": order.timestamp.isoformat()
            }
            for order in self.orders.values()
        ]
    
    def get_positions(self) -> List[Dict]:
        """Get all open positions with live P&L"""
        return [
            {
                "tradingsymbol": pos.symbol,
                "exchange": pos.exchange,
                "product": pos.product,
                "quantity": pos.quantity,
                "average_price": pos.average_price,
                "last_price": pos.last_price,
                "invested_amount": pos.buy_value - pos.sell_value,
                "current_value": pos.quantity * pos.last_price,
                "pnl": pos.unrealised_pnl,
                "day_buy_quantity": pos.buy_quantity,
                "day_sell_quantity": pos.sell_quantity
            }
            for pos in self.positions.values()
        ]
    
    def get_portfolio(self) -> Dict:
        """
        Get complete paper portfolio summary
        
        Returns:
            Dict with paper_funds, paper_portfolio, and statistics
        """
        total_unrealized_pnl = sum(p.unrealised_pnl for p in self.positions.values())
        
        # INVESTED FUNDS logic:
        # User wants to see Allocated + Actually Invested as "Invested"
        display_invested = self.invested_funds + self.reserved_funds
        
        return {
            "paper_funds": {
                "virtual_capital": self.VIRTUAL_CAPITAL,
                "available_funds": self.available_funds,
                "invested_funds": display_invested,
                "reserved_funds": self.reserved_funds, # Explicit field if needed
                "realized_pnl": self.realized_pnl,
                "total_value": self.available_funds + display_invested + total_unrealized_pnl
            },
            "paper_portfolio": [
                {
                    "symbol": pos.symbol,
                    "exchange": pos.exchange,
                    "quantity": pos.quantity,
                    "average_price": pos.average_price,
                    "current_price": pos.last_price,
                    "invested_amount": pos.average_price * pos.quantity,
                    "current_value": pos.last_price * pos.quantity,
                    "unrealized_pnl": pos.unrealised_pnl,
                    "pnl_percent": (pos.unrealised_pnl / (pos.average_price * pos.quantity) * 100) if pos.quantity > 0 else 0
                }
                for pos in self.positions.values()
            ],
            "statistics": {
                "total_positions": len(self.positions),
                "total_unrealized_pnl": total_unrealized_pnl,
                "total_realized_pnl": self.realized_pnl,
                "total_pnl": self.realized_pnl + total_unrealized_pnl,
                "trades_today": self.trades_today
            }
        }
    
    def get_trade_history(self) -> List[Dict]:
        """Get completed paper trades history"""
        return [
            {
                "timestamp": trade.get("timestamp").isoformat() if isinstance(trade.get("timestamp"), datetime) else trade.get("timestamp"),
                "order_id": trade.get("order_id"),
                "symbol": trade.get("symbol"),
                "action": trade.get("action"),
                "quantity": trade.get("quantity"),
                "price": trade.get("price"),
                "value": trade.get("quantity", 0) * trade.get("price", 0),
                "tag": trade.get("tag")
            }
            for trade in self.trades
        ]
    
    def get_performance_stats(self) -> Dict:
        """
        Calculate performance statistics from trade history
        
        Returns win rate, avg profit/loss, best/worst trades, profit factor
        """
        if len(self.trades) == 0:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0,
                "avg_profit": 0,
                "avg_loss": 0,
                "avg_pnl": 0,
                "best_trade": 0,
                "worst_trade": 0,
                "profit_factor": 0,
                "total_profit": 0,
                "total_loss": 0
            }
        
        # Group trades by symbol to calculate P&L per round trip
        symbol_trades = {}
        for trade in self.trades:
            symbol = trade.get("symbol")
            if symbol not in symbol_trades:
                symbol_trades[symbol] = []
            symbol_trades[symbol].append(trade)
        
        # Calculate P&L for completed round trips
        completed_trades_pnl = []
        
        for symbol, trades in symbol_trades.items():
            position = 0
            buy_value = 0
            
            for trade in trades:
                action = trade.get("action")
                qty = trade.get("quantity", 0)
                price = trade.get("price", 0)
                
                if action == "BUY":
                    buy_value += qty * price
                    position += qty
                elif action == "SELL":
                    if position > 0:
                        # Calculate P&L for this sell
                        avg_buy_price = buy_value / position if position > 0 else 0
                        pnl = (price - avg_buy_price) * qty
                        completed_trades_pnl.append(pnl)
                        
                        # Update position
                        position -= qty
                        if position > 0:
                            buy_value = avg_buy_price * position
                        else:
                            buy_value = 0
        
        if len(completed_trades_pnl) == 0:
            # Use realized P&L if available
            completed_trades_pnl = [self.realized_pnl] if self.realized_pnl != 0 else [0]
        
        # Calculate statistics
        winning_trades = [pnl for pnl in completed_trades_pnl if pnl > 0]
        losing_trades = [pnl for pnl in completed_trades_pnl if pnl < 0]
        
        total_profit = sum(winning_trades) if winning_trades else 0
        total_loss = abs(sum(losing_trades)) if losing_trades else 0
        
        return {
            "total_trades": len(completed_trades_pnl),
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": (len(winning_trades) / len(completed_trades_pnl) * 100) if completed_trades_pnl else 0,
            "avg_profit": (sum(winning_trades) / len(winning_trades)) if winning_trades else 0,
            "avg_loss": (sum(losing_trades) / len(losing_trades)) if losing_trades else 0,
            "avg_pnl": sum(completed_trades_pnl) / len(completed_trades_pnl) if completed_trades_pnl else 0,
            "best_trade": max(completed_trades_pnl) if completed_trades_pnl else 0,
            "worst_trade": min(completed_trades_pnl) if completed_trades_pnl else 0,
            "profit_factor": (total_profit / total_loss) if total_loss > 0 else (total_profit if total_profit > 0 else 0),
            "total_profit": total_profit,
            "total_loss": total_loss
        }
    
    def get_order_history(self, order_id: str) -> Dict:
        """Get order details"""
        order = self.orders.get(order_id)
        if not order:
            return {}
        
        return {
            "order_id": order.order_id,
            "status": order.status.value,
            "filled_quantity": order.filled_quantity,
            "pending_quantity": order.pending_quantity,
            "average_price": order.average_price
        }
    
    # ==================== LOGGING ====================
    
    def _log_order(self, order: PaperOrder, action: str):
        """
        Log paper trade with clear indication
        
        CRITICAL: All logs must show [PAPER TRADE] to prevent confusion
        """
        print("\n" + "="*60)
        print(f"[PAPER TRADE] {action}")
        print("="*60)
        print(f"⚠️  NO REAL MONEY - SIMULATION ONLY")
        print(f"Time:       {order.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Order ID:   {order.order_id}")
        print(f"Symbol:     {order.tradingsymbol}")
        print(f"Exchange:   {order.exchange}")
        print(f"Action:     {order.transaction_type}")
        print(f"Quantity:   {order.quantity}")
        print(f"Order Type: {order.order_type}")
        print(f"Product:    {order.product}")
        print(f"Status:     {order.status.value}")
        
        if order.average_price:
            print(f"Price:      ₹{order.average_price:.2f}")
        
        if order.trigger_price:
            print(f"SL:         ₹{order.trigger_price:.2f}")
        
        if order.tag:
            print(f"Tag:        {order.tag}")
        
        print(f"Reason:     Simulated fill using LTP")
        print("="*60)
        print()
    
    def print_summary(self):
        """Print trading summary"""
        print("\n" + "="*60)
        print("📊 PAPER TRADING SUMMARY")
        print("="*60)
        print(f"Trades Today:    {self.trades_today}")
        print(f"Open Positions:  {len(self.positions)}")
        print(f"Daily P&L:       ₹{self.daily_pnl:.2f}")
        print(f"Total P&L:       ₹{self.total_pnl:.2f}")
        print("="*60)
        print()


# Global paper trading engine instance
paper_engine = PaperTradingEngine()


def get_paper_engine() -> PaperTradingEngine:
    """Get the global paper trading engine"""
    return paper_engine
