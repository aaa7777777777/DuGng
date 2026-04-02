"""
后台智能体集群
模拟 Antigravity 的多 Agent 并行观测模式
"""

import threading
import time
import json
from datetime import datetime
from config import AGENT_ROLES


class AgentCluster:
    """
    智能体集群管理器

    三个角色：
    - observer: 每隔一段时间自动观察用户进度并给出简评
    - advisor: 响应用户主动提问，给出时间建议
    - critic: 定期审视整体计划合理性
    """

    def __init__(self, ai_engine, data_store):
        self.ai = ai_engine
        self.store = data_store
        self.running = False
        self._observer_thread = None
        self._callbacks = {}  # event_name -> [callback_fn]
        self.observation_interval = 600  # 10分钟观测一次
        self.last_observations = []

    def on(self, event, callback):
        """注册事件回调: 'observation', 'advice', 'critique'"""
        if event not in self._callbacks:
            self._callbacks[event] = []
        self._callbacks[event].append(callback)

    def _emit(self, event, data):
        for cb in self._callbacks.get(event, []):
            try:
                cb(data)
            except Exception as e:
                print(f"[Agent callback error] {e}")

    def start(self):
        """启动后台观测"""
        if not self.ai.is_available:
            return
        self.running = True
        self._observer_thread = threading.Thread(target=self._observer_loop, daemon=True)
        self._observer_thread.start()

    def stop(self):
        self.running = False

    def _observer_loop(self):
        """后台观测循环"""
        # 启动后等30秒再开始第一次观测
        time.sleep(30)

        while self.running:
            try:
                self._run_observation()
            except Exception as e:
                print(f"[Observer error] {e}")

            # 等待下一次观测
            for _ in range(self.observation_interval):
                if not self.running:
                    return
                time.sleep(1)

    def _run_observation(self):
        """执行一次自动观测"""
        snapshot = self.store.get_snapshot()
        role = AGENT_ROLES["observer"]

        prompt = (
            f"以下是用户当前的任务进度数据（JSON）：\n"
            f"```json\n{json.dumps(snapshot, ensure_ascii=False, indent=2)}\n```\n\n"
            f"请根据数据给出你的观察。重点关注：\n"
            f"1. 今天的时间分配是否合理\n"
            f"2. 哪些任务进度滞后\n"
            f"3. 是否有值得提醒的事项\n"
            f"简短回复，不超过3条。"
        )

        messages = [{"role": "user", "content": prompt}]
        result = self.ai.chat_sync(messages, system_prompt=role["system_prompt"])

        if result:
            observation = {
                "time": datetime.now().strftime("%H:%M"),
                "agent": "observer",
                "content": result,
            }
            self.last_observations.append(observation)
            # 只保留最近20条
            self.last_observations = self.last_observations[-20:]
            self._emit("observation", observation)

    def ask_advisor(self, question, task_context=None, callback=None):
        """主动向建议者提问"""
        role = AGENT_ROLES["advisor"]
        snapshot = self.store.get_snapshot()

        prompt = f"用户的任务数据：\n```json\n{json.dumps(snapshot, ensure_ascii=False, indent=2)}\n```\n\n"

        if task_context:
            prompt += f"用户正在讨论的任务: {task_context}\n\n"

        prompt += f"用户的问题: {question}"

        messages = [{"role": "user", "content": prompt}]

        def _on_result(result, error):
            response = {
                "time": datetime.now().strftime("%H:%M"),
                "agent": "advisor",
                "question": question,
                "content": result if result else f"[错误] {error}",
            }
            self._emit("advice", response)
            if callback:
                callback(response)

        self.ai.chat(messages, system_prompt=role["system_prompt"], callback=_on_result)

    def ask_critic(self, callback=None):
        """请求审视者审视整体计划"""
        role = AGENT_ROLES["critic"]
        snapshot = self.store.get_snapshot()

        prompt = (
            f"以下是用户的完整任务规划和当前进度：\n"
            f"```json\n{json.dumps(snapshot, ensure_ascii=False, indent=2)}\n```\n\n"
            f"请审视这个计划：\n"
            f"1. 总体时间安排是否现实？\n"
            f"2. 有没有过度乐观的预估？\n"
            f"3. 任务之间有没有冲突？\n"
            f"4. 给出你的优先级排序建议。"
        )

        messages = [{"role": "user", "content": prompt}]

        def _on_result(result, error):
            response = {
                "time": datetime.now().strftime("%H:%M"),
                "agent": "critic",
                "content": result if result else f"[错误] {error}",
            }
            self._emit("critique", response)
            if callback:
                callback(response)

        self.ai.chat(messages, system_prompt=role["system_prompt"], callback=_on_result)

    def discuss_task_time(self, task_name, substep_name, current_est, user_message, callback=None):
        """针对特定步骤的时间讨论"""
        role = AGENT_ROLES["advisor"]

        prompt = (
            f"用户想讨论一个具体步骤的时间预估：\n"
            f"- 任务: {task_name}\n"
            f"- 步骤: {substep_name}\n"
            f"- 当前预估: {current_est} 分钟 ({current_est/60:.1f}小时)\n\n"
            f"用户说: {user_message}\n\n"
            f"请帮助用户评估这个时间预估是否合理，并给出你的建议预估值和理由。"
            f"如果你建议调整，请明确给出新的分钟数。"
        )

        messages = [{"role": "user", "content": prompt}]

        def _on_result(result, error):
            response = {
                "time": datetime.now().strftime("%H:%M"),
                "agent": "advisor",
                "task": task_name,
                "substep": substep_name,
                "content": result if result else f"[错误] {error}",
            }
            self._emit("advice", response)
            if callback:
                callback(response)

        self.ai.chat(messages, system_prompt=role["system_prompt"], callback=_on_result)
