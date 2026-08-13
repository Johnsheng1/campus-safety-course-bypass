<div align="center">

# 🛡️ campus-safety-course-bypass

**Claude Skill — 校园安全教育课程自动学习助手**

自动完成校园安全教育平台（`wap.xiaoyuananquantong.com`）的新生必修课程学习与正式考试。
一键刷完 10 门安全教育课，章节测试 + 正式考试全自动，正式考试模拟人类答题节奏。

[![Skill][skill-badge]][skill]　[![License: MIT][license-badge]][license]

</div>

[skill-badge]: https://img.shields.io/badge/Claude-Skill-blueviolet
[skill]: #-安装
[license-badge]: https://img.shields.io/badge/License-MIT-green.svg
[license]: #-开源协议

---

## ✨ 功能特性

| 能力 | 说明 |
|------|------|
| 🖼️ **图片页秒过** | 绕过"每张图停留 20 秒"限制，注入脚本接管翻页逻辑直接跳到最后 |
| 📚 **题库自动匹配** | 基于 `data/题库库紧凑.json` 对题干做模糊匹配，单选/多选/判断全覆盖 |
| 🖱️ **真实点击模拟** | 触发页面原生 `setVle()`，提交体带题目 ID，杜绝 `500` 错误 |
| 🔁 **错题自愈** | 测试未通过时自动进错题页逆向确认正确答案，修正题库后重考 |
| ⏱️ **人类节奏答题** | 正式考试每题随机停顿 0.5–3 秒，贴近真实答题行为 |
| 📦 **题库随包携带** | 10 章题库解析好放在 `data/` 目录，开箱即用 |

---

## 🧠 工作原理

平台交互链路如下，本 Skill 在每一环注入自动化：

```
课程列表 → 图片学习页(20s/图) → 章节测试(单选/多选/判断) → 下一章(×10) → 正式考试(50题,90分合格)
    │            │                    │                        │                │
    │       注入脚本接管         题库匹配+模拟点击          点击"下一章"     题库匹配+人类节奏
    │       nextTop 翻页        触发原生 setVle()                            逐题作答
    │       markArticleViewed   交卷校验 isSuccess:true
```

**关键点**：平台提交参数必须是 `question={题目ID}-{选项}`（多选为 `~ID-A~ID-B...`），
只有通过点击选项触发原生 `setVle()` 才能生成该格式 —— 直接改隐藏 input 会让提交接口返回 `500`。

---

## 📁 目录结构

```
campus-safety-course/
├── SKILL.md                      # 主流程文档（注入脚本、坑点、验证清单）
├── README.md                     # 本说明
├── scripts/
│   └── parse_question_bank.py    # docx 题库 → JSON 答案映射库解析脚本
└── data/
    ├── 题库库.json               # 完整题库（章节→题型→题干→答案+选项）
    ├── 题库库紧凑.json           # 紧凑版（注入浏览器首选）
    ├── 题库提取.txt              # docx 原始文本
    └── bank_js_国家安全.js       # 单章注入示例
```

---

## 📦 安装

### 方式一：Claude 技能市场（推荐）

把本仓库的 `campus-safety-course` 目录放入 Claude Agent 的 Skills 目录：

```
<Agent 工作目录>/Skills/campus-safety-course/
```

然后在技能管理中注册 `campus-safety-course` 即可。

### 方式二：手动安装

```bash
git clone https://github.com/<your-name>/campus-safety-course.git
# 将 campus-safety-course 文件夹复制到 Skills 目录后注册
```

### 依赖

- [CherryStudio](https://cherry-ai.com/) / Claude Code 等支持 Agent Skills 的环境
- 浏览器 MCP（Chrome 控制）已连接并登录目标平台

---

## 🚀 使用

1. 用浏览器打开课程列表页并完成登录（需已选课）。
2. 对 Agent 说：
   > **"帮我刷安全教育课程"**
3. Agent 按流程自动完成：10 门课图片学习 → 章节测试 → 正式考试。

### 题库更新

课程题库更新时，用解析脚本重新生成：

```bash
python scripts/parse_question_bank.py "新题库.docx" "data/题库库.json"
```

---

## ⚠️ 免责声明

本项目**仅供学习与研究自动化脚本编写使用**，请勿用于任何违反校规、平台规则或
法律法规的场景。使用者应自行承担使用本项目产生的一切后果。作者不对因滥用导致的
任何损失负责。请尊重平台使用条款与课程考核的严肃性。

---

## 📄 开源协议

本项目基于 [MIT License](LICENSE) 开源。

<div align="center">

**如果觉得有用，欢迎 ⭐ Star 支持！**

</div>
