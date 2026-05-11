"""
TradingAgents 客户版固定启动脚本

用途：
1. 不进入 tradingagents 命令行交互界面。
2. 客户只需要修改本文件顶部的“客户配置区”。
3. 默认使用 Claude / Anthropic API。
4. 运行后会在终端输出最终决策，并保存 Markdown 结果文件。

注意：
TradingAgents 是研究性质的多智能体金融分析框架，不构成投资建议。
一次运行会调用多次大模型 API，分析师越多、辩论轮数越多、模型越强，费用越高。
"""

import os
import json
import traceback
from datetime import datetime
from pathlib import Path

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG


# ============================================================
# 一、客户配置区：客户主要改这里
# ============================================================

# Claude API Key
# 推荐方式：在系统环境变量里配置 ANTHROPIC_API_KEY
# 如果客户不会配置环境变量，也可以直接填在这里。
# 示例：ANTHROPIC_API_KEY = "sk-ant-xxxxxxxx"
# 不建议把真实 Key 发给别人，也不要提交到 GitHub。
ANTHROPIC_API_KEY = ""  # 请使用环境变量 ANTHROPIC_API_KEY 或填写您的 Key

# 股票代码
# 示例：
# 美股：AAPL、MSFT、NVDA、TSLA、SPY、QQQ
# 注意：具体支持哪些市场，取决于 TradingAgents 当前数据源。
TICKER = "AAPL"
# TICKERS = ["AAPL", "MSFT", "NVDA", "TSLA"] 

# 分析日期
# 格式：YYYY-MM-DD
# 建议使用最近的交易日。
ANALYSIS_DATE = "2026-04-10"

# 输出语言
# 常见可选值：English / Chinese
# 如果项目当前版本不支持 language 字段，脚本会自动跳过。
LANGUAGE = "Chinese"

# 是否开启调试模式
# True：终端会输出更多过程信息，方便排查问题
# False：输出更简洁
DEBUG = True


# ============================================================
# 二、模型配置区
# ============================================================

# 模型供应商
# 使用 Claude API 时一般填写：anthropic
# 其他可能选项：openai、google、deepseek、qwen、ollama、openrouter
# 具体以当前项目支持为准。
LLM_PROVIDER = "anthropic"

# 快速思考模型
# 用于普通分析、摘要、较轻任务。
# 建议先用低成本模型测试。
# Claude 常见模型名可能包括：
# claude-3-5-haiku-latest
# claude-3-5-sonnet-latest
# claude-sonnet-4-5
# claude-haiku-4-5
# 具体模型名必须以当前 Anthropic API 和 TradingAgents 支持为准。
QUICK_THINK_LLM = "claude-sonnet-4-6"

# 深度思考模型
# 用于更复杂的推理任务，费用通常更高。
# 客户预算有限时，可以先和 QUICK_THINK_LLM 填一样。
DEEP_THINK_LLM = "claude-sonnet-4-6"

# 后端地址
# 一般 Claude 官方 API 不需要改。
# 如果使用 OpenRouter / 中转 / 本地模型，可能需要配置。
# 不懂就保持 None。
BACKEND_URL = None


# ============================================================
# 三、分析师团队配置区
# ============================================================

# 分析师团队
# 可选项通常包括：
# market：技术/市场分析
# social：社交媒体/情绪分析
# news：新闻分析
# fundamentals：基本面分析
#
# 费用影响：
# 选择越多，调用次数越多，费用越高，速度越慢。
#
# 最省钱测试：
# ANALYSTS = ["market"]
#
# 完整分析：
ANALYSTS = ["market", "social", "news", "fundamentals"]


# ============================================================
# 四、研究深度和成本控制区
# ============================================================

# 多空研究员最大辩论轮数
# 0：基本不辩论，最省钱
# 1：推荐客户默认值
# 2 或以上：更深入，但更慢、更贵
MAX_DEBATE_ROUNDS = 1

# 风控团队最大讨论轮数
# 0：基本不讨论，省钱
# 1：推荐客户默认值
# 2 或以上：更深入，但更慢、更贵
MAX_RISK_DISCUSS_ROUNDS = 1

# 是否开启在线工具
# True：可能联网获取新闻、行情、财务等信息，结果更丰富，但可能更慢
# False：少用外部工具，速度和稳定性可能更好
# 是否生效取决于当前 TradingAgents 版本。
ONLINE_TOOLS = True


# ============================================================
# 五、输出配置区
# ============================================================

# 是否保存最终结果
SAVE_RESULT = True

# 是否保存完整调试信息
# True：会额外保存 state，方便开发者查看 TradingAgents 到底输出了什么
# False：只保存最终决策
SAVE_DEBUG_STATE = True

# 输出目录
OUTPUT_DIR = "outputs"


# ============================================================
# 六、工具函数区：一般不用改
# ============================================================

def set_config_if_exists(config: dict, key: str, value):
    """
    只在 DEFAULT_CONFIG 已存在该字段时才设置。
    这样可以避免当前 TradingAgents 版本没有某个字段时直接报错。
    """
    if key in config:
        config[key] = value
        print(f"已设置配置项：{key} = {value}")
    else:
        print(f"提示：当前 DEFAULT_CONFIG 中没有字段 {key}，已跳过。")


