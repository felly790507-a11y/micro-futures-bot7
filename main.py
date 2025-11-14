import json
from datetime import datetime
import shioaji as sj
from shioaji.constant import QuoteType, QuoteVersion

from StrategyState import StrategyState
from TickEngine import TickEngine
from KlineInitializer import KlineInitializer
from TradeLogger import TradeLogger
from TickRecorder import TickRecorder

# ====== 讀取設定與登入 ======
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

simulation_mode = config.get("simulation", True)
api_key = config["api_key"]
secret_key = config["secret_key"]

api = sj.Shioaji(simulation=simulation_mode)
api.login(api_key=api_key, secret_key=secret_key)
print(f"✅ 登入成功｜模式：{'模擬' if simulation_mode else '真實'}")

# ====== 憑證啟用（真實模式） ======
if not simulation_mode and "ca_path" in config:
    api.activate_ca(
        ca_path=config["ca_path"],
        ca_passwd=config["ca_passwd"],
        person_id=config["person_id"]
    )
    print("✅ 憑證啟用成功")

# ====== 合約選擇（取最早交割月） ======
contracts = [c for c in api.Contracts.Futures.TMF if c.code[-2:] not in ["R1", "R2"]]
contract = min(contracts, key=lambda c: c.delivery_date)
print(f"✅ 使用合約：{contract.code}")

# ====== 初始化策略模組 ======
kline = KlineInitializer(api, contract)
kline.fetch_kline()
kline.compute_indicators()
indicators = kline.get_indicators()

# ====== 初始化狀態與記錄模組 ======
bias = "auto"
state = StrategyState()
tick_recorder = TickRecorder(filename="tick_record.csv")
trade_logger = TradeLogger(tick_recorder=tick_recorder)
tick_engine = TickEngine(state, bias, indicators, trade_logger, tick_recorder)

# ====== 訂閱 Tick 並註冊回調 ======
api.quote.subscribe(contract, quote_type=QuoteType.Tick, version=QuoteVersion.v1)

@api.on_tick_fop_v1()
def tick_callback(exchange, tick):
    tick_dict = {
        "price": tick.close,
        "volume": tick.volume,
        "bid": getattr(tick, "bid_price", None),
        "ask": getattr(tick, "ask_price", None),
        "timestamp": tick.datetime,
        "rsi": indicators.get("rsi", 50),
        "macd": indicators.get("macd", 0),
        "macd_signal": indicators.get("macd_signal", 0),
        "kd_k": indicators.get("kd_k", 50),
        "kd_d": indicators.get("kd_d", 50)
    }
    tick_engine.on_tick(tick_dict)

# ====== 主程式掛住等待 Tick ======
if __name__ == "__main__":
    print("🚀 等待 Tick 資料中...")
    while True:
        pass  # 或 time.sleep(1)
