-- 1. Tạo Database (nếu chưa có)
CREATE DATABASE IF NOT EXISTS crypto_db;
USE crypto_db;

-- 2. Tạo bảng lưu trữ dữ liệu giá Spot và các chỉ báo kỹ thuật (Technical Indicators)
-- Lưu ý: Các cột có dấu chấm và số như BBL_20_2.0 phải được bao quanh bởi dấu ` `
CREATE TABLE IF NOT EXISTS spot_ohlcv (
    timestamp DATETIME PRIMARY KEY,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    volume DOUBLE,
    SMA20 DOUBLE,
    SMA50 DOUBLE,
    SMA200 DOUBLE,
    EMA DOUBLE,
    RSI DOUBLE,
    ATR DOUBLE,
    Volatility DOUBLE,
    `BBL_20_2.0` DOUBLE,
    `BBM_20_2.0` DOUBLE,
    `BBU_20_2.0` DOUBLE,
    MACD_12_26_9 DOUBLE
);

-- 3. Tạo bảng lưu trữ dữ liệu On-chain (Bitcoin Network)
CREATE TABLE IF NOT EXISTS onchain_metrics (
    timestamp DATETIME PRIMARY KEY,
    hash_rate DOUBLE,
    n_unique_addresses DOUBLE,
    onchain_transactions DOUBLE
);

-- 4. Tạo bảng lưu trữ dữ liệu Kinh tế vĩ mô (Macro Data)
CREATE TABLE IF NOT EXISTS macro_data (
    timestamp DATETIME PRIMARY KEY,
    DXY DOUBLE,
    SP500 DOUBLE,
    NASDAQ DOUBLE,
    FED_RATE DOUBLE,
    CPI DOUBLE
);

-- 5. Tạo bảng lưu trữ chỉ số tâm lý (Fear & Greed Index)
CREATE TABLE IF NOT EXISTS fear_greed_index (
    timestamp DATETIME PRIMARY KEY,
    fng_val INT
);