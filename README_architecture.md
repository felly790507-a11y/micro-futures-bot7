# micro-futures-bot7
micro-futures-bot
Repository comparison
micro-futures-bot7（新版，含 v4 方向）
主要目錄：backtest、config、engines、io、model、pipeline

頂層檔案：KlineInitializer.py、StrategyLoop.py、TickPatternTracker.py、main.py、README.md、shioaji.log

pipeline 新增 polars_indicator_utils.py（偏向使用 Polars 產出指標）

backtest/config/engines/io/model 皆有檔案更新，進度較完整且面向 v4 回測/視覺化/最佳化的工具鏈

micro-futures-bot6（舊版，v3 為主）
主要檔案：DecisionEngine.py、ExitStrategySimulator.py、IndicatorEngine.py、KlineInitializer.py、LoginManager.py、MultiTimeframeEngine.py、StrategyLoop.py、StrategyState.py、TickEngine.py、TickPatternTracker.py、TickRecorder.py、TradeAnalyzer.py、TradeLogger.py、main.py、polars_indicator_utils.py

已有完整 v3 的交易迴圈與模組，但未見 v4 的回測工具鏈目錄（例如 backtest/engines/io/models 的細分）

已完成的模組（此次設計新增/修訂）
engines/DecisionEngine_v2.py：v4 回歸型決策引擎，提供 bias、bias_prob、entry_score_v2、exit_score_v2 與 evaluate_tick 整合輸出。

engines/DecisionEngine.py：v3 規則型決策引擎，補齊 score_exit，對齊 TickEngine。

engines/StrategyState.py：外部化風控參數、支援 exit_score、time/ticks/ATR 停損停利與加碼邏輯。

engines/TickEngine.py：整合 v3/v4 引擎、ParamsStore、IndicatorEngine、MultiTimeframeEngine、TradeLogger、TickRecorder。

backtest/BacktestRunner.py：集中回測執行，串接 TickEngine 與 TradeAnalyzer。

backtest/BacktestDataLoader.py：K 線資料轉 tick。

backtest/ResultVisualizer.py：盈虧曲線、勝率分布、版本比較。

backtest/PerformanceReporter.py：Sharpe、最大回撤、平均持倉時間。

backtest/WalkforwardTester.py：分段校正 + 回測，版本化權重。

backtest/Optimizer.py：多參數組合最佳化。

backtest/ReportExporter.py：CSV/Markdown 報告匯出。

models/ParamsStore.py：權重版本管理（JSON）。

以上模組補齊了 micro-futures-bot7 的 backtest 與 models 層，使其能從 v3 過渡到 v4 的回歸型測試與維運工具鏈。

架構引用關係
資料流總覽
BacktestDataLoader → ticks → BacktestRunner → TickEngine → DecisionEngine(v3)/DecisionEngine_v2(v4) + StrategyState

TickEngine → IndicatorEngine + MultiTimeframeEngine → features → DecisionEngine_v2.evaluate_tick()

TickEngine → TradeLogger（交易事件） + TickRecorder（tick 樣本）

BacktestRunner 結束 → TradeAnalyzer、PerformanceReporter、ResultVisualizer

WalkforwardTester → RegressionCalibrator（權重校正，假定 models 目錄內）→ 更新 ParamsStore → 重新回測

Optimizer → 多參數組合 → BacktestRunner → ReportExporter

模組間依賴細節
TickEngine

依賴 engines：StrategyState、DecisionEngine(v3)、DecisionEngine_v2(v4)

依賴 io：TradeLogger、TickRecorder

依賴 指標層：IndicatorEngine.extract_features、MultiTimeframeEngine

依賴 models：ParamsStore

DecisionEngine_v2

依賴 models：ParamsStore.get_weights() 提供權重

依賴 指標層：features（rsi/macd/ema/bband_pos/atr/adx/vwap/volume 與 MTF 特徵）

StrategyState

依賴 config：risk/decision 中的停損停利、ticks/minutes、exit_threshold

BacktestRunner

依賴 engines：TickEngine、StrategyState

依賴 io：TradeLogger、TickRecorder、TradeAnalyzer

依賴 models：ParamsStore

依賴 config：ConfigManager（提供 risk/decision 參數）

ResultVisualizer、PerformanceReporter、ReportExporter

依賴 io：TradeLogger 的輸出檔（trade_log.csv 等）

