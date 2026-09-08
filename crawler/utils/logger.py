"""日志工具：统一控制台 + 文件日志。"""

import logging
import sys
from pathlib import Path

from config import LOG_DIR

_FMT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def setup_logger(name: str = "crawler", level: int = logging.INFO) -> logging.Logger:
    """创建并返回一个带控制台和文件输出的 logger。"""
    logger = logging.getLogger(name)
    if logger.handlers:  # 已初始化则直接复用
        return logger

    logger.setLevel(level)
    logger.propagate = False

    formatter = logging.Formatter(_FMT)

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    logger.addHandler(console)

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(LOG_DIR / f"{name}.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    return setup_logger(name or __name__)
