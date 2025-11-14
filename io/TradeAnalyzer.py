import csv
from collections import defaultdict

class TradeAnalyzer:
    def __init__(self, filename="trade_log.csv", fee_per_trade=2.1):
        self.filename = filename
        self.fee = fee_per_trade
        self.trades = []
        self.results = []

    def load_trades(self):
        with open(self.filename, newline="") as f:
            reader = csv.DictReader(f)
            self.trades = list(reader)

    def analyze(self):
        self.load_trades()
        entry = None
        for row in self.trades:
            action = row["action"]
            if action == "ENTER":
                entry = row
            elif action in ("STOPLOSS", "LOCK_PROFIT", "EXIT", "TIME_EXIT", "TAKEPROFIT") and entry:
                try:
                    pnl = float(row["price"]) - float(entry["price"])
                except ValueError:
                    continue  # 若 price 欄位有問題，跳過

                direction = entry.get("direction", "")
                if direction == "short":
                    pnl = -pnl
                net_pnl = pnl - self.fee

                result = {
                    "entry_price": float(entry.get("price", 0)),
                    "exit_price": float(row.get("price", 0)),
                    "entry_time": entry.get("timestamp", ""),
                    "exit_time": row.get("timestamp", ""),
                    "entry_score": int(entry.get("entry_score", 0) or 0),
                    "direction": direction,
                    "bias": entry.get("bias", ""),
                    "momentum": float(entry.get("momentum", 0) or 0),
                    "reversal": str(entry.get("reversal", "False")) == "True",
                    "direction_score": int(entry.get("direction_score", 0) or 0),
                    "pnl": pnl,
                    "net_pnl": net_pnl,
                    "outcome": "win" if net_pnl > 0 else "loss"
                }
                self.results.append(result)
                entry = None
    def summary(self):
        wins = [r for r in self.results if r["outcome"] == "win"]
        losses = [r for r in self.results if r["outcome"] == "loss"]

        # 連勝連敗計算
        max_win_streak = max_loss_streak = 0
        current_streak = 0
        last_outcome = None
        for r in self.results:
            if r["outcome"] == last_outcome:
                current_streak += 1
            else:
                current_streak = 1
                last_outcome = r["outcome"]
            if r["outcome"] == "win":
                max_win_streak = max(max_win_streak, current_streak)
            else:
                max_loss_streak = max(max_loss_streak, current_streak)

        print(f"📊 總交易次數：{len(self.results)}")
        if self.results:
            print(f"✅ 勝率（扣手續費）：{len(wins) / len(self.results) * 100:.1f}%")
        print(f"💰 平均實際獲利：{sum(r['net_pnl'] for r in wins) / len(wins):.2f}" if wins else "💰 無獲利紀錄")
        print(f"❌ 平均實際虧損：{sum(r['net_pnl'] for r in losses) / len(losses):.2f}" if losses else "❌ 無虧損紀錄")
        print(f"🔥 最大連勝：{max_win_streak}｜最大連敗：{max_loss_streak}")

        # 分數區間分析
        print("\n📈 各分數區間績效（扣手續費）：")
        score_groups = defaultdict(list)
        for r in self.results:
            score_groups[r["entry_score"]].append(r)
        for score in sorted(score_groups):
            group = score_groups[score]
            win_count = sum(1 for r in group if r["outcome"] == "win")
            pnl_avg = sum(r["net_pnl"] for r in group) / len(group)
            print(f"  分數 {score}：{len(group)} 筆｜勝率 {win_count / len(group) * 100:.1f}%｜平均淨損益 {pnl_avg:.2f}")

        # 多空方向分析
        print("\n📊 多空方向績效（扣手續費）：")
        direction_groups = defaultdict(list)
        for r in self.results:
            direction_groups[r["direction"]].append(r)
        for direction in ["long", "short"]:
            group = direction_groups[direction]
            if group:
                win_count = sum(1 for r in group if r["outcome"] == "win")
                pnl_avg = sum(r["net_pnl"] for r in group) / len(group)
                print(f"  {direction.upper()}：{len(group)} 筆｜勝率 {win_count / len(group) * 100:.1f}%｜平均淨損益 {pnl_avg:.2f}")

        # bias 判斷分析
        print("\n📊 Bias 判斷績效（扣手續費）：")
        bias_groups = defaultdict(list)
        for r in self.results:
            bias_groups[r["bias"]].append(r)
        for bias in ["bullish", "bearish", "neutral"]:
            group = bias_groups[bias]
            if group:
                win_count = sum(1 for r in group if r["outcome"] == "win")
                pnl_avg = sum(r["net_pnl"] for r in group) / len(group)
                print(f"  {bias.upper()}：{len(group)} 筆｜勝率 {win_count / len(group) * 100:.1f}%｜平均淨損益 {pnl_avg:.2f}")

        # momentum 分析
        print("\n📊 Momentum 區間績效：")
        momentum_groups = {
            "強推升勢": [],
            "弱升": [],
            "盤整": [],
            "弱跌": [],
            "強推下殺": []
        }
        for r in self.results:
            m = r["momentum"]
            if m > 6:
                momentum_groups["強推升勢"].append(r)
            elif m > 3:
                momentum_groups["弱升"].append(r)
            elif -3 <= m <= 3:
                momentum_groups["盤整"].append(r)
            elif m < -3 and m >= -6:
                momentum_groups["弱跌"].append(r)
            else:
                momentum_groups["強推下殺"].append(r)
        for label, group in momentum_groups.items():
            if group:
                win_count = sum(1 for r in group if r["outcome"] == "win")
                pnl_avg = sum(r["net_pnl"] for r in group) / len(group)
                print(f"  {label}：{len(group)} 筆｜勝率 {win_count / len(group) * 100:.1f}%｜平均淨損益 {pnl_avg:.2f}")

        # reversal 分析
        print("\n📊 Reversal 狀態績效：")
        rev_groups = defaultdict(list)
        for r in self.results:
            key = "反轉盤" if r["reversal"] else "非反轉"
            rev_groups[key].append(r)
        for label, group in rev_groups.items():
            win_count = sum(1 for r in group if r["outcome"] == "win")
            pnl_avg = sum(r["net_pnl"] for r in group) / len(group)
            print(f"  {label}：{len(group)} 筆｜勝率 {win_count / len(group) * 100:.1f}%｜平均淨損益 {pnl_avg:.2f}")

        # direction_score 分析
        print("\n📊 Direction Score 績效：")
        ds_groups = defaultdict(list)
        for r in self.results:
            ds_groups[r["direction_score"]].append(r)
        for score in sorted(ds_groups):
            group = ds_groups[score]
            win_count = sum(1 for r in group if r["outcome"] == "win")
            pnl_avg = sum(r["net_pnl"] for r in group) / len(group)
            print(f"  分數 {score}：{len(group)} 筆｜勝率 {win_count / len(group) * 100:.1f}%｜平均淨損益 {pnl_avg:.2f}")

        # 額外提示
        if len(score_groups) == 1 and 0 in score_groups:
            print("\n⚠️ 所有交易分數皆為 0，請確認 TradeLogger 是否正確記錄 entry_score。")

        # 進場條件命中率分析
        print("\n📊 進場條件命中率分析：")
        conditions = {
            "entry_score>=3": lambda r: r["entry_score"] >= 3,
            "momentum<-3": lambda r: r["momentum"] < -3,
            "direction_score==1": lambda r: r["direction_score"] == 1,
            "reversal=False": lambda r: not r["reversal"],
        }
        for label, cond in conditions.items():
            group = [r for r in self.results if cond(r)]
            if group:
                win_count = sum(1 for r in group if r["outcome"] == "win")
                pnl_avg = sum(r["net_pnl"] for r in group) / len(group)
                print(f"  {label}：{len(group)} 筆｜勝率 {win_count / len(group) * 100:.1f}%｜平均淨損益 {pnl_avg:.2f}")

# ✅ 程式入口：直接執行時會跑分析並輸出報告
if __name__ == "__main__":
    analyzer = TradeAnalyzer(filename="trade_log.csv", fee_per_trade=2.1)
    analyzer.analyze()
    analyzer.summary()