def safe_to_text(obj) -> str:
    """
    尽量把对象转成文本。
    有些 state 里可能包含复杂对象，直接 json.dumps 可能失败。
    """
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2, default=str)
    except Exception:
        return str(obj)


def prepare_api_key():
    """
    准备 Claude API Key。
    优先使用系统环境变量；如果没有，再使用本文件中的 ANTHROPIC_API_KEY。
    """
    if os.getenv("ANTHROPIC_API_KEY"):
        print("已检测到系统环境变量 ANTHROPIC_API_KEY。")
        return

    if ANTHROPIC_API_KEY.strip():
        os.environ["ANTHROPIC_API_KEY"] = ANTHROPIC_API_KEY.strip()
        print("已使用 run_customer.py 中填写的 ANTHROPIC_API_KEY。")
        return

    raise RuntimeError(
        "没有检测到 Claude API Key。\n"
        "请二选一：\n"
        "1. 在系统环境变量中配置 ANTHROPIC_API_KEY；\n"
        "2. 在 run_customer.py 顶部填写 ANTHROPIC_API_KEY。"
    )


def build_config():
    """
    基于 DEFAULT_CONFIG 构建客户配置。
    注意：不同版本 TradingAgents 的字段可能不同，所以这里做兼容处理。
    """
    config = DEFAULT_CONFIG.copy()

    # 模型相关配置
    set_config_if_exists(config, "llm_provider", LLM_PROVIDER)
    set_config_if_exists(config, "quick_think_llm", QUICK_THINK_LLM)
    set_config_if_exists(config, "deep_think_llm", DEEP_THINK_LLM)

    if BACKEND_URL:
        set_config_if_exists(config, "backend_url", BACKEND_URL)

    # 分析师团队
    set_config_if_exists(config, "analysts", ANALYSTS)

    # 语言
    set_config_if_exists(config, "output_language", LANGUAGE)

    # 成本控制
    set_config_if_exists(config, "max_debate_rounds", MAX_DEBATE_ROUNDS)
    set_config_if_exists(config, "max_risk_discuss_rounds", MAX_RISK_DISCUSS_ROUNDS)

    # 在线工具
    set_config_if_exists(config, "online_tools", ONLINE_TOOLS)

    return config


def save_outputs(ticker: str, analysis_date: str, decision, state=None):
    """
    保存输出结果。
    """
    output_path = Path(OUTPUT_DIR)
    output_path.mkdir(parents=True, exist_ok=True)

    now_text = datetime.now().strftime("%Y%m%d_%H%M%S")

    result_file = output_path / f"result_{ticker}_{analysis_date}_{now_text}.md"

    with open(result_file, "w", encoding="utf-8") as f:
        f.write("# TradingAgents 分析结果\n\n")
        f.write(f"- 股票代码：{ticker}\n")
        f.write(f"- 分析日期：{analysis_date}\n")
        f.write(f"- 模型供应商：{LLM_PROVIDER}\n")
        f.write(f"- 快速思考模型：{QUICK_THINK_LLM}\n")
        f.write(f"- 深度思考模型：{DEEP_THINK_LLM}\n")
        f.write(f"- 分析师团队：{ANALYSTS}\n")
        f.write(f"- 多空辩论轮数：{MAX_DEBATE_ROUNDS}\n")
        f.write(f"- 风控讨论轮数：{MAX_RISK_DISCUSS_ROUNDS}\n\n")

        f.write("## 最终决策\n\n")
        f.write(str(decision))
        f.write("\n")

    print(f"\n最终结果已保存到：{result_file}")

    if SAVE_DEBUG_STATE and state is not None:
        debug_file = output_path / f"debug_state_{ticker}_{analysis_date}_{now_text}.txt"
        with open(debug_file, "w", encoding="utf-8") as f:
            f.write(safe_to_text(state))

        print(f"调试信息已保存到：{debug_file}")


def main():
    """
    主程序入口。
    """
    try:
        print("开始运行 TradingAgents 客户版脚本...\n")

        prepare_api_key()

        config = build_config()

        print("\n当前生效配置如下：")
        print(safe_to_text(config))
        print("\n正在初始化 TradingAgents...\n")

        ta = TradingAgentsGraph(debug=DEBUG, config=config)

        print(f"开始分析：{TICKER}，日期：{ANALYSIS_DATE}\n")
        state, decision = ta.propagate(TICKER, ANALYSIS_DATE)

        print("\n========== 最终交易决策 ==========\n")
        print(decision)

        if SAVE_RESULT:
            save_outputs(TICKER, ANALYSIS_DATE, decision, state)

        print("\n运行完成。")

    except Exception as e:
        print("\n运行失败。")
        print("错误信息：")
        print(str(e))

        print("\n可能原因：")
        print("1. Claude API Key 没有配置，或者 Key 无效。")
        print("2. 模型名不被当前 Anthropic API 或 TradingAgents 支持。")
        print("3. 网络无法访问 Anthropic 或行情/新闻数据源。")
        print("4. TradingAgents 当前版本的配置字段和脚本字段不一致。")
        print("5. 依赖没有安装完整，可以尝试重新执行：pip install .")

        print("\n详细报错如下：")
        traceback.print_exc()


if __name__ == "__main__":
    main()