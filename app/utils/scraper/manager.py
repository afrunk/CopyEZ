from typing import List, Optional

from .base import BaseScraper, ScrapeResult
from .wechat import WechatScraper


class ScrapeManager:
    """统一入口：根据 URL 自动选择对应爬虫"""

    def __init__(self) -> None:
        self._scrapers: List[BaseScraper] = [
            WechatScraper(),
            # 后续可以在这里继续追加：ZhihuScraper(), ToutiaoScraper(), XinhuaScraper() ...
        ]

    def fetch(self, url: str) -> Optional[ScrapeResult]:
        if not url:
            return None

        for scraper in self._scrapers:
            try:
                if scraper.can_handle(url):
                    return scraper.fetch(url)
            except Exception:
                # 单个爬虫失败不影响整体，可按需写日志
                continue
        return None


scrape_manager = ScrapeManager()

