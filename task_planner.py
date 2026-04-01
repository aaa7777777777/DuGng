#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════
  时间规划实时监测工具 v1.0
  Task Time Planner & Live Tracker
═══════════════════════════════════════════════════

  安装依赖: pip install ttkbootstrap
  运行: python task_planner.py
"""

import json
import os
import time
import copy
from datetime import datetime, timedelta
from pathlib import Path

try:
    import ttkbootstrap as ttk
    from ttkbootstrap.constants import *
    from ttkbootstrap.dialogs import Messagebox
    from ttkbootstrap.tooltip import ToolTip
except ImportError:
    print("请先安装 ttkbootstrap: pip install ttkbootstrap")
    exit(1)

# ─────────────────────────────────────────────
# 数据文件路径
# ─────────────────────────────────────────────
DATA_FILE = Path.home() / ".task_planner_data.json"
LOG_FILE = Path.home() / ".task_planner_log.json"

# ─────────────────────────────────────────────
# 默认任务配置
# ─────────────────────────────────────────────
DEFAULT_TASKS = [
    {
        "name": "交易 & 复盘",
        "category": "fixed",
        "color": "#FF6B6B",
        "total_hours": 0,
        "daily_target_min": 150,
        "logged_min": 0,
        "substeps": [
            {"name": "盘前准备", "est_min": 30, "done": False},
            {"name": "盯盘执行", "est_min": 60, "done": False},
            {"name": "复盘记录", "est_min": 60, "done": False},
        ],
        "notes": "固定锚点任务，每日必做",
    },
    {
        "name": "FX交易（新品种）",
        "category": "deep",
        "color": "#FF8E53",
        "total_hours": 50,
        "daily_target_min": 60,
        "logged_min": 0,
        "substeps": [
            {"name": "货币对特性学习", "est_min": 600, "done": False},
            {"name": "模拟盘磨合（2-4周）", "est_min": 1200, "done": False},
            {"name": "建立交易规则", "est_min": 600, "done": False},
            {"name": "小仓实盘验证", "est_min": 600, "done": False},
        ],
        "notes": "⚠️ 细磨型：盘感需要屏幕时间积累，不可压缩",
    },
    {
        "name": "写论文",
        "category": "deep",
        "color": "#4ECDC4",
        "total_hours": 70,
        "daily_target_min": 120,
        "logged_min": 0,
        "substeps": [
            {"name": "文献阅读与梳理", "est_min": 1200, "done": False},
            {"name": "方法论/实验设计", "est_min": 900, "done": False},
            {"name": "初稿撰写", "est_min": 1500, "done": False},
            {"name": "修改与迭代", "est_min": 600, "done": False},
        ],
        "notes": "⚠️ 方法论阶段需要整块时间(≥2h)，不要碎片化处理",
    },
    {
        "name": "Kaggle Nemotron项目",
        "category": "deep",
        "color": "#45B7D1",
        "total_hours": 40,
        "daily_target_min": 90,
        "logged_min": 0,
        "substeps": [
            {"name": "数据理解 & EDA", "est_min": 420, "done": False},
            {"name": "Baseline搭建", "est_min": 600, "done": False},
            {"name": "特征工程 & 调参迭代", "est_min": 900, "done": False},
            {"name": "文档整理 & 提交", "est_min": 240, "done": False},
        ],
        "notes": "模型训练等待期间可穿插其他任务",
    },
    {
        "name": "投简历 & 找活动",
        "category": "daily",
        "color": "#96CEB4",
        "total_hours": 0,
        "daily_target_min": 45,
        "logged_min": 0,
        "substeps": [
            {"name": "浏览岗位/活动", "est_min": 20, "done": False},
            {"name": "定制简历投递", "est_min": 25, "done": False},
            {"name": "跟进回复", "est_min": 10, "done": False},
        ],
        "notes": "每天都做，保持管道流动，不需要深度",
    },
    {
        "name": "小工具开发",
        "category": "random",
        "color": "#FFEAA7",
        "total_hours": 20,
        "daily_target_min": 0,
        "logged_min": 0,
        "substeps": [
            {"name": "需求明确", "est_min": 60, "done": False},
            {"name": "编码实现", "est_min": 360, "done": False},
            {"name": "测试调整", "est_min": 120, "done": False},
        ],
        "notes": "随机任务，适合状态不好或等待间隙做",
    },
    {
        "name": "行李箱产业链排查",
        "category": "random",
        "color": "#DDA0DD",
        "total_hours": 15,
        "daily_target_min": 0,
        "logged_min": 0,
        "substeps": [
            {"name": "上游供应商调研", "est_min": 180, "done": False},
            {"name": "中游制造与渠道", "est_min": 180, "done": False},
            {"name": "下游零售与竞品", "est_min": 180, "done": False},
            {"name": "整理报告", "est_min": 120, "done": False},
        ],
        "notes": "碎片时间推进，每周2-3个时段即可",
    },
]

CATEGORY_LABELS = {
    "fixed": "⏰ 固定时间",
    "deep":  "🌊 深水区·细磨",
    "daily": "📋 日常推进",
    "random": "🎲 随机任务",
}

CATEGORY_STYLE = {
    "fixed": "danger",
    "deep":  "warning",
    "daily": "success",
    "random": "info",
}


class TaskPlannerApp:
    """主应用类"""

    def __init__(self):
        self.root = ttk.Window(
            title="时间规划实时监测 · Task Planner v1.0",
            themename="darkly",
            size=(1280, 860),
            resizable=(True, True),
        )
        self.root.place_window_center()

        # 加载数据
        self.tasks = self.load_data()
        self.daily_log = self.load_daily_log()

        # 计时状态
        self.active_task_idx = None
        self.timer_running = False
        self.timer_start = None
        self.elapsed_seconds = 0

        # 今日
        self.today_str = datetime.now().strftime("%Y-%m-%d")

        self.build_ui()
        self.tick()

    # ═══════════════════════════════════════════
    #  数据持久化
    # ═══════════════════════════════════════════
    def load_data(self):
        if DATA_FILE.exists():
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return copy.deepcopy(DEFAULT_TASKS)

    def save_data(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.tasks, f, ensure_ascii=False, indent=2)

    def load_daily_log(self):
        if LOG_FILE.exists():
            try:
                with open(LOG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def save_daily_log(self):
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.daily_log, f, ensure_ascii=False, indent=2)

    def log_session(self, task_name, minutes):
        """记录一次计时到日志"""
        if self.today_str not in self.daily_log:
            self.daily_log[self.today_str] = {}
        if task_name not in self.daily_log[self.today_str]:
            self.daily_log[self.today_str][task_name] = 0
        self.daily_log[self.today_str][task_name] += minutes
        self.save_daily_log()

    # ═══════════════════════════════════════════
    #  UI 构建
    # ═══════════════════════════════════════════
    def build_ui(self):
        # ── 顶部栏 ──
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill=X)

        ttk.Label(
            top, text="⏱ 时间规划实时监测", font=("", 18, "bold")
        ).pack(side=LEFT)

        self.clock_label = ttk.Label(top, text="", font=("Consolas", 14))
        self.clock_label.pack(side=RIGHT, padx=20)

        self.timer_display = ttk.Label(
            top, text="未在计时", font=("Consolas", 15, "bold"), bootstyle="secondary"
        )
        self.timer_display.pack(side=RIGHT, padx=20)

        # ── 主面板 ──
        paned = ttk.PanedWindow(self.root, orient=HORIZONTAL)
        paned.pack(fill=BOTH, expand=True, padx=10, pady=5)

        # 左侧：任务卡片
        left_frame = ttk.Frame(paned, padding=5)
        paned.add(left_frame, weight=3)

        canvas = ttk.Canvas(left_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(left_frame, orient=VERTICAL, command=canvas.yview)
        self.task_container = ttk.Frame(canvas)
        self.task_container.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=self.task_container, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

        # 跨平台滚轮
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)        # Windows/macOS
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))  # Linux
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        self.task_widgets = []
        for idx, task in enumerate(self.tasks):
            self._create_task_card(idx, task)

        # 右侧：详情
        right_frame = ttk.Frame(paned, padding=10)
        paned.add(right_frame, weight=2)

        ttk.Label(
            right_frame, text="任务详情 & 步骤提示", font=("", 14, "bold")
        ).pack(anchor=W, pady=(0, 10))

        self.detail_text = ttk.Text(
            right_frame, wrap="word", font=("", 11), height=25
        )
        self.detail_text.pack(fill=BOTH, expand=True)

        self._show_welcome()

        # ── 底部统计栏 ──
        bottom = ttk.Frame(self.root, padding=10)
        bottom.pack(fill=X)

        self.stats_label = ttk.Label(bottom, text="", font=("", 11))
        self.stats_label.pack(side=LEFT)

        ttk.Button(
            bottom,
            text="🔄 重置数据",
            bootstyle="outline-danger",
            command=self.reset_data,
        ).pack(side=RIGHT, padx=5)

        ttk.Button(
            bottom,
            text="📊 导出报告",
            bootstyle="outline-info",
            command=self.export_report,
        ).pack(side=RIGHT, padx=5)

        ttk.Button(
            bottom,
            text="📅 今日统计",
            bootstyle="outline-success",
            command=self.show_today_stats,
        ).pack(side=RIGHT, padx=5)

        self.update_stats()

    def _show_welcome(self):
        self.detail_text.config(state="normal")
        self.detail_text.delete("1.0", "end")
        self.detail_text.insert(
            "1.0",
            "← 点击左侧任务的「📋 详情」查看\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "  操作说明\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "  ▶ 开始  →  对该任务开始实时计时\n"
            "  ⏹ 停止  →  结束计时，时间自动累加\n"
            "  📋 详情  →  查看子步骤、时间预估、完成日期\n"
            "  ✅ 打勾  →  在详情中勾选已完成的子步骤\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "  任务分类\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "  ⏰ 固定时间  →  每日锚点，雷打不动\n"
            "  🌊 深水区    →  需要时间细磨，不可压缩\n"
            "  📋 日常推进  →  保持节奏，不求深度\n"
            "  🎲 随机任务  →  见缝插针，碎片处理\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "  数据存储\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"  任务数据: {DATA_FILE}\n"
            f"  每日日志: {LOG_FILE}\n",
        )
        self.detail_text.config(state="disabled")

    # ── 任务卡片 ─────────────────────────────
    def _create_task_card(self, idx, task):
        cat = task.get("category", "random")
        style = CATEGORY_STYLE.get(cat, "info")

        card = ttk.LabelFrame(
            self.task_container,
            text=f"  {CATEGORY_LABELS.get(cat, cat)}  ",
            bootstyle=style,
            padding=10,
        )
        card.pack(fill=X, pady=4, padx=5)

        # 行1: 名称 + 按钮
        row1 = ttk.Frame(card)
        row1.pack(fill=X)

        ttk.Label(row1, text=task["name"], font=("", 13, "bold")).pack(side=LEFT)

        btn_frame = ttk.Frame(row1)
        btn_frame.pack(side=RIGHT)

        start_btn = ttk.Button(
            btn_frame,
            text="▶ 开始",
            bootstyle=f"outline-{style}",
            command=lambda i=idx: self.start_timer(i),
            width=8,
        )
        start_btn.pack(side=LEFT, padx=2)

        stop_btn = ttk.Button(
            btn_frame,
            text="⏹ 停止",
            bootstyle=style,
            command=lambda i=idx: self.stop_timer(i),
            width=8,
        )
        stop_btn.pack(side=LEFT, padx=2)

        detail_btn = ttk.Button(
            btn_frame,
            text="📋 详情",
            bootstyle="outline-light",
            command=lambda i=idx: self.show_detail(i),
            width=8,
        )
        detail_btn.pack(side=LEFT, padx=2)

        # 行2: 进度条 + 数据
        row2 = ttk.Frame(card)
        row2.pack(fill=X, pady=(8, 0))

        progress_val = self._calc_progress(task)
        pb = ttk.Progressbar(
            row2, value=progress_val, bootstyle=f"{style}-striped", length=400
        )
        pb.pack(side=LEFT, fill=X, expand=True, padx=(0, 10))

        info_text = self._format_info(task, progress_val)
        info_label = ttk.Label(row2, text=info_text, font=("", 10))
        info_label.pack(side=RIGHT)

        # 行3: 备注
        if task.get("notes"):
            ttk.Label(card, text=task["notes"], font=("", 9), foreground="#888").pack(
                anchor=W, pady=(4, 0)
            )

        self.task_widgets.append(
            {
                "card": card,
                "progress_bar": pb,
                "info_label": info_label,
                "start_btn": start_btn,
                "stop_btn": stop_btn,
            }
        )

    def _calc_progress(self, task):
        if task["total_hours"] > 0:
            return min(100, (task["logged_min"] / 60) / task["total_hours"] * 100)
        steps = task.get("substeps", [])
        if not steps:
            return 0
        done = sum(1 for s in steps if s.get("done"))
        return done / len(steps) * 100

    def _format_info(self, task, progress_val):
        if task["total_hours"] > 0:
            remaining_h = max(0, task["total_hours"] - task["logged_min"] / 60)
            if task["daily_target_min"] > 0:
                remaining_days = remaining_h * 60 / task["daily_target_min"]
                return f"{progress_val:.0f}%  |  剩余≈{remaining_h:.1f}h  |  ≈{remaining_days:.0f}天"
            return f"{progress_val:.0f}%  |  剩余≈{remaining_h:.1f}h"
        return f"已累计 {task['logged_min']:.0f} 分钟"

    # ═══════════════════════════════════════════
    #  计时器
    # ═══════════════════════════════════════════
    def start_timer(self, idx):
        # 如果有正在计时的任务，先停
        if self.timer_running and self.active_task_idx is not None:
            self.stop_timer(self.active_task_idx)

        self.active_task_idx = idx
        self.timer_running = True
        self.timer_start = time.time()
        self.elapsed_seconds = 0

        for i, w in enumerate(self.task_widgets):
            w["start_btn"].config(state="disabled" if i == idx else "normal")

        self.timer_display.config(bootstyle="warning")

    def stop_timer(self, idx):
        if not self.timer_running or self.active_task_idx != idx:
            return

        elapsed = time.time() - self.timer_start
        elapsed_min = elapsed / 60

        self.tasks[idx]["logged_min"] = self.tasks[idx].get("logged_min", 0) + elapsed_min
        self.log_session(self.tasks[idx]["name"], elapsed_min)

        self.timer_running = False
        self.active_task_idx = None
        self.timer_start = None
        self.elapsed_seconds = 0

        self.task_widgets[idx]["start_btn"].config(state="normal")
        self.timer_display.config(text="未在计时", bootstyle="secondary")

        self.save_data()
        self.refresh_card(idx)
        self.update_stats()

    def refresh_card(self, idx):
        task = self.tasks[idx]
        w = self.task_widgets[idx]
        progress_val = self._calc_progress(task)
        w["progress_bar"]["value"] = progress_val
        w["info_label"].config(text=self._format_info(task, progress_val))

    # ═══════════════════════════════════════════
    #  详情面板（含子步骤打勾）
    # ═══════════════════════════════════════════
    def show_detail(self, idx):
        task = self.tasks[idx]
        self.detail_text.config(state="normal")
        self.detail_text.delete("1.0", "end")

        cat_label = CATEGORY_LABELS.get(task["category"], task["category"])
        logged_h = task["logged_min"] / 60

        lines = []
        lines.append(f"{'━' * 44}")
        lines.append(f"  {task['name']}")
        lines.append(f"  类型: {cat_label}")
        lines.append(f"{'━' * 44}\n")

        # 时间概览
        lines.append(f"  ⏱  已投入: {logged_h:.1f} 小时 ({task['logged_min']:.0f} 分钟)")

        if task["total_hours"] > 0:
            remaining_h = max(0, task["total_hours"] - logged_h)
            pct = min(100, logged_h / task["total_hours"] * 100)
            lines.append(f"  📊 总进度: {pct:.1f}%")
            lines.append(f"  📦 预估总量: {task['total_hours']} 小时")
            lines.append(f"  📉 剩余: ≈{remaining_h:.1f} 小时")

            if task["daily_target_min"] > 0:
                days = remaining_h * 60 / task["daily_target_min"]
                target_date = datetime.now() + timedelta(days=days)
                lines.append(f"")
                lines.append(f"  📅 每日投入 {task['daily_target_min']} 分钟")
                lines.append(f"     → 预计 {days:.0f} 天后完成")
                lines.append(f"     → 完成日期: {target_date.strftime('%Y-%m-%d')}")
        elif task["daily_target_min"] > 0:
            lines.append(f"  📅 每日目标: {task['daily_target_min']} 分钟")

        # 今日投入
        today_min = self.daily_log.get(self.today_str, {}).get(task["name"], 0)
        lines.append(f"\n  📌 今日已投入: {today_min:.0f} 分钟")
        if task["daily_target_min"] > 0:
            remaining_today = max(0, task["daily_target_min"] - today_min)
            if remaining_today > 0:
                lines.append(f"     今日还差: {remaining_today:.0f} 分钟")
            else:
                lines.append(f"     ✅ 今日目标已达成!")

        # 子步骤
        lines.append(f"\n{'─' * 44}")
        lines.append(f"  子步骤明细")
        lines.append(f"{'─' * 44}\n")

        total_est = 0
        done_est = 0

        for i, step in enumerate(task.get("substeps", [])):
            status = "✅" if step.get("done") else "⬜"
            est_h = step["est_min"] / 60
            total_est += step["est_min"]
            if step.get("done"):
                done_est += step["est_min"]

            lines.append(f"  {status}  {step['name']}")
            lines.append(f"      预估: {est_h:.1f}h ({step['est_min']} 分钟)")

            if not step.get("done"):
                if step["est_min"] >= 600:
                    lines.append(f"      💡 大块任务 → 建议拆成多个2h时段")
                    lines.append(f"         预计需要 {step['est_min']//120} 个深度工作时段")
                elif step["est_min"] >= 180:
                    lines.append(f"      💡 需要整块时间 (≥2h) 集中推进")
                elif step["est_min"] >= 60:
                    lines.append(f"      💡 中等任务 → 安排1个专注时段")
                else:
                    lines.append(f"      💡 碎片时间可完成")
            lines.append("")

        if total_est > 0:
            lines.append(
                f"  合计: {total_est / 60:.1f}h 预估"
                f" | {done_est / 60:.1f}h 已完成"
                f" | {(total_est - done_est) / 60:.1f}h 剩余"
            )

        # 备注
        if task.get("notes"):
            lines.append(f"\n{'─' * 44}")
            lines.append(f"  📌 {task['notes']}")

        # 深水区提示
        if task["category"] == "deep":
            lines.append(f"\n{'─' * 44}")
            lines.append(f"  🌊 深水区提醒")
            lines.append(f"{'─' * 44}")
            lines.append(f"  这类任务的特点是：投入时间不一定立刻")
            lines.append(f"  看到产出，但停下来一定会退步。")
            lines.append(f"")
            lines.append(f"  → 每天固定时间坐下来，哪怕只推进一点")
            lines.append(f"  → 碰壁 = 正在学习，不是浪费时间")
            lines.append(f"  → 记录每次卡住的点，下次继续攻克")

        # 操作提示
        lines.append(f"\n{'━' * 44}")
        lines.append(f"  在终端中编辑子步骤完成状态：")
        lines.append(f"  修改 {DATA_FILE}")
        lines.append(f"  将对应 substep 的 done 改为 true")
        lines.append(f"  或使用下方「切换完成状态」按钮")
        lines.append(f"{'━' * 44}")

        self.detail_text.insert("1.0", "\n".join(lines))
        self.detail_text.config(state="disabled")

        # 在详情面板下方添加子步骤切换按钮
        self._add_substep_buttons(idx)

    def _add_substep_buttons(self, task_idx):
        """在详情文本框下方动态添加子步骤完成切换按钮"""
        # 清理旧按钮
        if hasattr(self, "_substep_btn_frame"):
            self._substep_btn_frame.destroy()

        parent = self.detail_text.master
        self._substep_btn_frame = ttk.Frame(parent, padding=5)
        self._substep_btn_frame.pack(fill=X, pady=(5, 0))

        ttk.Label(
            self._substep_btn_frame, text="切换完成状态:", font=("", 10, "bold")
        ).pack(anchor=W)

        task = self.tasks[task_idx]
        for i, step in enumerate(task.get("substeps", [])):
            icon = "✅" if step.get("done") else "⬜"
            btn = ttk.Button(
                self._substep_btn_frame,
                text=f"{icon} {step['name']}",
                bootstyle="outline-success" if step.get("done") else "outline-secondary",
                command=lambda ti=task_idx, si=i: self.toggle_substep(ti, si),
            )
            btn.pack(fill=X, pady=1)

    def toggle_substep(self, task_idx, step_idx):
        """切换子步骤完成状态"""
        step = self.tasks[task_idx]["substeps"][step_idx]
        step["done"] = not step.get("done", False)
        self.save_data()
        self.refresh_card(task_idx)
        self.show_detail(task_idx)  # 刷新详情

    # ═══════════════════════════════════════════
    #  统计
    # ═══════════════════════════════════════════
    def update_stats(self):
        total_logged = sum(t.get("logged_min", 0) for t in self.tasks)
        total_remaining = sum(
            max(0, t["total_hours"] * 60 - t.get("logged_min", 0))
            for t in self.tasks
            if t["total_hours"] > 0
        )
        deep_remaining = sum(
            max(0, t["total_hours"] * 60 - t.get("logged_min", 0))
            for t in self.tasks
            if t["category"] == "deep" and t["total_hours"] > 0
        )

        today_total = sum(self.daily_log.get(self.today_str, {}).values())

        self.stats_label.config(
            text=(
                f"总投入: {total_logged / 60:.1f}h  │  "
                f"有限任务剩余: {total_remaining / 60:.1f}h  │  "
                f"深水区剩余: {deep_remaining / 60:.1f}h  │  "
                f"今日: {today_total:.0f}min  │  "
                f"{self.today_str}"
            )
        )

    def show_today_stats(self):
        """显示今日各任务投入统计"""
        self.detail_text.config(state="normal")
        self.detail_text.delete("1.0", "end")

        today_data = self.daily_log.get(self.today_str, {})

        lines = []
        lines.append(f"{'━' * 44}")
        lines.append(f"  📅 今日时间投入 ({self.today_str})")
        lines.append(f"{'━' * 44}\n")

        if not today_data:
            lines.append("  今天还没有计时记录，开始工作吧！\n")
        else:
            total = 0
            for name, mins in sorted(today_data.items(), key=lambda x: -x[1]):
                bar_len = int(mins / 5)
                bar = "█" * bar_len
                lines.append(f"  {name}")
                lines.append(f"    {bar} {mins:.0f} 分钟 ({mins/60:.1f}h)")
                lines.append("")
                total += mins

            lines.append(f"{'─' * 44}")
            lines.append(f"  合计: {total:.0f} 分钟 ({total/60:.1f} 小时)")

        # 各任务今日达标情况
        lines.append(f"\n{'━' * 44}")
        lines.append(f"  今日目标达成情况")
        lines.append(f"{'━' * 44}\n")

        for task in self.tasks:
            if task["daily_target_min"] > 0:
                done_min = today_data.get(task["name"], 0)
                target = task["daily_target_min"]
                pct = min(100, done_min / target * 100)
                icon = "✅" if pct >= 100 else "🔲"
                lines.append(f"  {icon} {task['name']}")
                lines.append(f"     {done_min:.0f}/{target} 分钟 ({pct:.0f}%)")
                lines.append("")

        self.detail_text.insert("1.0", "\n".join(lines))
        self.detail_text.config(state="disabled")

        # 清理子步骤按钮
        if hasattr(self, "_substep_btn_frame"):
            self._substep_btn_frame.destroy()

    # ═══════════════════════════════════════════
    #  每秒刷新
    # ═══════════════════════════════════════════
    def tick(self):
        now = datetime.now()
        self.clock_label.config(text=now.strftime("%H:%M:%S"))

        # 检查跨日
        new_today = now.strftime("%Y-%m-%d")
        if new_today != self.today_str:
            self.today_str = new_today

        # 更新计时显示
        if self.timer_running and self.timer_start:
            elapsed = time.time() - self.timer_start
            m, s = divmod(int(elapsed), 60)
            h, m = divmod(m, 60)
            task_name = self.tasks[self.active_task_idx]["name"]
            self.timer_display.config(
                text=f"● {task_name}  {h:02d}:{m:02d}:{s:02d}"
            )

        self.root.after(1000, self.tick)

    # ═══════════════════════════════════════════
    #  工具方法
    # ═══════════════════════════════════════════
    def reset_data(self):
        result = Messagebox.yesno("确定要重置所有任务数据吗？\n（日志不会被清除）", "确认重置")
        if result == "Yes":
            self.tasks = copy.deepcopy(DEFAULT_TASKS)
            self.save_data()
            for w in self.task_widgets:
                w["card"].destroy()
            self.task_widgets.clear()
            for idx, task in enumerate(self.tasks):
                self._create_task_card(idx, task)
            self.update_stats()
            self._show_welcome()

    def export_report(self):
        lines = []
        lines.append(f"时间规划报告")
        lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"{'=' * 50}\n")

        for task in self.tasks:
            cat = CATEGORY_LABELS.get(task["category"], "")
            logged_h = task["logged_min"] / 60

            lines.append(f"[{cat}] {task['name']}")
            lines.append(f"  已投入: {logged_h:.1f}h ({task['logged_min']:.0f}min)")

            if task["total_hours"] > 0:
                remaining = max(0, task["total_hours"] - logged_h)
                progress = min(100, logged_h / task["total_hours"] * 100)
                lines.append(f"  进度: {progress:.0f}% | 剩余: {remaining:.1f}h")
                if task["daily_target_min"] > 0:
                    days = remaining * 60 / task["daily_target_min"]
                    target_date = datetime.now() + timedelta(days=days)
                    lines.append(f"  预计完成: {target_date.strftime('%Y-%m-%d')} (约{days:.0f}天)")

            for step in task.get("substeps", []):
                status = "✅" if step.get("done") else "⬜"
                lines.append(f"    {status} {step['name']} (预估{step['est_min']}min)")

            lines.append("")

        # 追加最近7天日志
        lines.append(f"\n{'=' * 50}")
        lines.append(f"最近7天投入记录")
        lines.append(f"{'=' * 50}\n")

        for i in range(6, -1, -1):
            d = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            day_data = self.daily_log.get(d, {})
            total = sum(day_data.values())
            lines.append(f"  {d}: {total:.0f} 分钟")
            for name, mins in sorted(day_data.items(), key=lambda x: -x[1]):
                lines.append(f"    - {name}: {mins:.0f}min")

        report_path = (
            Path.home() / f"task_report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
        )
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        Messagebox.ok(f"报告已导出到:\n{report_path}", "导出成功")

    # ═══════════════════════════════════════════
    #  启动
    # ═══════════════════════════════════════════
    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()

    def on_close(self):
        """关闭前保存 & 停止计时"""
        if self.timer_running and self.active_task_idx is not None:
            self.stop_timer(self.active_task_idx)
        self.save_data()
        self.root.destroy()


if __name__ == "__main__":
    app = TaskPlannerApp()
    app.run()
