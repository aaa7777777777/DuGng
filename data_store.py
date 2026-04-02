"""
数据持久化层
"""

import json
import copy
from datetime import datetime
from config import DATA_FILE, LOG_FILE, KNOWLEDGE_FILE, HISTORY_FILE, DEFAULT_TASKS


class DataStore:
    """统一数据读写"""

    def __init__(self):
        self.tasks = self._load_json(DATA_FILE, copy.deepcopy(DEFAULT_TASKS))
        self.daily_log = self._load_json(LOG_FILE, {})
        self.knowledge = self._load_json(KNOWLEDGE_FILE, {"items": [], "patterns": []})
        self.ai_history = self._load_json(HISTORY_FILE, {"sessions": []})

    @staticmethod
    def _load_json(path, default):
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return default

    @staticmethod
    def _save_json(path, data):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def save_tasks(self):
        self._save_json(DATA_FILE, self.tasks)

    def save_log(self):
        self._save_json(LOG_FILE, self.daily_log)

    def save_knowledge(self):
        self._save_json(KNOWLEDGE_FILE, self.knowledge)

    def save_ai_history(self):
        self._save_json(HISTORY_FILE, self.ai_history)

    def save_all(self):
        self.save_tasks()
        self.save_log()
        self.save_knowledge()
        self.save_ai_history()

    def log_session(self, task_name, minutes):
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in self.daily_log:
            self.daily_log[today] = {}
        if task_name not in self.daily_log[today]:
            self.daily_log[today][task_name] = 0
        self.daily_log[today][task_name] += minutes
        self.save_log()

    def get_snapshot(self):
        """生成当前状态快照，供 AI 分析"""
        today = datetime.now().strftime("%Y-%m-%d")
        today_log = self.daily_log.get(today, {})

        snapshot = {
            "date": today,
            "today_total_min": sum(today_log.values()),
            "today_breakdown": today_log,
            "tasks": [],
        }
        for t in self.tasks:
            logged_h = t["logged_min"] / 60
            info = {
                "name": t["name"],
                "category": t["category"],
                "total_hours": t["total_hours"],
                "logged_hours": round(logged_h, 1),
                "daily_target_min": t["daily_target_min"],
                "progress_pct": round(
                    min(100, logged_h / t["total_hours"] * 100) if t["total_hours"] > 0 else 0, 1
                ),
                "substeps": [
                    {
                        "name": s["name"],
                        "est_min": s["est_min"],
                        "actual_min": s.get("actual_min", 0),
                        "done": s["done"],
                    }
                    for s in t.get("substeps", [])
                ],
            }
            if t["total_hours"] > 0:
                remaining_h = max(0, t["total_hours"] - logged_h)
                info["remaining_hours"] = round(remaining_h, 1)
                if t["daily_target_min"] > 0:
                    info["remaining_days"] = round(remaining_h * 60 / t["daily_target_min"])
            snapshot["tasks"].append(info)

        return snapshot

    def reset_tasks(self):
        self.tasks = copy.deepcopy(DEFAULT_TASKS)
        self.save_tasks()
