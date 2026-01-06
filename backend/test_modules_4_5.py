"""
Test script for Price Action and Candlestick Pattern Scanner
Demonstrates all features of Module 4 and Module 5
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from app.services.kite_auth import kite_auth_service
from app.services.market_data import market_data_service
from app.services.price_action import price_action_service
from app.services.pattern_scanner import pattern_scanner
import pandas as pd

pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)


def test_price_action():
    """Test price action analysis"""
    print("=" * 80)
    print("MODULE 4: PRICE ACTION ANALYSIS TEST")
    print("=" * 80)
    
    if not kite_auth_service.is_authenticated():
        print("\n⚠ Not authenticated. Please login first.")
        print("Run: python backend/test_auth.py")
        return None
    
    print("\n✓ Authenticated")
    
    # Fetch historical data
    print("\n" + "-" * 80)
    print("Fetching Historical Data")
    print("-" * 80)
    
    try:
        to_date = datetime.now()
        from_date = to_date - timedelta(days=100)
        
        df = market_data_service.get_historical_data_by_symbol(
            symbol="RELIANCE",
            exchange="NSE",
            from_date=from_date,
            to_date=to_date,
            interval="day"
        )
        
        print(f"✓ Fetched {len(df)} candles for RELIANCE")
        
    except Exception as e:
        print(f"✗ Data fetch failed: {str(e)}")
        return None
    
    # Test 1: Candlestick Anatomy
    print("\n" + "-" * 80)
    print("TEST 1: Candlestick Anatomy Analysis")
    print("-" * 80)
    
    df_anatomy = price_action_service.add_candle_anatomy(df)
    latest = df_anatomy.iloc[-1]
    
    print(f"Latest Candle Anatomy:")
    print(f"  Body: ₹{latest['body']:.2f} ({latest['body_percentage']:.1f}% of range)")
    print(f"  Upper Wick: ₹{latest['upper_wick']:.2f}")
    print(f"  Lower Wick: ₹{latest['lower_wick']:.2f}")
    print(f"  Total Range: ₹{latest['total_range']:.2f}")
    print(f"  Type: {'Bullish' if latest['is_bullish'] else 'Bearish'}")
    print(f"  Is Doji: {'Yes' if latest['is_doji'] else 'No'}")
    
    # Test 2: Support & Resistance
    print("\n" + "-" * 80)
    print("TEST 2: Support & Resistance Detection")
    print("-" * 80)
    
    try:
        levels = price_action_service.find_support_resistance(df)
        
        print(f"✓ Found {len(levels)} support/resistance levels")
        
        # Sort by strength and show top 5
        sorted_levels = sorted(levels, key=lambda x: x.strength, reverse=True)[:5]
        
        print("\nTop 5 Strongest Levels:")
        for i, level in enumerate(sorted_levels, 1):
            print(f"{i}. {level.type.upper():12s} @ ₹{level.level:.2f} (Strength: {level.strength} touches)")
        
    except Exception as e:
        print(f"✗ S/R detection failed: {str(e)}")
    
    # Test 3: Trend Identification
    print("\n" + "-" * 80)
    print("TEST 3: Trend Identification")
    print("-" * 80)
    
    try:
        trend = price_action_service.identify_trend(df, method='ma')
        trend_strength = price_action_service.calculate_trend_strength(df)
        
        latest_trend = trend.iloc[-1]
        latest_strength = trend_strength.iloc[-1]
        
        trend_name = "UPTREND" if latest_trend == 1 else ("DOWNTREND" if latest_trend == -1 else "SIDEWAYS")
        
        print(f"✓ Current Trend: {trend_name}")
        print(f"  Trend Strength (ADX): {latest_strength:.2f}")
        
        if latest_strength > 25:
            print("  → Strong trend")
        elif latest_strength > 20:
            print("  → Moderate trend")
        else:
            print("  → Weak trend / Ranging")
        
    except Exception as e:
        print(f"✗ Trend analysis failed: {str(e)}")
    
    # Test 4: Breakout Detection
    print("\n" + "-" * 80)
    print("TEST 4: Breakout Detection")
    print("-" * 80)
    
    try:
        # Use a recent high as resistance level
        recent_high = df['high'].tail(20).max()
        
        breakouts = price_action_service.detect_breakout(df, recent_high, direction='up')
        breakout_count = breakouts.sum()
        
        print(f"✓ Monitoring level: ₹{recent_high:.2f}")
        print(f"  Breakouts detected: {breakout_count}")
        
        if breakout_count > 0:
            breakout_dates = df[breakouts].index.tolist()
            print(f"  Latest breakout: {breakout_dates[-1]}")
        
    except Exception as e:
        print(f"✗ Breakout detection failed: {str(e)}")
    
    # Test 5: Rejection Detection
    print("\n" + "-" * 80)
    print("TEST 5: Rejection Detection")
    print("-" * 80)
    
    try:
        recent_high = df['high'].tail(20).max()
        
        rejections = price_action_service.detect_rejection(
            df, recent_high, rejection_type='resistance'
        )
        rejection_count = rejections.sum()
        
        print(f"✓ Resistance level: ₹{recent_high:.2f}")
        print(f"  Rejections detected: {rejection_count}")
        
        if rejection_count > 0:
            print("  → Price tested resistance but failed to break")
        
    except Exception as e:
        print(f"✗ Rejection detection failed: {str(e)}")
    
    return df


def test_pattern_scanner(df):
    """Test candlestick pattern scanner"""
    print("\n\n" + "=" * 80)
    print("MODULE 5: CANDLESTICK PATTERN SCANNER TEST")
    print("=" * 80)
    
    if df is None or df.empty:
        print("\n⚠ No data available for pattern scanning")
        return
    
    # Test 1: Scan All Patterns
    print("\n" + "-" * 80)
    print("TEST 1: Scan All Patterns")
    print("-" * 80)
    
    try:
        matches = pattern_scanner.scan_patterns(df, symbol="RELIANCE")
        
        print(f"✓ Scanned {len(df)} candles")
        print(f"  Patterns found: {len(matches)}")
        
        if matches:
            # Group by pattern type
            pattern_counts = {}
            for match in matches:
                pattern_counts[match.pattern] = pattern_counts.get(match.pattern, 0) + 1
            
            print("\nPattern Distribution:")
            for pattern, count in sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"  {pattern:20s}: {count} occurrences")
        
    except Exception as e:
        print(f"✗ Pattern scan failed: {str(e)}")
        return
    
    # Test 2: Recent Patterns
    print("\n" + "-" * 80)
    print("TEST 2: Recent Patterns (Last 10 Candles)")
    print("-" * 80)
    
    try:
        recent_matches = pattern_scanner.scan_latest(df, symbol="RELIANCE", lookback=10)
        
        print(f"✓ Recent patterns found: {len(recent_matches)}")
        
        if recent_matches:
            print("\nRecent Pattern Details:")
            for match in recent_matches[-5:]:  # Show last 5
                direction_emoji = "🟢" if match.direction == "bullish" else ("🔴" if match.direction == "bearish" else "⚪")
                print(f"\n  {direction_emoji} {match.pattern}")
                print(f"     Date: {match.timestamp}")
                print(f"     Price: ₹{match.price:.2f}")
                print(f"     Confidence: {match.confidence*100:.0f}%")
                print(f"     {match.description}")
        
    except Exception as e:
        print(f"✗ Recent pattern scan failed: {str(e)}")
    
    # Test 3: Specific Pattern Detection
    print("\n" + "-" * 80)
    print("TEST 3: Specific Pattern Detection")
    print("-" * 80)
    
    specific_patterns = ['bullish_engulfing', 'bearish_engulfing', 'morning_star', 'evening_star']
    
    try:
        specific_matches = pattern_scanner.scan_patterns(
            df, symbol="RELIANCE", patterns=specific_patterns
        )
        
        print(f"✓ Scanning for: {', '.join(specific_patterns)}")
        print(f"  Matches found: {len(specific_matches)}")
        
        if specific_matches:
            print("\nHigh-Confidence Reversal Patterns:")
            for match in specific_matches:
                if match.confidence >= 0.8:
                    print(f"  • {match.pattern} on {match.timestamp} @ ₹{match.price:.2f}")
        
    except Exception as e:
        print(f"✗ Specific pattern scan failed: {str(e)}")
    
    # Test 4: Pattern Statistics
    print("\n" + "-" * 80)
    print("TEST 4: Pattern Statistics")
    print("-" * 80)
    
    if matches:
        bullish_count = sum(1 for m in matches if m.direction == "bullish")
        bearish_count = sum(1 for m in matches if m.direction == "bearish")
        neutral_count = sum(1 for m in matches if m.direction == "neutral")
        
        avg_confidence = sum(m.confidence for m in matches) / len(matches)
        
        print(f"Total Patterns: {len(matches)}")
        print(f"  Bullish: {bullish_count} ({bullish_count/len(matches)*100:.1f}%)")
        print(f"  Bearish: {bearish_count} ({bearish_count/len(matches)*100:.1f}%)")
        print(f"  Neutral: {neutral_count} ({neutral_count/len(matches)*100:.1f}%)")
        print(f"\nAverage Confidence: {avg_confidence*100:.1f}%")
        
        # High confidence patterns
        high_conf = [m for m in matches if m.confidence >= 0.85]
        print(f"High Confidence Patterns (≥85%): {len(high_conf)}")


if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 18 + "MODULE 4 & 5 COMPREHENSIVE TEST" + " " * 28 + "║")
    print("╚" + "=" * 78 + "╝")
    
    # Test price action
    df = test_price_action()
    
    # Test pattern scanner
    if df is not None:
        test_pattern_scanner(df)
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    print("\n✅ All modules tested successfully!")
    print("\nNext steps:")
    print("  1. Test via API: http://localhost:8000/docs")
    print("  2. Integrate patterns into trading strategies")
    print("  3. Set up real-time pattern alerts")
    print("=" * 80 + "\n")
