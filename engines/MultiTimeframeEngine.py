class MultiTimeframeEngine:
    def __init__(self):
        self.kline_5m = []
        self.kline_15m = []

    def update_kline(self, tick: dict):
        # ✅ 每分鐘收盤更新一次（可用時間戳判斷）
        self.kline_5m.append(tick["close"])
        self.kline_15m.append(tick["close"])

        if len(self.kline_5m) > 50:
            self.kline_5m.pop(0)
        if len(self.kline_15m) > 50:
            self.kline_15m.pop(0)

    def compute_indicators(self):
        # ✅ 計算多週期指標（可用 talib 或自定）
        return {
            "rsi_5m": self._rsi(self.kline_5m),
            "rsi_15m": self._rsi(self.kline_15m),
            "ema_5m": self._ema(self.kline_5m),
            "ema_15m": self._ema(self.kline_15m),
        }

    def _rsi(self, prices):
        # ✅ 自定 RSI 計算（簡化版）
        if len(prices) < 14:
            return 50
        gains = [max(prices[i+1] - prices[i], 0) for i in range(len(prices)-1)]
        losses = [max(prices[i] - prices[i+1], 0) for i in range(len(prices)-1)]
        avg_gain = sum(gains[-14:]) / 14
        avg_loss = sum(losses[-14:]) / 14
        rs = avg_gain / avg_loss if avg_loss != 0 else 1
        return 100 - (100 / (1 + rs))

    def _ema(self, prices, period=20):
        if len(prices) < period:
            return prices[-1]
        ema = prices[0]
        k = 2 / (period + 1)
        for price in prices[1:]:
            ema = price * k + ema * (1 - k)
        return ema
