# claude-code-source-code

> Claude Code 源码档案与 Python 重写的研究仓库

本仓库包含两个子项目，从不同角度对 Claude Code（Anthropic 官方 CLI 工具）进行深度研究：

| 子项目 | 语言 | 性质 | 文件数 |
|--------|------|------|--------|
| [claude-code-source-code](#一-claude-code-source-code) | TypeScript | 反编译源码档案（v2.1.88） | 1,884 个 |
| [claw-code](#二-claw-code) | Python | 清室架构重写 | 66 个 |

---

## 一、claude-code-source-code

Claude Code v2.1.88 的反编译/解包源码，从 npm 包 `@anthropic-ai/claude-code@2.1.88` 还原，约 163,318 行 TypeScript 代码。

### 整体架构

```
claude-code-source-code/
├── src/
│   ├── main.tsx              # CLI 入口与 REPL 引导（4,683 行）
│   ├── query.ts              # 主代理循环核心（最大单文件，785KB）
│   ├── QueryEngine.ts        # SDK/Headless 查询生命周期引擎
│   ├── Tool.ts               # 工具接口定义 + buildTool 工厂
│   ├── commands.ts           # 斜杠命令定义（~25K 行）
│   ├── tools.ts              # 工具注册与预设
│   ├── context.ts            # 用户输入上下文处理
│   ├── history.ts            # 会话历史管理
│   ├── cost-tracker.ts       # API 成本追踪
│   ├── setup.ts              # 首次运行初始化
│   │
│   ├── cli/                  # CLI 基础设施（stdio、structured transports）
│   ├── commands/             # ~87 个斜杠命令实现
│   ├── components/           # React/Ink 终端 UI（33 个子目录）
│   ├── tools/                # 40+ 工具实现（44 个子目录）
│   ├── services/             # 业务逻辑层（22 个子目录）
│   ├── utils/                # 工具函数库
│   ├── state/                # 应用状态管理
│   ├── types/                # TypeScript 类型定义
│   ├── hooks/                # React Hooks
│   ├── bridge/               # Claude Desktop 远程桥接
│   ├── remote/               # 远程模式
│   ├── coordinator/          # 多代理协调
│   ├── tasks/                # 任务管理
│   ├── assistant/            # KAIROS 助手模式
│   ├── memdir/               # 长期记忆管理
│   ├── plugins/              # 插件系统
│   ├── voice/                # 语音模式
│   └── vim/                  # Vim 模式
│
├── docs/                     # 深度分析文档（中英双语）
│   ├── en/                   # English analysis
│   └── zh/                   # 中文分析
├── vendor/                   # 第三方依赖
├── stubs/                    # 模块存根
├── types/                    # 全局类型定义
├── utils/                    # 顶层工具函数
├── scripts/                  # 构建脚本
└── package.json
```

### 核心执行流程

```
用户输入
  ↓
processUserInput()         # 解析 /slash 命令
  ↓
query()                    # 主代理循环（query.ts）
  ├── fetchSystemPromptParts()    # 组装系统提示词
  ├── StreamingToolExecutor       # 并行工具执行
  ├── autoCompact()               # 上下文自动压缩
  └── runTools()                  # 工具编排调度
  ↓
yield SDKMessage           # 流式返回给消费者
```

### 技术栈

| 组件 | 技术 |
|------|------|
| 语言 | TypeScript 6.0+ |
| 运行时 | Bun（编译为 Node.js >= 18 bundle） |
| Claude API | Anthropic SDK |
| 终端 UI | React + Ink |
| 代码压缩 | esbuild |
| 数据验证 | Zod |
| 工具协议 | MCP（Model Context Protocol） |

### 主要模块说明

#### 工具系统（40+ 工具）

| 类别 | 工具 |
|------|------|
| 文件操作 | FileReadTool、FileEditTool、FileWriteTool |
| 代码搜索 | GlobTool、GrepTool |
| 系统执行 | BashTool |
| 网络访问 | WebFetchTool、WebSearchTool |
| 任务管理 | TaskCreateTool、TaskUpdateTool、TaskGetTool、TaskListTool |
| 子代理 | AgentTool |
| 代码环境 | NotebookEditTool、REPLTool、LSPTool |
| Git 工作流 | EnterWorktreeTool、ExitWorktreeTool |
| 配置与权限 | ConfigTool、AskUserQuestionTool |
| 记忆与规划 | TodoWriteTool、EnterPlanModeTool、ExitPlanModeTool |
| 自动化 | ScheduleCronTool、RemoteTriggerTool、SleepTool |
| MCP 集成 | MCPTool |

#### 斜杠命令（~87 个）

`/commit` `/commit-push-pr` `/review` `/resume` `/session` `/memory` `/config` `/skills` `/help` `/voice` `/desktop` `/mcp` `/permissions` `/theme` `/vim` `/copy` 等

#### 权限系统

- 三种模式：`default`（询问用户）/ `bypass`（自动允许）/ `strict`（自动拒绝）
- 工具级别粒度控制
- 基于 ML 的自动化权限推断分类器
- 权限规则持久化存储

#### 上下文管理

- 自动压缩策略（autoCompact）：Reactive 压缩、微压缩、裁剪压缩
- 上下文折叠（CONTEXT_COLLAPSE）
- Token 计数与估计
- 会话转录与持久化

#### 分析文档（`docs/`）

| 文档 | 内容 |
|------|------|
| 01-遥测与隐私 | 双层分析管道（Anthropic + Datadog）、无退出开关 |
| 02-隐藏功能与模型代号 | Capybara、Tengu、Fennec、Numbat 等内部代号 |
| 03-卧底模式 | Anthropic 员工在公开库自动进入卧底模式 |
| 04-远程控制与紧急开关 | 每小时轮询、6+ Killswitch、危险变更弹窗 |
| 05-未来路线图 | KAIROS 自主代理、语音模式、17 个未上线工具 |

---

## 二、claw-code

对 Claude Code 的 Python 清室重写（不包含原始代码副本），专注于架构镜像与研究。由 [@instructkr](https://github.com/instructkr)（Sigrid Jin）完成，成为全球最快达到 30K stars 的 GitHub 仓库之一。

### 整体架构

```
claw-code/
├── src/
│   ├── __init__.py               # 包导出接口
│   ├── main.py                   # CLI 入口（~200 行）
│   ├── query_engine.py           # 查询引擎核心
│   ├── runtime.py                # 运行时会话管理
│   ├── models.py                 # 共享数据类
│   ├── commands.py               # 命令元数据与执行框架
│   ├── tools.py                  # 工具元数据与执行框架
│   ├── permissions.py            # 权限上下文管理
│   ├── context.py                # 移植上下文
│   ├── setup.py                  # 工作区初始化
│   ├── session_store.py          # 会话持久化
│   ├── transcript.py             # 会话转录存储
│   ├── port_manifest.py          # 工作区清单生成
│   ├── execution_registry.py     # 执行注册表
│   ├── history.py                # 历史日志
│   ├── parity_audit.py           # 与 TypeScript 源码奇偶审计
│   ├── remote_runtime.py         # 远程模式模拟
│   ├── bootstrap_graph.py        # 启动图生成
│   ├── command_graph.py          # 命令图分割
│   ├── tool_pool.py              # 工具池组装
│   │
│   ├── reference_data/           # JSON 快照数据（驱动命令/工具元数据）
│   │   ├── commands_snapshot.json
│   │   └── tools_snapshot.json
│   │
│   ├── commands/                 # 命令实现子目录
│   ├── tools/                    # 工具实现子目录
│   ├── services/                 # 业务逻辑服务
│   ├── components/               # 终端 UI 组件（Python 版）
│   ├── state/                    # 状态管理
│   ├── types/                    # 类型定义
│   ├── utils/                    # 工具函数
│   ├── remote/                   # 远程模式
│   ├── bridge/                   # 桥接模块
│   ├── hooks/                    # Hook 系统
│   ├── memdir/                   # 记忆管理
│   ├── vim/                      # Vim 模式
│   ├── voice/                    # 语音模式
│   └── plugins/                  # 插件系统
│
└── tests/                        # 验证测试
```

### 核心类

| 类 / 模块 | 职责 |
|-----------|------|
| `QueryEnginePort` | 查询引擎，处理消息提交、流式输出、会话压缩 |
| `PortRuntime` | 运行时管理，负责路由、会话启动、轮次循环 |
| `PortManifest` | 工作区清单，生成 Markdown 概览 |
| `ToolPermissionContext` | 工具权限上下文（allow/deny/ask） |
| `WorkspaceSetup` | 环境检测与初始化报告 |
| `TranscriptStore` | 会话转录，支持追加、压缩、回放 |

### CLI 命令

```bash
python3 -m src.main [COMMAND]

# 概览
summary              # Markdown 工作区概览
manifest             # 打印清单
subsystems           # 列出 Python 模块

# 路由与索引
commands             # 列出所有命令
tools                # 列出所有工具
route [PROMPT]       # 将提示词路由到对应命令/工具

# 执行
bootstrap [PROMPT]   # 启动运行时会话
turn-loop [PROMPT]   # 运行轮次循环（--max-turns）
exec-command NAME    # 执行命令
exec-tool NAME       # 执行工具

# 会话管理
flush-transcript     # 持久化会话转录
load-session ID      # 加载已保存会话

# 远程模式
remote-mode TARGET   # 模拟远程控制
ssh-mode TARGET      # 模拟 SSH 分支
teleport-mode TARGET # 模拟 Teleport 分支

# 审计与配置
parity-audit         # 与 TypeScript 源码一致性比较
setup-report         # 启动配置报告
bootstrap-graph      # 启动阶段图
command-graph        # 命令图分割视图
tool-pool            # 工具池组装视图
```

### 设计特点

- **快照驱动**：通过 JSON 快照文件加载命令/工具元数据，无需完整实现逻辑
- **清室重写**：不包含原始 TypeScript 代码，独立实现
- **奇偶审计**：内置 `parity_audit.py` 追踪与原实现的差距
- **轻量架构**：66 个文件实现核心框架，适合学习与扩展

---

## 两个项目对比

| 维度 | claude-code-source-code | claw-code |
|------|------------------------|-----------|
| 语言 | TypeScript | Python |
| 代码量 | ~163,000 行 | ~5,000 行 |
| 性质 | 反编译源码档案 | 清室架构重写 |
| 功能完整度 | 完整（100%） | 架构框架（~20%） |
| 核心循环 | `query.ts`（785KB） | `QueryEnginePort`（~200 行） |
| 工具系统 | 40+ 完整实现 | 快照元数据 + 执行框架 |
| 命令系统 | ~87 个完整实现 | 快照元数据 + 执行框架 |
| 主要用途 | 深度学习完整实现细节 | 架构理解、移植研究 |

---

## 许可与声明

本仓库仅供学术研究与教育目的使用。两个子项目均基于公开可获取的信息构建。使用者应自行遵守相关法律法规及服务条款。
