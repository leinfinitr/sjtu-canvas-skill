# Contributing to SJTU Canvas Skill

感谢你愿意为 SJTU Canvas Skill 贡献代码、文档或使用反馈。本项目面向上海交通大学 Canvas 用户，目标是在合规前提下帮助学生更高效地整理课程资料、课堂视频字幕和复习上下文。

## 开发环境

本项目使用 Python 和 `uv` 管理依赖。

```bash
git clone https://github.com/leinfinitr/sjtu-canvas-skill.git
cd sjtu-canvas-skill
uv sync --extra dev
```

运行测试：

```bash
uv run python -m pytest -q
```

检查 CLI 是否能正常启动：

```bash
uv run main --help
```

## 项目结构

```text
scripts/        # CLI、Canvas API、SJTU 课堂视频、材料抽取和复习上下文生成逻辑
tests/          # 单元测试与 CLI 行为测试
README.md       # 面向学生用户的使用说明
SKILL.md        # 面向 agent 的 skill 描述
```

## 贡献流程

1. Fork 本仓库并创建 feature branch。
2. 修改代码或文档。
3. 运行测试：`uv run python -m pytest -q`。
4. 确认没有提交 `.env`、Cookie、Token、课程文件或私人学习资料。
5. 提交 Pull Request，并说明改动动机、测试结果和潜在兼容性影响。

## Commit message 规范

本仓库推荐使用英文提交信息，并采用如下格式：

```text
[type]: message
```

示例：

```text
[doc]: update readme
[feat]: add subtitle fallback
[fix]: handle expired canvas cookie
[ci]: add github actions workflow
[chore]: update project metadata
```

常用 type：

- `[feat]`：新增功能
- `[fix]`：修复问题
- `[doc]`：文档更新
- `[test]`：测试相关
- `[ci]`：CI/CD 相关
- `[build]`：构建、依赖、打包配置
- `[chore]`：其他维护性修改

## 安全与隐私要求

请不要在 issue、PR、commit、测试 fixture 或文档示例中包含真实的：

- Canvas API Token
- `oc.sjtu.edu.cn` Cookie
- jAccount 凭据
- 课程视频、字幕、课件等非公开课程资料

文档示例请使用占位符，例如：

```bash
TOKEN="your_canvas_api_token"
OC_COOKIE="your_oc_cookie"
```

如果你不小心提交了敏感信息，请立即撤销或失效相关凭证，并在必要时联系维护者处理历史记录。

## 设计原则

- 优先支持个人学习、课程复习和本地资料整理。
- 不绕过 Canvas 或课堂视频平台的权限控制。
- 不鼓励批量传播课程资料、视频或字幕。
- 命令行接口应尽量保持可组合、可测试、适合 agent 调用。
- 对外输出日志时必须避免泄露 Cookie、Token 等敏感凭证。

## 致谢

本项目开发过程中使用了 Hermes Agent 与 GPT-5.5 辅助设计、实现和测试，并参考、借鉴了以下开源项目的思路与实现：

- [Hydroiodic/sjtu-canvas-skill](https://github.com/Hydroiodic/sjtu-canvas-skill)
- [Okabe-Rintarou-0/SJTU-Canvas-Helper](https://github.com/Okabe-Rintarou-0/SJTU-Canvas-Helper)

感谢这些项目为 SJTU Canvas 自动化与学习工具生态提供的探索。
