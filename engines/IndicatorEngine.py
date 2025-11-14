import numpy as np

def _compute_rsi(close_prices: list, period: int = 14) -> float:
    if len(close_prices) < period + 1:
        return 50.0
    deltas = np.diff(close_prices[-(period + 1):])
    gains = np.where(deltas > 0, deltas, 0).sum()
    losses = np.where(deltas < 0, -deltas, 0).sum()
    avg_gain = gains / period
    avg_loss = losses / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 1)

def _compute_macd(close_prices: list, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> dict:
    if len(close_prices) < slow_period + signal_period:
        return {"macd": 0.0, "macd_signal": 0.0, "macd_hist": 0.0}
    def ema(prices, period):
        alpha = 2 / (period + 1)
        ema_val = prices[0]
        for p in prices[1:]:
            ema_val = alpha * p + (1 - alpha) * ema_val
        return ema_val
    fast_ema = ema(close_prices[-fast_period:], fast_period)
    slow_ema = ema(close_prices[-slow_period:], slow_period)
    macd = fast_ema - slow_ema
    signal = ema([macd] + [fast_ema - slow_ema for _ in range(signal_period)], signal_period)
    hist = macd - signal
    return {
        "macd": round(macd, 2),
        "macd_signal": round(signal, 2),
        "macd_hist": round(hist, 2)
    }

def _compute_kd(close_prices: list, high_prices: list, low_prices: list, period: int = 9, prev_k: float = 50, prev_d: float = 50) -> dict:
    if len(close_prices) < period:
        return {"kd_k": 50.0, "kd_d": 50.0}
    low_min = min(low_prices[-period:])
    high_max = max(high_prices[-period:])
    rsv = (close_prices[-1] - low_min) / (high_max - low_min) * 100 if high_max != low_min else 50
    k = (2/3) * prev_k + (1/3) * rsv
    d = (2/3) * prev_d + (1/3) * k
    return {
        "kd_k": round(k, 1),
        "kd_d": round(d, 1)
    }

def _compute_bollinger(close_prices: list, period: int = 20, std_factor: float = 2.0) -> dict:
    if len(close_prices) < period:
        return {
            "bband_upper": 0.0,
            "bband_middle": 0.0,
            "bband_lower": 0.0,
            "bband_signal": "Neutral"
        }
    recent = close_prices[-period:]
    ma = np.mean(recent)
    std = np.std(recent)
    upper = ma + std_factor * std
    lower = ma - std_factor * std
    close = close_prices[-1]
    signal = "Neutral"
    if close > upper:
        signal = "BreakUp"
    elif close < lower:
        signal = "BreakDown"
    return {
        "bband_upper": round(upper, 2),
        "bband_middle": round(ma, 2),
        "bband_lower": round(lower, 2),
        "bband_signal": signal
    }

def _compute_atr(highs: list, lows: list, closes: list, period: int = 14) -> float:
    if len(highs) < period + 1 or len(lows) < period + 1 or len(closes) < period + 1:
        return 0.0
    trs = []
    for i in range(1, period + 1):
        high = highs[-i]
        low = lows[-i]
        prev_close = closes[-i - 1]
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        trs.append(tr)
    atr = np.mean(trs)
    return round(atr, 2)

def _compute_ema(prices: list, period: int) -> float:
    if len(prices) < period:
        return prices[-1] if prices else 0.0
    alpha = 2 / (period + 1)
    ema_val = prices[0]
    for p in prices[1:]:
        ema_val = alpha * p + (1 - alpha) * ema_val
    return round(ema_val, 2)

def _compute_adx(highs: list, lows: list, closes: list, period: int = 14) -> float:
    if len(highs) < period + 1:
        return 0.0
    plus_dm, minus_dm, tr_list = [], [], []
    for i in range(1, period + 1):
        up_move = highs[-i] - highs[-i - 1]
        down_move = lows[-i - 1] - lows[-i]
        plus_dm.append(up_move if up_move > down_move and up_move > 0 else 0)
        minus_dm.append(down_move if down_move > up_move and down_move > 0 else 0)
        tr = max(highs[-i] - lows[-i], abs(highs[-i] - closes[-i - 1]), abs(lows[-i] - closes[-i - 1]))
        tr_list.append(tr)
    tr_sum = sum(tr_list)
    if tr_sum == 0:
        return 0.0
    plus_di = 100 * sum(plus_dm) / tr_sum
    minus_di = 100 * sum(minus_dm) / tr_sum
    dx = abs(plus_di - minus_di) / (plus_di + minus_di) * 100 if (plus_di + minus_di) != 0 else 0
    return round(dx, 2)

def _compute_vwap(close_prices: list, volumes: list) -> float:
    if not close_prices or not volumes or len(close_prices) != len(volumes):
        return 0.0
    pv = sum([p * v for p, v in zip(close_prices, volumes)])
    total_volume = sum(volumes)
    return round(pv / total_volume, 2) if total_volume > 0 else 0.0

def compute_all_indicators(close_prices: list, high_prices: list, low_prices: list, volumes: list = None) -> dict:
    indicators = {}
    indicators["rsi"] = _compute_rsi(close_prices)
    indicators.update(_compute_macd(close_prices))
    indicators.update(_compute_kd(close_prices, high_prices, low_prices))
    indicators.update(_compute_bollinger(close_prices))
    indicators["atr"] = _compute_atr(high_prices, low_prices, close_prices)
    indicators["ema5"] = _compute_ema(close_prices, 5)
    indicators["ema20"] = _compute_ema(close_prices, 20)
    indicators["adx"] = _compute_adx(high_prices, low_prices, close_prices)
    indicators["vwap"] = _compute_vwap(close_prices, volumes) if volumes else 0.0
    indicators["close"] = close_prices[-1] if close_prices else 0
    return indicators
