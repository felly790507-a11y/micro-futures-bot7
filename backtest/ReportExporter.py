# strategy_v4/backtest/ReportExporter.py

import csv
from pathlib import Path
from typing import Dict, Any, List

class ReportExporter:
    """
    報告匯出器：
    - 將回測與最佳化結果輸出成 CSV 或 Markdown
    - 支援多組結果比較
    """

    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_csv(self, results: List[Dict[str, Any]], filename: str = "report.csv"):
        """匯出成 CSV"""
        path = self.output_dir / filename
        if not results:
            print("[Exporter] 無結果可匯出")
            return

        keys = list(results[0].keys())
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            for r in results:
                writer.writerow(r)

        print(f"[Exporter] 已匯出 CSV 報告：{path}")

    def export_markdown(self, results: List[Dict[str, Any]], filename: str = "report.md", title: str = "回測報告"):
        """匯出成 Markdown"""
        path = self.output_dir / filename
        if not results:
            print("[Exporter] 無結果可匯出")
            return

        keys = list(results[0].keys())
        with path.open("w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n")
            f.write("| " + " | ".join(keys) + " |\n")
            f.write("|" + " --- |" * len(keys) + "\n")
            for r in results:
                f.write("| " + " | ".join(str(r.get(k, "")) for k in keys) + " |\n")

        print(f"[Exporter] 已匯出 Markdown 報告：{path}")
