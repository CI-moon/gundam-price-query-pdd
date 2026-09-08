"""HTTP 请求下载器：会话复用、重试退避、限速、超时。"""

import time
from dataclasses import dataclass, field
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import REQUEST
from crawler.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Fetcher:
    """带重试与限速的 HTTP 下载器。

    Attributes:
        timeout: 单次请求超时秒数。
        retries: 最大重试次数。
        retry_backoff: 重试退避基数（秒），第 n 次重试等待 backoff * 2**n。
        min_interval: 两次请求的最小间隔（秒）。
        headers: 默认请求头。
        session: requests.Session，可复用连接（默认自动创建）。
        _last_request_at: 上次请求时间戳，用于限速。
    """

    timeout: float = REQUEST["timeout"]
    retries: int = REQUEST["retries"]
    retry_backoff: float = REQUEST["retry_backoff"]
    min_interval: float = REQUEST["min_interval"]
    headers: dict = field(default_factory=lambda: dict(REQUEST["headers"]))
    session: requests.Session | None = None
    _last_request_at: float = field(default=0.0, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.session is None:
            retry = Retry(
                total=self.retries,
                backoff_factor=self.retry_backoff,
                status_forcelist=(500, 502, 503, 504),
                allowed_methods=frozenset({"GET", "HEAD"}),
            )
            adapter = HTTPAdapter(max_retries=retry)
            self.session = requests.Session()
            self.session.mount("http://", adapter)
            self.session.mount("https://", adapter)

    def _throttle(self) -> None:
        """按 min_interval 限速，避免请求过快触发反爬。"""
        elapsed = time.monotonic() - self._last_request_at
        if self._last_request_at and elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self._last_request_at = time.monotonic()

    def fetch(self, url: str, *, encoding: str | None = None, **kwargs) -> requests.Response:
        """下载指定 URL，返回已校验的 Response。

        Args:
            url: 目标地址。
            encoding: 页面编码；不传则按响应头自动判断。
            **kwargs: 透传给 requests.get 的额外参数（params、cookies 等）。

        Raises:
            requests.RequestException: 重试后仍失败。
        """
        self._throttle()
        resp = self.session.get(
            url,
            timeout=self.timeout,
            headers={**self.headers, **kwargs.pop("headers", {})},
            **kwargs,
        )
        resp.raise_for_status()
        if encoding:
            resp.encoding = encoding
        elif resp.encoding is None or resp.encoding.lower() == "iso-8859-1":
            # 无 charset 时优先从 HTML meta 推断，其次用 UTF-8
            resp.encoding = resp.apparent_encoding or "utf-8"
        logger.debug("GET %s -> %s", url, resp.status_code)
        return resp

    @staticmethod
    def is_same_domain(url: str, allowed: str | list[str]) -> bool:
        """判断 URL 是否属于允许的域名集合。"""
        host = urlparse(url).netloc.lower()
        allowed_hosts = [allowed] if isinstance(allowed, str) else list(allowed)
        return any(host == a.lower() or host.endswith("." + a.lower()) for a in allowed_hosts)

    def close(self) -> None:
        self.session.close()
