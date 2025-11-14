# strategy_v4/config/ConfigManager.py

import json
from pathlib import Path
from typing import Dict, Any

class ConfigManager:
    """
    配置管理器：
    - 集中管理策略的風控與決策參數
    - 支援 JSON 檔案讀取
    - 提供 get_risk_params / get_decision_params 等接口
    """

    def __init__(self, config_path: str | Path = "strategy_config.json"):
        self.path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._loaded = False

    def load(self) -> None:
        """載入配置檔案"""
        if self.path.exists():
            with self.path.open("r", encoding="utf-8") as f:
                self._config = json.load(f)
        else:
            # 預設配置
            self._config = {
                "risk": {
                    "stoploss_atr_mult": 2.0,
                    "takeprofit_atr_mult": 3.0,
                    "max_ticks": 50,
                    "max_minutes": 30
                },
                "decision": {
                    "entry_threshold": 0.0,
                    "exit_threshold": 0.0,
                    "bias_prob_threshold": 0.55
                }
            }
        self._loaded = True

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """取得指定配置值"""
        if not self._loaded:
            self.load()
        return self._config.get(section, {}).get(key, default)

    def get_risk_params(self) -> Dict[str, Any]:
        """取得風控參數"""
        if not self._loaded:
            self.load()
        return self._config.get("risk", {})

    def get_decision_params(self) -> Dict[str, Any]:
        """取得決策參數"""
        if not self._loaded:
            self.load()
        return self._config.get("decision", {})

    def update(self, section: str, key: str, value: Any) -> None:
        """更新配置值並寫回檔案"""
        if not self._loaded:
            self.load()
        if section not in self._config:
            self._config[section] = {}
        self._config[section][key] = value
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(self._config, f, ensure_ascii=False, indent=2)
