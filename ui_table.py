"""
右侧上部：步骤详情表格 + 时间估算（全部可编辑）
"""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.tableview import Tableview
from datetime import datetime, timedelta


class TaskTablePanel:
    """右侧任务详情表格"""

    def __init__(self, parent, data_store):
        self.parent = parent
        self.store = data_store
        self.current_task = None

        self.frame = ttk.Frame(parent, padding=5)
        self._build()

    def _build(self):
        # 任务信息头
        self.header_frame = ttk.Frame(self.frame)
        self.header_frame.pack(fill=X, pady=(0, 5))

        self.task_name_label = ttk.Label(
            self.header_frame, text="选择左侧任务查看详情", font=("", 14, "bold")
        )
        self.task_name_label.pack(side=LEFT)

        self.task_meta_label = ttk.Label(
            self.header_frame, text="", font=("", 10), foreground="#888"
        )
        self.task_meta_label.pack(side=RIGHT)

        # 统计行
        self.stats_frame = ttk.Frame(self.frame)
        self.stats_frame.pack(fill=X, pady=(0, 8))

        self.stat_labels = {}
        for key, text in [
            ("logged", "已投入"), ("remaining", "剩余"),
            ("daily", "每日目标"), ("finish", "预计完成"),
        ]:
            f = ttk.Frame(self.stats_frame)
            f.pack(side=LEFT, padx=10)
            ttk.Label(f, text=text, font=("", 9), foreground="#888").pack()
            lbl = ttk.Label(f, text="--", font=("", 12, "bold"))
            lbl.pack()
            self.stat_labels[key] = lbl

        # 表格
        columns = [
            {"text": "步骤名称", "stretch": True},
            {"text": "预估(min)", "stretch": False, "width": 90},
            {"text": "实际(min)", "stretch": False, "width": 90},
            {"text": "差值", "stretch": False, "width": 70},
            {"text": "状态", "stretch": False, "width": 70},
            {"text": "执行建议", "stretch": True, "width": 150},
        ]

        self.table_frame = ttk.Frame(self.frame)
        self.table_frame.pack(fill=BOTH, expand=True)

        # 用 Treeview 模拟可编辑表格
        self.table = ttk.Treeview(
            self.table_frame,
            columns=("est", "actual", "diff", "status", "hint"),
            show="headings",
            height=8,
        )
        self.table.heading("est", text="预估(min)")
        self.table.heading("actual", text="实际(min)")
        self.table.heading("diff", text="差值")
        self.table.heading("status", text="状态")
        self.table.heading("hint", text="执行建议")

        self.table.column("est", width=80, anchor=CENTER)
        self.table.column("actual", width=80, anchor=CENTER)
        self.table.column("diff", width=70, anchor=CENTER)
        self.table.column("status", width=70, anchor=CENTER)
        self.table.column("hint", width=200, anchor=W)

        # 添加步骤名列
        self.table["columns"] = ("name", "est", "actual", "diff", "status", "hint")
        self.table.heading("name", text="步骤名称")
        self.table.column("name", width=180, anchor=W)

        table_scroll = ttk.Scrollbar(self.table_frame, orient=VERTICAL, command=self.table.yview)
        self.table.configure(yscrollcommand=table_scroll.set)
        self.table.pack(side=LEFT, fill=BOTH, expand=True)
        table_scroll.pack(side=RIGHT, fill=Y)

        # 双击编辑
        self.table.bind("<Double-1>", self._on_table_double_click)

        # 底部编辑栏
        edit_frame = ttk.LabelFrame(self.frame, text="快速编辑选中步骤", padding=8)
        edit_frame.pack(fill=X, pady=(8, 0))

        row1 = ttk.Frame(edit_frame)
        row1.pack(fill=X)

        ttk.Label(row1, text="预估:").pack(side=LEFT)
        self.edit_est = ttk.Entry(row1, width=8)
        self.edit_est.pack(side=LEFT, padx=(2, 10))
        ttk.Label(row1, text="min").pack(side=LEFT, padx=(0, 15))

        ttk.Label(row1, text="实际:").pack(side=LEFT)
        self.edit_actual = ttk.Entry(row1, width=8)
        self.edit_actual.pack(side=LEFT, padx=(2, 10))
        ttk.Label(row1, text="min").pack(side=LEFT, padx=(0, 15))

        ttk.Button(
            row1, text="💾 保存", bootstyle="success", width=8,
            command=self._save_edit,
        ).pack(side=LEFT, padx=5)

        ttk.Button(
            row1, text="✅ 切换完成", bootstyle="outline-info", width=10,
            command=self._toggle_done,
        ).pack(side=LEFT, padx=5)

    def show_task(self, task, substep=None):
        """显示指定任务的详情表格"""
        self.current_task = task
        if not task:
            return

        # 更新头部
        self.task_name_label.config(text=task["name"])
        self.task_meta_label.config(text=task.get("notes", ""))

        # 更新统计
        logged_h = task["logged_min"] / 60
        self.stat_labels["logged"].config(text=f"{logged_h:.1f}h")

        if task["total_hours"] > 0:
            remaining = max(0, task["total_hours"] - logged_h)
            self.stat_labels["remaining"].config(text=f"{remaining:.1f}h")
        else:
            self.stat_labels["remaining"].config(text="持续性")

        if task["daily_target_min"] > 0:
            self.stat_labels["daily"].config(text=f"{task['daily_target_min']}min/天")
            if task["total_hours"] > 0:
                remaining = max(0, task["total_hours"] - logged_h)
                days = remaining * 60 / task["daily_target_min"]
                finish_date = datetime.now() + timedelta(days=days)
                self.stat_labels["finish"].config(text=finish_date.strftime("%m/%d"))
            else:
                self.stat_labels["finish"].config(text="--")
        else:
            self.stat_labels["daily"].config(text="无目标")
            self.stat_labels["finish"].config(text="--")

        # 更新表格
        self.table.delete(*self.table.get_children())

        for step in task.get("substeps", []):
            est = step["est_min"]
            actual = step.get("actual_min", 0)
            diff = actual - est
            diff_str = f"{diff:+.0f}" if actual > 0 else "--"
            status = "✅" if step.get("done") else "⬜"

            # 执行建议
            if step.get("done"):
                hint = "已完成"
            elif est >= 600:
                hint = f"大块·拆{est//120}个2h时段"
            elif est >= 180:
                hint = "需整块时间≥2h"
            elif est >= 60:
                hint = "中等·1个专注时段"
            else:
                hint = "碎片时间可完成"

            self.table.insert(
                "", END,
                iid=step["id"],
                values=(step["name"], est, f"{actual:.0f}", diff_str, status, hint),
            )

        # 选中特定 substep
        if substep:
            try:
                self.table.selection_set(substep["id"])
                self.edit_est.delete(0, END)
                self.edit_est.insert(0, str(substep["est_min"]))
                self.edit_actual.delete(0, END)
                self.edit_actual.insert(0, str(substep.get("actual_min", 0)))
            except Exception:
                pass

    def _on_table_double_click(self, event):
        sel = self.table.selection()
        if not sel or not self.current_task:
            return
        step_id = sel[0]
        for step in self.current_task.get("substeps", []):
            if step["id"] == step_id:
                self.edit_est.delete(0, END)
                self.edit_est.insert(0, str(step["est_min"]))
                self.edit_actual.delete(0, END)
                self.edit_actual.insert(0, str(step.get("actual_min", 0)))
                break

    def _save_edit(self):
        sel = self.table.selection()
        if not sel or not self.current_task:
            return
        step_id = sel[0]
        for step in self.current_task.get("substeps", []):
            if step["id"] == step_id:
                try:
                    step["est_min"] = int(self.edit_est.get() or step["est_min"])
                except ValueError:
                    pass
                try:
                    step["actual_min"] = float(self.edit_actual.get() or 0)
                except ValueError:
                    pass
                self.store.save_tasks()
                self.show_task(self.current_task)
                break

    def _toggle_done(self):
        sel = self.table.selection()
        if not sel or not self.current_task:
            return
        step_id = sel[0]
        for step in self.current_task.get("substeps", []):
            if step["id"] == step_id:
                step["done"] = not step.get("done", False)
                self.store.save_tasks()
                self.show_task(self.current_task)
                break

    def get_selected_step(self):
        """返回当前选中的步骤"""
        sel = self.table.selection()
        if not sel or not self.current_task:
            return None, None
        step_id = sel[0]
        for step in self.current_task.get("substeps", []):
            if step["id"] == step_id:
                return self.current_task, step
        return self.current_task, None
