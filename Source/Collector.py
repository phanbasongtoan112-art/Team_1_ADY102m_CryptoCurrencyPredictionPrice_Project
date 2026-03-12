import numpy as np
np.object = object
np.typeDict = dict

import ccxt
import pandas as pd
import pandas_ta as ta
import time
import sqlite3

# Kết nối (hoặc tạo) cơ sở dữ liệu SQLite
db_path = "crypto_database.db"
conn = sqlite3.connect(db_path)

def get_binance_data():
    print("🚀 Đang kéo dữ liệu từ Binance (từ 2020 đến nay)...")
    exchange = ccxt.binance()
    symbol = 'BTC/USDT'
    timeframe = '1d'

    # Lấy mốc thời gian cũ nhất (01/01/2020)
    since = exchange.parse8601('2020-01-01T00:00:00Z')
    all_ohlcv = []

    # Vòng lặp kéo dữ liệu liên tục
    while True:
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since, limit=1000)
            if len(ohlcv) == 0:
                break
            all_ohlcv.extend(ohlcv)
            since = ohlcv[-1][0] + 1 
            time.sleep(0.1)
        except Exception as e:
            print(f"Lỗi khi lấy dữ liệu: {e}")
            break

    # Xử lý dữ liệu
    df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

    # Tính toán các chỉ báo (RSI, MACD)
    df["RSI"] = ta.rsi(df["close"], 14)
    macd = ta.macd(df["close"])
    if macd is not None:
        df["MACD"] = macd.iloc[:, 0]

    # Xóa các dòng có giá trị NaN do chỉ báo gây ra
    df = df.dropna().reset_index(drop=True)


    
    # Lưu vào DATABASE SQLITE
    print(f"💾 Đang lưu vào {db_path} (bảng 'spot_ohlcv')...")
    df.to_sql("spot_ohlcv", con=conn, if_exists="replace", index=False)
    
    print(f"✅ HOÀN TẤT! Đã lưu {len(df)} ngày giao dịch vào '{db_path}'")
    conn.close()

if __name__ == "__main__":
    get_binance_data()



