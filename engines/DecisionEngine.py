class DecisionEngine:
    def __init__(self, market_bias: str, indicators: dict, tick_tracker=None):
        self.market_bias = market_bias
        self.indicators = indicators
        self.tick_tracker = tick_tracker

        # 進場門檻配置
        self.cfg = {
            "adx_consolidation": 20,
            "momentum_abs_min": 3,
            "bull_score_min": 3,
            "bear_score_max": -2,
            "neutral_score_abs": 3,
            "rsi_overbought": 70,
            "rsi_bullish_min": 55,
            "rsi_bearish_max": 45,
            "atr_high": 20,   # ATR 高波動門檻
            "atr_low": 5      # ATR 低波動門檻
        }

    def detect_market_bias(self, tick: dict) -> str:
        adx = tick.get("adx", 0)
        if adx < self.cfg["adx_consolidation"]:
            return "neutral"

        ema5, ema20 = tick.get("ema5", 0), tick.get("ema20", 0)
        macd, signal, hist = tick.get("macd", 0), tick.get("macd_signal", 0), tick.get("macd_hist", 0)
        rsi = tick.get("rsi", 50)

        score = 0
        score += 1 if ema5 > ema20 else -1
        score += 1 if macd > signal else -1
        score += 1 if hist > 0.3 else (-1 if hist < -0.3 else 0)
        score += 1 if rsi > 65 else (-1 if rsi < 35 else 0)

        if score > 0: return "bullish"
        if score < 0: return "bearish"
        return "neutral"

    def entry_strength_score(self, tick: dict) -> int:
        score = 0
        macd, signal, hist = tick.get("macd", 0), tick.get("macd_signal", 0), tick.get("macd_hist", 0)
        rsi = tick.get("rsi", 50)
        ema5, ema20 = tick.get("ema5", 0), tick.get("ema20", 0)
        vwap = tick.get("vwap", 0)
        close = tick.get("close", 0)
        adx = tick.get("adx", 0)
        atr = tick.get("atr", 0)
        volume = tick.get("volume", 0)

        # 盤整過濾
        if adx < self.cfg["adx_consolidation"] and abs(macd - signal) < 0.3:
            return -99

        # 趨勢加分
        if macd > signal and hist > 0.8: score += 1
        if close > vwap and ema5 > ema20 and rsi > self.cfg["rsi_bullish_min"]: score += 1

        # 多週期確認
        if tick.get("is_ready_5m") and tick.get("is_ready_15m"):
            if tick.get("rsi_5m", 50) > 55 and tick.get("ema_15m", 0) > tick.get("ema_5m", 0):
                score += 1

        # VWAP + 成交量
        if close > vwap and volume >= 5:
            score += 1

        # ATR + ADX 結合
        if adx > 20 and atr >= self.cfg["atr_high"]:
            score += 1
        elif atr <= self.cfg["atr_low"]:
            score -= 1

        # TickPatternTracker 形態判斷
        if self.tick_tracker:
            if self.tick_tracker.is_three_up():  # 連續三根陽線
                score += 1
            if self.tick_tracker.is_sharp_drop_rebound():  # 急跌後反彈
                score += 1
            momentum = self.tick_tracker.get_momentum()
            direction_score = self.tick_tracker.get_direction_score()
            tick["momentum"] = momentum
            tick["direction_score"] = direction_score
            if abs(momentum) >= self.cfg["momentum_abs_min"]: score += 1
            score += direction_score

        return score

    def score_entry(self, tick: dict) -> int:
        return self.entry_strength_score(tick)

    def should_enter(self, tick: dict) -> bool:
        score = self.entry_strength_score(tick)
        if score == -99:
            return False

        bias = self.market_bias if self.market_bias != "auto" else self.detect_market_bias(tick)
        tick["bias"] = bias

        if abs(tick.get("momentum", 0)) < self.cfg["momentum_abs_min"]:
            return False
        if tick.get("direction_score", 0) == 0:
            return False
        if not tick.get("is_ready", False):
            return False

        if bias == "bullish":
            return (score >= self.cfg["bull_score_min"] and
                    tick.get("close", 0) > tick.get("vwap", 0) and
                    tick.get("ema5", 0) > tick.get("ema20", 0) and
                    tick.get("rsi", 50) < self.cfg["rsi_overbought"])
        elif bias == "bearish":
            return (score <= self.cfg["bear_score_max"] and
                    tick.get("ema5", 0) < tick.get("ema20", 0))
        else:
            return abs(score) >= self.cfg["neutral_score_abs"]
