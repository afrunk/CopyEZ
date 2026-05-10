import abc
from dataclasses import dataclass
from typing import Optional


@dataclass
class ScrapeResult:
    """统一的抓取结果结构"""

    title: str
    content: str


class BaseScraper(abc.ABC):
    """所有站点爬虫的抽象基类"""

    @abc.abstractmethod
    def can_handle(self, url: str) -> bool:
        """当前爬虫是否支持处理该 URL"""

    @abc.abstractmethod
    def fetch(self, url: str, timeout: int = 10) -> Optional[ScrapeResult]:
        """执行抓取，返回标准化结果；失败时返回 None 或抛出异常"""

