import polars as pl
import polars_talib as plta
import pandas as pd

def compute_polars_indicators(df, target_len=None, debug=False) -> pl.DataFrame:
    if isinstance(df, pd.DataFrame):
        df = pl.from_pandas(df)

    if df is None or df.shape[0] < 30:
        if debug:
            print(f"⚠️ K 線資料不足（{df.shape[0] if df is not None else 0} 筆），無法計算技術指標")
        return pl.DataFrame()

    required_cols = {"close", "high", "low"}
    missing = required_cols - set(df.columns)
    if missing:
        if debug:
            print(f"⚠️ 缺少必要欄位：{missing}")
        return df

    df = df.with_columns([
        pl.col("close").cast(pl.Float64),
        pl.col("high").cast(pl.Float64),
        pl.col("low").cast(pl.Float64)
    ])

    # RSI
    try:
        df = df.with_columns([
            pl.col("close").ta.rsi(14).alias("rsi")
        ])
    except Exception as e:
        if debug:
            print(f"❌ RSI 計算失敗：{e}")

    # MACD
    try:
        df = df.with_columns([
            pl.col("close").ewm_mean(span=12).alias("ema_fast"),
            pl.col("close").ewm_mean(span=26).alias("ema_slow")
        ])
        if "ema_fast" in df.columns and "ema_slow" in df.columns:
            df = df.with_columns([
                (pl.col("ema_fast") - pl.col("ema_slow")).alias("macd")
            ])
        if "macd" in df.columns:
            df = df.with_columns([
                pl.col("macd").ewm_mean(span=9).alias("macd_signal")
            ])
        if "macd" in df.columns and "macd_signal" in df.columns:
            df = df.with_columns([
                (pl.col("macd") - pl.col("macd_signal")).alias("macd_hist")
            ])
        if debug:
            print("✅ MACD 計算成功")
    except Exception as e:
        if debug:
            print(f"❌ MACD 計算失敗：{e}")

    # KD
    try:
        stoch = plta.stoch(
            high=pl.col("high"),
            low=pl.col("low"),
            close=pl.col("close"),
            fastk_period=9,
            slowk_period=3,
            slowd_period=3
        )
        df = df.with_columns([
            stoch.struct.field("slowk").alias("kd_k"),
            stoch.struct.field("slowd").alias("kd_d")
        ])
    except Exception as e:
        if debug:
            print(f"❌ KD 計算失敗：{e}")

    # ATR
    try:
        df = df.with_columns([
            pl.col("close").ta.atr(14).alias("atr")
        ])
    except Exception as e:
        if debug:
            print(f"❌ ATR 計算失敗：{e}")

    # BBand
    try:
        bband = plta.bbands(pl.col("close"), timeperiod=20)
        df = df.with_columns([
            bband.struct.field("upperband").alias("bband_upper"),
            bband.struct.field("middleband").alias("bband_middle"),
            bband.struct.field("lowerband").alias("bband_lower")
        ])
        if "bband_upper" in df.columns and "bband_lower" in df.columns:
            df = df.with_columns([
                pl.when(pl.col("close") > pl.col("bband_upper")).then(pl.lit("BreakUp"))
                 .when(pl.col("close") < pl.col("bband_lower")).then(pl.lit("BreakDown"))
                 .otherwise(pl.lit("Neutral")).alias("bband_signal")
            ])
        if debug:
            print("✅ BBand 計算成功")
    except Exception as e:
        if debug:
            print(f"❌ BBand 計算失敗：{e}")

    return df.tail(target_len or df.shape[0])


def prepare_kbar(df_raw: pl.DataFrame, length: int = 30) -> pl.DataFrame:
    df_kbar = df_raw.tail(length + 100)
    print(f"📊 目前 K 線筆數：{df_kbar.shape[0]}")

    df_kbar = compute_polars_indicators(df_kbar, target_len=length, debug=True)
    df_kbar = df_kbar.tail(length)

    latest = safe_last(df_kbar)
    macd = latest.get("macd")
    signal = latest.get("macd_signal")
    dt = latest.get("datetime")

    if macd is not None and signal is not None:
        print(f"✅ MACD 已啟用｜時間：{dt}｜MACD：{macd:.2f}｜Signal：{signal:.2f}")
    else:
        print(f"⚠️ MACD 尚未啟用（macd={macd}, signal={signal}）")

    verify_indicators(df_kbar)
    print(f"📦 最終 K 線欄位：{df_kbar.columns}")
    return df_kbar


def merge_indicators(df_kbar: pl.DataFrame) -> pl.DataFrame:
    df_kbar = df_kbar.with_columns([
        pl.col("datetime").dt.truncate("1m").alias("datetime")
    ])

    target_len = df_kbar.shape[0]
    df_ind = compute_polars_indicators(df_kbar, target_len=target_len, debug=True)

    indicator_cols = [col for col in [
        "macd", "macd_signal", "macd_hist",
        "rsi", "kd_k", "kd_d", "bband_signal"
    ] if col in df_ind.columns]

    for col in indicator_cols:
        try:
            series = df_ind[col]
            if series.shape[0] == df_kbar.shape[0]:
                df_kbar = df_kbar.with_columns([series])
        except Exception as e:
            print(f"⚠️ 合併失敗：{col} → {e}")

    return df_kbar


def safe_last(df):
    if df is None or df.shape[0] == 0:
        return {}
    try:
        if isinstance(df, pl.DataFrame):
            return dict(zip(df.columns, df.row(-1)))
        elif isinstance(df, pd.DataFrame):
            return df.iloc[-1].to_dict()
        elif isinstance(df, pl.Series):
            return {df.name: df[-1]}
    except Exception as e:
        print(f"⚠️ safe_last 錯誤：{e}")
    return {}


def verify_indicators(df: pl.DataFrame, expected=None):
    expected = expected or ["macd", "macd_signal", "macd_hist", "rsi", "kd_k", "kd_d", "bband_signal"]
    missing = [col for col in expected if col not in df.columns]
    if missing:
        print(f"⚠️ 缺少指標欄位：{missing}")
    else:
        print("✅ 所有指標欄位已成功合併")
