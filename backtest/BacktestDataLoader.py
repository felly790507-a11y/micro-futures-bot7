# strategy_v4/backtest/BacktestDataLoader.py

import pandas as pd
from typing import List, Dict
from datetime import datetime

class BacktestDataLoader:
    """
    回測資料載入器：
    - 從 CSV 或 DataFrame 載入 K 線資料
    - 轉換成 tick 格式供 BacktestRunner 使用
    """

    def __init__(self, file_path: str | None = None, df: pd.DataFrame | None = None):
        self.file_path = file_path
        self.df = df

    def load(self) -> pd.DataFrame:
        """載入資料"""
        if self.df is not None:
            return self.df
        if self.file_path:
            return pd.read_csv(self.file_path)
        raise ValueError("必須提供 file_path 或 df")

    def to_ticks(self) -> List[Dict]:
        """轉換成 tick 格式"""
        df = self.load()

        ticks = []
        for _, row in df.iterrows():
            tick = {
                "timestamp": self._parse_time(row.get("timestamp") or row.get("Date")),
                "price": float(row.get("close") or row.get("Close")),
                "volume": float(row.get("volume") or row.get("Volume", 0)),
                "open": float(row.get("open") or row.get("Open", 0)),
                "high": float(row.get("high") or row.get("High", 0)),
                "low": float(row.get("low") or row.get("Low", 0)),
                # 預留指標欄位，方便 IndicatorEngine 使用
                "rsi": row.get("rsi", None),
                "macd": row.get("macd", None),
                "macd_signal": row.get("macd_signal", None),
                "kd_k": row.get("kd_k", None),
                "kd_d": row.get("kd_d", None),
                "atr": row.get("atr", None),
                "adx": row.get("adx", None),
                "vwap": row.get("vwap", None),
                "ema5": row.get("ema5", None),
                "ema20": row.get("ema20", None),
                "bband_pos": row.get("bband_pos", None),
                "bband_width": row.get("bband_width", None),
                "vol_roc": row.get("vol_roc", None),
                "rsi_1m": row.get("rsi_1m", None),
                "ema_1m": row.get("ema_1m", None),
                "rsi_5m": row.get("rsi_5m", None),
                "ema_5m": row.get("ema_5m", None),
                "rsi_15m": row.get("rsi_15m", None),
                "ema_15m": row.get("ema_15m", None),
            }
            ticks.append(tick)
        return ticks

    def _parse_time(self, ts) -> datetime:
        """轉換 timestamp"""
        if isinstance(ts, datetime):
            return ts
        try:
            return pd.to_datetime(ts)
        except Exception:
            return datetime.now()
