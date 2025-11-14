import csv
from datetime import datetime

class TradeLogger:
    def __init__(self, filename="trade_log.csv", tick_recorder=None):
        self.filename = filename
        self.tick_recorder = tick_recorder  # ✅ 注入 TickRecorder 實例
        self.fields = [
            "timestamp", "action", "direction", "price",
            "max_profit", "max_loss", "tick_since_entry",
            "rsi", "macd", "macd_signal", "kd_k", "kd_d",
            "volume", "bband_signal", "ema5", "ema20", "adx", "vwap",
            "entry_score", "bias",
            "momentum", "reversal", "direction_score"
        ]
        try:
            with open(self.filename, "x", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=self.fields)
                writer.writeheader()
        except FileExistsError:
            pass

    def build_row(self, action: str, state: dict, price: float, tick: dict, extra_fields: dict = None) -> dict:
        row = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": action,
            "direction": state.get("direction", ""),
            "price": price,
            "max_profit": round(state.get("max_profit", 0), 2),
            "max_loss": round(state.get("max_loss", 0), 2),
            "tick_since_entry": state.get("tick_since_entry", 0),
            "rsi": round(tick.get("rsi", 0), 1) if tick.get("rsi") is not None else 0,
            "macd": round(tick.get("macd", 0), 2),
            "macd_signal": round(tick.get("macd_signal", 0), 2),
            "kd_k": round(tick.get("kd_k", 0), 1),
            "kd_d": round(tick.get("kd_d", 0), 1),
            "volume": tick.get("volume", 0),
            "bband_signal": tick.get("bband_signal", ""),
            "ema5": round(tick.get("ema5", 0), 2),
            "ema20": round(tick.get("ema20", 0), 2),
            "adx": round(tick.get("adx", 0), 1),
            "vwap": round(tick.get("vwap", 0), 2),
            "entry_score": tick.get("entry_score", 0),
            "bias": tick.get("bias", ""),
            "momentum": round(tick.get("momentum", 0), 2),
            "reversal": "True" if tick.get("reversal", False) else "False",
            "direction_score": tick.get("direction_score", 0)
        }
        if extra_fields:
            for k, v in extra_fields.items():
                if k not in row:
                    row[k] = v
        return row

    def log(self, action: str, state: dict, price: float, tick: dict, extra_fields: dict = None):
        row = self.build_row(action, state, price, tick, extra_fields)
        try:
            with open(self.filename, "a", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=self.fields)
                writer.writerow(row)
            print(f"[LOGGER] 已記錄 {action} @ {price}")
        except PermissionError:
            print(f"[LOGGER] 無法寫入 {self.filename}，可能正在被 Excel 開啟中。")

        # ✅ TickRecorder 連動
        if self.tick_recorder:
            if action == "ENTER":
                trade_id = f"{row['timestamp']}_{row['direction']}_{row['price']}"
                self.tick_recorder.start_trade(trade_id)
            elif action in ("STOPLOSS", "LOCK_PROFIT", "EXIT", "TIME_EXIT", "TAKEPROFIT"):
                self.tick_recorder.force_flush()
