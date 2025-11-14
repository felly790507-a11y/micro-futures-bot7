# strategy_v4/io/TickRecorder.py

import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

class TickRecorder:
    """
    Tick 資料紀錄器：
    - 記錄每筆 tick 的指標與分數
    - 支援 v3/v4 模式，增加 mode、params_version、bias_prob、entry_score_v2、exit_score_v2 欄位
    """

    def __init__(self, record_path: str | Path = "tick_data.csv", buffer_size: int = 100):
        self.path = Path(record_path)
        self.buffer_size = buffer_size
        self.buffer: List[List[Any]] = []
        self._initialized = False

    def _init_file(self):
        """初始化 CSV 檔案，建立標題列"""
        if not self._initialized:
            with self.path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp", "price", "volume",
                    "bias", "bias_prob",
                    "entry_score", "entry_score_v2", "exit_score_v2",
                    "mode", "params_version",
                    "rsi", "macd", "macd_signal", "kd_k", "kd_d",
                    "atr", "adx", "vwap", "ema5", "ema20",
                    "bband_pos", "bband_width", "vol_roc",
                    "unrealized_profit", "max_profit", "max_loss", "tick_since_entry"
                ])
            self._initialized = True

    def record_tick(self, tick: Dict[str, Any]):
        """將 tick 資料寫入 buffer"""
        if not self._initialized:
            self._init_file()

        row = [
            tick.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            tick.get("price", ""),
            tick.get("volume", ""),
            tick.get("bias", ""),
            tick.get("bias_prob", ""),
            tick.get("entry_score", ""),
            tick.get("entry_score_v2", ""),
            tick.get("exit_score_v2", ""),
            tick.get("mode", ""),
            tick.get("params_version", ""),
            tick.get("rsi", ""),
            tick.get("macd", ""),
            tick.get("macd_signal", ""),
            tick.get("kd_k", ""),
            tick.get("kd_d", ""),
            tick.get("atr", ""),
            tick.get("adx", ""),
            tick.get("vwap", ""),
            tick.get("ema5", ""),
            tick.get("ema20", ""),
            tick.get("bband_pos", ""),
            tick.get("bband_width", ""),
            tick.get("vol_roc", ""),
            tick.get("unrealized_profit", ""),
            tick.get("max_profit", ""),
            tick.get("max_loss", ""),
            tick.get("tick_since_entry", "")
        ]

        self.buffer.append(row)

        if len(self.buffer) >= self.buffer_size:
            self.flush()

    def flush(self):
        """將 buffer 寫入檔案"""
        if not self.buffer:
            return
        with self.path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(self.buffer)
        self.buffer.clear()

    def force_flush(self):
        """強制立即寫入檔案"""
        self.flush()
