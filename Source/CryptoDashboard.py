import numpy as np
np.object = object
np.typeDict = dict

import streamlit as st
import pandas as pd
import sqlite3
import os
from sklearn.metrics import mean_squared_error, r2_score

# Cấu hình trang web
st.set_page_config(page_title="AI Crypto Dashboard", layout="wide", page_icon="🚀")
st.title("🚀 Hệ thống AI Phân Tích & Dự Đoán Giá Bitcoin")

DB_PATH = "crypto_database.db"

def load_data(table_name):
    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        try:
            df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
            conn.close()
            return df
        except:
            conn.close()
            return None
    return None

# Menu thanh điều hướng
st.sidebar.header("🎯 Menu Quản Lý")
menu = ["1. 📦 Tiền Xử Lý & Thống Kê (EDA)", "2. 🤖 Đánh Giá Mô Hình AI", "3. 📈 Trực Quan Hóa (Biểu Đồ)"]
choice = st.sidebar.radio("Chọn bảng điều khiển:", menu)

# ==========================================
# TAB 1: THỐNG KÊ MÔ TẢ & TIỀN XỬ LÝ
# ==========================================
if choice == "1. 📦 Tiền Xử Lý & Thống Kê (EDA)":
    st.header("📦 Thống Kê Mô Tả Dữ Liệu (Descriptive Statistics)")
    df_raw = load_data("spot_ohlcv")
    
    if df_raw is not None:
        st.success(f"✅ Dữ liệu đã được Tiền xử lý (xóa bỏ NaN) và đồng nhất đơn vị tính (USDT). Tổng mẫu: **{len(df_raw)}** ngày.")
        
        st.subheader("Bảng Thống Kê Toán Học (Min, Max, Mean, Variance, Std)")
        # Lấy các cột giá trị cần thống kê
        cols_to_stat = ['open', 'high', 'low', 'close', 'volume']
        
        # Dùng thư viện tính toán các giá trị thống kê mô tả
        stats_df = df_raw[cols_to_stat].describe().T
        stats_df['variance'] = df_raw[cols_to_stat].var() # Tính phương sai
        
        # Sắp xếp lại các cột hiển thị cho đẹp
        display_stats = stats_df[['min', 'max', 'mean', 'std', 'variance']].copy()
        display_stats.columns = ['Giá trị Nhỏ nhất (Min)', 'Giá trị Lớn nhất (Max)', 'Trung bình (Mean)', 'Độ lệch chuẩn (Std)', 'Phương sai (Variance)']
        
        st.dataframe(display_stats, use_container_width=True)
        
        st.subheader("Dữ liệu thô sau tiền xử lý")
        st.dataframe(df_raw, use_container_width=True)
    else:
        st.warning("⚠️ Chưa có dữ liệu. Hãy chạy file 'collector.py' trước!")

# ==========================================
# TAB 2: KIỂM ĐỊNH MÔ HÌNH HỌC (Model Evaluation)
# ==========================================
elif choice == "2. 🤖 Đánh Giá Mô Hình AI":
    st.header("🤖 Báo cáo Hiệu suất Mô hình (Model Performance)")
    df_pred = load_data("ai_6_years_predictions")
    
    if df_pred is not None:
        y_true = df_pred['Actual_Price']
        y_pred = df_pred['AI_Predicted_Price']
        
        # CÁC ĐỘ ĐO ĐÁNH GIÁ MÔ HÌNH HỌC
        mape = (abs(y_true - y_pred) / y_true).mean() * 100
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        r2 = r2_score(y_true, y_pred)
        
        st.info("💡 **Trả lời câu hỏi: AI đã học và bám sát dữ liệu hay chưa?**")
        col1, col2, col3 = st.columns(3)
        col1.metric("Sai số phần trăm (MAPE)", f"{mape:.2f}%", help="Mức độ sai lệch trung bình theo %")
        col2.metric("Sai số toàn phương (RMSE)", f"{rmse:.2f} USD", help="Độ chênh lệch tuyệt đối trung bình")
        col3.metric("Hệ số xác định (R2 Score)", f"{r2:.4f}", help="Càng gần 1.0 nghĩa là mô hình học dữ liệu càng tốt")
        
        if r2 > 0.8:
            st.success(f"🔥 Kết luận: Với R2 = {r2:.4f}, mô hình đã học và giải thích được rất tốt dữ liệu giá.")
        
        st.subheader("Bảng so sánh chi tiết")
        st.dataframe(df_pred, use_container_width=True)
    else:
        st.warning("⚠️ Chưa có kết quả từ AI. Hãy chạy file 'train_model.py' trước!")

# ==========================================
# TAB 3: TRỰC QUAN HÓA BẰNG BIỂU ĐỒ
# ==========================================
elif choice == "3. 📈 Trực Quan Hóa (Biểu Đồ)":
    st.header("📈 Trực Quan Hóa Dữ Liệu (Data Visualization)")
    df_pred = load_data("ai_6_years_predictions")
    df_raw = load_data("spot_ohlcv")
    
    if df_pred is not None and df_raw is not None:
        # Biểu đồ Volume
        st.subheader("1. Phân phối Khối lượng giao dịch (Trading Volume)")
        chart_vol = df_raw.set_index('timestamp')['volume']
        st.bar_chart(chart_vol, color="#1f77b4")
        
        # Biểu đồ So sánh AI vs Thực tế
        st.subheader("2. Biểu đồ Dự đoán AI vs Giá Thực Tế")
        df_pred['Date'] = pd.to_datetime(df_pred['Date'])
        chart_data = df_pred.set_index('Date')[['Actual_Price', 'AI_Predicted_Price']]
        
        st.line_chart(chart_data, color=["#1f77b4", "#ff7f0e"])
        
    else:
        st.warning("⚠️ Hãy đảm bảo bạn đã chạy cả 2 file Thu thập và Train model!")

st.sidebar.markdown("---")
st.sidebar.info("💡 **Ghi chú báo cáo:** Dữ liệu đã được áp dụng Min-Max Scaler trong quá trình Train AI.")