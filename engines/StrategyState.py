from datetime import datetime, timedelta

class StrategyState:
    def __init__(self):
        self.reset()
        self.last_rsi = 50
        self.last_macd = 0
        self.last_kd_k = 50
        self.last_kd_d = 50
        self.max_position_size = 1

        # ✅ 新增風控參數
        self.cooldown_seconds = 30       # 進場冷卻期
        self.hard_stoploss = 40.0        # 硬停損：浮虧超過 -40 直接出場
        self.hard_time_seconds = 180     # 最長持倉秒數（3 分鐘）
        self.max_ticks_hold = 90         # 最長持倉 tick 數

        # 連敗控制
        self.consecutive_losses = 0
        self.disable_until = None

    def reset(self):
        self.in_position = False
        self.direction = None
        self.entry_price = None
        self.entry_time = None
        self.last_entry_time = None
        self.max_profit = 0.0
        self.max_loss = 0.0
        self.recent_prices = []
        self.current_position_size = 0
        self.tick_since_entry = 0

    def can_enter(self) -> bool:
        now = datetime.now()
        if self.disable_until and now < self.disable_until:
            print("⚠️ 連敗冷卻中，暫停進場")
            return False
        if self.last_entry_time and (now - self.last_entry_time).total_seconds() < self.cooldown_seconds:
            print("⚠️ 進場冷卻中，跳過進場")
            return False
        return True

    def enter(self, direction: str, price: float):
        if self.in_position:
            print("⚠️ 已持倉，忽略重複進場")
            return
        if not self.can_enter():
            return
        self.reset()
        self.in_position = True
        self.direction = direction
        self.entry_price = price
        self.entry_time = datetime.now()
        self.last_entry_time = self.entry_time
        self.current_position_size = 1
        print(f"[ENTER] {direction} @ {price}｜時間={self.entry_time.strftime('%H:%M:%S')}")

    def update_profit_loss(self, current_price: float):
        if not self.in_position or self.entry_price is None:
            return
        profit = current_price - self.entry_price if self.direction == "long" else self.entry_price - current_price
        self.max_profit = max(self.max_profit, profit)
        self.max_loss = min(self.max_loss, profit)
        self.recent_prices.append(current_price)
        if len(self.recent_prices) > 30:
            self.recent_prices.pop(0)
        self.tick_since_entry += 1

    def get_unrealized_profit(self, current_price: float) -> float:
        if not self.in_position or self.entry_price is None:
            return 0.0
        return current_price - self.entry_price if self.direction == "long" else self.entry_price - current_price

    def get_recent_high(self) -> float:
        return max(self.recent_prices) if self.recent_prices else 0.0

    def get_dynamic_stoploss(self, atr: float = None, multiplier: float = 2.0) -> float:
        if atr and atr > 0:
            return -atr * multiplier
        if len(self.recent_prices) < 5:
            return -20.0
        diffs = [abs(self.recent_prices[i] - self.recent_prices[i - 1]) for i in range(1, len(self.recent_prices))]
        avg_move = sum(diffs) / len(diffs)
        return -avg_move * multiplier

    def should_stoploss(self, current_price: float, atr: float = None) -> bool:
        if not self.in_position:
            return False
        # ✅ 硬停損
        unreal = self.get_unrealized_profit(current_price)
        if unreal <= -self.hard_stoploss:
            print(f"[HARD STOP] 浮虧 {unreal:.1f} ≥ {self.hard_stoploss}")
            return True
        # 動態停損
        if self.tick_since_entry < 3:
            return False
        threshold = self.get_dynamic_stoploss(atr)
        return self.max_loss <= threshold

    def should_takeprofit(self, current_price: float, atr: float = None, cost: float = 21.0, multiplier: float = 2.0) -> bool:
        if atr and atr > 0:
            target = max(atr * multiplier, cost + 6)
        else:
            target = 40.0
        return self.max_profit >= target

    def should_hold(self) -> bool:
        if not self.in_position:
            return False
        time_held = (datetime.now() - self.entry_time).total_seconds()
        if time_held >= self.hard_time_seconds:
            return False
        return time_held < self.hard_time_seconds and (self.max_profit > 15 or self.tick_since_entry < self.max_ticks_hold)

    def should_exit_by_tick(self, max_tick: int = None) -> bool:
        limit = max_tick if max_tick is not None else self.max_ticks_hold
        return self.in_position and self.tick_since_entry >= limit

    def just_entered(self, seconds: int = 3) -> bool:
        if not self.in_position or self.last_entry_time is None:
            return False
        return (datetime.now() - self.last_entry_time).total_seconds() < seconds

    def mark_trade_result(self, realized_profit: float):
        if realized_profit <= 0:
            self.consecutive_losses += 1
            if self.consecutive_losses >= 6:
                self.disable_until = datetime.now() + timedelta(minutes=30)
                print("⛔ 連敗達標，暫停交易 30 分鐘")
        else:
            self.consecutive_losses = 0

    def get_status(self) -> dict:
        return {
            "in_position": self.in_position,
            "direction": self.direction,
            "entry_price": self.entry_price,
            "entry_time": self.entry_time,
            "max_profit": self.max_profit,
            "max_loss": self.max_loss,
            "current_position_size": self.current_position_size,
            "tick_since_entry": self.tick_since_entry
        }

    def exit(self, current_price: float = None):
        if not self.in_position:
            print("⚠️ 無持倉可出場")
            return
        realized = 0.0
        if current_price is not None and self.entry_price is not None:
            realized = current_price - self.entry_price if self.direction == "long" else self.entry_price - current_price
        print(f"[EXIT] {self.direction}｜入場 {self.entry_price}｜出場 {current_price if current_price else '—'}｜浮盈：{self.max_profit:.1f}｜浮虧：{self.max_loss:.1f}｜實盈：{realized:.1f}")
        self.mark_trade_result(realized)
        self.reset()
