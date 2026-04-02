"""
主界面：组装所有面板
"""

import time
from datetime import datetime

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox

from data_store import DataStore
from ai_engine import AIEngine
from agents import AgentCluster
from ui_tree import TaskTreePanel
from ui_table import TaskTablePanel
from ui_ai_panel import AIPanelFrame


class MainApp:
    """主应用"""

    def __init__(self):
        self.root = ttk.Window(
            title="时间规划实时监测 · AI-Powered Task Planner v2.0",
            themename="darkly",
            size=(1400, 900),
            resizable=(True, True),
        )
        self.root.place_window_center()

        # 核心组件
        self.store = DataStore()
        self.ai = AIEngine()
        self.agents = AgentCluster(self.ai, self.store)

        # 计时器状态
        self.active_task = None
        self.timer_running = False
        self.timer_start = None

        self._build_ui()

        # 启动后台 Agent
        self.agents.start()

        # 启动刷新循环
        self._tick()

    def _build_ui(self):
        # ── 顶部栏 ──
        top = ttk.Frame(self.root, padding=(10, 8))
        top.pack(fill=X)

        ttk.Label(top, text="⏱ 时间规划实时监测", font=("", 17, "bold")).pack(side=LEFT)

        self.clock_label = ttk.Label(top, text="", font=("Consolas", 13))
        self.clock_label.pack(side=RIGHT, padx=15)

        self.timer_display = ttk.Label(
            top, text="未在计时", font=("Consolas", 14, "bold"), bootstyle="secondary"
        )
        self.timer_display.pack(side=RIGHT, padx=15)

        # ── 主面板 (三列) ──
        main_paned = ttk.PanedWindow(self.root, orient=HORIZONTAL)
        main_paned.pack(fill=BOTH, expand=True, padx=8, pady=4)

        # 左侧：树状图
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=3)

        self.tree_panel = TaskTreePanel(
            left_frame,
            self.store,
            on_select=self._on_task_select,
            on_timer_start=self._start_timer,
            on_timer_stop=self._stop_timer,
        )
        self.tree_panel.frame.pack(fill=BOTH, expand=True)

        # 右侧：上下分割（表格 + AI）
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=4)

        right_paned = ttk.PanedWindow(right_frame, orient=VERTICAL)
        right_paned.pack(fill=BOTH, expand=True)

        # 右上：表格
        table_frame = ttk.Frame(right_paned)
        right_paned.add(table_frame, weight=3)

        self.table_panel = TaskTablePanel(table_frame, self.store)
        self.table_panel.frame.pack(fill=BOTH, expand=True)

        # 右下：AI 面板
        ai_frame = ttk.Frame(right_paned)
        right_paned.add(ai_frame, weight=2)

        self.ai_panel = AIPanelFrame(
            ai_frame,
            self.agents,
            self.ai,
            self.store,
            get_context_fn=self._get_current_context,
        )
        self.ai_panel.frame.pack(fill=BOTH, expand=True)

        # ── 底部栏 ──
        bottom = ttk.Frame(self.root, padding=(10, 6))
        bottom.pack(fill=X)

        self.stats_label = ttk.Label(bottom, text="", font=("", 10))
        self.stats_label.pack(side=LEFT)

        ttk.Button(
            bottom, text="🔄 重置", bootstyle="outline-danger",
            command=self._reset, width=8,
        ).pack(side=RIGHT, padx=4)

        ttk.Button(
            bottom, text="📊 导出", bootstyle="outline-info",
            command=self._export, width=8,
        ).pack(side=RIGHT, padx=4)

        self._update_stats()

    # ── 事件 ──────────────────────────────────
    def _on_task_select(self, task, substep):
        """树状图选择回调"""
        if task:
            self.table_panel.show_task(task, substep)

    def _get_current_context(self):
        """给 AI 面板提供当前上下文"""
        return self.table_panel.get_selected_step()

    # ── 计时器 ────────────────────────────────
    def _start_timer(self, task):
        if self.timer_running:
            self._stop_timer()

        self.active_task = task
        self.timer_running = True
        self.timer_start = time.time()
        self.timer_display.config(bootstyle="warning")

    def _stop_timer(self):
        if not self.timer_running or not self.active_task:
            return

        elapsed = time.time() - self.timer_start
        elapsed_min = elapsed / 60

        self.active_task["logged_min"] += elapsed_min
        self.store.log_session(self.active_task["name"], elapsed_min)
        self.store.save_tasks()

        self.timer_running = False
        self.timer_start = None
        self.timer_display.config(text="未在计时", bootstyle="secondary")

        # 刷新
        self.tree_panel.refresh()
        self.table_panel.show_task(self.active_task)
        self._update_stats()
        self.active_task = None

    # ── 刷新循环 ──────────────────────────────
    def _tick(self):
        now = datetime.now()
        self.clock_label.config(text=now.strftime("%H:%M:%S"))

        if self.timer_running and self.timer_start and self.active_task:
            elapsed = time.time() - self.timer_start
            m, s = divmod(int(elapsed), 60)
            h, m = divmod(m, 60)
            self.timer_display.config(
                text=f"● {self.active_task['name']}  {h:02d}:{m:02d}:{s:02d}"
            )

        self.root.after(1000, self._tick)

    # ── 统计 ──────────────────────────────────
    def _update_stats(self):
        today = datetime.now().strftime("%Y-%m-%d")
        today_log = self.store.daily_log.get(today, {})
        today_total = sum(today_log.values())

        total_logged = sum(t.get("logged_min", 0) for t in self.store.tasks)
        total_remaining = sum(
            max(0, t["total_hours"] * 60 - t.get("logged_min", 0))
            for t in self.store.tasks if t["total_hours"] > 0
        )

        self.stats_label.config(
            text=(
                f"总投入: {total_logged/60:.1f}h  │  "
                f"剩余: {total_remaining/60:.1f}h  │  "
                f"今日: {today_total:.0f}min  │  "
                f"AI: {self.ai.provider if self.ai.is_available else '未连接'}  │  "
                f"{today}"
            )
        )

    # ── 工具 ──────────────────────────────────
    def _reset(self):
        r = Messagebox.yesno("确定重置所有任务数据？", "确认")
        if r == "Yes":
            self.store.reset_tasks()
            self.tree_panel.refresh()
            self._update_stats()

    def _export(self):
        from pathlib import Path
        from datetime import timedelta

        lines = [
            f"时间规划报告 - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "=" * 50, "",
        ]

        for task in self.store.tasks:
            logged_h = task["logged_min"] / 60
            lines.append(f"[{task['category']}] {task['name']}")
            lines.append(f"  已投入: {logged_h:.1f}h")
            if task["total_hours"] > 0:
                remaining = max(0, task["total_hours"] - logged_h)
                lines.append(f"  剩余: {remaining:.1f}h")
            for s in task.get("substeps", []):
                icon = "✅" if s["done"] else "⬜"
                lines.append(f"    {icon} {s['name']} (预估{s['est_min']}min, 实际{s.get('actual_min',0):.0f}min)")
            lines.append("")

        path = Path.home() / f"task_report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
        path.write_text("\n".join(lines), encoding="utf-8")
        Messagebox.ok(f"已导出: {path}", "完成")

    # ── 启动 ──────────────────────────────────
    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    def _on_close(self):
        if self.timer_running:
            self._stop_timer()
        self.agents.stop()
        self.store.save_all()
        self.root.destroy()
