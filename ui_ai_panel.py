"""
右侧下部 / 独立窗口：AI 观测与反馈面板
"""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from datetime import datetime


class AIPanelFrame:
    """AI 对话与观测面板"""

    def __init__(self, parent, agent_cluster, ai_engine, data_store, get_context_fn=None):
        """
        Args:
            parent: 父容器
            agent_cluster: AgentCluster 实例
            ai_engine: AIEngine 实例
            data_store: DataStore 实例
            get_context_fn: 返回 (current_task, current_step) 的函数
        """
        self.parent = parent
        self.agents = agent_cluster
        self.ai = ai_engine
        self.store = data_store
        self.get_context = get_context_fn

        self.chat_history = []  # 对话历史
        self.detached_window = None

        self.frame = ttk.Frame(parent, padding=5)
        self._build()

        # 注册 Agent 回调
        self.agents.on("observation", self._on_observation)
        self.agents.on("advice", self._on_advice)
        self.agents.on("critique", self._on_critique)

    def _build(self):
        # 顶部工具栏
        toolbar = ttk.Frame(self.frame)
        toolbar.pack(fill=X, pady=(0, 5))

        ttk.Label(toolbar, text="🤖 AI 助手", font=("", 12, "bold")).pack(side=LEFT)

        # AI 切换
        self.provider_var = ttk.StringVar(value=self.ai.provider if self.ai.is_available else "无")
        provider_menu = ttk.OptionMenu(
            toolbar, self.provider_var,
            self.provider_var.get(),
            *self.ai.available_providers,
            command=self._switch_provider,
        )
        provider_menu.pack(side=RIGHT, padx=5)
        ttk.Label(toolbar, text="模型:", font=("", 9)).pack(side=RIGHT)

        # 独立窗口按钮
        ttk.Button(
            toolbar, text="⧉ 弹出窗口", bootstyle="outline-light",
            command=self._detach_window, width=10,
        ).pack(side=RIGHT, padx=5)

        # 快捷按钮栏
        quick_bar = ttk.Frame(self.frame)
        quick_bar.pack(fill=X, pady=(0, 5))

        ttk.Button(
            quick_bar, text="👁 立即观测", bootstyle="outline-warning",
            command=self._request_observation, width=12,
        ).pack(side=LEFT, padx=2)

        ttk.Button(
            quick_bar, text="🔍 审视计划", bootstyle="outline-danger",
            command=self._request_critique, width=12,
        ).pack(side=LEFT, padx=2)

        ttk.Button(
            quick_bar, text="⏱ 讨论时间", bootstyle="outline-info",
            command=self._discuss_time, width=12,
        ).pack(side=LEFT, padx=2)

        ttk.Button(
            quick_bar, text="🗑 清空", bootstyle="outline-secondary",
            command=self._clear_chat, width=6,
        ).pack(side=RIGHT, padx=2)

        # 对话显示区
        self.chat_display = ttk.Text(
            self.frame, wrap="word", font=("", 10), height=12,
            state="disabled",
        )
        self.chat_display.pack(fill=BOTH, expand=True, pady=(0, 5))

        # 配置标签样式
        self.chat_display.tag_config("observer", foreground="#FFD93D")
        self.chat_display.tag_config("advisor", foreground="#6BCB77")
        self.chat_display.tag_config("critic", foreground="#FF6B6B")
        self.chat_display.tag_config("user", foreground="#4D96FF")
        self.chat_display.tag_config("system", foreground="#888888")
        self.chat_display.tag_config("time", foreground="#666666")

        # 输入区
        input_frame = ttk.Frame(self.frame)
        input_frame.pack(fill=X)

        self.input_entry = ttk.Entry(input_frame, font=("", 11))
        self.input_entry.pack(side=LEFT, fill=X, expand=True, padx=(0, 5))
        self.input_entry.bind("<Return>", self._on_send)
        self.input_entry.insert(0, "输入问题，或选中步骤后点「讨论时间」...")

        self.input_entry.bind("<FocusIn>", self._clear_placeholder)

        ttk.Button(
            input_frame, text="发送", bootstyle="info",
            command=self._on_send, width=6,
        ).pack(side=RIGHT)

        # 欢迎消息
        self._append_message("system", "系统", self._get_welcome_text())

    def _get_welcome_text(self):
        if not self.ai.is_available:
            return (
                "⚠️ 未检测到 API Key。请在项目根目录创建 .env 文件并配置：\n"
                "KIMI_API_KEY=your-key  或  CLAUDE_API_KEY=your-key\n"
                "配置后重启应用。"
            )
        providers = ", ".join(self.ai.available_providers)
        return (
            f"AI 助手已就绪 ✓  可用模型: {providers}\n"
            f"后台观测者每10分钟自动分析你的进度。\n"
            f"你可以随时提问，或选中表格中的步骤点「讨论时间」。"
        )

    def _switch_provider(self, value):
        self.ai.set_provider(value)
        self._append_message("system", "系统", f"已切换到 {value} 模型")

    def _clear_placeholder(self, event):
        if self.input_entry.get().startswith("输入问题"):
            self.input_entry.delete(0, "end")

    # ── 消息显示 ──────────────────────────────
    def _append_message(self, role, name, content):
        """向聊天区追加消息"""
        self.chat_display.config(state="normal")

        now = datetime.now().strftime("%H:%M")
        tag = role if role in ("observer", "advisor", "critic", "user", "system") else "system"

        self.chat_display.insert("end", f"[{now}] ", "time")
        self.chat_display.insert("end", f"{name}: ", tag)
        self.chat_display.insert("end", f"{content}\n\n")

        self.chat_display.see("end")
        self.chat_display.config(state="disabled")

        # 同步到独立窗口
        if self.detached_window and self.detached_window.winfo_exists():
            self._sync_to_detached(now, name, content, tag)

    def _sync_to_detached(self, time_str, name, content, tag):
        try:
            w = self._detached_chat
            w.config(state="normal")
            w.insert("end", f"[{time_str}] ", "time")
            w.insert("end", f"{name}: ", tag)
            w.insert("end", f"{content}\n\n")
            w.see("end")
            w.config(state="disabled")
        except Exception:
            pass

    # ── 事件处理 ──────────────────────────────
    def _on_observation(self, data):
        """后台观测回调（从子线程调用，需要 thread-safe）"""
        self.frame.after(0, lambda: self._append_message(
            "observer", f"👁 观测者 [{data['time']}]", data["content"]
        ))

    def _on_advice(self, data):
        self.frame.after(0, lambda: self._append_message(
            "advisor", f"💡 建议者", data["content"]
        ))

    def _on_critique(self, data):
        self.frame.after(0, lambda: self._append_message(
            "critic", f"🔍 审视者", data["content"]
        ))

    def _on_send(self, event=None):
        text = self.input_entry.get().strip()
        if not text or text.startswith("输入问题"):
            return

        self.input_entry.delete(0, "end")
        self._append_message("user", "你", text)

        # 获取当前上下文
        task_context = None
        if self.get_context:
            task, step = self.get_context()
            if task:
                task_context = task["name"]
                if step:
                    task_context += f" > {step['name']}"

        self.agents.ask_advisor(text, task_context=task_context)

    def _request_observation(self):
        self._append_message("system", "系统", "正在请求 AI 观测...")

        def _run():
            self.agents._run_observation()

        import threading
        threading.Thread(target=_run, daemon=True).start()

    def _request_critique(self):
        self._append_message("system", "系统", "正在请求计划审视...")
        self.agents.ask_critic()

    def _discuss_time(self):
        """讨论选中步骤的时间预估"""
        if not self.get_context:
            return

        task, step = self.get_context()
        if not task:
            self._append_message("system", "系统", "请先在左侧选择一个任务")
            return

        if not step:
            self._append_message("system", "系统", "请在右侧表格中选择一个具体步骤")
            return

        self._append_message(
            "system", "系统",
            f"正在讨论: {task['name']} > {step['name']} (当前预估{step['est_min']}min)"
        )

        user_msg = self.input_entry.get().strip()
        if not user_msg or user_msg.startswith("输入问题"):
            user_msg = "请帮我评估这个步骤的时间预估是否合理，并给出你的建议。"

        self.input_entry.delete(0, "end")
        self._append_message("user", "你", user_msg)

        self.agents.discuss_task_time(
            task_name=task["name"],
            substep_name=step["name"],
            current_est=step["est_min"],
            user_message=user_msg,
        )

    def _clear_chat(self):
        self.chat_display.config(state="normal")
        self.chat_display.delete("1.0", "end")
        self.chat_display.config(state="disabled")

    # ── 独立窗口 ──────────────────────────────
    def _detach_window(self):
        if self.detached_window and self.detached_window.winfo_exists():
            self.detached_window.lift()
            return

        self.detached_window = ttk.Toplevel(self.parent)
        self.detached_window.title("🤖 AI 助手 - 独立窗口")
        self.detached_window.geometry("600x700")

        # 复制聊天区
        self._detached_chat = ttk.Text(
            self.detached_window, wrap="word", font=("", 11), state="disabled"
        )
        self._detached_chat.pack(fill=BOTH, expand=True, padx=10, pady=10)

        self._detached_chat.tag_config("observer", foreground="#FFD93D")
        self._detached_chat.tag_config("advisor", foreground="#6BCB77")
        self._detached_chat.tag_config("critic", foreground="#FF6B6B")
        self._detached_chat.tag_config("user", foreground="#4D96FF")
        self._detached_chat.tag_config("system", foreground="#888888")
        self._detached_chat.tag_config("time", foreground="#666666")

        # 复制当前聊天内容
        self._detached_chat.config(state="normal")
        current = self.chat_display.get("1.0", "end")
        self._detached_chat.insert("1.0", current)
        self._detached_chat.config(state="disabled")

        # 输入
        input_f = ttk.Frame(self.detached_window)
        input_f.pack(fill=X, padx=10, pady=(0, 10))

        detach_input = ttk.Entry(input_f, font=("", 11))
        detach_input.pack(side=LEFT, fill=X, expand=True, padx=(0, 5))

        def _send_detached(event=None):
            text = detach_input.get().strip()
            if text:
                detach_input.delete(0, "end")
                self._append_message("user", "你", text)
                task_context = None
                if self.get_context:
                    task, step = self.get_context()
                    if task:
                        task_context = task["name"]
                self.agents.ask_advisor(text, task_context=task_context)

        detach_input.bind("<Return>", _send_detached)
        ttk.Button(input_f, text="发送", bootstyle="info", command=_send_detached).pack(side=RIGHT)
