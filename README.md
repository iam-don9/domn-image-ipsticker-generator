# domn-image-ipsticker-generator

![domn-image-ipsticker-generator 封面](assets/readme/hero.webp)

> IP 角色 → 可审阅的透明贴纸批量生成。

## 是什么

IP 角色 → 可审阅的透明贴纸批量生成。本仓库是一个 Agent 技能（SKILL.md 为唯一权威定义），把上面的方法论沉淀为可被对话触发的可执行流程。

## 怎么做（工作流）

<p align="center">
  <img src="./assets/readme/workflow.svg" width="100%" alt="domn-image-ipsticker-generator 工作流：锁定 IP → 出草图 → 批量生成 → 透明裁切 → 命名归档。批量生成与裁切前需审批">
</p>

1. **锁定 IP**
2. **出草图**
3. **批量生成**
4. **透明裁切**
5. **命名归档**

## 怎么用

将本仓库放入支持 `SKILL.md` 的 Agent 技能目录：

- **WorkBuddy**：`~/.workbuddy/skills/domn-image-ipsticker-generator/`
- **Codex / 其他**：对应 skills 目录

然后在对话中触发，例如：

```
用 domn-image-ipsticker-generator 帮我处理一段需求。
```

## 依赖

纯提示词方法论 + references/ 弹药库；出图依赖图像生成模型.

## 仓库结构

```
domn-image-ipsticker-generator/
├── SKILL.md                 # 技能定义（唯一权威）
├── references/              # 方法论弹药库
├── assets/                  # 模板 / 占位素材
└── assets/readme/           # 本 README 的视觉资产（hero.webp / workflow.svg）
```

## 许可

本仓库内容以 `SKILL.md` 为唯一权威定义。如附带 `LICENSE` 文件，以其为准。

---

*README 由 `beautify-github-readme` 生成 · 封面图来自作者作品集，强调色由封面图采样派生。*
