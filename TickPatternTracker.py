class TickPatternTracker:
    def __init__(self):
        self.prices = []

    def update(self, price: float):
        """更新價格序列"""
        self.prices.append(price)
        if len(self.prices) > 50:  # 保留最近 50 筆
            self.prices.pop(0)

    def get_momentum(self) -> float:
        """計算最新動能（最後一筆與前一筆差值）"""
        if len(self.prices) < 2:
            return 0
        return self.prices[-1] - self.prices[-2]

    def get_direction_score(self) -> int:
        """方向分數：最近三筆比較"""
        if len(self.prices) < 3:
            return 0
        return 1 if self.prices[-1] > self.prices[-3] else -1

    def is_three_up(self) -> bool:
        """判斷是否連續三根陽線（價格連續上升）"""
        if len(self.prices) < 3:
            return False
        return self.prices[-1] > self.prices[-2] > self.prices[-3]

    def is_sharp_drop_rebound(self) -> bool:
        """判斷是否急跌後反彈"""
        if len(self.prices) < 3:
            return False
        # 急跌：前兩筆差距大於 10；反彈：最新價格大於上一筆
        return (self.prices[-3] - self.prices[-2] > 10 and
                self.prices[-1] > self.prices[-2])
