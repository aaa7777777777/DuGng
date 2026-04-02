# ⏱ AI-Powered Task Planner v2.0

一个集成 AI 实时观测的桌面时间规划工具。

借鉴 Google Antigravity 的 Agent 工作台理念：多智能体并行观测你的任务进展，实时给出反馈和建议。

---

## 核心特性

### 📂 左侧：任务树状图
- 所有项目和子步骤以树形结构展示
- 右键菜单：开始计时 / 标记完成 / 编辑 / 添加 / 删除
- 双击编辑任务属性
- 实时显示进度百分比和剩余时间

### 📊 右上：步骤表格 + 时间估算
- 每个子步骤的预估时间、实际时间、差值一目了然
- 所有字段可直接编辑
- 自动计算执行建议（整块/碎片/大块拆分）
- 统计行显示已投入、剩余、预计完成日期

### 🤖 右下：AI 助手面板
- **实时对话**：随时和 AI 讨论任务时间分配
- **自动观测**：后台观测者每10分钟分析进度并提醒
- **计划审视**：一键让 AI 审视整体计划合理性
- **时间讨论**：选中具体步骤，AI 帮你评估时间预估
- **独立窗口**：可弹出为单独窗口，不占主界面空间

### 🧠 后台智能体集群
- **观测者 (Observer)**：自动监测进度，发现滞后和异常
- **建议者 (Advisor)**：回答提问，给出具体时间建议
- **审视者 (Critic)**：审视整体计划，挑战不合理假设

### 🔌 双 AI 通道
- **Kimi (Moonshot)**：OpenAI 兼容接口，国内访问友好
- **Claude (Anthropic)**：原生 API，深度推理能力强
- 运行时可随时切换

---

## 快速开始

```bash
# 克隆
git clone https://github.com/你的用户名/task-planner.git
cd task-planner

# 安装依赖
pip install -r requirements.txt

# 配置 API Key
cp .env.example .env
# 编辑 .env，填入你的 API Key

# 运行
python task_planner.py
