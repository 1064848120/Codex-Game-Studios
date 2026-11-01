# Codex Game Studios · 使用指南

[项目首页](README.md) · [English](README.en.md)

基于 [Claude-Code-Game-Studios](https://github.com/Donchitos/Claude-Code-Game-Studios)
制作的非官方 Codex 适配，保留原作者 MIT 许可和原始资料。

**只用 Codex。你描述游戏目标，工作室自己安排流程，不需要逐个选择或输入技能。**

## 如何开始

在 Codex 中打开整个 game-studios-universal 项目文件夹，新建项目聊天，直接说：

> 我要用 Godot 做这款游戏，这是我的设计资料。请按工作室完整流程推进，
> 先整理策划、系统关系、数值经济和 UI 方案，再实现可玩的 Demo。
> 已确定的信息不要反复问我，需要我决定游戏方向时再问。

不用安装 Claude Code，不用运行其他 AI，不用记任何 $ 命令。
AGENTS.md 是默认入口，工作室总控会自行读取流程和角色。
已有项目可以说“根据现有策划和代码继续开发”；中断后说“继续”即可恢复。
如果只要求策划或评审，总控会停在该目标，不会擅自开发整款游戏。

## 你实际经历的流程

1. 总控读取你的资料与已有进度，找出冲突、缺口和需要你决定的内容。
2. 根据项目规模与目标，安排概念、系统策划、数值、UI、技术方案。
3. 检查各系统依赖和验收标准，再拆分开发任务。
4. 按任务实现、运行、检查、复核；完成一个内部步骤后继续下一步。
5. 保存结果、证据与进度。遇到真正需要你的决策时，直接问具体问题。

你不会再被要求“运行设计技能”“现在点数值技能”“接着输入开发技能”。
技能是总控内部使用的工具，不是给用户操作的菜单。

原项目保留的完整阶段是：
概念 → 系统设计 → 技术准备 → 预制作 → 正式制作 → 打磨 → 发布准备。
总控按目标和实际配置选择路线，不会为修一个小 Bug 重走全部阶段。
发布准备不意味着自动上传、发布或提交代码。

## 本版新增的衔接

- 默认工作室总控：自然语言入口，内部选择角色与工作流。
- 保留 49 个角色、74 个原工作流，另加 1 个 Codex 总控技能。
- 保留数值、UI/UX、Godot、素材、架构、QA、版本阶段等原项目资料。
- 原 start 的“让用户输入下一条命令”已改为内部继续。
- 本地进度账本记录当前目标、步骤、验收与证据，支持中断继续。
- 缺少证据、失败检查或未回答的重要问题不能标记完成。
- 已通过的证据后来改变，会要求重新检查受影响工作。
- 原生 Claude 配置留作来源资料；上一版的跨 AI 交接程序已移除。

## 状态在哪里

production/studio/run.json：本次目标、步骤和完成证据。
production/session-state/active.md：会话恢复摘要。
production/studio/history/：已完成目标的历史记录。

这些文件由 Codex 维护，不需要你手工编辑。
进度脚本本身不会调用 AI，也不会在关掉 Codex 后继续后台运行。
自动衔接发生在正在运行的 Codex 任务内；中断后从记录恢复。

如果需要查看适配层本身，可以使用统一入口：

```text
python tools/ai/studio.py audit --json
python tools/ai/studio.py guard --profile full --scope all
python tools/ai/studio.py skills
```

这些是维护和诊断入口，正常开发仍然直接用自然语言，不能用它们代替
工作室总控的策划和开发判断。

## 已验证的范围

- 32 项自动化测试：新项目路线、已有项目接续、仅设计范围、简化路线、
  重复系统、内部自动选下一步、中断恢复、失败门禁、证据失效和归档等。
- 75 个 Codex 技能格式检查。
- 105 处阶段引用完整性。
- 解压到独立目录后重新运行校验和测试。

这些测试验证流程与状态管理。它们不是“完整游戏已经制作并试玩”的证明，
也不能保证模型每次做出的策划和数值判断正确。
具体记录见 docs/ai/VALIDATION.md。

## 能力边界

原版 15 个 Claude 事件 Hook 的项目级职责已由 `tools/ai/hooks.py`、
`tools/ai/guard.py` 和可选 `.githooks/` 提供等价入口；Codex 私有的事件传输
和通知 UI 仍由主机负责。完整映射见 `docs/ai/HOOK-PARITY.md`。
49 个角色是专业职责与提示词，不代表同时运行 49 个后台 Agent。
允许且支持时可用 Codex 原生子代理；顺序角色审阅会明确标为自审。
需要真正独立复核的门禁不能用自审冒充。
截图、运行和试玩验证依赖实际可用的 Godot 与观察工具。
本仓库提供制作流程与工具，不包含一款已经完成的示例游戏。

## 维护说明（由 AI 使用）

适配后的提示词位于 ai/，Codex 技能位于 .agents/skills/。
ai/ 和原 74 个 studio-* 入口由转换器生成；总控入口单独维护。
不要编辑生成文件后直接覆盖。原始 .claude/ 文件仍为上游来源。

内部校验：
~~~text
python tools/ai/export-universal.py --check
python tools/ai/validate.py
python -m unittest discover -s tests/adapter -v
~~~

进度工具的内部接口见 docs/ai/WORKFLOW-STATE.md，正常用户不用操作。
源码、版权和更新说明见 UPSTREAM.md 与 LICENSE。


