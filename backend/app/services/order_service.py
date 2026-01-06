"""
Order Management Service
Handles order placement, modification, cancellation, and portfolio queries

PAPER TRADING MODE: This service now supports paper trading to prevent real orders
"""
from typing import Dict, List, Optional, Tuple
import pandas as pd
import time
from kiteconnect import KiteConnect
from app.services.kite_auth import kite_auth_service
from app.services.paper_trading import paper_engine, PAPER_TRADING_MODE


class OrderService:
    """
    Service for order management and portfolio operations
    - Place, modify, cancel orders
    - Fetch orders, positions, holdings
    """
    
    def _get_kite(self) -> KiteConnect:
        """Get authenticated Kite instance"""
        return kite_auth_service.get_kite_instance()
    
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
        validity: str = "DAY",
        disclosed_quantity: Optional[int] = None,
        tag: Optional[str] = None
    ) -> str:
        """
        Place an order (PAPER TRADING MODE ENABLED)
        
        If PAPER_TRADING_MODE = True: Simulates order, no real money
        If PAPER_TRADING_MODE = False: Places real order on Zerodha
        
        Args:
            tradingsymbol: Trading symbol (e.g., "RELIANCE")
            exchange: Exchange (NSE, BSE, NFO, etc.)
            transaction_type: BUY or SELL
            quantity: Order quantity
            order_type: MARKET, LIMIT, SL, SL-M
            product: CNC, MIS, NRML
            price: Limit price (required for LIMIT orders)
            trigger_price: Trigger price (required for SL orders)
            validity: DAY or IOC
            disclosed_quantity: Disclosed quantity for iceberg orders
            tag: Custom tag for order tracking
            
        Returns:
            Order ID
        """
        # ==================== PAPER TRADING MODE ====================
        if PAPER_TRADING_MODE:
            return paper_engine.place_order(
                tradingsymbol=tradingsymbol,
                exchange=exchange,
                transaction_type=transaction_type,
                quantity=quantity,
                order_type=order_type,
                product=product,
                price=price,
                trigger_price=trigger_price,
                tag=tag
            )
        
        # ==================== REAL TRADING MODE ====================
        # WARNING: Below code will place REAL orders on Zerodha!
        try:
            kite = self._get_kite()
            
            order_params = {
                "tradingsymbol": tradingsymbol,
                "exchange": exchange,
                "transaction_type": transaction_type,
                "quantity": quantity,
                "order_type": order_type,
                "product": product,
                "validity": validity
            }
            
            # Add optional parameters
            if price is not None:
                order_params["price"] = price
            if trigger_price is not None:
                order_params["trigger_price"] = trigger_price
            if disclosed_quantity is not None:
                order_params["disclosed_quantity"] = disclosed_quantity
            if tag is not None:
                order_params["tag"] = tag
            
            order_id = kite.place_order(**order_params)
            
            print(f"✓ REAL ORDER placed: {order_id} - {transaction_type} {quantity} {tradingsymbol}")
            return order_id
            
        except Exception as e:
            raise Exception(f"Failed to place order: {str(e)}")
    
    def place_market_order(
        self,
        tradingsymbol: str,
        exchange: str,
        transaction_type: str,
        quantity: int,
        product: str = "MIS",
        tag: Optional[str] = None
    ) -> str:
        """
        Convenience method for market orders
        
        Args:
            tradingsymbol: Trading symbol
            exchange: Exchange
            transaction_type: BUY or SELL
            quantity: Order quantity
            product: CNC, MIS, NRML
            tag: Custom tag
            
        Returns:
            Order ID
        """
        return self.place_order(
            tradingsymbol=tradingsymbol,
            exchange=exchange,
            transaction_type=transaction_type,
            quantity=quantity,
            order_type="MARKET",
            product=product,
            tag=tag
        )
    
    def place_limit_order(
        self,
        tradingsymbol: str,
        exchange: str,
        transaction_type: str,
        quantity: int,
        price: float,
        product: str = "MIS",
        tag: Optional[str] = None
    ) -> str:
        """
        Convenience method for limit orders
        
        Args:
            tradingsymbol: Trading symbol
            exchange: Exchange
            transaction_type: BUY or SELL
            quantity: Order quantity
            price: Limit price
            product: CNC, MIS, NRML
            tag: Custom tag
            
        Returns:
            Order ID
        """
        return self.place_order(
            tradingsymbol=tradingsymbol,
            exchange=exchange,
            transaction_type=transaction_type,
            quantity=quantity,
            order_type="LIMIT",
            price=price,
            product=product,
            tag=tag
        )
    
    def place_stoploss_order(
        self,
        tradingsymbol: str,
        exchange: str,
        transaction_type: str,
        quantity: int,
        trigger_price: float,
        price: Optional[float] = None,
        product: str = "MIS",
        tag: Optional[str] = None
    ) -> str:
        """
        Place stop-loss order
        
        Args:
            tradingsymbol: Trading symbol
            exchange: Exchange
            transaction_type: BUY or SELL
            quantity: Order quantity
            trigger_price: Trigger price
            price: Limit price (None for SL-M)
            product: CNC, MIS, NRML
            tag: Custom tag
            
        Returns:
            Order ID
        """
        order_type = "SL" if price is not None else "SL-M"
        
        return self.place_order(
            tradingsymbol=tradingsymbol,
            exchange=exchange,
            transaction_type=transaction_type,
            quantity=quantity,
            order_type=order_type,
            trigger_price=trigger_price,
            price=price,
            product=product,
            tag=tag
        )
    
    def place_market_order_with_sl(
        self,
        tradingsymbol: str,
        exchange: str,
        transaction_type: str,
        quantity: int,
        sl_price: float,
        product: str = "MIS",
        tag: Optional[str] = None,
        max_retries: int = 10
    ) -> Dict[str, str]:
        """
        Place a market order and immediately place a stop-loss order
        
        This is the pattern used in supertrend and other strategies where:
        1. Market order is placed for entry
        2. Stop-loss order is placed to protect position
        
        Args:
            tradingsymbol: Trading symbol
            exchange: Exchange
            transaction_type: BUY or SELL (for market order)
            quantity: Order quantity
            sl_price: Stop-loss price
            product: CNC, MIS, NRML
            tag: Custom tag
            max_retries: Max retries to fetch order status (default: 10)
            
        Returns:
            Dictionary with market_order_id and sl_order_id
            
        Example:
            # Buy with stop-loss
            result = order_service.place_market_order_with_sl(
                tradingsymbol="RELIANCE",
                exchange="NSE",
                transaction_type="BUY",
                quantity=10,
                sl_price=2540.0
            )
        """
        # ==================== PAPER TRADING MODE ====================
        if PAPER_TRADING_MODE:
            # Place market order (paper trading)
            market_order_id = self.place_market_order(
                tradingsymbol=tradingsymbol,
                exchange=exchange,
                transaction_type=transaction_type,
                quantity=quantity,
                product=product,
                tag=tag
            )
            
            # Place SL order (paper trading) - opposite transaction type
            sl_transaction_type = "SELL" if transaction_type == "BUY" else "BUY"
            sl_order_id = paper_engine.place_order(
                tradingsymbol=tradingsymbol,
                exchange=exchange,
                transaction_type=sl_transaction_type,
                quantity=quantity,
                order_type="SL-M",
                product=product,
                trigger_price=sl_price,
                tag=f"SL_{tag}" if tag else "SL"
            )
            
            print(f"✓ [PAPER] Market + SL orders: Market={market_order_id}, SL={sl_order_id}")
            
            return {
                'success': True,
                'market_order_id': market_order_id,
                'sl_order_id': sl_order_id
            }
        
        # ==================== REAL TRADING MODE ====================
        try:
            kite = self._get_kite()
            
            # Place market order
            market_order_id = self.place_market_order(
                tradingsymbol=tradingsymbol,
                exchange=exchange,
                transaction_type=transaction_type,
                quantity=quantity,
                product=product,
                tag=tag
            )
            
            # Wait for market order to complete and then place SL
            order_completed = False
            for attempt in range(max_retries):
                try:
                    orders = self.get_orders()
                    for order in orders:
                        if order["order_id"] == market_order_id:
                            if order["status"] == "COMPLETE":
                                order_completed = True
                                break
                            elif order["status"] in ["REJECTED", "CANCELLED"]:
                                print(f"✗ Market order {market_order_id} was {order['status']}")
                                return {
                                    'success': False,
                                    'market_order_id': market_order_id,
                                    'sl_order_id': None,
                                    'message': f"Market order {order['status']}"
                                }
                    
                    if order_completed:
                        break
                    
                    time.sleep(0.5)
                except Exception as e:
                    print(f"Error checking order status (attempt {attempt+1}): {str(e)}")
            
            if not order_completed:
                print(f"⚠ Market order status unclear, placing SL anyway")
            
            # Determine SL transaction type (opposite of market order)
            sl_transaction_type = "SELL" if transaction_type == "BUY" else "BUY"
            
            # Place stop-loss order
            sl_order_id = self.place_stoploss_order(
                tradingsymbol=tradingsymbol,
                exchange=exchange,
                transaction_type=sl_transaction_type,
                quantity=quantity,
                trigger_price=sl_price,
                price=sl_price,  # SL order (not SL-M)
                product=product,
                tag=f"SL_{tag}" if tag else "SL"
            )
            
            print(f"✓ Market + SL orders placed: Market={market_order_id}, SL={sl_order_id}")
            
            return {
                'success': True,
                'market_order_id': market_order_id,
                'sl_order_id': sl_order_id,
                'message': 'Orders placed successfully'
            }
            
        except Exception as e:
            raise Exception(f"Failed to place market order with SL: {str(e)}")
    
    def place_bracket_order(
        self,
        tradingsymbol: str,
        exchange: str,
        transaction_type: str,
        quantity: int,
        price: float,
        squareoff: int,
        stoploss: int,
        trailing_stoploss: Optional[int] = None,
        product: str = "MIS",
        tag: Optional[str] = None
    ) -> str:
        """
        Place a bracket order (BO) with automatic stop-loss and target
        
        Bracket orders are advanced intraday orders that allow you to place:
        - Main order (limit order)
        - Target order (profit booking)
        - Stop-loss order (risk management)
        - Optional trailing stop-loss
        
        Args:
            tradingsymbol: Trading symbol (e.g., "RELIANCE")
            exchange: Exchange (NSE, BSE, NFO, etc.)
            transaction_type: BUY or SELL
            quantity: Order quantity
            price: Limit price for the main order (BO must be limit order)
            squareoff: Target profit in absolute points (e.g., 6 * ATR)
            stoploss: Stop-loss in absolute points (e.g., 3 * ATR)
            trailing_stoploss: Trailing SL in ticks (optional, e.g., 2)
            product: Product type (only MIS supported for BO)
            tag: Custom tag for order tracking
            
        Returns:
            Order ID
            
        Example:
            # Buy RELIANCE with 10 point target and 5 point SL
            order_id = order_service.place_bracket_order(
                tradingsymbol="RELIANCE",
                exchange="NSE",
                transaction_type="BUY",
                quantity=1,
                price=2550.0,
                squareoff=10,  # Target: 2560
                stoploss=5,    # SL: 2545
                trailing_stoploss=2
            )
        
        Note:
            - Bracket orders are only available for intraday (MIS)
            - The main order must be a LIMIT order
            - squareoff and stoploss are in absolute points, not percentage
            - trailing_stoploss moves SL as price moves in your favor
        """
        try:
            kite = self._get_kite()
            
            order_params = {
                "tradingsymbol": tradingsymbol,
                "exchange": exchange,
                "transaction_type": transaction_type,
                "quantity": quantity,
                "order_type": "LIMIT",  # BO must be LIMIT order
                "price": price,
                "product": product,
                "variety": "bo",  # Bracket Order variety
                "squareoff": squareoff,
                "stoploss": stoploss
            }
            
            # Add optional trailing stop-loss
            if trailing_stoploss is not None:
                order_params["trailing_stoploss"] = trailing_stoploss
            
            # Add tag if provided
            if tag is not None:
                order_params["tag"] = tag
            
            order_id = kite.place_order(**order_params)
            
            print(f"✓ Bracket Order placed: {order_id} - {transaction_type} {quantity} {tradingsymbol}")
            print(f"  Price: {price}, Target: +{squareoff}, SL: -{stoploss}")
            if trailing_stoploss:
                print(f"  Trailing SL: {trailing_stoploss} ticks")
            
            return order_id
            
        except Exception as e:
            raise Exception(f"Failed to place bracket order: {str(e)}")
    
    # ==================== ORDER MODIFICATION ====================
    
    def modify_order(
        self,
        order_id: str,
        quantity: Optional[int] = None,
        price: Optional[float] = None,
        trigger_price: Optional[float] = None,
        order_type: Optional[str] = None,
        validity: Optional[str] = None
    ) -> str:
        """
        Modify an existing order (PAPER TRADING MODE ENABLED)
        
        Args:
            order_id: Order ID to modify
            quantity: New quantity
            price: New price
            trigger_price: New trigger price
            order_type: New order type
            validity: New validity
            
        Returns:
            Order ID
        """
        # ==================== PAPER TRADING MODE ====================
        if PAPER_TRADING_MODE:
            paper_engine.modify_order(
                order_id=order_id,
                quantity=quantity,
                price=price,
                trigger_price=trigger_price
            )
            return order_id
        
        # ==================== REAL TRADING MODE ====================
        try:
            kite = self._get_kite()
            
            modify_params = {}
            if quantity is not None:
                modify_params["quantity"] = quantity
            if price is not None:
                modify_params["price"] = price
            if trigger_price is not None:
                modify_params["trigger_price"] = trigger_price
            if order_type is not None:
                modify_params["order_type"] = order_type
            if validity is not None:
                modify_params["validity"] = validity
            
            result = kite.modify_order(order_id, **modify_params)
            
            print(f"✓ REAL ORDER modified: {order_id}")
            return result
            
        except Exception as e:
            raise Exception(f"Failed to modify order: {str(e)}")
    
    # ==================== ORDER CANCELLATION ====================
    
    def cancel_order(self, order_id: str, variety: str = "regular") -> str:
        """
        Cancel an order (PAPER TRADING MODE ENABLED)
        
        Args:
            order_id: Order ID
            variety: Order variety (regular, amo, co, iceberg)
            
        Returns:
            Order ID
        """
        # ==================== PAPER TRADING MODE ====================
        if PAPER_TRADING_MODE:
            paper_engine.cancel_order(order_id)
            return order_id
        
        # ==================== REAL TRADING MODE ====================
        try:
            kite = self._get_kite()
            result = kite.cancel_order(variety, order_id)
            
            print(f"✓ REAL ORDER cancelled: {order_id}")
            return result
            
        except Exception as e:
            raise Exception(f"Failed to cancel order: {str(e)}")
    
    # ==================== ORDER QUERIES ====================
    
    def get_orders(self) -> List[Dict]:
        """
        Get all orders for the day
        
        Returns:
            List of order dictionaries
        """
        try:
            kite = self._get_kite()
            orders = kite.orders()
            return orders
        except Exception as e:
            raise Exception(f"Failed to fetch orders: {str(e)}")
    
    def get_order_history(self, order_id: str) -> List[Dict]:
        """
        Get order history (all modifications)
        
        Args:
            order_id: Order ID
            
        Returns:
            List of order history entries
        """
        try:
            kite = self._get_kite()
            history = kite.order_history(order_id)
            return history
        except Exception as e:
            raise Exception(f"Failed to fetch order history: {str(e)}")
    
    def get_trades(self) -> List[Dict]:
        """
        Get all executed trades for the day
        
        Returns:
            List of trade dictionaries
        """
        try:
            kite = self._get_kite()
            trades = kite.trades()
            return trades
        except Exception as e:
            raise Exception(f"Failed to fetch trades: {str(e)}")
    
    # ==================== PORTFOLIO QUERIES ====================
    
    def get_positions(self) -> Dict:
        """
        Get current positions (PAPER TRADING MODE ENABLED)
        
        Returns:
            Dictionary with 'net' and 'day' positions
        """
        # ==================== PAPER TRADING MODE ====================
        if PAPER_TRADING_MODE:
            positions = paper_engine.get_positions()
            return {
                "net": positions,
                "day": positions
            }
        
        # ==================== REAL TRADING MODE ====================
        try:
            kite = self._get_kite()
            positions = kite.positions()
            return positions
        except Exception as e:
            raise Exception(f"Failed to fetch positions: {str(e)}")
    
    def get_holdings(self) -> List[Dict]:
        """
        Get long-term holdings
        
        Returns:
            List of holding dictionaries
        """
        try:
            kite = self._get_kite()
            holdings = kite.holdings()
            return holdings
        except Exception as e:
            raise Exception(f"Failed to fetch holdings: {str(e)}")
    
    def convert_position(
        self,
        tradingsymbol: str,
        exchange: str,
        transaction_type: str,
        position_type: str,
        quantity: int,
        old_product: str,
        new_product: str
    ) -> bool:
        """
        Convert position product type (e.g., MIS to CNC)
        
        Args:
            tradingsymbol: Trading symbol
            exchange: Exchange
            transaction_type: BUY or SELL
            position_type: day or overnight
            quantity: Quantity to convert
            old_product: Current product type
            new_product: Target product type
            
        Returns:
            Success status
        """
        try:
            kite = self._get_kite()
            
            result = kite.convert_position(
                tradingsymbol=tradingsymbol,
                exchange=exchange,
                transaction_type=transaction_type,
                position_type=position_type,
                quantity=quantity,
                old_product=old_product,
                new_product=new_product
            )
            
            print(f"✓ Position converted: {tradingsymbol} from {old_product} to {new_product}")
            return True
            
        except Exception as e:
            raise Exception(f"Failed to convert position: {str(e)}")
    
    # ==================== AUTO SQUARE OFF ====================
    
    def square_off_all_positions(
        self, 
        max_retries: int = 10,
        product_type: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Close all open positions by placing reverse market orders
        
        This function iterates through all positions and:
        - For long positions (quantity > 0): Places SELL market orders
        - For short positions (quantity < 0): Places BUY market orders
        
        Args:
            max_retries: Maximum retry attempts for fetching positions (default: 10)
            product_type: Filter by product type ('MIS', 'CNC', 'NRML', None for all)
            
        Returns:
            Dictionary with summary:
            {
                'success': True/False,
                'closed_positions': int,
                'failed_positions': List[str],
                'order_ids': List[str]
            }
        """
        try:
            # Fetch current positions with retry logic
            pos_df = None
            for attempt in range(max_retries):
                try:
                    positions = self.get_positions()
                    pos_df = pd.DataFrame(positions["day"])
                    break
                except Exception as e:
                    print(f"Can't extract position data...retrying ({attempt+1}/{max_retries})")
                    time.sleep(0.5)
            
            if pos_df is None or pos_df.empty:
                return {
                    'success': True,
                    'closed_positions': 0,
                    'failed_positions': [],
                    'order_ids': [],
                    'message': 'No open positions found'
                }
            
            # Filter by product type if specified
            if product_type:
                pos_df = pos_df[pos_df['product'] == product_type]
            
            closed_count = 0
            failed_positions = []
            order_ids = []
            
            # Close each position
            for i in range(len(pos_df)):
                ticker = pos_df["tradingsymbol"].iloc[i]
                quantity = pos_df["quantity"].iloc[i]
                exchange = pos_df["exchange"].iloc[i]
                product = pos_df["product"].iloc[i]
                
                # Skip if no open position
                if quantity == 0:
                    continue
                
                try:
                    # Long position: Sell to close
                    if quantity > 0:
                        order_id = self.place_market_order(
                            tradingsymbol=ticker,
                            exchange=exchange,
                            transaction_type="SELL",
                            quantity=quantity,
                            product=product,
                            tag="AUTO_SQUAREOFF"
                        )
                        order_ids.append(order_id)
                        closed_count += 1
                        print(f"✓ Closed LONG position: {ticker} x{quantity}")
                    
                    # Short position: Buy to close
                    elif quantity < 0:
                        order_id = self.place_market_order(
                            tradingsymbol=ticker,
                            exchange=exchange,
                            transaction_type="BUY",
                            quantity=abs(quantity),
                            product=product,
                            tag="AUTO_SQUAREOFF"
                        )
                        order_ids.append(order_id)
                        closed_count += 1
                        print(f"✓ Closed SHORT position: {ticker} x{abs(quantity)}")
                
                except Exception as e:
                    failed_positions.append(f"{ticker}: {str(e)}")
                    print(f"✗ Failed to close position {ticker}: {str(e)}")
            
            return {
                'success': len(failed_positions) == 0,
                'closed_positions': closed_count,
                'failed_positions': failed_positions,
                'order_ids': order_ids,
                'message': f'Closed {closed_count} positions'
            }
            
        except Exception as e:
            return {
                'success': False,
                'closed_positions': 0,
                'failed_positions': [],
                'order_ids': [],
                'message': f'Error: {str(e)}'
            }
    
    def cancel_all_pending_orders(
        self, 
        max_retries: int = 10,
        max_attempts_per_order: int = 5
    ) -> Dict[str, any]:
        """
        Cancel all pending orders (OPEN or TRIGGER PENDING status)
        
        Args:
            max_retries: Maximum retry attempts for fetching orders (default: 10)
            max_attempts_per_order: Maximum attempts to cancel each order (default: 5)
            
        Returns:
            Dictionary with summary:
            {
                'success': True/False,
                'cancelled_orders': int,
                'failed_orders': List[str],
                'order_ids': List[str]
            }
        """
        try:
            # Fetch all orders with retry logic
            ord_df = None
            for attempt in range(max_retries):
                try:
                    orders = self.get_orders()
                    ord_df = pd.DataFrame(orders)
                    break
                except Exception as e:
                    print(f"Can't extract order data...retrying ({attempt+1}/{max_retries})")
                    time.sleep(0.5)
            
            if ord_df is None or ord_df.empty:
                return {
                    'success': True,
                    'cancelled_orders': 0,
                    'failed_orders': [],
                    'order_ids': [],
                    'message': 'No orders found'
                }
            
            # Filter pending orders
            pending_statuses = ["TRIGGER PENDING", "OPEN"]
            pending_orders = ord_df[ord_df['status'].isin(pending_statuses)]["order_id"].tolist()
            
            if not pending_orders:
                return {
                    'success': True,
                    'cancelled_orders': 0,
                    'failed_orders': [],
                    'order_ids': [],
                    'message': 'No pending orders found'
                }
            
            cancelled_count = 0
            failed_orders = []
            cancelled_ids = []
            
            # Try to cancel each order with retry logic
            attempt = 0
            while len(pending_orders) > 0 and attempt < max_attempts_per_order:
                for order_id in pending_orders[:]:  # Iterate over copy
                    try:
                        self.cancel_order(order_id)
                        pending_orders.remove(order_id)
                        cancelled_ids.append(order_id)
                        cancelled_count += 1
                        print(f"✓ Cancelled order: {order_id}")
                    except Exception as e:
                        print(f"Unable to cancel order {order_id}: {str(e)}")
                
                attempt += 1
                if len(pending_orders) > 0:
                    time.sleep(0.5)  # Brief pause before retry
            
            # Any remaining orders are failures
            if len(pending_orders) > 0:
                failed_orders = [f"{oid}: Max attempts exceeded" for oid in pending_orders]
            
            return {
                'success': len(failed_orders) == 0,
                'cancelled_orders': cancelled_count,
                'failed_orders': failed_orders,
                'order_ids': cancelled_ids,
                'message': f'Cancelled {cancelled_count} orders'
            }
            
        except Exception as e:
            return {
                'success': False,
                'cancelled_orders': 0,
                'failed_orders': [],
                'order_ids': [],
                'message': f'Error: {str(e)}'
            }
    
    def auto_square_off(
        self,
        close_positions: bool = True,
        cancel_orders: bool = True,
        product_type: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Complete auto square off: Close all positions and cancel all pending orders
        
        This is typically used at end of day or for risk management to:
        1. Close all open positions
        2. Cancel all pending orders
        
        Args:
            close_positions: Whether to close open positions (default: True)
            cancel_orders: Whether to cancel pending orders (default: True)
            product_type: Filter positions by product type ('MIS', 'CNC', 'NRML', None for all)
            
        Returns:
            Dictionary with complete summary
        """
        result = {
            'positions': None,
            'orders': None,
            'success': True,
            'message': 'Auto square off completed'
        }
        
        # Close positions
        if close_positions:
            print("=" * 60)
            print("CLOSING ALL OPEN POSITIONS")
            print("=" * 60)
            pos_result = self.square_off_all_positions(product_type=product_type)
            result['positions'] = pos_result
            if not pos_result['success']:
                result['success'] = False
        
        # Cancel pending orders
        if cancel_orders:
            print("\n" + "=" * 60)
            print("CANCELLING ALL PENDING ORDERS")
            print("=" * 60)
            ord_result = self.cancel_all_pending_orders()
            result['orders'] = ord_result
            if not ord_result['success']:
                result['success'] = False
        
        # Summary
        print("\n" + "=" * 60)
        print("AUTO SQUARE OFF SUMMARY")
        print("=" * 60)
        if result['positions']:
            print(f"Positions closed: {result['positions']['closed_positions']}")
            if result['positions']['failed_positions']:
                print(f"Failed positions: {len(result['positions']['failed_positions'])}")
        
        if result['orders']:
            print(f"Orders cancelled: {result['orders']['cancelled_orders']}")
            if result['orders']['failed_orders']:
                print(f"Failed orders: {len(result['orders']['failed_orders'])}")
        
        print("=" * 60)
        
        return result


# Global singleton instance
order_service = OrderService()
