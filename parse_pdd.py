"""拼多多搜索结果文本 → 结构化 CSV。

输入：data/raw/pdd_rg_raw.txt（浏览器采集的页面文本，每行一个元素）
输出：data/pdd_rg_prices.csv（标题、价格、销量）

过滤规则：
- 仅保留标题包含 RG（不区分大小写）的万代 RG 系列商品
- 排除标题含「图中9款 / 图中九款 / 盲盒」的词条
"""

import csv
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
RAW_FILE = BASE_DIR / "data" / "raw" / "pdd_rg_raw.txt"
OUT_FILE = BASE_DIR / "data" / "pdd_rg_prices.csv"

# 私有图标与零宽字符，直接清理
_CLEAN_RE = re.compile(r"[\ue000-\uf8ff\u200b\u200c\u200d\ufeff]")

# 独立成行的标签词（出现在标题与价格之间，或商品之间）
_TAG_RE = re.compile(
    r"^(仅剩\d+件|立减\d+元|券后|假一赔十|即将售罄|限\d+件|顺丰包邮|退货包运费|"
    r"发货前可快速退款|已包邮|分期付款|正品发票|包邮|24小时发货|\d+天内发货|"
    r"好评超\d+%同款|店铺好评[\d.万+]+条|全店好评[\d.万+]+条|已抢\d+件|"
    r"本店已拼[\d.万+]+\+|本店已拼\d+|正在加载中|顶部|试试搜这些|"
    r"用手机浏览器扫码在拼多多App打开|商品|综合|销量|价格|品牌|筛选|"
    r"秋季特惠|回头客常拼|1:144|日本|拼装|MG|14岁以上|大陆版|RG|万代RG)$"
)

# 排除词条（用户指定）
_EXCLUDE_WORDS = ("图中9款", "图中九款", "盲盒")

# RG 系列判定：RG 前不得是字母数字（独立词），RG 后不得跟字母（排除 RGM 等编号），
# 但允许跟数字/符号（RG32、RG1/144、RG2.0 都是 RG 系列）；
# RGU 为 RG 2.0 标识、RG 后跟 PB（RGPB限定=RG PB限定）也保留
_RG_RE = re.compile(r"(?<![A-Za-z0-9])RG(?![A-Za-z])|RGU|RG(?=PB)", re.IGNORECASE)


def clean_line(line: str) -> str:
    return _CLEAN_RE.sub("", line).strip()


def is_tag_line(line: str) -> bool:
    return bool(_TAG_RE.match(line))


def looks_like_title(line: str) -> bool:
    """标题判定：较长、非标签行、含 RG/高达/模型/拼装 等特征。"""
    if len(line) < 6 or is_tag_line(line):
        return False
    return ("rg" in line.lower()) or ("高达" in line) or ("模型" in line) or ("拼装" in line)


def parse_price(lines: list[str], i: int) -> tuple[float, int]:
    """从 ¥ 所在行开始解析价格，返回 (价格, 消费到的行号)。"""
    num = lines[i + 1] if i + 1 < len(lines) else ""
    j = i + 2
    if j < len(lines) and re.fullmatch(r"\.\d+", lines[j]):
        num += lines[j]
        j += 1
    try:
        price = float(num)
    except ValueError:
        price = 0.0
    return price, j


def parse_sales(lines: list[str], j: int) -> str:
    """价格之后的一行通常是销量信息，取到就返回。"""
    if j < len(lines) and re.match(r"^(本店已拼|已抢|店铺好评|全店好评)", lines[j]):
        return lines[j]
    return ""


def main() -> None:
    if not RAW_FILE.exists():
        raise SystemExit(f"未找到原始数据文件：{RAW_FILE}")

    raw = RAW_FILE.read_text(encoding="utf-8")
    lines = [clean_line(l) for l in raw.splitlines()]
    lines = [l for l in lines if l]

    items: list[dict] = []
    for i, line in enumerate(lines):
        if line != "¥":
            continue
        price, j = parse_price(lines, i)
        if price <= 0:
            continue

        # 从价格前向上回溯，找最近一条标题
        title = ""
        for k in range(i - 1, max(-1, i - 15), -1):
            if looks_like_title(lines[k]):
                title = lines[k]
                break
            if len(lines[k]) > 25 and "高达" not in lines[k] and "模型" not in lines[k]:
                break  # 遇到明显无关的长文本（如推荐语），停止回溯
        if not title:
            continue

        # 去掉拼在标题尾部的发货时间（如 7天内发货）
        title = re.sub(r"(\d+天内发货|\d+小时发货)$", "", title).strip()
        if not _RG_RE.search(title):
            continue  # 只保留 RG 系列（独立词 RG 或 RGU）
        if any(w in title for w in _EXCLUDE_WORDS):
            continue  # 排除用户指定的词条

        items.append({"标题": title, "价格": f"{price:.2f}", "销量": parse_sales(lines, j)})

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUT_FILE.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["标题", "价格", "销量"])
        writer.writeheader()
        writer.writerows(items)

    print(f"解析完成：共 {len(items)} 条商品 → {OUT_FILE}")


if __name__ == "__main__":
    main()
