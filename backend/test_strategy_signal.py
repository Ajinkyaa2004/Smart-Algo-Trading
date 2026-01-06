
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app.strategies.base_strategy import StrategyConfig, SignalType
# Import the strategy class directly
from app.strategies.ema_scalping_strategy import EMAScalpingStrategy

def test_ema_strategy_logic():
    print("="*60)
    print("🧪 TESTING STRATEGY LOGIC: EMA Scalping (9/21)")
    print("="*60)

    # 1. Create Synthetic Data (Uptrend / Golden Cross)
    # We need enough data points for EMA calculation (at least 21 + buffer)
    periods = 50
    dates = [datetime.now() - timedelta(minutes=5 * i) for i in range(periods)]
    dates.reverse()

    # Create a crossover scenario:
    # 1. Long period of flat/low price (Fast < Slow)
    # 2. Sharp jump at the end (Fast > Slow)
    
    # 48 candles at 100
    # 2 candles at 110
    
    prices = np.concatenate([
        np.full(45, 100.0), 
        np.array([100.0, 102.0, 105.0, 110.0, 115.0]) # Sharp rise
    ])
    
    # Actually, we need to tune it so the cross happens at the last step.
    # Let's simple check:
    # Previous: Fast < Slow
    # Current: Fast > Slow
    
    # Let's try a simpler approach manually constructed if needed, 
    # but let's try a sharp V shape.
    prices = np.concatenate([
        np.linspace(120, 100, 48), # Slow decline
        np.array([120.0, 140.0])   # Sudden massive spike
    ])
    
    df = pd.DataFrame({
        'date': dates,
        'open': prices,
        'high': prices + 1,
        'low': prices - 1,
        'close': prices,
        'volume': 1000
    })

    print("📊 Generated Synthetic Data with Crossover...")

    # 2. Initialize Strategy
    config = StrategyConfig(
        name="Test_Strategy",
        symbol="TEST_SYMBOL",
        capital=10000,
        params={"fast_period": 9, "slow_period": 21}
    )
    strategy = EMAScalpingStrategy(config)

    # 3. Process Logic
    # We call generate_signal. 
    # Note: The strategy calculates EMAs internally.
    
    # Current price (last close)
    current_price = df.iloc[-1]['close']
    
    print(f"🔍 Checking for signal at Price: {current_price}...")
    
    signal = strategy.generate_signal(df, current_price)

    # 4. specific check for EMAs to show WHY it worked
    # Recalculate EMAs here just to display
    df['ema_fast'] = df['close'].ewm(span=9, adjust=False).mean()
    df['ema_slow'] = df['close'].ewm(span=21, adjust=False).mean()
    
    prev = df.iloc[-2]
    curr = df.iloc[-1]
    
    print("\n📈 Technical Indicator Values:")
    print(f"   Previous Fast EMA: {prev['ema_fast']:.2f} | Slow EMA: {prev['ema_slow']:.2f}")
    print(f"   Current  Fast EMA: {curr['ema_fast']:.2f} | Slow EMA: {curr['ema_slow']:.2f}")
    
    if prev['ema_fast'] <= prev['ema_slow'] and curr['ema_fast'] > curr['ema_slow']:
        print("   ✅ CONDITION MET: Fast EMA crossed above Slow EMA")
    else:
        print("   ❌ CONDITION NOT MET")

    # 5. Result
    print("\n🎯 Result:")
    if signal:
        print(f"   ✅ SIGNAL GENERATED: {signal.signal_type.name}")
        print(f"   Reason: {signal.reason}")
    else:
        print("   ❌ NO SIGNAL GENERATED (Logic failed or conditions not met)")

if __name__ == "__main__":
    test_ema_strategy_logic()
