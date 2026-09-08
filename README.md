# 高达价格查询（pdd）

拼多多万代 RG 系列高达模型价格采集与查询项目，基于 `requests` + `BeautifulSoup` 爬虫框架 + 浏览器采集。

## 查询结果位置

- **价格数据表**：`data/pdd_rg_prices.csv`（列：标题、价格、销量，utf-8-sig 编码，Excel 可直接打开）
- **采集原始文本**：`data/raw/pdd_rg_raw.txt`（浏览器抓取的拼多多搜索结果页面文本）
- **解析脚本**：`parse_pdd.py`（把原始文本解析为价格表，重新抓取数据后覆盖原始文本再运行即可刷新）

```bash
# 重新生成价格表
python parse_pdd.py
```

查询示例见文末「数据查询」。

## 项目结构

```
python-crawler/
├── main.py                  # 命令行入口
├── config.py                # 全局配置（请求头、超时、重试、限速等）
├── requirements.txt         # 依赖清单
├── crawler/
│   ├── core/
│   │   ├── fetcher.py       # HTTP 下载器：连接复用 / 重试退避 / 限速
│   │   ├── parser.py        # HTML 解析工具（BeautifulSoup 封装）
│   │   └── saver.py         # 结果保存：CSV、JSONL
│   ├── spiders/
│   │   ├── base.py          # 爬虫基类（抓取→解析→翻页 标准流程）
│   │   └── quotes_spider.py # 示例爬虫（quotes.toscrape.com）
│   └── utils/
│       └── logger.py        # 日志（控制台 + 文件）
├── data/                    # 抓取结果输出目录（自动创建）
└── logs/                    # 日志目录（自动创建）
```

## 快速开始

```bash
# 1. 创建虚拟环境并安装依赖
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt

# 2. 运行示例爬虫（quotes.toscrape.com 是官方练习站点）
python main.py --pages 3

# 3. 查看结果
#    data/result.csv   用 Excel 可直接打开
#    data/result.jsonl 每行一条 JSON
```

## 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--spider` | 要运行的爬虫名 | `quotes` |
| `--pages` | 最大抓取页数 | `10` |
| `--output` | 输出路径（不含扩展名） | `data/result` |
| `--format` | 输出格式，逗号分隔 | `csv,jsonl` |

## 如何新增一个爬虫

1. 在 `crawler/spiders/` 下新建文件（如 `example_spider.py`）。
2. 继承 `BaseSpider`，实现：

```python
from bs4 import BeautifulSoup
from collections.abc import Iterable
from crawler.spiders.base import BaseSpider

class ExampleSpider(BaseSpider):
    name = "example"
    allowed_domains = "example.com"        # 只抓该域名内的链接
    start_urls = ["https://example.com/"]  # 入口地址

    def parse(self, soup: BeautifulSoup, url: str) -> Iterable[dict]:
        for el in soup.select(".item"):
            yield {"title": el.get_text(strip=True), "url": url}

    def next_page(self, soup: BeautifulSoup, url: str) -> str | None:
        return None  # 返回下一页地址，或 None 表示结束
```

3. 在 `main.py` 的 `_register_spiders()` 中登记：

```python
from crawler.spiders.example_spider import ExampleSpider
SPIDERS[ExampleSpider.name] = ExampleSpider
```

4. 运行：`python main.py --spider example`

## 数据查询

方式一：直接打开 `data/pdd_rg_prices.csv`（Excel / WPS 筛选、排序）。

方式二：Python 标准库查询：

```python
import csv

with open("data/pdd_rg_prices.csv", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

rows.sort(key=lambda r: float(r["价格"]))   # 按价格升序
for r in rows[:5]:                            # 最便宜的 5 款
    print(r["价格"], r["标题"])
```

方式三：pandas 查询（需 `pip install pandas`）：

```python
import pandas as pd
df = pd.read_csv("data/pdd_rg_prices.csv")
df.sort_values("价格")                     # 按价格排序
df[df["价格"] < 200]                       # 筛选 200 元以下
df["价格"].describe()                      # 均值 / 中位数 / 分位数
df[df["标题"].str.contains("牛高达")]       # 关键词筛选
```

## 说明与注意事项

- **限速与重试**：默认请求间隔 0.5 秒、失败重试 3 次（指数退避），可在 `config.py` 调整。
- **合法性**：爬取前请确认目标站点 `robots.txt` 与相关法规，控制抓取频率，勿抓取需登录或明确禁止的页面；示例站点 `quotes.toscrape.com` 专为爬虫练习设计。
- **编码**：CSV 以 `utf-8-sig` 保存，Excel 直接打开不乱码。
