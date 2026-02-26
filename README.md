# wechat-feishu-digest

> **一键爬取微信公众号最新文章，AI 聚合摘要，输出到飞书文档或本地 Markdown**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/)

## ✨ 功能特性

- 🕷 **纯爬虫模式**：无需 AI，基于搜狗微信搜索，获取公众号最新文章
- 🤖 **AI 智能聚合**：调用 OpenRouter（step-3-5-flash 等模型）对文章做主题聚合与要点提炼
- 📄 **飞书文档输出**：自动创建飞书文档，结构化展示文章列表与 AI 摘要
- 💾 **本地文件输出**：同时生成 `digest.md`（可读报告）和 `raw.json`（原始数据）
- ⚙️ **高度可配置**：通过 `.env` 文件自定义账号、天数、模型、输出目标
- 🔋 **零外部依赖**：Python 仅使用标准库（`urllib`, `subprocess`, `json` 等）

## 🚀 快速开始

### 1. 克隆 & 安装依赖

```bash
git clone https://github.com/your-org/wechat-feishu-digest.git
cd wechat-feishu-digest

# 安装 Node.js 搜索脚本依赖（只需一次）
cd wechat_search && npm install cheerio && cd ..
```

### 2. 配置

```bash
cp .env.example .env
# 编辑 .env，填入飞书 App 凭据和/或 OpenRouter API Key
```

### 3. 运行

```bash
# 一键运行（根据 .env 自动选择输出目标）
python run.py

# 或使用 shell 包装脚本
bash run.sh
```

## ⚙️ 配置说明

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `FEISHU_APP_ID` | 飞书应用 App ID | 空（不输出飞书） |
| `FEISHU_APP_SECRET` | 飞书应用 App Secret | 空 |
| `FEISHU_SHARE_OPENID` | 自动共享给此用户的 Open ID | 空 |
| `OPENROUTER_API_KEY` | OpenRouter API Key | 空（跳过 AI 摘要） |
| `OPENROUTER_MODEL` | AI 模型 | `stepfun/step-3.5-flash:free` |
| `LOCAL_OUTPUT_DIR` | 本地输出目录 | `./output` |
| `ACCOUNTS` | 爬取的公众号（逗号分隔） | `机器之心,新智元,量子位` |
| `SEARCH_DAYS` | 爬取最近 N 天 | `7` |
| `SEARCH_NUM` | 每账号最多抓取条数 | `30` |

## 🛠 命令行参数

```
python run.py [选项]

选项:
  --days N          爬取最近 N 天（覆盖 .env 设置）
  --output TARGET   输出目标: feishu / local / both / auto（默认 auto）
  --no-ai           跳过 AI 聚合摘要
  --dry-run         仅爬取并预览，不写任何输出
  --config FILE     指定配置文件（默认 .env）
```

## 📁 输出示例

**飞书文档**：自动创建、自动共享，包含元信息、AI 摘要（如配置）、各账号文章列表

**本地输出** (`output/2026-02-26_digest.md`)：

```markdown
# AI公众号周报｜机器之心·新智元·量子位（2026-02-19 ~ 2026-02-26）

> 合计：34 篇

## 📊 AI 智能摘要

### 大模型进展
- DeepSeek GitHub 密集更新，V4 版本预期即将发布
- GLM-5 技术论文全公开，智谱开源力度持续加大
...

## 机器之心（15 篇）
- [2026-02-25] [科技前沿|医疗领域DeepSeek时刻](https://...)
...
```

## 🏗 项目结构

```
wechat-feishu-digest/
├── run.py                    # 统一入口
├── run.sh                    # 一键运行脚本
├── .env.example              # 配置模板
├── src/
│   ├── config.py             # 配置加载
│   ├── crawler.py            # 微信文章爬取
│   ├── summarizer.py         # OpenRouter AI 摘要
│   └── outputs/
│       ├── feishu.py         # 飞书文档输出
│       └── local.py          # 本地文件输出
├── wechat_search/            # Node.js 搜索脚本
│   └── scripts/
│       └── search_wechat.js
└── output/                   # 本地输出目录（自动创建）
```

## 🔑 获取飞书凭据

1. 访问 [飞书开放平台](https://open.feishu.cn/app)，创建「自建应用」
2. 在「权限管理」中开启：
   - `docx:document` （读写文档）
   - `drive:drive` （管理云空间）
3. 复制 App ID 和 App Secret 填入 `.env`

## 📄 License

[MIT](LICENSE)

---

## 🖥 Web UI

```bash
bash run.sh --ui        # 启动 UI：http://localhost:8765
bash run.sh --ui --port 9000
```

界面功能：
- 账号/关键词可视化编辑（三组独立配置）
- OpenRouter API Key 输入（带显示/隐藏）
- 本地输出目录、飞书配置
- 一键运行 + 实时日志流

---

## 📦 打包为 .exe（Windows）

> 依赖：Python 3.8+、Node.js（均需加入 PATH）

```powershell
# 在项目根目录运行（PowerShell）
.\build\build.ps1

# 或者双击 build\build.bat
```

打包完成后：

```
dist/
  wechat-digest.exe   ← 双击运行，浏览器自动打开 UI
  .env.example        ← 首次使用复制为 .env 并填写配置
```

- 首次运行会在 `wechat-digest.exe` 旁边创建 `.env` 和 `output/` 目录
- 如果系统无 Node.js，脚本会自动下载便携版 `node.exe`（约 40MB）并打包进去
