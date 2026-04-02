"""
左侧：任务树状图
"""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from config import CATEGORY_LABELS, CATEGORY_STYLE


class TaskTreePanel:
    """左侧任务树状图面板"""

    def __init__(self, parent, data_store, on_select=None, on_timer_start=None, on_timer_stop=None):
        self.parent = parent
        self.store = data_store
        self.on_select = on_select
        self.on_timer_start = on_timer_start
        self.on_timer_stop = on_timer_stop

        self.frame = ttk.Frame(parent, padding=5)
        self._build()

    def _build(self):
        # 标题栏
        header = ttk.Frame(self.frame)
        header.pack(fill=X, pady=(0, 5))
        ttk.Label(header, text="📂 项目总览", font=("", 14, "bold")).pack(side=LEFT)

        btn_frame = ttk.Frame(header)
        btn_frame.pack(side=RIGHT)

        ttk.Button(
            btn_frame, text="＋ 添加任务", bootstyle="outline-success",
            command=self._add_task_dialog, width=10,
        ).pack(side=LEFT, padx=2)

        # 树状图
        columns = ("category", "progress", "remaining", "status")
        self.tree = ttk.Treeview(
            self.frame,
            columns=columns,
            show="tree headings",
            height=25,
            selectmode="browse",
        )

        self.tree.heading("#0", text="任务 / 步骤", anchor=W)
        self.tree.heading("category", text="类型", anchor=CENTER)
        self.tree.heading("progress", text="进度", anchor=CENTER)
        self.tree.heading("remaining", text="剩余", anchor=CENTER)
        self.tree.heading("status", text="状态", anchor=CENTER)

        self.tree.column("#0", width=250, minwidth=200)
        self.tree.column("category", width=100, minwidth=80, anchor=CENTER)
        self.tree.column("progress", width=80, minwidth=60, anchor=CENTER)
        self.tree.column("remaining", width=100, minwidth=80, anchor=CENTER)
        self.tree.column("status", width=80, minwidth=60, anchor=CENTER)

        scrollbar = ttk.Scrollbar(self.frame, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

        # 绑定选择事件
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.tree.bind("<Double-1>", self._on_double_click)

        # 右键菜单
        self.context_menu = ttk.Menu(self.tree, tearoff=0)
        self.context_menu.add_command(label="▶ 开始计时", command=self._ctx_start_timer)
        self.context_menu.add_command(label="⏹ 停止计时", command=self._ctx_stop_timer)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="✅ 标记完成", command=self._ctx_toggle_done)
        self.context_menu.add_command(label="✏️ 编辑", command=self._ctx_edit)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="＋ 添加子步骤", command=self._ctx_add_substep)
        self.context_menu.add_command(label="🗑 删除", command=self._ctx_delete)

        self.tree.bind("<Button-3>", self._show_context_menu)  # Windows/Linux
        self.tree.bind("<Button-2>", self._show_context_menu)  # macOS

        self.refresh()

    def refresh(self):
        """重建树"""
        self.tree.delete(*self.tree.get_children())

        for task in self.store.tasks:
            cat_label = CATEGORY_LABELS.get(task["category"], "")
            logged_h = task["logged_min"] / 60

            if task["total_hours"] > 0:
                pct = min(100, logged_h / task["total_hours"] * 100)
                remaining_h = max(0, task["total_hours"] - logged_h)
                progress_str = f"{pct:.0f}%"
                if task["daily_target_min"] > 0:
                    days = remaining_h * 60 / task["daily_target_min"]
                    remaining_str = f"{remaining_h:.1f}h / {days:.0f}天"
                else:
                    remaining_str = f"{remaining_h:.1f}h"
            else:
                steps = task.get("substeps", [])
                done_count = sum(1 for s in steps if s.get("done"))
                progress_str = f"{done_count}/{len(steps)}"
                remaining_str = f"累计{logged_h:.1f}h"

            all_done = all(s.get("done") for s in task.get("substeps", []))
            status_str = "✅ 完成" if all_done and task.get("substeps") else "🔄 进行中"

            task_id = task["id"]
            self.tree.insert(
                "", END,
                iid=task_id,
                text=f"  {task['name']}",
                values=(cat_label, progress_str, remaining_str, status_str),
                open=task.get("expanded", True),
            )

            # 子步骤
            for step in task.get("substeps", []):
                step_status = "✅" if step.get("done") else "⬜"
                est_h = step["est_min"] / 60
                actual = step.get("actual_min", 0)

                self.tree.insert(
                    task_id, END,
                    iid=step["id"],
                    text=f"  {step_status}  {step['name']}",
                    values=(
                        "",
                        f"{actual:.0f}/{step['est_min']}min",
                        f"预估{est_h:.1f}h",
                        step_status,
                    ),
                )

    def _on_tree_select(self, event):
        sel = self.tree.selection()
        if sel and self.on_select:
            item_id = sel[0]
            # 找到对应的 task 和可能的 substep
            task, substep = self._find_item(item_id)
            self.on_select(task, substep)

    def _on_double_click(self, event):
        """双击编辑"""
        self._ctx_edit()

    def _find_item(self, item_id):
        """根据 ID 找 task 和 substep"""
        for task in self.store.tasks:
            if task["id"] == item_id:
                return task, None
            for step in task.get("substeps", []):
                if step["id"] == item_id:
                    return task, step
        return None, None

    def _find_parent_task(self, item_id):
        """根据子步骤ID找父任务"""
        for task in self.store.tasks:
            for step in task.get("substeps", []):
                if step["id"] == item_id:
                    return task
        return None

    def _show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def _ctx_start_timer(self):
        sel = self.tree.selection()
        if sel and self.on_timer_start:
            task, _ = self._find_item(sel[0])
            if task:
                self.on_timer_start(task)

    def _ctx_stop_timer(self):
        if self.on_timer_stop:
            self.on_timer_stop()

    def _ctx_toggle_done(self):
        sel = self.tree.selection()
        if not sel:
            return
        task, substep = self._find_item(sel[0])
        if substep:
            substep["done"] = not substep.get("done", False)
            self.store.save_tasks()
            self.refresh()

    def _ctx_edit(self):
        sel = self.tree.selection()
        if not sel:
            return
        task, substep = self._find_item(sel[0])
        if substep:
            self._edit_substep_dialog(task, substep)
        elif task:
            self._edit_task_dialog(task)

    def _ctx_add_substep(self):
        sel = self.tree.selection()
        if not sel:
            return
        item_id = sel[0]
        task, _ = self._find_item(item_id)
        if not task:
            task = self._find_parent_task(item_id)
        if task:
            self._add_substep_dialog(task)

    def _ctx_delete(self):
        sel = self.tree.selection()
        if not sel:
            return
        item_id = sel[0]
        task, substep = self._find_item(item_id)

        if substep:
            parent_task = self._find_parent_task(item_id)
            if parent_task:
                parent_task["substeps"] = [s for s in parent_task["substeps"] if s["id"] != item_id]
                self.store.save_tasks()
                self.refresh()
        elif task:
            self.store.tasks = [t for t in self.store.tasks if t["id"] != item_id]
            self.store.save_tasks()
            self.refresh()

    # ── 对话框 ──────────────────────────────
    def _add_task_dialog(self):
        dialog = ttk.Toplevel(self.parent)
        dialog.title("添加新任务")
        dialog.geometry("400x350")
        dialog.grab_set()

        ttk.Label(dialog, text="任务名称:").pack(anchor=W, padx=20, pady=(15, 2))
        name_var = ttk.StringVar()
        ttk.Entry(dialog, textvariable=name_var, width=40).pack(padx=20)

        ttk.Label(dialog, text="类型:").pack(anchor=W, padx=20, pady=(10, 2))
        cat_var = ttk.StringVar(value="deep")
        cat_frame = ttk.Frame(dialog)
        cat_frame.pack(anchor=W, padx=20)
        for key, label in CATEGORY_LABELS.items():
            ttk.Radiobutton(cat_frame, text=label, variable=cat_var, value=key).pack(anchor=W)

        ttk.Label(dialog, text="预估总时长(小时), 0=持续性:").pack(anchor=W, padx=20, pady=(10, 2))
        hours_var = ttk.StringVar(value="0")
        ttk.Entry(dialog, textvariable=hours_var, width=10).pack(anchor=W, padx=20)

        ttk.Label(dialog, text="每日目标(分钟), 0=无:").pack(anchor=W, padx=20, pady=(10, 2))
        daily_var = ttk.StringVar(value="0")
        ttk.Entry(dialog, textvariable=daily_var, width=10).pack(anchor=W, padx=20)

        def _save():
            import time as _t
            new_id = f"task_{int(_t.time()*1000)}"
            task = {
                "id": new_id,
                "name": name_var.get() or "未命名任务",
                "category": cat_var.get(),
                "total_hours": float(hours_var.get() or 0),
                "daily_target_min": int(daily_var.get() or 0),
                "logged_min": 0,
                "expanded": True,
                "substeps": [],
                "notes": "",
            }
            self.store.tasks.append(task)
            self.store.save_tasks()
            self.refresh()
            dialog.destroy()

        ttk.Button(dialog, text="保存", bootstyle="success", command=_save).pack(pady=15)

    def _add_substep_dialog(self, task):
        dialog = ttk.Toplevel(self.parent)
        dialog.title(f"为「{task['name']}」添加子步骤")
        dialog.geometry("380x200")
        dialog.grab_set()

        ttk.Label(dialog, text="步骤名称:").pack(anchor=W, padx=20, pady=(15, 2))
        name_var = ttk.StringVar()
        ttk.Entry(dialog, textvariable=name_var, width=35).pack(padx=20)

        ttk.Label(dialog, text="预估时间(分钟):").pack(anchor=W, padx=20, pady=(10, 2))
        est_var = ttk.StringVar(value="60")
        ttk.Entry(dialog, textvariable=est_var, width=10).pack(anchor=W, padx=20)

        def _save():
            import time as _t
            step = {
                "id": f"s{int(_t.time()*1000)}",
                "name": name_var.get() or "未命名步骤",
                "est_min": int(est_var.get() or 60),
                "actual_min": 0,
                "done": False,
                "notes": "",
            }
            task["substeps"].append(step)
            self.store.save_tasks()
            self.refresh()
            dialog.destroy()

        ttk.Button(dialog, text="保存", bootstyle="success", command=_save).pack(pady=15)

    def _edit_task_dialog(self, task):
        dialog = ttk.Toplevel(self.parent)
        dialog.title(f"编辑任务: {task['name']}")
        dialog.geometry("400x400")
        dialog.grab_set()

        ttk.Label(dialog, text="任务名称:").pack(anchor=W, padx=20, pady=(15, 2))
        name_var = ttk.StringVar(value=task["name"])
        ttk.Entry(dialog, textvariable=name_var, width=40).pack(padx=20)

        ttk.Label(dialog, text="类型:").pack(anchor=W, padx=20, pady=(10, 2))
        cat_var = ttk.StringVar(value=task["category"])
        cat_frame = ttk.Frame(dialog)
        cat_frame.pack(anchor=W, padx=20)
        for key, label in CATEGORY_LABELS.items():
            ttk.Radiobutton(cat_frame, text=label, variable=cat_var, value=key).pack(anchor=W)

        ttk.Label(dialog, text="预估总时长(小时):").pack(anchor=W, padx=20, pady=(10, 2))
        hours_var = ttk.StringVar(value=str(task["total_hours"]))
        ttk.Entry(dialog, textvariable=hours_var, width=10).pack(anchor=W, padx=20)

        ttk.Label(dialog, text="每日目标(分钟):").pack(anchor=W, padx=20, pady=(10, 2))
        daily_var = ttk.StringVar(value=str(task["daily_target_min"]))
        ttk.Entry(dialog, textvariable=daily_var, width=10).pack(anchor=W, padx=20)

        ttk.Label(dialog, text="备注:").pack(anchor=W, padx=20, pady=(10, 2))
        notes_var = ttk.StringVar(value=task.get("notes", ""))
        ttk.Entry(dialog, textvariable=notes_var, width=40).pack(padx=20)

        def _save():
            task["name"] = name_var.get()
            task["category"] = cat_var.get()
            task["total_hours"] = float(hours_var.get() or 0)
            task["daily_target_min"] = int(daily_var.get() or 0)
            task["notes"] = notes_var.get()
            self.store.save_tasks()
            self.refresh()
            dialog.destroy()

        ttk.Button(dialog, text="保存", bootstyle="success", command=_save).pack(pady=15)

    def _edit_substep_dialog(self, task, substep):
        dialog = ttk.Toplevel(self.parent)
        dialog.title(f"编辑步骤: {substep['name']}")
        dialog.geometry("380x250")
        dialog.grab_set()

        ttk.Label(dialog, text="步骤名称:").pack(anchor=W, padx=20, pady=(15, 2))
        name_var = ttk.StringVar(value=substep["name"])
        ttk.Entry(dialog, textvariable=name_var, width=35).pack(padx=20)

        ttk.Label(dialog, text="预估时间(分钟):").pack(anchor=W, padx=20, pady=(10, 2))
        est_var = ttk.StringVar(value=str(substep["est_min"]))
        ttk.Entry(dialog, textvariable=est_var, width=10).pack(anchor=W, padx=20)

        ttk.Label(dialog, text="实际用时(分钟):").pack(anchor=W, padx=20, pady=(10, 2))
        actual_var = ttk.StringVar(value=str(substep.get("actual_min", 0)))
        ttk.Entry(dialog, textvariable=actual_var, width=10).pack(anchor=W, padx=20)

        done_var = ttk.BooleanVar(value=substep.get("done", False))
        ttk.Checkbutton(dialog, text="已完成", variable=done_var).pack(anchor=W, padx=20, pady=5)

        def _save():
            substep["name"] = name_var.get()
            substep["est_min"] = int(est_var.get() or 0)
            substep["actual_min"] = float(actual_var.get() or 0)
            substep["done"] = done_var.get()
            self.store.save_tasks()
            self.refresh()
            dialog.destroy()

        ttk.Button(dialog, text="保存", bootstyle="success", command=_save).pack(pady=15)
