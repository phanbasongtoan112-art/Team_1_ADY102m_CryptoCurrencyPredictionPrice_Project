import ccxt
import requests
import pandas as pd
import pandas_ta as ta
from fredapi import Fred
from sqlalchemy import create_engine, text
import urllib.parse
from datetime import date
import time

# --- CẤU HÌNH ---
START_DATE = pd.Timestamp("2020-01-01")
SYMBOL = "BTC/USDT"
FRED_API_KEY = "9413dede70caf9007f0518ba171713e3"
DB_USER = "root"
DB_PASS = "Binh@n32160260"
DB_NAME = "crypto_db"

encoded_pass = urllib.parse.quote_plus(DB_PASS)
engine = create_engine(f"mysql+mysqlconnector://{DB_USER}:{encoded_pass}@localhost:3306/{DB_NAME}")

def get_max_timestamp(table_name):
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT MAX(timestamp) FROM {table_name}"))
            res = result.fetchone()[0]
            return pd.to_datetime(res) if res else None
    except Exception:
        return None

def update_spot_ohlcv():
    print("🚀 Đang cập nhật Spot Market Data...")
    exchange = ccxt.binance()
    last_ts = get_max_timestamp("spot_ohlcv")
    
    # Nếu đã có dữ liệu, lùi lại 200 ngày để tính toán lại các chỉ báo (SMA200) cho chính xác
    if last_ts:
        fetch_since = int((last_ts - pd.Timedelta(days=200)).timestamp() * 1000)
    else:
        fetch_since = int((START_DATE - pd.Timedelta(days=300)).timestamp() * 1000)

    all_ohlcv = []
    now_ms = int(time.time() * 1000)
    
    while fetch_since < now_ms:
        try:
            ohlcv = exchange.fetch_ohlcv(SYMBOL, timeframe='1d', since=fetch_since, limit=1000)
            if not ohlcv: break
            all_ohlcv.extend(ohlcv)
            fetch_since = ohlcv[-1][0] + 1
            time.sleep(0.1)
        except Exception as e:
            print(f"⚠️ Lỗi API Binance: {e}"); time.sleep(2); break

    if all_ohlcv:
        df = pd.DataFrame(all_ohlcv, columns=["timestamp","open","high","low","close","volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df = df.drop_duplicates(subset=['timestamp']).sort_values("timestamp")

        # Tính toán Technical Indicators
        df["SMA20"] = ta.sma(df["close"], 20)
        df["SMA50"] = ta.sma(df["close"], 50)
        df["SMA200"] = ta.sma(df["close"], 200)
        df["EMA"] = ta.ema(df["close"], 20)
        df["RSI"] = ta.rsi(df["close"], 14)
        df["ATR"] = ta.atr(df["high"], df["low"], df["close"])
        df["Volatility"] = df["close"].rolling(20).std()
        
        bb = ta.bbands(df["close"], 20)
        df["BBL_20_2.0"], df["BBM_20_2.0"], df["BBU_20_2.0"] = bb.iloc[:, 0], bb.iloc[:, 1], bb.iloc[:, 2]
        df["MACD_12_26_9"] = ta.macd(df["close"]).iloc[:, 0]

        # Chỉ lọc lấy dữ liệu từ START_DATE và mới hơn dữ liệu cũ trong DB
        df_final = df.query("timestamp >= @START_DATE")
        if last_ts:
            df_final = df_final[df_final["timestamp"] > last_ts]

        if not df_final.empty:
            df_final.to_sql("spot_ohlcv", con=engine, if_exists="append", index=False)
            print(f"✅ Xong Spot: Đã thêm {len(df_final)} dòng mới.")
        else:
            print("☕ Spot Data đã là mới nhất.")

def update_onchain_macro_sentiment():
    print("🌐 Đang cập nhật On-chain, Macro và Sentiment...")
    master_range = pd.date_range(start=START_DATE, end=date.today(), freq='D')
    
    try:
        # 1. On-chain (Blockchain.info)
        def fetch_blockchain(chart):
            total_days = (pd.Timestamp.now() - START_DATE).days + 10
            url = f"https://api.blockchain.info/charts/{chart}?timespan={total_days}days&sampled=false&format=json"
            r = requests.get(url).json()["values"]
            t = pd.DataFrame(r, columns=["x", "y"]).rename(columns={"y": chart.replace('-', '_')})
            t["timestamp"] = pd.to_datetime(t["x"], unit="s").dt.normalize()
            return t[["timestamp", chart.replace('-', '_')]]

        onchain = fetch_blockchain("hash-rate")
        onchain = pd.merge(onchain, fetch_blockchain("n-unique-addresses"), on="timestamp", how="outer")
        onchain = pd.merge(onchain, fetch_blockchain("n-transactions"), on="timestamp", how="outer")
        onchain = onchain.sort_values("timestamp").ffill().query("timestamp >= @START_DATE")
        onchain.rename(columns={"n_transactions": "onchain_transactions"}).to_sql("onchain_metrics", con=engine, if_exists="replace", index=False)

        # 2. Macro (FRED)
        fred = Fred(api_key=FRED_API_KEY)
        macro = pd.DataFrame(index=master_range)
        macro_map = {"DXY":"DTWEXBGS", "SP500":"SP500", "NASDAQ":"NASDAQCOM", "FED_RATE":"FEDFUNDS", "CPI":"CPIAUCSL"}
        for name, fid in macro_map.items():
            s = fred.get_series(fid, observation_start=START_DATE)
            macro = macro.join(pd.DataFrame(s, columns=[name]), how='left')
        macro = macro.ffill().reset_index().rename(columns={"index": "timestamp"})
        macro.to_sql("macro_data", con=engine, if_exists="replace", index=False)

        # 3. Sentiment (Fear & Greed)
        fng_res = requests.get("https://api.alternative.me/fng/?limit=0").json()["data"]
        fng_df = pd.DataFrame(fng_res)
        fng_df["timestamp"] = pd.to_datetime(fng_df["timestamp"].astype(int), unit="s").dt.normalize()
        fng_df["fng_val"] = pd.to_numeric(fng_df["value"])
        fng_df = fng_df[["timestamp", "fng_val"]].drop_duplicates(subset=['timestamp'])
        fng_df = fng_df.set_index("timestamp").reindex(master_range).ffill().reset_index()
        fng_df.columns = ["timestamp", "fng_val"]
        fng_df.to_sql("fear_greed_index", con=engine, if_exists="replace", index=False)
        
        print("✅ Cập nhật On-chain, Macro, Sentiment hoàn tất.")
    except Exception as e:
        print(f"❌ Lỗi xử lý dữ liệu: {e}")

if __name__ == "__main__":
    update_spot_ohlcv()
    update_onchain_macro_sentiment()