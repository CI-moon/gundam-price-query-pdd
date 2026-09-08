"""命令行入口。

用法示例：
    python main.py                     # 使用默认爬虫，默认翻页数
    python main.py --spider quotes --pages 3
    python main.py --output data/quotes.csv --format csv,jsonl
"""

import argparse
from pathlib import Path

from config import BASE_DIR, CRAWL, DATA_DIR
from crawler.core.saver import Saver
from crawler.utils.logger import get_logger

logger = get_logger("main")

# 已注册的爬虫：name -> 类。新增爬虫时在此登记。
SPIDERS = {}


def _register_spiders() -> None:
    from crawler.spiders.quotes_spider import QuotesSpider

    SPIDERS[QuotesSpider.name] = QuotesSpider


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="通用 Python 爬虫框架")
    parser.add_argument("--spider", default=CRAWL["default_spider"], help="要运行的爬虫名")
    parser.add_argument("--pages", type=int, default=CRAWL["max_pages"], help="最大抓取页数")
    parser.add_argument("--output", default=str(DATA_DIR / "result"), help="输出文件路径（不含扩展名）")
    parser.add_argument(
        "--format",
        default="csv,jsonl",
        help="输出格式，逗号分隔：csv,jsonl（默认两者都输出）",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    _register_spiders()

    spider_cls = SPIDERS.get(args.spider)
    if spider_cls is None:
        logger.error("未知爬虫：%s，可用：%s", args.spider, ", ".join(SPIDERS))
        return 1

    spider = spider_cls(max_pages=args.pages)
    rows = spider.run()
    spider.fetcher.close()

    if not rows:
        logger.warning("未抓到任何数据，跳过保存。")
        return 0

    out_base = Path(args.output)
    saver = Saver(out_base.parent)
    if "csv" in args.format:
        saver.save_csv(out_base.with_suffix(".csv").name, rows)
    if "jsonl" in args.format:
        saver.save_jsonl(out_base.with_suffix(".jsonl").name, rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
