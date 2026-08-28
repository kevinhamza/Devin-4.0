# Devin/plugins/crypto_trading.py
# Purpose: A plugin for cryptocurrency market analysis, technical analysis,
#          and simulated trading using exchange APIs and AI.

import logging
import os
from typing import Optional, Dict, Any

try:
    import ccxt
    CCXT_AVAILABLE = True
except ImportError:
    CCXT_AVAILABLE = False

try:
    import pandas as pd
    import pandas_ta as ta
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    from modules.ai_tools.ai_composer import AIComposer # For AI signal generation
    AI_TOOLS_AVAILABLE = True
except ImportError:
    AI_TOOLS_AVAILABLE = False


# Configure basic logging
logger = logging.getLogger("CryptoTrader")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)

class CryptoTrader:
    """
    Provides tools for crypto analysis and simulated trading.
    """
    def __init__(self, exchange_id: str = 'binance', api_key: Optional[str] = None, secret_key: Optional[str] = None):
        if not CCXT_AVAILABLE or not PANDAS_AVAILABLE:
            raise ImportError("ccxt, pandas, and pandas-ta are required. 'pip install ccxt pandas pandas-ta'")
        
        self.api_key = api_key or os.getenv("EXCHANGE_API_KEY")
        self.secret_key = secret_key or os.getenv("EXCHANGE_SECRET_KEY")
        
        try:
            exchange_class = getattr(ccxt, exchange_id)
            self.exchange = exchange_class({
                'apiKey': self.api_key,
                'secret': self.secret_key,
            })
            # Use sandbox mode if the exchange supports it
            if self.exchange.has['sandbox']:
                logger.warning("Exchange supports sandbox mode. Enabling it.")
                self.exchange.set_sandbox_mode(True)
        except AttributeError:
            raise ValueError(f"Exchange '{exchange_id}' is not supported by ccxt.")
        except Exception as e:
            raise ConnectionError(f"Failed to initialize exchange: {e}")

        self.ai_composer = None
        if AI_TOOLS_AVAILABLE and os.getenv("OPENAI_API_KEY"):
            self.ai_composer = AIComposer()

    def fetch_ohlcv(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> Optional[pd.DataFrame]:
        """Fetches historical OHLCV data for a given symbol."""
        logger.info(f"Fetching {limit} candles for {symbol} on timeframe {timeframe}...")
        try:
            if not self.exchange.has['fetchOHLCV']:
                logger.error("This exchange does not support fetching OHLCV data.")
                return None
            
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            logger.error(f"Failed to fetch OHLCV data for {symbol}: {e}")
            return None

    def add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Adds a set of common technical indicators to the OHLCV DataFrame."""
        if df.empty:
            return df
        logger.info("Calculating technical indicators (RSI, MACD, EMA)...")
        # Use pandas-ta to add indicators. The `append=True` argument adds them as new columns.
        df.ta.ema(length=50, append=True)
        df.ta.ema(length=200, append=True)
        df.ta.rsi(append=True)
        df.ta.macd(append=True)
        return df

    def place_simulated_order(self, symbol: str, side: str, amount: float, order_type: str = "market"):
        """Logs a simulated trade order without executing it."""
        logger.warning("--- [SIMULATED TRADE] ---")
        logger.warning(f"Order: {side.upper()} {amount} of {symbol} at {order_type} price.")
        logger.warning("This is a simulation. No real order was placed.")
        logger.warning("To enable real trading, you must modify the code and use real API keys.")
        # In a real application, you would uncomment the following lines:
        # try:
        #     order = self.exchange.create_order(symbol, order_type, side, amount)
        #     logger.info(f"Successfully placed order: {order}")
        # except Exception as e:
        #     logger.error(f"Failed to place real order: {e}")

    def get_ai_trading_signal(self, symbol: str, timeframe: str = '1h') -> Optional[str]:
        """Uses AI to generate a trading signal based on technical indicators."""
        if not self.ai_composer:
            logger.error("AI Composer is not available. Cannot generate AI signal.")
            return None
            
        logger.info(f"Generating AI trading signal for {symbol}...")
        df = self.fetch_ohlcv(symbol, timeframe)
        if df is None or df.empty:
            return None
        
        df = self.add_technical_indicators(df)
        latest_data = df.iloc[-1] # Get the most recent candle's data
        
        # Create a context for the AI Composer
        context = {
            "symbol": symbol,
            "timeframe": timeframe,
            "price": latest_data['close'],
            "rsi": f"{latest_data['RSI_14']:.2f}",
            "ema_50": f"{latest_data['EMA_50']:.2f}",
            "ema_200": f"{latest_data['EMA_200']:.2f}",
            "macd_line": f"{latest_data['MACD_12_26_9']:.2f}",
            "macd_signal": f"{latest_data['MACDs_12_26_9']:.2f}"
        }
        
        # Add a custom template to the composer for this task
        self.ai_composer.prompt_templates['crypto_signal'] = (
            "You are a professional cryptocurrency technical analyst. Based on the following data for {symbol} on the {timeframe} timeframe, "
            "provide a trading signal ('BUY', 'SELL', or 'HOLD') and a brief, one-sentence rationale.\n\n"
            "Current Price: {price}\n"
            "RSI(14): {rsi}\n"
            "EMA(50): {ema_50}\n"
            "EMA(200): {ema_200}\n"
            "MACD Line: {macd_line}\n"
            "MACD Signal Line: {macd_signal}\n\n"
            "Signal and Rationale:"
        )
        
        return self.ai_composer.compose('crypto_signal', context)

# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== Crypto Analysis & Trading Prototype 📈🤖 ===")
    print("=========================================================")
    print("!!! WARNING: This script interacts with cryptocurrency exchange APIs. !!!")
    print("!!! Trading is simulated by default. Do not use with real funds without understanding the risk. !!!")
    
    # Initialize without API keys for public data access
    try:
        trader = CryptoTrader(exchange_id='binance')
        
        # --- 1. Data Fetching and Analysis Demo ---
        print("\n--- 1. Fetching and Analyzing Market Data for BTC/USDT ---")
        btc_df = trader.fetch_ohlcv('BTC/USDT', timeframe='4h', limit=210)
        if btc_df is not None:
            btc_df = trader.add_technical_indicators(btc_df)
            print("Latest data with technical indicators:")
            # Display the last 5 rows of the DataFrame
            print(btc_df.tail())
        
        # --- 2. AI Trading Signal Demo ---
        print("\n\n--- 2. Generating AI Trading Signal ---")
        if trader.ai_composer:
            signal = trader.get_ai_trading_signal('ETH/USDT', timeframe='1h')
            if signal:
                print(f"AI Signal for ETH/USDT: {signal}")
        else:
            print("AI Composer not available (likely missing OpenAI API key). Skipping AI signal demo.")
            
        # --- 3. Simulated Trading Demo ---
        print("\n\n--- 3. Demonstrating a Simulated Trade ---")
        trader.place_simulated_order(symbol='BTC/USDT', side='buy', amount=0.01)

    except Exception as e:
        logger.error(f"Demo failed: {e}")


    print("\n=========================================================")
    print("=== Crypto Trading Prototype Complete ===")
    print("=========================================================")
