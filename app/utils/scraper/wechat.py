import logging
import re
from typing import Optional

import requests
from bs4 import BeautifulSoup

from .base import BaseScraper, ScrapeResult


class WechatScraper(BaseScraper):
    """微信公众号文章抓取器"""

    WECHAT_HOST_PATTERNS = (
        "mp.weixin.qq.com",
        "weixin.qq.com",
    )

    def can_handle(self, url: str) -> bool:
        if not url:
            return False
        return any(host in url for host in self.WECHAT_HOST_PATTERNS)

    def fetch(self, url: str, timeout: int = 10) -> Optional[ScrapeResult]:
        if not self.can_handle(url):
            return None

        headers = {
            # 模拟常见桌面浏览器，避免极简单 UA 拦截
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/123.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "zh-CN,zh;q=0.9",
        }

        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()

        html = resp.text
        soup = BeautifulSoup(html, "html.parser")

        # 0. 全局预清洗：先把明显无关/干扰性的标签和容器从 DOM 树中物理删除
        #    这样后续无论是标题还是正文提取，都不会被这些“牛皮癣”污染。
        for tag_name in ("script", "style", "svg", "iframe", "video"):
            for t in soup.find_all(tag_name):
                t.decompose()

        # 微信常见的工具栏、二维码、赞赏等区域 class
        noise_classes = (
            "rich_media_tool",
            "qr_code_pc",
            "reward_area",
        )
        for cls in noise_classes:
            for t in soup.select(f".{cls}"):
                t.decompose()

        # 1. 标题：微信通常放在 #activity-name
        title_el = soup.select_one("#activity-name") or soup.find("h1")
        title = title_el.get_text(strip=True) if title_el else ""

        # 2. 正文：微信正文容器 #js_content
        content_root = soup.select_one("#js_content")
        if not content_root:
            # 兜底：尝试常见正文容器
            for selector in ("article", ".rich_media_content", ".article-content"):
                content_root = soup.select_one(selector)
                if content_root:
                    break

        if not content_root:
            logging.warning("WechatScraper: 未找到正文容器")
            # 调试输出：打印页面部分 HTML，帮助分析结构变化
            try:
                print("\n==== [WechatScraper DEBUG] 未找到正文容器 ====")
                print(f"URL: {url}")
                snippet = soup.prettify()[:1500]
                print(snippet)
                print("==== [WechatScraper DEBUG END] ====\n")
            except Exception:
                pass
            return ScrapeResult(title=title or url, content="")

        # 2.1 全解析度段落重构：递归识别块级“叶子节点”，为每个内容块强制断行
        paragraphs = []

        BLOCK_TAGS = {"p", "section", "div", "h1", "h2", "h3", "h4", "h5", "h6"}

        def _is_noise_text(text: str) -> bool:
            """判定是否为应剔除的尾部噪音段落/尾部开始标记"""
            if not text:
                return False
            # 关键词熔断：一旦命中，就认为正文已经结束
            noise_keywords = [
                "来源丨",
                "记者丨",
                "编辑丨",
                "校对丨",
                "审核丨",
                "精彩内容不要错过",
                "这些精彩内容不要错过",
                "小布快报",
                "扫描二维码",
                "扫描二维码关注",
                "戳这里",
                "戳这里，让小布知道你“在看”",
                "往期推荐",
            ]
            t = text.replace(" ", "")
            return any(k in t for k in noise_keywords)

        def _extract_block_text(node) -> str:
            """从单个块级节点中提取纯文本，并压缩多余空白"""
            text = node.get_text(separator=" ", strip=True)
            if not text:
                return ""
            text = re.sub(r"\s+", " ", text).strip()
            return text

        def _is_pure_block(node) -> bool:
            """判断当前块级节点内部是否还包含其他块级节点（避免“复读机”）"""
            for d in node.descendants:
                if d is node:
                    continue
                name = getattr(d, "name", None)
                if name and name in BLOCK_TAGS:
                    # 内部还有块级子节点，父节点不再单独作为段落
                    return False
            return True

        def _upgrade_heading(text: str, node) -> str:
            """将疑似小标题自动升级为 Markdown 二级标题"""
            if not text:
                return text

            # 显式标题标签直接升级
            if getattr(node, "name", None) in ("h1", "h2", "h3", "h4", "h5", "h6"):
                return f"## {text}"

            stripped = text.strip()
            # 简短、无句号/问号/感叹号/句末标点，多为小标题，如“01 依法履职尽责”
            if len(stripped) <= 20 and not re.search(r"[。？?！!；;，,\.]", stripped):
                return f"## {stripped}"

            return text

        # 遍历 content_root 下的所有后代节点，按 DOM 顺序抽取“叶子块级段落”
        for node in content_root.descendants:
            name = getattr(node, "name", None)
            if not name:
                continue

            # 显式换行标签：转成一个空段落，保留公众号用 <br> 做出来的空行
            if name == "br":
                paragraphs.append("")
                continue

            if name not in BLOCK_TAGS:
                continue

            # 只处理“纯块级叶子节点”，避免父节点重复包含子节点内容
            if not _is_pure_block(node):
                continue

            text = _extract_block_text(node)

            # 空块：如果内部包含 <br>，保留为空行；否则跳过
            if not text:
                if node.find("br"):
                    paragraphs.append("")
                continue

            # 一旦命中“来源丨/记者丨/扫描二维码/往期推荐”等尾部噪音标记：
            # - 当前段落不再收录
            # - 立即停止后续所有内容的抓取（硬熔断），保证尾部宣传/工具栏全部被切断
            if _is_noise_text(text):
                break

            text = _upgrade_heading(text, node)
            paragraphs.append(text)

        # content 统一按 Markdown 段落格式组织：段与段之间两个换行符
        content = "\n\n".join(paragraphs)

        # 如果经过过滤后一个段落都没有：
        # 1）打印调试信息；
        # 2）退回到“整块提取”的兜底方案，宁可多一点噪音也不要空白正文。
        if not content.strip():
            try:
                print("\n==== [WechatScraper DEBUG] 段落全部为空，启用兜底提取 ====")
                print(f"URL: {url}")
                print("content_root 首屏 HTML：")
                snippet = content_root.prettify()[:1500]
                print(snippet)
                print("==== [WechatScraper DEBUG END] ====\n")
            except Exception:
                pass

            # 兜底：直接对整个 content_root 做一次文本提取
            fallback_text = _extract_block_text(content_root)
            content = fallback_text or ""

        return ScrapeResult(title=title or url, content=content)

