import pandas as pd
from datetime import datetime

class ExitStrategySimulator:
    def __init__(self, tick_file="tick_record.csv", trade_file="trade_log.csv"):
        self.tick_df = pd.read_csv(tick_file)
        self.trade_df = pd.read_csv(trade_file)

        if "trade_id" not in self.trade_df.columns:
            def format_trade_id(row):
                ts_raw = row["timestamp"]
                for fmt in ("%Y/%m/%d %H:%M", "%Y-%m-%d %H:%M:%S"):
                    try:
                        ts = datetime.strptime(ts_raw, fmt)
                        ts_str = ts.strftime("%Y-%m-%d %H:%M:%S")
                        return f"{ts_str}_{row['direction']}_{float(row['price']):.1f}"
                    except ValueError:
                        continue
                print(f"⚠️ trade_id 轉換失敗：{ts_raw}")
                return None

            self.trade_df["trade_id"] = self.trade_df.apply(format_trade_id, axis=1)

    def fix_tick_timestamp_by_index(self, base_date="2025-11-13", start_time="09:34:59", interval_sec=0.2):
        base = pd.to_datetime(f"{base_date} {start_time}")
        self.tick_df["timestamp"] = self.tick_df["tick_index"].apply(
            lambda i: base + pd.to_timedelta(i * interval_sec, unit="s")
        )

    def simulate_exit_by_min_momentum(self, momentum_threshold=-3, direction_score_filter=None):
        matched_ids = set(self.trade_df["trade_id"]) & set(self.tick_df["trade_id"])
        print(f"✅ 可比對的 trade_id 筆數：{len(matched_ids)}")

        simulated_results = []
        triggered_ids = []

        for trade_id, group in self.tick_df.groupby("trade_id"):
            entry_row = self.trade_df[self.trade_df["trade_id"] == trade_id]
            if entry_row.empty:
                continue
            entry_price = entry_row.iloc[0]["price"]
            direction = entry_row.iloc[0]["direction"]

            exit_row = self.trade_df[
                (self.trade_df["trade_id"] == trade_id) &
                (self.trade_df["action"].isin(["LOCK_PROFIT", "STOPLOSS", "EXIT", "TAKEPROFIT", "TIME_EXIT"]))
            ]
            if exit_row.empty:
                continue
            original_exit_price = exit_row.iloc[0]["price"]
            exit_time = pd.to_datetime(exit_row.iloc[0]["timestamp"])

            group = group.copy()
            try:
                group["momentum"] = group["momentum"].astype(float)
                group["direction_score"] = group["direction_score"].astype(int)
                group["price"] = group["price"].astype(float)
            except Exception as e:
                print(f"⚠️ 欄位轉換失敗：{trade_id}｜錯誤：{e}")
                continue

            min_tick = group.loc[group["momentum"].idxmin()]
            tick_time = pd.to_datetime(min_tick["timestamp"])
            if tick_time >= exit_time:
                continue

            if min_tick["momentum"] <= momentum_threshold:
                if direction_score_filter is None or min_tick["direction_score"] == direction_score_filter:
                    simulated_exit_price = min_tick["price"]
                    triggered_ids.append(trade_id)
                else:
                    simulated_exit_price = original_exit_price
            else:
                simulated_exit_price = original_exit_price

            simulated_pl = simulated_exit_price - entry_price if direction == "long" else entry_price - simulated_exit_price
            simulated_results.append(simulated_pl)

        win_rate = sum(1 for r in simulated_results if r > 0) / len(simulated_results) * 100 if simulated_results else 0
        avg_pl = sum(simulated_results) / len(simulated_results) if simulated_results else 0

        return {
            "mode": "min_momentum",
            "momentum_threshold": momentum_threshold,
            "direction_score": direction_score_filter,
            "win_rate": win_rate,
            "avg_pnl": avg_pl,
            "triggered_count": len(triggered_ids),
            "triggered_ids": triggered_ids
        }
    def scan_by_min_momentum(self, momentum_thresholds=[-2, -3, -4], direction_scores=[-1, 0, None]):
        print("\n📊 掃描最弱 tick（min momentum）出場策略：")
        results = []
        for threshold in momentum_thresholds:
            for score in direction_scores:
                result = self.simulate_exit_by_min_momentum(threshold, score)
                print(f"  momentum<={result['momentum_threshold']}｜dir_score={result['direction_score']}｜勝率={result['win_rate']:.1f}%｜平均損益={result['avg_pnl']:.2f}｜命中={result['triggered_count']}")
                results.append(result)
        return results

    def scan_trade_log_by_momentum(self, momentum_threshold=-2):
        print("\n📊 掃描 trade_log.csv 是否命中最弱 momentum 條件：")
        triggered = []
        for _, row in self.trade_df.iterrows():
            tid = row["trade_id"]
            ts = pd.to_datetime(row["timestamp"])
            direction = "long" if "long" in tid else "short"
            nearby = self.tick_df[
                (self.tick_df["timestamp"] >= ts - pd.Timedelta(seconds=3)) &
                (self.tick_df["timestamp"] <= ts + pd.Timedelta(seconds=3))
            ]
            match = nearby[
                (nearby["momentum"] <= momentum_threshold) &
                ((nearby["direction_score"] == -1) if direction == "short" else (nearby["direction_score"] == 1))
            ]
            if not match.empty:
                triggered.append(tid)
        print(f"✅ 命中筆數：{len(triggered)}")
        for i, tid in enumerate(triggered[:10]):
            print(f"  {i+1}. {tid}")

    def show_momentum_distribution(self):
        print("\n📊 momentum 分布統計：")
        try:
            self.tick_df["momentum"] = self.tick_df["momentum"].astype(float)
            print(self.tick_df["momentum"].describe())
            print("\n📌 最低 momentum：", self.tick_df["momentum"].min())
        except Exception as e:
            print("⚠️ momentum 欄位轉換失敗：", e)

    def show_tick_time_range(self):
        print("\n📊 tick_record.csv 時間範圍：")
        try:
            times = pd.to_datetime(self.tick_df["timestamp"], errors="coerce")
            print(f"  最早：{times.min()}｜最晚：{times.max()}")
        except Exception as e:
            print("⚠️ 時間欄位轉換失敗：", e)

    def check_tick_trade_id(self, top_n=10):
        print(f"\n📋 tick_record.csv 中的 trade_id 範例（前 {top_n} 筆）：")
        try:
            print(self.tick_df["trade_id"].dropna().unique()[:top_n])
        except Exception as e:
            print("⚠️ 無法讀取 trade_id 欄位：", e)
