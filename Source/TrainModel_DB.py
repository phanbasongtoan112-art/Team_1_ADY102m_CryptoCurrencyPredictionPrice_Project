import numpy as np
np.object = object
np.typeDict = dict

import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
import sqlite3

# Kết nối Database SQLite
db_path = "crypto_database.db"
conn = sqlite3.connect(db_path)

def train_and_predict_6_years():
    print("🚀 Bắt đầu đọc dữ liệu từ SQL Database...")
    try:
        df = pd.read_sql("SELECT * FROM spot_ohlcv", con=conn)
    except Exception as e:
        print("❌ Chưa có Database. Hãy chạy file collector.py trước!")
        return

    # Chuẩn bị dữ liệu
    features = ['close', 'volume', 'RSI', 'MACD']
    data = df[features].values
    
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(data)
    
    close_scaler = MinMaxScaler(feature_range=(0, 1))
    close_scaler.fit(df[['close']])

    # Chuỗi 60 ngày
    LOOK_BACK = 60
    X, y = [], []
    for i in range(LOOK_BACK, len(scaled_data)):
        X.append(scaled_data[i-LOOK_BACK:i])
        y.append(scaled_data[i, 0])
        
    X, y = np.array(X), np.array(y)
    
    # Khởi tạo Model AI
    print("🧠 Đang huấn luyện AI (Xin chờ một lát)...")
    model = Sequential([
        LSTM(64, return_sequences=True, input_shape=(X.shape[1], X.shape[2])),
        Dropout(0.2),
        LSTM(64, return_sequences=False),
        Dropout(0.2),
        Dense(1)
    ])
    model.compile(optimizer='adam', loss='mse')
    
    # Train 10 epochs cho nhanh
    model.fit(X, y, batch_size=32, epochs=10, verbose=1)

    print("\n🔮 Đang tính toán dự đoán cho 6 năm qua...")
    all_predictions_scaled = model.predict(X)
    predicted_prices = close_scaler.inverse_transform(all_predictions_scaled).flatten()
    actual_prices = close_scaler.inverse_transform(y.reshape(-1, 1)).flatten()
    
    dates = df['timestamp'].iloc[LOOK_BACK:].values

    # LƯU KẾT QUẢ VÀO DATABASE
    print("💾 Đang lưu kết quả dự đoán vào SQL Database...")
    results_df = pd.DataFrame({
        'Date': pd.to_datetime(dates),
        'Actual_Price': actual_prices,
        'AI_Predicted_Price': predicted_prices
    })
    results_df['Error_USD'] = abs(results_df['Actual_Price'] - results_df['AI_Predicted_Price'])
    results_df.to_sql("ai_6_years_predictions", con=conn, if_exists="replace", index=False)
    
    # XUẤT FILE HÌNH ẢNH
    print("📊 Đang xuất file hình ảnh biểu đồ...")
    plt.figure(figsize=(16, 8))
    plt.plot(results_df['Date'], results_df['Actual_Price'], color='blue', label='Giá Thực Tế', alpha=0.6)
    plt.plot(results_df['Date'], results_df['AI_Predicted_Price'], color='red', label='AI Dự Đoán', alpha=0.8)
    
    plt.title('AI DỰ ĐOÁN GIÁ BITCOIN TRONG 6 NĂM (2020 - 2026)')
    plt.xlabel('Thời Gian')
    plt.title('AI DỰ ĐOÁN GIÁ BITCOIN TRONG 6 NĂM (2020 - 2026)')
    plt.xlabel('Thời Gian')
    plt.ylabel('Giá (USDT)')
    plt.legend()
    plt.grid(True)
    
    plt.savefig('BieuDo_DuDoan_6Nam.png', dpi=300)
    print("✅ ĐÃ XUẤT ẢNH: Hãy kiểm tra file 'BieuDo_DuDoan_6Nam.png'")
    print("✅ ĐÃ XUẤT DATABASE: Dữ liệu nằm trong bảng 'ai_6_years_predictions'")
    
    # plt.show() # Tạm ẩn để không bị đứng màn hình chờ tắt ảnh
    conn.close()

if __name__ == "__main__":
    train_and_predict_6_years()
