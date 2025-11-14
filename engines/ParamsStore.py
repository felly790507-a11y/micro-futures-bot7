# strategy_v4/models/ParamsStore.py

import json
from pathlib import Path
from typing import Dict, Any


class ParamsStore:
    def __init__(self, json_path: str | Path = "calibrated_params.json"):
        self.path = Path(json_path)
        self._data: Dict[str, Any] = {}
        self._loaded = False

    def load(self) -> None:
        if self.path.exists():
            with self.path.open("r", encoding="utf-8") as f:
                self._data = json.load(f)
            self._loaded = True
        else:
            self._data = {"version": "unversioned", "weights": {}}
            self._loaded = True

    def get_version(self) -> str:
        if not self._loaded:
            self.load()
        return str(self._data.get("version", "unversioned"))

    def get_weights(self) -> Dict[str, float]:
        if not self._loaded:
            self.load()
        w = self._data.get("weights", {})
        return {k: float(v) for k, v in w.items()}

    def update(self, version: str, weights: Dict[str, float]) -> None:
        self._data = {"version": version, "weights": weights}
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)
        self._loaded = True
