#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════
  时间规划实时监测工具 v2.0
  AI-Powered Task Planner & Live Tracker
═══════════════════════════════════════════════════════

  安装: pip install -r requirements.txt
  配置: 复制 .env.example 为 .env 并填入 API Key
  运行: python task_planner.py
"""

from ui_main import MainApp


def main():
    app = MainApp()
    app.run()


if __name__ == "__main__":
    main()
