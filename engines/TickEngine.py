from StrategyState import StrategyState
from DecisionEngine import DecisionEngine
from TickPatternTracker import TickPatternTracker
from TradeLogger import TradeLogger
from TickRecorder import TickRecorder
from IndicatorEngine import compute_all_indicators
from datetime import datetime

class TickEngine:
    def __init__(self, state: StrategyState, market_bias: str, indicators: dict, trade_logger=None, tick_recorder=None):
        self.state = state
        self.market_bias = market_bias
        self.indicators = indicators
        self.tick_tracker = TickPatternTracker()
        self.decision_engine = DecisionEngine(market_bias, indicators)
        self.decision_engine.tick_tracker = self.tick_tracker
        self.logger = trade_logger if trade_logger else TradeLogger()
        self.tick_recorder = tick_recorder

        self.close_prices = []
        self.high_prices = []
        self.low_prices = []
        self.volumes = []
        self.close_5m = []
        self.close_15m = []

    def compute_rsi(self, prices, period=14):
        if len(prices) < period + 1:
            return 50.0
        gains = [max(prices[i+1] - prices[i], 0) for i in range(len(prices)-1)]
        losses = [max(prices[i] - prices[i+1], 0) for i in range(len(prices)-1)]
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return round(100 - (100 / (1 + rs)), 1)

    def compute_ema(self, prices, period=20):
        if not prices:
            return 0.0
        if len(prices) < period:
            return prices[-1]
        ema_val = prices[0]
        k = 2 / (period + 1)
        for price in prices[1:]:
            ema_val = price * k + ema_val * (1 - k)
        return round(ema_val, 2)

    def _choose_direction(self, tick: dict) -> str:
        # 用 direction_score 與 bias 一致性選方向
        dir_score = tick.get("direction_score", 0)
        bias = tick.get("bias", "neutral")
        if dir_score > 0 and bias == "bullish":
            return "long"
        if dir_score < 0 and bias == "bearish":
            return "short"
        # 若不一致，以 momentum 決定
        return "long" if tick.get("momentum", 0) > 0 else "short"

    def on_tick(self, tick: dict):
        price = float(tick.get("price", 0))
        volume = float(tick.get("volume", 0))
        timestamp = tick.get("timestamp", datetime.now())

        self.close_prices.append(price)
        self.high_prices.append(price)
        self.low_prices.append(price)
        self.volumes.append(volume)

        if len(self.close_prices) % 5 == 0:
            self.close_5m.append(price)
            if len(self.close_5m) > 120:
                self.close_5m.pop(0)
        if len(self.close_prices) % 15 == 0:
            self.close_15m.append(price)
            if len(self.close_15m) > 120:
                self.close_15m.pop(0)

        indicators = compute_all_indicators(self.close_prices, self.high_prices, self.low_prices, self.volumes)
        tick.update(indicators)
        self.indicators.update(indicators)

        tick["rsi_5m"] = self.compute_rsi(self.close_5m)
        tick["rsi_15m"] = self.compute_rsi(self.close_15m)
        tick["ema_5m"] = self.compute_ema(self.close_5m, 5)
        tick["ema_15m"] = self.compute_ema(self.close_15m, 15)

        tick["is_ready_5m"] = len(self.close_5m) >= 20
        tick["is_ready_15m"] = len(self.close_15m) >= 20
        tick["is_ready"] = len(self.close_prices) >= 30

        self.tick_tracker.update(price)
        self.state.update_profit_loss(price)

        self.state.last_rsi = tick.get("rsi", 50)
        self.state.last_macd = tick.get("macd", 0)
        self.state.last_kd_k = tick.get("kd_k", 50)
        self.state.last_kd_d = tick.get("kd_d", 50)

        tick["recent_high"] = self.state.get_recent_high()
        tick["max_profit"] = self.state.max_profit
        tick["max_loss"] = self.state.max_loss
        tick["tick_since_entry"] = self.state.tick_since_entry
        tick["unrealized_profit"] = self.state.get_unrealized_profit(price) if self.state.in_position else 0.0

        bias = self.decision_engine.detect_market_bias(tick)
        tick["bias"] = bias
        entry_score = self.decision_engine.score_entry(tick)
        tick["entry_score"] = entry_score

        print(f"[TICK] {timestamp}｜Price={price:.0f}｜RSI={tick['rsi']:.1f}｜MACD={tick['macd']:.2f}｜Signal={tick['macd_signal']:.2f}｜KD=({tick['kd_k']:.1f}/{tick['kd_d']:.1f})｜BBand={tick['bband_signal']}｜ATR={tick['atr']:.2f}｜ADX={tick['adx']:.1f}｜VWAP={tick['vwap']:.1f}｜EMA=({tick['ema5']:.1f}/{tick['ema20']:.1f})｜RSI(5m/15m)={tick['rsi_5m']:.1f}/{tick['rsi_15m']:.1f}｜Bias={bias}｜Score={entry_score}")

        if self.tick_recorder:
            self.tick_recorder.record_tick(tick)

        # 進場
        if not self.state.in_position:
            if self.decision_engine.should_enter(tick):
                print("[ENTER_TRIGGER] 進場條件成立，準備進場")
                direction = self._choose_direction(tick)
                self.state.enter(direction, price)
                self.logger.log("ENTER", self.state.get_status(), price, tick)
            return

        # 剛進場冷卻
        if self.state.just_entered(seconds=3):
            return
        # 出場判斷（順序：硬停損／動態停損／鎖利／時間／不續抱）
        if self.state.should_stoploss(price, tick.get("atr", 0)):
            print(f"[STOPLOSS] Triggered @ {price}")
            self.logger.log("STOPLOSS", self.state.get_status(), price, tick)
            self.state.exit(price)
            if self.tick_recorder:
                self.tick_recorder.force_flush()

        elif self.state.should_takeprofit(price, tick.get("atr", 0)):
            print(f"[TAKEPROFIT] Triggered @ {price}")
            self.logger.log("TAKEPROFIT", self.state.get_status(), price, tick)
            self.state.exit(price)
            if self.tick_recorder:
                self.tick_recorder.force_flush()

        elif hasattr(self.state, "should_lock_profit") and self.state.should_lock_profit(tick, price):
            print(f"[LOCK] 指標轉弱或價格回落，獲利鎖定 @ {price}")
            self.logger.log("LOCK_PROFIT", self.state.get_status(), price, tick)
            self.state.exit(price)
            if self.tick_recorder:
                self.tick_recorder.force_flush()

        elif self.state.should_exit_by_tick():
            print(f"[TIME_EXIT] 超過最大持倉 tick，自動出場 @ {price}")
            self.logger.log("TIME_EXIT", self.state.get_status(), price, tick)
            self.state.exit(price)
            if self.tick_recorder:
                self.tick_recorder.force_flush()

        elif not self.state.should_hold():
            print(f"[EXIT] 不續抱，準備出場 @ {price}")
            self.logger.log("EXIT", self.state.get_status(), price, tick)
            self.state.exit(price)
            if self.tick_recorder:
                self.tick_recorder.force_flush()

        elif hasattr(self.state, "should_add") and self.state.should_add(price, tick):
            print("[ADD] 加碼條件成立")
            self.state.current_position_size += 1
            self.logger.log("ADD", self.state.get_status(), price, tick)
