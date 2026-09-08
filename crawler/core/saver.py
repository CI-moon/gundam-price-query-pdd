"""结果保存器：CSV（utf-8-sig，Excel 可直接打开）与 JSONL。"""

import csv
import json
from pathlib import Path
from typing import Iterable

from crawler.utils.logger import get_logger

logger = get_logger(__name__)


class Saver:
    """把抓取到的字典列表写入 CSV 和/或 JSONL 文件。"""

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def save_csv(self, filename: str, rows: Iterable[dict]) -> Path:
        """保存为 CSV，按第一条数据的键作为表头。返回文件路径。"""
        rows = list(rows)
        if not rows:
            logger.warning("没有数据可保存为 CSV：%s", filename)
            return self.output_dir / filename

        path = self.output_dir / filename
        with path.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        logger.info("已保存 CSV：%s（%d 条）", path, len(rows))
        return path

    def save_jsonl(self, filename: str, rows: Iterable[dict]) -> Path:
        """保存为 JSONL（每行一条 JSON），适合后续增量处理。"""
        rows = list(rows)
        path = self.output_dir / filename
        with path.open("w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        logger.info("已保存 JSONL：%s（%d 条）", path, len(rows))
        return path
