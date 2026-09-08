"""示例爬虫：抓取 quotes.toscrape.com 的名言、作者与标签，并自动翻页。

该站点是专门用于爬虫练习的公开站点，可直接运行验证。
换成真实目标站点时，改写 start_urls、parse 与 next_page 即可。
"""

from collections.abc import Iterable

from bs4 import BeautifulSoup

from crawler.spiders.base import BaseSpider


class QuotesSpider(BaseSpider):
    name = "quotes"
    allowed_domains = "quotes.toscrape.com"
    start_urls = ["https://quotes.toscrape.com/page/1/"]

    def parse(self, soup: BeautifulSoup, url: str) -> Iterable[dict]:
        for quote in soup.select("div.quote"):
            yield {
                "text": quote.select_one("span.text").get_text(strip=True),
                "author": quote.select_one("small.author").get_text(strip=True),
                "tags": [t.get_text(strip=True) for t in quote.select("a.tag")],
            }

    def next_page(self, soup: BeautifulSoup, url: str) -> str | None:
        next_el = soup.select_one("li.next > a")
        if next_el is None:
            return None
        return "https://quotes.toscrape.com" + next_el.get("href")
