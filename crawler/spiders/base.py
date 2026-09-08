"""爬虫基类：定义 抓取 → 解析 → 产出 的标准流程。

子类需要实现：
- name / allowed_domains / start_urls 三个类属性
- parse(response) 方法：返回 dict 列表（每条为一笔数据）
- 可选：next_page(response) 返回下一页 URL 或 None

run() 会按 start_urls 逐个抓取，自动翻页并收集数据。
"""

from collections.abc import Iterable

from bs4 import BeautifulSoup
from requests import Response

from crawler.core.fetcher import Fetcher
from crawler.core.parser import parse_html
from crawler.utils.logger import get_logger

logger = get_logger(__name__)


class BaseSpider:
    name: str = "base"                       # 爬虫标识，命令行 --spider 使用
    allowed_domains: str | list[str] = []    # 只抓取这些域名内的链接
    start_urls: list[str] = []               # 入口 URL
    max_pages: int = 10                      # 最大翻页数（含入口页）

    def __init__(self, fetcher: Fetcher | None = None, max_pages: int | None = None) -> None:
        self.fetcher = fetcher or Fetcher()
        if max_pages is not None:
            self.max_pages = max_pages
        self.results: list[dict] = []

    # ---- 子类必须实现 ----
    def parse(self, soup: BeautifulSoup, url: str) -> Iterable[dict]:
        """解析页面，返回数据字典的列表。"""
        raise NotImplementedError

    # ---- 可选扩展 ----
    def next_page(self, soup: BeautifulSoup, url: str) -> str | None:
        """返回下一页 URL；没有则返回 None。默认不翻页。"""
        return None

    def process_item(self, item: dict) -> dict:
        """保存前对单条数据的加工钩子，默认原样返回。"""
        return item

    # ---- 运行框架 ----
    def _allowed(self, url: str) -> bool:
        return Fetcher.is_same_domain(url, self.allowed_domains)

    def run(self) -> list[dict]:
        """执行抓取流程，返回全部数据。"""
        if not self.start_urls:
            raise ValueError(f"爬虫 {self.name} 未配置 start_urls")

        visited: set[str] = set()
        queue = list(self.start_urls)
        for page_no in range(1, self.max_pages + 1):
            if not queue:
                break
            url = queue.pop(0)
            if url in visited:
                continue
            visited.add(url)

            logger.info("[%s] 抓取 %d/%d：%s", self.name, page_no, self.max_pages, url)
            try:
                resp = self.fetcher.fetch(url)
            except Exception as exc:  # 网络/超时/HTTP 错误，记录后继续
                logger.warning("[%s] 抓取失败 %s：%s", self.name, url, exc)
                continue

            soup = parse_html(resp.text)
            for item in self.parse(soup, url):
                self.results.append(self.process_item(item))

            next_url = self.next_page(soup, url)
            if next_url and self._allowed(next_url) and next_url not in visited:
                queue.append(next_url)

        logger.info("[%s] 抓取完成，共 %d 条数据", self.name, len(self.results))
        return self.results
