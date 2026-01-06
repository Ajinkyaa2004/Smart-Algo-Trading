"""
Market Hours Utility
Provides functions to check if Indian stock markets are open
"""
from datetime import datetime, time
import pytz


class MarketHours:
    """Indian Stock Market hours checker"""
    
    # Indian timezone
    IST = pytz.timezone('Asia/Kolkata')
    
    # Market timings (Monday to Friday)
    PRE_OPEN_START = time(9, 0)   # 9:00 AM
    PRE_OPEN_END = time(9, 15)     # 9:15 AM
    MARKET_OPEN = time(9, 15)      # 9:15 AM
    MARKET_CLOSE = time(15, 30)    # 3:30 PM
    POST_CLOSE = time(16, 0)       # 4:00 PM
    
    # Market holidays for 2025 (update annually)
    # Source: NSE, BSE holiday calendars
    HOLIDAYS_2025 = [
        # January
        datetime(2025, 1, 26),  # Republic Day
        # February
        datetime(2025, 2, 26),  # Mahashivratri
        # March
        datetime(2025, 3, 14),  # Holi
        datetime(2025, 3, 31),  # Id-Ul-Fitr
        # April
        datetime(2025, 4, 10),  # Mahavir Jayanti
        datetime(2025, 4, 14),  # Dr. Ambedkar Jayanti
        datetime(2025, 4, 18),  # Good Friday
        # May
        datetime(2025, 5, 1),   # Maharashtra Day
        # June
        datetime(2025, 6, 7),   # Id-Ul-Adha (Bakri Id)
        # July
        # August
        datetime(2025, 8, 15),  # Independence Day
        datetime(2025, 8, 27),  # Ganesh Chaturthi
        # September
        # October
        datetime(2025, 10, 2),  # Gandhi Jayanti
        datetime(2025, 10, 21), # Dussehra
        datetime(2025, 10, 30), # Diwali-Laxmi Pujan
        # November
        datetime(2025, 11, 5),  # Diwali-Balipratipada
        datetime(2025, 11, 24), # Gurunanak Jayanti
        # December
        datetime(2025, 12, 25), # Christmas
    ]
    
    @classmethod
    def get_ist_now(cls) -> datetime:
        """Get current time in IST"""
        return datetime.now(cls.IST)
    
    @classmethod
    def is_market_holiday(cls, date: datetime = None) -> bool:
        """Check if given date is a market holiday"""
        if date is None:
            date = cls.get_ist_now()
        
        # Check if weekend (Saturday=5, Sunday=6)
        if date.weekday() >= 5:
            return True
        
        # Check if in holiday list
        date_only = date.date()
        for holiday in cls.HOLIDAYS_2025:
            if holiday.date() == date_only:
                return True
        
        return False
    
    @classmethod
    def get_market_status(cls) -> dict:
        """
        Get current market status
        
        Returns:
            dict with status, session, and timing info
        """
        now = cls.get_ist_now()
        current_time = now.time()
        
        # Check if holiday
        if cls.is_market_holiday(now):
            return {
                "status": "CLOSED",
                "session": "HOLIDAY",
                "current_time": now.strftime("%I:%M:%S %p"),
                "next_open": cls.get_next_market_open(now)
            }
        
        # Check if weekend
        if now.weekday() >= 5:
            return {
                "status": "CLOSED",
                "session": "WEEKEND",
                "current_time": now.strftime("%I:%M:%S %p"),
                "next_open": cls.get_next_market_open(now)
            }
        
        # Check pre-open
        if cls.PRE_OPEN_START <= current_time < cls.PRE_OPEN_END:
            market_open_today = cls.IST.localize(datetime.combine(now.date(), cls.MARKET_OPEN))
            return {
                "status": "PRE-OPEN",
                "session": "PRE-MARKET",
                "current_time": now.strftime("%I:%M:%S %p"),
                "opens_in": str(market_open_today - now).split('.')[0]
            }
        
        # Check market open
        if cls.MARKET_OPEN <= current_time < cls.MARKET_CLOSE:
            market_close_today = cls.IST.localize(datetime.combine(now.date(), cls.MARKET_CLOSE))
            return {
                "status": "OPEN",
                "session": "REGULAR",
                "current_time": now.strftime("%I:%M:%S %p"),
                "closes_in": str(market_close_today - now).split('.')[0]
            }
        
        # Check post-close
        if cls.MARKET_CLOSE <= current_time < cls.POST_CLOSE:
            return {
                "status": "CLOSED",
                "session": "POST-MARKET",
                "current_time": now.strftime("%I:%M:%S %p"),
                "next_open": cls.get_next_market_open(now)
            }
        
        # After hours
        return {
            "status": "CLOSED",
            "session": "AFTER-HOURS",
            "current_time": now.strftime("%I:%M:%S %p"),
            "next_open": cls.get_next_market_open(now)
        }
    
    @classmethod
    def is_market_open(cls) -> bool:
        """Check if market is currently open"""
        status = cls.get_market_status()
        return status["status"] == "OPEN"
    
    @classmethod
    def is_pre_open(cls) -> bool:
        """Check if market is in pre-open session"""
        status = cls.get_market_status()
        return status["status"] == "PRE-OPEN"
    
    @classmethod
    def should_stream_data(cls) -> bool:
        """Check if we should stream live data (market open or pre-open)"""
        status = cls.get_market_status()
        return status["status"] in ["OPEN", "PRE-OPEN"]
    
    @classmethod
    def get_next_market_open(cls, from_date: datetime = None) -> str:
        """Get next market open time"""
        if from_date is None:
            from_date = cls.get_ist_now()
        
        # Start checking from tomorrow if after market hours
        check_date = from_date
        if from_date.time() >= cls.MARKET_CLOSE:
            check_date = from_date.replace(hour=0, minute=0, second=0) + timedelta(days=1)
        else:
            check_date = from_date.replace(hour=9, minute=15, second=0)
        
        # Find next non-holiday weekday
        for i in range(10):  # Check next 10 days
            test_date = check_date + timedelta(days=i)
            if not cls.is_market_holiday(test_date):
                next_open = test_date.replace(hour=9, minute=15, second=0)
                return next_open.strftime("%d %b %Y, %I:%M %p")
        
        return "Unknown"


# Singleton instance
market_hours = MarketHours()


# Import for timedelta
from datetime import timedelta
