"""
Trading Bot Configuration

CRITICAL: Controls paper trading vs live trading mode
"""

# ==================== PAPER TRADING MODE ====================
# 
# Set to True: Simulates all trades, NO REAL MONEY
# Set to False: Places REAL orders on Zerodha (USE WITH EXTREME CAUTION!)
#
# DEFAULT: True (Safe mode)
#
PAPER_TRADING = True

# ==================== RISK MANAGEMENT ====================
# Maximum loss allowed per day (in rupees)
MAX_LOSS_PER_DAY = 5000.0

# Maximum number of simultaneous positions
MAX_POSITIONS = 3

# Risk per trade as percentage of capital
RISK_PER_TRADE = 0.01  # 1%

# Maximum trades allowed per day
MAX_TRADES_PER_DAY = 10

# ==================== STRATEGY DEFAULTS ====================
# Default capital allocation per symbol
DEFAULT_CAPITAL_PER_SYMBOL = 3000.0

# Available strategies: "supertrend", "ema_rsi", "renko_macd", "breakout", "pattern"
DEFAULT_STRATEGY = "supertrend"

# List of all available strategies
AVAILABLE_STRATEGIES = [
    "supertrend",
    "ema_rsi", 
    "renko_macd",
    "breakout",
    "pattern"
]

# Default product type (MIS, CNC, NRML)
DEFAULT_PRODUCT = "MIS"

# ==================== BOT SETTINGS ====================
# How often to check for signals (in seconds)
SIGNAL_CHECK_INTERVAL = 60

# Auto square-off time (24-hour format)
AUTO_SQUARE_OFF_HOUR = 15
AUTO_SQUARE_OFF_MINUTE = 15

# Enable tick data storage in SQLite
ENABLE_TICK_STORAGE = False

# ==================== LOGGING ====================
# Enable detailed logging
VERBOSE_LOGGING = True

# Log file path
LOG_FILE_PATH = "trading_bot.log"
