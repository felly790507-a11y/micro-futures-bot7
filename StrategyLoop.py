from datetime import datetime
import time

from KlineInitializer import KlineInitializer
from StrategyState import StrategyState
from TickEngine import TickEngine
from TradeLogger import TradeLogger

class StrategyLoop:
    def __init__(self, api=None, contract=None, simulation=True):
        self.api = api
        self.contract = contract
        self.simulation = simulation

        self.kline = KlineInitializer()
        self.state = StrategyState()
        self.tick_engine = None
        self.logger = TradeLogger()

    def initialize(self):
        print("[INIT] 抓取 K 線與指標中...")
        self.kline.fetch_kline()
        self.kline.compute_indicators()
        bias = self.kline.get_market_bias()
        print(f"[BIAS] 市場偏向：{bias}")

        self.tick_engine = TickEngine(self.state, bias, self.kline.indicators, trade_logger=self.logger)

    def simulate_ticks(self):
        print("[SIM] 模擬 Tick 資料流中...")
        ticks = [
            {"price": 27300, "volume": 20, "bid": 27299, "ask": 27301, "timestamp": datetime.now(), "rsi": 60},
            {"price": 27290, "volume": 18, "bid": 27289, "ask": 27291, "timestamp": datetime.now(), "rsi": 58},
            {"price": 27270, "volume": 22, "bid": 27269, "ask": 27271, "timestamp": datetime.now(), "rsi": 55},
            {"price": 27240, "volume": 25, "bid": 27239, "ask": 27241, "timestamp": datetime.now(), "rsi": 52},
            {"price": 27210, "volume": 30, "bid": 27209, "ask": 27211, "timestamp": datetime.now(), "rsi": 50}
        ]

        for tick in ticks:
            self.tick_engine.on_tick(tick)
            time.sleep(1)

        # 模擬結束後保險檢查：若還有持倉，強制平倉
        if self.state.in_position:
            print("[FORCE_EXIT] 模擬結束仍有持倉，強制平倉")
            self.logger.log("EXIT", self.state.get_status(), ticks[-1]["price"], ticks[-1])
            self.state.exit(ticks[-1]["price"])

    def run(self):
        self.initialize()

        if self.simulation:
            self.simulate_ticks()
        else:
            print("🚀 等待 Tick 觸發策略中...")
            # 在實盤模式下，也可定期檢查是否需要強制平倉
            if self.state.in_position and not self.state.should_hold():
                print("[FORCE_EXIT] 實盤模式保險平倉")
                self.logger.log("EXIT", self.state.get_status(), None, {})
                self.state.exit()
