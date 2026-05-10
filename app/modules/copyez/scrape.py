"""
Scraper (素材抓取) module.

Intelligent article scraping from web sources (WeChat public accounts, etc.).
"""

from flask import Blueprint, request, jsonify

from app.utils.scraper.manager import scrape_manager

scrape_bp = Blueprint("scrape", __name__)


@scrape_bp.route("/api/scrape", methods=["POST"])
def api_scrape():
    """
    API：素材智能抓取

    请求体（JSON 或表单）：
        { "url": "https://mp.weixin.qq.com/..." }

    返回：
        {
            "status": "success" / "error",
            "message": "...",
            "title": "...",
            "content": "..."
        }
    """
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or request.form.get("url") or "").strip()

    if not url:
        return jsonify(
            {
                "status": "error",
                "message": "请输入要抓取的链接",
            }
        ), 400

    result = None
    try:
        result = scrape_manager.fetch(url)
    except Exception as e:
        return jsonify(
            {
                "status": "error",
                "message": f"抓取失败：{str(e)}",
            }
        ), 500

    if not result:
        return jsonify(
            {
                "status": "error",
                "message": "当前暂不支持该链接来源，请确认是否为公众号文章",
            }
        ), 400

    return jsonify(
        {
            "status": "success",
            "title": result.title,
            "content": result.content,
        }
    )
