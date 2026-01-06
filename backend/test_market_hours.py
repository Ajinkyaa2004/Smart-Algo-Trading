"""
Test Market Hours Utility
Run this to verify market hours detection is working correctly
"""
import sys
sys.path.append('..')

from app.services.market_hours import market_hours
from datetime import datetime, timedelta

print("=" * 70)
print("🧪 TESTING MARKET HOURS UTILITY")
print("=" * 70)

# Test 1: Current market status
print("\n1️⃣  Current Market Status:")
print("-" * 70)
status = market_hours.get_market_status()
for key, value in status.items():
    print(f"   {key}: {value}")

# Test 2: Market open check
print("\n2️⃣  Market State Checks:")
print("-" * 70)
print(f"   Is market open? {market_hours.is_market_open()}")
print(f"   Is pre-open? {market_hours.is_pre_open()}")
print(f"   Should stream data? {market_hours.should_stream_data()}")

# Test 3: Simulate different times
print("\n3️⃣  Simulated Time Checks:")
print("-" * 70)

# Test weekday at 10:00 AM (market should be OPEN)
ist = market_hours.IST
now = market_hours.get_ist_now()

# Find next Monday
days_ahead = 0 - now.weekday()  # Monday is 0
if days_ahead <= 0:
    days_ahead += 7
test_date = now + timedelta(days=days_ahead)
test_date = test_date.replace(hour=10, minute=0, second=0)

print(f"   Simulating: {test_date.strftime('%A, %d %b %Y %I:%M %p')}")
# Note: We can't easily test this without modifying the class

# Test 4: Holiday check
print("\n4️⃣  Holiday Detection:")
print("-" * 70)
print(f"   Is today a holiday? {market_hours.is_market_holiday()}")
print(f"   Holidays in 2025: {len(market_hours.HOLIDAYS_2025)}")
print(f"   Next few holidays:")
for holiday in market_hours.HOLIDAYS_2025[:5]:
    print(f"      - {holiday.strftime('%d %b %Y (%A)')}")

# Test 5: Market timings
print("\n5️⃣  Market Timings (IST):")
print("-" * 70)
print(f"   Pre-open starts: {market_hours.PRE_OPEN_START.strftime('%I:%M %p')}")
print(f"   Market opens: {market_hours.MARKET_OPEN.strftime('%I:%M %p')}")
print(f"   Market closes: {market_hours.MARKET_CLOSE.strftime('%I:%M %p')}")
print(f"   Post-close ends: {market_hours.POST_CLOSE.strftime('%I:%M %p')}")

print("\n" + "=" * 70)
print("✅ ALL TESTS COMPLETED")
print("=" * 70)
print()