WalkforwardTester、Optimizer

依賴 BacktestRunner 與 ParamsStore，並間接依賴 TickEngine 與其整合的所有子模組

README_architecture.md（可直接放到根目錄）
Project architecture
Purpose
同時支援 v3 規則型與 v4 回歸型的微期交易系統。

提供完整回測、視覺化、最佳化與走勢分段校正工具鏈。

Directory structure
engines/

DecisionEngine.py（v3 規則型：bias、score_entry、score_exit、should_enter）

DecisionEngine_v2.py（v4 回歸型：evaluate_tick → bias、bias_prob、entry_score_v2、exit_score_v2）

StrategyState.py（持倉管理與風控：stoploss/takeprofit/exit_score/tick/time）

TickEngine.py（主循環：整合 v3/v4 引擎、指標、記錄）

io/

TradeLogger.py（交易事件記錄）

TickRecorder.py（tick 記錄）

TradeAnalyzer.py（回測分析彙總）

models/

ParamsStore.py（權重版本管理 JSON）

RegressionCalibrator.py（若存在：分段權重校正，寫入 ParamsStore）

backtest/

BacktestDataLoader.py（K 線轉 tick）

BacktestRunner.py（回測執行）

ResultVisualizer.py（盈虧曲線、勝率分布、版本比較）

PerformanceReporter.py（Sharpe、最大回撤、平均持倉時間）

WalkforwardTester.py（分段校正 + 回測）

Optimizer.py（多參數最佳化）

ReportExporter.py（CSV/Markdown 匯出）

config/

strategy_config.json（risk/decision 參數集合）

ConfigManager.py（若存在：載入配置）

pipeline/

polars_indicator_utils.py（以 Polars 產生指標）

root

KlineInitializer.py（資料準備）

StrategyLoop.py（線上策略迴圈；可參考 TickEngine 結構）

main.py（入口）

以上結構與檔案清單是基於 micro-futures-bot7、micro-futures-bot6 的現有檔案樹與我們的增補模組草案整理。

Module relationships
TickEngine

inputs: tick dict（含 price、volume、timestamp 和指標）

uses:

DecisionEngine_v2（v4）或 DecisionEngine（v3）

StrategyState（持倉/風控）

IndicatorEngine.extract_features + MultiTimeframeEngine（特徵）

TradeLogger、TickRecorder（記錄）

ParamsStore（v4 權重）

outputs: 交易事件、tick 記錄、狀態更新

BacktestRunner

inputs: ticks（list[dict]）

orchestrates: TickEngine → TradeAnalyzer

outputs: 分析結果（dict）、trade_log.csv、tick_data.csv

WalkforwardTester

split → calibrate → run → analyze → version manage

Optimizer

param_grid → run combinations → find best metric

Config contracts
decision

entry_threshold: float

exit_threshold: float

bias_prob_threshold: float

risk

stoploss_atr_mult: float

takeprofit_atr_mult: float

max_ticks: int

max_minutes: int

Data contracts
tick dict

required: price, volume, timestamp

common indicators: rsi, macd, macd_signal, macd_hist, ema5, ema20, adx, atr, vwap, bband_pos, is_ready, is_ready_5m, is_ready_15m

v4 fields (computed): bias, bias_prob, entry_score_v2, exit_score_v2, params_version, mode

Quick start
準備資料

使用 KlineInitializer.py 或 BacktestDataLoader.py 將 K 線轉成 ticks。

跑回測

BacktestRunner(mode="regression_based" | "rule_based").run(ticks)

視覺化與報告

ResultVisualizer("trade_log.csv").plot_pnl_curve()

PerformanceReporter("trade_log.csv").report()

ReportExporter().export_csv([...]); export_markdown([...])

走勢分段校正

WalkforwardTester(params_path, config_path).run_walkforward(ticks, segment_size=500)

參數最佳化

Optimizer(ticks).find_best(param_grid, mode="regression_based", metric="avg_pnl")

Notes
v4 的 DecisionEngine_v2 使用 ParamsStore 權重；沒有權重時會 fallback 到 default_weights。

StrategyState 應由 ConfigManager 或 config dict 注入 risk/decision 欄位，避免硬編碼。

v3/v4 可以並行；TickEngine 會根據 mode 切換分支。

pipeline/ 指標計算建議統一欄位名稱，避免 TickEngine 中 features 缺失。

