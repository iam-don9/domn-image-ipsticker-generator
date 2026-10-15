# domn-image-ipsticker-generator

![domn-image-ipsticker-generator 封面](assets/readme/hero.webp)

> 把 IP 角色参考图，按有审批闸门的流程产出一批透明背景、原生尺寸、语义命名的贴纸 PNG（默认严格 3×3 模版）。

## 真实产出样例

下面是这个技能**实际会产出**的东西（抽自仓库内的 references/ 真实交付样例），不是抽象描述：

```text
sticker_manifest.json 单条记录：
{ "id":"s03", "sequence":3, "emotion":"得意", "action":"比心",
  "camera":"3/4 近景", "asset_scope":"HALF_BODY", "aspect_ratio":"1:1",
  "source_mode":"PERSON_AND_STYLE", "bounding_box":[...], "output":"output/stickers/03_得意_比心.png" }
裁切命令：python scripts/split_3x3.py <source.png> <output-dir> --threshold 1 --margin 1
规则：FULL_BODY 必用 9:16；PROPS 禁出现人/手/身体；文件名只由 manifest 序列生成，绝不用图像内容猜名。
```

## 是什么

把 IP 角色参考图，按有审批闸门的流程产出一批透明背景、原生尺寸、语义命名的贴纸 PNG（默认严格 3×3 模版）。 本仓库是一个 Agent 技能（SKILL.md 为唯一权威定义），把上面的方法论沉淀为可被对话触发的可执行流程。

## 为什么不同

状态机带两道硬闸门(Gate01 生成前确认计划、Gate02 批量后确认质量)绝不跳过；始终用一张 4K 级 3×3 源图再按真实 Alpha 边缘外扩 1px 裁切，不机械等分、不降采样。

## 怎么做（工作流）

<p align="center">
  <img src="./assets/readme/workflow.svg" width="100%" alt="domn-image-ipsticker-generator 工作流：解析参考→建计划闸门1→样品批量→质检闸门2→裁切导出">
</p>

> 两道硬闸门不跳过；命名只由 manifest 决定

1. **解析参考** — 双维度(角色/风格)分析+声明不确定性，定 asset_scope
2. **建计划+闸门1** — 写 sticker_manifest.json，等用户批准范围/比例/3×3
3. **样品→批量** — 先小样评审，过审再整批，守同一角色锚点
4. **批量质检+闸门2** — contact sheet 查一致性/透明/对齐，等终审
5. **裁切导出** — alpha 感知裁切原生尺寸，按 manifest 命名

## 怎么用

将本仓库放入支持 `SKILL.md` 的 Agent 技能目录：

- **WorkBuddy**：`~/.workbuddy/skills/domn-image-ipsticker-generator/`
- **Codex / 其他**：对应 skills 目录

然后在对话中触发，例如：

```
用 domn-image-ipsticker-generator 从这只猫角色参考图生成一套 3×3 得意/比心表情包贴纸。
```

## 依赖

纯提示词方法论 + references/ 弹药库；涉及出图/视频时依赖外部图像生成或文生视频模型。

## 仓库结构

```
domn-image-ipsticker-generator/
├── SKILL.md                 # 技能定义（唯一权威）
├── assets/                  # 模板 / 占位素材
├── references/              # 方法论弹药库
└── assets/readme/           # 本 README 的视觉资产（hero.webp / workflow.svg）
```

## 许可

本仓库内容以 `SKILL.md` 为唯一权威定义。如附带 `LICENSE` 文件，以其为准。

---

*README 由 `beautify-github-readme` 生成 · 封面图来自作者作品集，强调色由封面采样派生；工作流图为每技能独立 motif。*