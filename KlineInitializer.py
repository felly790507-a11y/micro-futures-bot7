import polars as pl
from polars_indicator_utils import prepare_kbar, safe_last

class KlineInitializer:
    def __init__(self, api, contract):
        self.api = api
        self.contract = contract
        self.df_kbar = None
        self.indicators = {}

    def get_kbar_from_api(self) -> pl.DataFrame:
        import pandas as pd
        import polars as pl

        kbars = self.api.kbars(self.contract)
        df = pd.DataFrame(dict(kbars))  # ✅ 修正 .items() 錯誤
        df["ts"] = pd.to_datetime(df["ts"])
        df.rename(columns={"ts": "datetime"}, inplace=True)

        # ✅ 標準化欄位名稱為小寫，供指標模組使用
        df.rename(columns={
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume"
        }, inplace=True)

        return pl.from_pandas(df)

    def fetch_kline(self):
        """
        從 API 抓取原始 K 線資料
        """
        self.df_kbar = self.get_kbar_from_api()

    def compute_indicators(self):
        """
        計算技術指標並儲存最後一筆指標值
        """
        self.df_kbar = prepare_kbar(self.df_kbar)
        self.indicators = safe_last(self.df_kbar)

    def get_market_bias(self) -> str:
        """
        根據 MACD 判斷市場偏多或偏空
        """
        macd = self.indicators.get("macd")
        signal = self.indicators.get("macd_signal")

        if macd is None or signal is None:
            return "neutral"
        return "bullish" if macd > signal else "bearish"

    def get_kbar(self) -> pl.DataFrame:
        return self.df_kbar

    def get_indicators(self) -> dict:
        return self.indicators

    def get_kbar_with_indicators(self) -> pl.DataFrame:
        return self.df_kbar

    def get_kbar_latest(self) -> dict:
        return self.indicators

    def get_kbar_tail(self, n=30) -> pl.DataFrame:
        return self.df_kbar.tail(n)

    def get_kbar_columns(self) -> list:
        return self.df_kbar.columns if self.df_kbar is not None else []
