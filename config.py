"""
全局配置 & 默认任务定义
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── 路径 ──
APP_DIR = Path.home() / ".task_planner"
APP_DIR.mkdir(exist_ok=True)
DATA_FILE = APP_DIR / "tasks.json"
LOG_FILE = APP_DIR / "daily_log.json"
KNOWLEDGE_FILE = APP_DIR / "ai_knowledge.json"
HISTORY_FILE = APP_DIR / "ai_history.json"

# ── API 配置 ──
KIMI_API_KEY = os.getenv("KIMI_API_KEY", "")
KIMI_BASE_URL = os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1")
KIMI_MODEL = os.getenv("KIMI_MODEL", "moonshot-v1-128k")

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250514")

DEFAULT_AI_PROVIDER = os.getenv("DEFAULT_AI_PROVIDER", "kimi")

# ── 智能体角色 ──
AGENT_ROLES = {
    "observer": {
        "name": "观测者",
        "icon": "👁",
        "system_prompt": (
            "你是一个时间管理观测者。你的职责是：\n"
            "1. 实时观察用户的任务进度数据\n"
            "2. 识别时间分配不合理的地方（某任务投入过多/过少）\n"
            "3. 发现用户可能卡住的深水区任务\n"
            "4. 给出简短、可操作的观察结论\n"
            "回复要简洁，每次不超过3条观察，用中文。"
        ),
    },
    "advisor": {
        "name": "建议者",
        "icon": "💡",
        "system_prompt": (
            "你是一个时间规划顾问。用户会和你讨论特定任务的时间分配。你的职责是：\n"
            "1. 根据任务性质（冲刺型/细磨型/等待型）给出时间预估\n"
            "2. 帮助用户拆解子步骤并预估每步时间\n"
            "3. 识别可以并行的步骤和必须串行的步骤\n"
            "4. 给出每日/每周的具体安排建议\n"
            "回复要具体、有数字、可执行，用中文。"
        ),
    },
    "critic": {
        "name": "审视者",
        "icon": "🔍",
        "system_prompt": (
            "你是一个计划审视者。你的职责是：\n"
            "1. 审视用户的整体任务安排是否现实\n"
            "2. 识别过度乐观的时间预估\n"
            "3. 指出任务间的冲突和资源竞争\n"
            "4. 挑战用户的假设，但给出建设性替代方案\n"
            "要诚实直接，不要迎合，用中文。"
        ),
    },
}

# ── 任务类型 ──
CATEGORY_LABELS = {
    "fixed": "⏰ 固定时间",
    "deep": "🌊 深水区·细磨",
    "daily": "📋 日常推进",
    "random": "🎲 随机任务",
}

CATEGORY_STYLE = {
    "fixed": "danger",
    "deep": "warning",
    "daily": "success",
    "random": "info",
}

# ── 默认任务 ──
DEFAULT_TASKS = [
    {
        "id": "task_001",
        "name": "交易 & 复盘",
        "category": "fixed",
        "total_hours": 0,
        "daily_target_min": 150,
        "logged_min": 0,
        "expanded": True,
        "substeps": [
            {"id": "s001_1", "name": "盘前准备", "est_min": 30, "actual_min": 0, "done": False, "notes": ""},
            {"id": "s001_2", "name": "盯盘执行", "est_min": 60, "actual_min": 0, "done": False, "notes": ""},
            {"id": "s001_3", "name": "复盘记录", "est_min": 60, "actual_min": 0, "done": False, "notes": ""},
        ],
        "notes": "固定锚点任务，每日必做",
    },
    {
        "id": "task_002",
        "name": "FX交易（新品种）",
        "category": "deep",
        "total_hours": 50,
        "daily_target_min": 60,
        "logged_min": 0,
        "expanded": True,
        "substeps": [
            {"id": "s002_1", "name": "货币对特性学习", "est_min": 600, "actual_min": 0, "done": False, "notes": ""},
            {"id": "s002_2", "name": "模拟盘磨合（2-4周）", "est_min": 1200, "actual_min": 0, "done": False, "notes": ""},
            {"id": "s002_3", "name": "建立交易规则", "est_min": 600, "actual_min": 0, "done": False, "notes": ""},
            {"id": "s002_4", "name": "小仓实盘验证", "est_min": 600, "actual_min": 0, "done": False, "notes": ""},
        ],
        "notes": "盘感需要屏幕时间积累，不可压缩",
    },
    {
        "id": "task_003",
        "name": "写论文",
        "category": "deep",
        "total_hours": 70,
        "daily_target_min": 120,
        "logged_min": 0,
        "expanded": True,
        "substeps": [
            {"id": "s003_1", "name": "文献阅读与梳理", "est_min": 1200, "actual_min": 0, "done": False, "notes": ""},
            {"id": "s003_2", "name": "方法论/实验设计", "est_min": 900, "actual_min": 0, "done": False, "notes": ""},
            {"id": "s003_3", "name": "初稿撰写", "est_min": 1500, "actual_min": 0, "done": False, "notes": ""},
            {"id": "s003_4", "name": "修改与迭代", "est_min": 600, "actual_min": 0, "done": False, "notes": ""},
        ],
        "notes": "方法论阶段需要整块时间(≥2h)",
    },
    {
        "id": "task_004",
        "name": "Kaggle Nemotron项目",
        "category": "deep",
        "total_hours": 40,
        "daily_target_min": 90,
        "logged_min": 0,
        "expanded": True,
        "substeps": [
            {"id": "s004_1", "name": "数据理解 & EDA", "est_min": 420, "actual_min": 0, "done": False, "notes": ""},
            {"id": "s004_2", "name": "Baseline搭建", "est_min": 600, "actual_min": 0, "done": False, "notes": ""},
            {"id": "s004_3", "name": "特征工程 & 调参迭代", "est_min": 900, "actual_min": 0, "done": False, "notes": ""},
            {"id": "s004_4", "name": "文档整理 & 提交", "est_min": 240, "actual_min": 0, "done": False, "notes": ""},
        ],
        "notes": "模型训练等待期间可穿插其他任务",
    },
    {
        "id": "task_005",
        "name": "投简历 & 找活动",
        "category": "daily",
        "total_hours": 0,
        "daily_target_min": 45,
        "logged_min": 0,
        "expanded": True,
        "substeps": [
            {"id": "s005_1", "name": "浏览岗位/活动", "est_min": 20, "actual_min": 0, "done": False, "notes": ""},
            {"id": "s005_2", "name": "定制简历投递", "est_min": 25, "actual_min": 0, "done": False, "notes": ""},
            {"id": "s005_3", "name": "跟进回复", "est_min": 10, "actual_min": 0, "done": False, "notes": ""},
        ],
        "notes": "每天都做，保持管道流动",
    },
    {
        "id": "task_006",
        "name": "小工具开发",
        "category": "random",
        "total_hours": 20,
        "daily_target_min": 0,
        "logged_min": 0,
        "expanded": True,
        "substeps": [
            {"id": "s006_1", "name": "需求明确", "est_min": 60, "actual_min": 0, "done": False, "notes": ""},
            {"id": "s006_2", "name": "编码实现", "est_min": 360, "actual_min": 0, "done": False, "notes": ""},
            {"id": "s006_3", "name": "测试调整", "est_min": 120, "actual_min": 0, "done": False, "notes": ""},
        ],
        "notes": "随机任务，碎片时间处理",
    },
    {
        "id": "task_007",
        "name": "行李箱产业链排查",
        "category": "random",
        "total_hours": 15,
        "daily_target_min": 0,
        "logged_min": 0,
        "expanded": True,
        "substeps": [
            {"id": "s007_1", "name": "上游供应商调研", "est_min": 180, "actual_min": 0, "done": False, "notes": ""},
            {"id": "s007_2", "name": "中游制造与渠道", "est_min": 180, "actual_min": 0, "done": False, "notes": ""},
            {"id": "s007_3", "name": "下游零售与竞品", "est_min": 180, "actual_min": 0, "done": False, "notes": ""},
            {"id": "s007_4", "name": "整理报告", "est_min": 120, "actual_min": 0, "done": False, "notes": ""},
        ],
        "notes": "碎片时间推进，每周2-3个时段",
    },
]
