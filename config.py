"""全局配置：请求参数、爬取策略、输出目录等。"""

from pathlib import Path

# 项目根目录（本文件所在目录）
BASE_DIR = Path(__file__).resolve().parent

# 输出目录
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"

# 请求配置
REQUEST = {
    "timeout": 15,            # 单次请求超时（秒）
    "retries": 3,             # 失败重试次数
    "retry_backoff": 2.0,     # 重试退避基数（秒），指数增长
    "min_interval": 0.5,      # 两次请求之间的最小间隔（秒），避免请求过快
    "headers": {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    },
}

# 爬取策略
CRAWL = {
    "default_spider": "quotes",   # 默认运行的爬虫
    "max_pages": 10,              # 默认最大翻页数
    "respect_robots": True,       # 是否尊重 robots.txt（简化实现，仅做提示性检查）
}
