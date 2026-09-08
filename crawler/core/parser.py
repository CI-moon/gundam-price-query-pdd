"""HTML 解析工具：基于 BeautifulSoup 的常用提取函数。"""

from bs4 import BeautifulSoup, Tag

__all__ = ["parse_html", "extract_text", "extract_all_text", "extract_attr", "find_items"]


def parse_html(html: str, parser: str = "lxml") -> BeautifulSoup:
    """把 HTML 字符串解析为 BeautifulSoup 对象。"""
    return BeautifulSoup(html, parser)


def extract_text(node: Tag, selector: str, default: str = "") -> str:
    """取第一个匹配节点的文本，去掉首尾空白；没有匹配则返回 default。"""
    el = node.select_one(selector)
    if el is None:
        return default
    return el.get_text(strip=True)


def extract_all_text(node: Tag, selector: str) -> list[str]:
    """取所有匹配节点的文本（去空白）。"""
    return [el.get_text(strip=True) for el in node.select(selector)]


def extract_attr(node: Tag, selector: str, attr: str, default: str = "") -> str:
    """取第一个匹配节点的某个属性值；没有匹配或属性缺失则返回 default。"""
    el = node.select_one(selector)
    if el is None:
        return default
    return el.get(attr, default)


def find_items(root: Tag, selector: str) -> list[Tag]:
    """返回所有匹配选择器的节点列表，供逐条解析。"""
    return root.select(selector)
