"""
Production Configuration
This file contains production-ready settings
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ==================== PAPER TRADING MODE ====================
PAPER_TRADING = os.getenv("PAPER_TRADING", "True").lower() == "true"

# ==================== RISK MANAGEMENT ====================
MAX_LOSS_PER_DAY = float(os.getenv("MAX_LOSS_PER_DAY", "5000.0"))
MAX_POSITIONS = int(os.getenv("MAX_POSITIONS", "3"))
RISK_PER_TRADE = float(os.getenv("RISK_PER_TRADE", "0.01"))
MAX_TRADES_PER_DAY = int(os.getenv("MAX_TRADES_PER_DAY", "10"))

# ==================== STRATEGY DEFAULTS ====================
DEFAULT_CAPITAL_PER_SYMBOL = float(os.getenv("DEFAULT_CAPITAL_PER_SYMBOL", "3000.0"))
DEFAULT_PRODUCT = os.getenv("DEFAULT_PRODUCT", "MIS")

# ==================== BOT SETTINGS ====================
SIGNAL_CHECK_INTERVAL = int(os.getenv("SIGNAL_CHECK_INTERVAL", "60"))
AUTO_SQUARE_OFF_HOUR = int(os.getenv("AUTO_SQUARE_OFF_HOUR", "15"))
AUTO_SQUARE_OFF_MINUTE = int(os.getenv("AUTO_SQUARE_OFF_MINUTE", "15"))
ENABLE_TICK_STORAGE = os.getenv("ENABLE_TICK_STORAGE", "False").lower() == "true"

# ==================== LOGGING ====================
VERBOSE_LOGGING = os.getenv("VERBOSE_LOGGING", "True").lower() == "true"