Roadmap
回歸權重校正（RegressionCalibrator）與版本化（ParamsStore.update）對齊。

擴充 TradeAnalyzer 輸出指標，與 PerformanceReporter 接軌。

加入單元測試（pytest），覆蓋 TickEngine 進出場、StrategyState 風控、DecisionEngine_v2 分數一致性。

整合 VS Code tasks.json 一鍵回測與一鍵報告。

如果你同意，我可以把這份 README_architecture.md 產出為 Markdown 檔內容，並補上最小的 config/strategy_config.json 範例，確保重開環境後能一鍵跑通。你要我加上範例 config 與 sample tick schema 嗎？

github.com

felly790507-a11y/micro-futures-bot7

顯示全部
好
展碩，我幫你把進度與架構整理成一份 README_architecture.md 初版，這樣即使重開瀏覽器也能快速回復設計狀態。

README_architecture.md
專案架構概覽
本專案同時支援 v3 規則型 與 v4 回歸型 的微期交易系統，並提供完整的回測、視覺化、最佳化與走勢分段校正工具鏈。

目錄結構
engines/

DecisionEngine.py → v3 規則型：bias、score_entry、score_exit、should_enter

DecisionEngine_v2.py → v4 回歸型：evaluate_tick → bias、bias_prob、entry_score_v2、exit_score_v2

StrategyState.py → 持倉管理與風控：stoploss/takeprofit/exit_score/tick/time

TickEngine.py → 主循環：整合 v3/v4 引擎、指標、記錄

io/

TradeLogger.py → 交易事件記錄

TickRecorder.py → tick 記錄

TradeAnalyzer.py → 回測分析彙總

models/

ParamsStore.py → 權重版本管理 JSON

RegressionCalibrator.py → 分段權重校正，寫入 ParamsStore

backtest/

BacktestDataLoader.py → K 線轉 tick

BacktestRunner.py → 回測執行

ResultVisualizer.py → 盈虧曲線、勝率分布、版本比較

PerformanceReporter.py → Sharpe、最大回撤、平均持倉時間

WalkforwardTester.py → 分段校正 + 回測

Optimizer.py → 多參數最佳化

ReportExporter.py → CSV/Markdown 匯出

config/

strategy_config.json → risk/decision 參數集合

ConfigManager.py → 載入配置

pipeline/

polars_indicator_utils.py → 以 Polars 產生指標

root

KlineInitializer.py → 資料準備

StrategyLoop.py → 線上策略迴圈；可參考 TickEngine 結構

main.py → 入口

模組引用關係
TickEngine

inputs: tick dict（含 price、volume、timestamp 和指標）

uses: DecisionEngine_v2（v4）或 DecisionEngine（v3）、StrategyState、IndicatorEngine.extract_features、MultiTimeframeEngine、TradeLogger、TickRecorder、ParamsStore

outputs: 交易事件、tick 記錄、狀態更新

BacktestRunner

inputs: ticks（list[dict]）

orchestrates: TickEngine → TradeAnalyzer

outputs: 分析結果（dict）、trade_log.csv、tick_data.csv

WalkforwardTester

split → calibrate → run → analyze → version manage

Optimizer

param_grid → run combinations → find best metric

Config contracts
decision

entry_threshold: float

exit_threshold: float

bias_prob_threshold: float

risk

stoploss_atr_mult: float

takeprofit_atr_mult: float

max_ticks: int

max_minutes: int

Data contracts
tick dict

required: price, volume, timestamp

common indicators: rsi, macd, macd_signal, macd_hist, ema5, ema20, adx, atr, vwap, bband_pos, is_ready, is_ready_5m, is_ready_15m

v4 fields (computed): bias, bias_prob, entry_score_v2, exit_score_v2, params_version, mode

Quick start
準備資料

使用 KlineInitializer.py 或 BacktestDataLoader.py 將 K 線轉成 ticks。

跑回測

BacktestRunner(mode="regression_based" | "rule_based").run(ticks)

視覺化與報告

ResultVisualizer("trade_log.csv").plot_pnl_curve()

PerformanceReporter("trade_log.csv").report()

ReportExporter().export_csv([...]); export_markdown([...])

走勢分段校正

WalkforwardTester(params_path, config_path).run_walkforward(ticks, segment_size=500)

參數最佳化

Optimizer(ticks).find_best(param_grid, mode="regression_based", metric="avg_pnl")
