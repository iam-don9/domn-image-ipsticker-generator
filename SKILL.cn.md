---
name: domn-image-ipsticker-generator
description: |
  将 IP 角色参考图转成可审核、可批量规划的透明贴纸 PNG。用户想要保持角色一致的表情贴纸、3×3 素材板、语义文件名或原生尺寸 Alpha 裁切时使用。流程区分人物参考与画风参考，在批量生成和自动拆剪前分别要求人工确认，并以 Manifest 作为唯一命名来源。
trigger-words: [IP sticker, character stickers, sticker sheet, batch stickers, transparent stickers, 贴纸, 表情贴纸, IP形象, 贴纸素材库, 批量生成贴纸]
---

# IP 人物贴纸资产生产

当用户要把参考图变成可审核、可局部重生成、可自动拆剪和归档的 IP 贴纸资产时使用本 Skill。把它当作带人工门禁的生产流水线。只有连接的工具实际产出图片、抠图结果或 ZIP 后，才能声称这些交付物存在。

## 运行契约

- **Module（模块）：** 对外只暴露参考输入、生成简报、确认决定和导出请求。
- **Interface（接口）：** 调用方需要知道当前状态、所需确认、输入格式、输出路径、Manifest ID 和错误模式，不需要知道内部提示词拼接或裁切算法。
- **Implementation（实现）：** 将参考解析、提示词构造、网格定位、边缘留白、RGBA 转换和打包隐藏在接口之后。
- **Depth（深度）：** 用少量状态变更操作承载复杂流程，避免堆出许多只透传参数的浅模块。
- **Adapter（适配器）：** 生图、背景移除和归档分别由适配器承担。只有一个实现时保留概念接缝，不增加投机性抽象。
- 返回结构化产物和错误；不得隐藏失败或静默重试。

## 状态机与双 Gate

只维护一个当前状态并记录转移：

`INIT -> REFERENCE_UPLOADED -> REFERENCE_ANALYZED -> GENERATION_PLAN_CREATED -> WAITING_USER_CONFIRMATION -> SAMPLE_GENERATING -> SAMPLE_REVIEW -> WAITING_SAMPLE_APPROVAL -> BATCH_GENERATING -> BATCH_GENERATED -> QUALITY_CHECK -> WAITING_FINAL_APPROVAL -> CROPPING -> EXPORTING -> NAMING -> PACKAGING -> COMPLETED`

Gate 01 是 `WAITING_USER_CONFIRMATION`。必须展示并取得明确确认：参考人物、参考画风、是否改变画风、目标画风、资产范围（`AVATAR` 头像、`HALF_BODY` 半身、`FULL_BODY` 全身、`PROPS` 周边或 `COMBINATION` 组合）、画面比例、贴纸类型、3×3 排版、背景、描边、撕纸边缘、单枚尺寸和数量。未确认不得批量生成。

Gate 02 是 `WAITING_FINAL_APPROVAL`。批量生成后必须暂停并展示预览，取得对角色一致性、表情、镜头可读性、拼贴处理、描边、撕纸边缘、透明背景和 3×3 对齐的明确确认。未确认不得进入拆剪或导出。

禁止捷径：`REFERENCE_ANALYZED -> BATCH_GENERATING`、未获样张确认就从 `SAMPLE_REVIEW` 批量生成、未获最终确认就从 `BATCH_GENERATED` 拆剪。

## 工作流

### 1. 解析参考图

先确认存在可读取的图片，并分别分析两个维度，同时标出不确定项：

- 人物：身份、脸型、眼睛、嘴、耳朵、头发/毛发、身体比例、配色、服装、配件、标志特征和性格。
- 画风：媒介、渲染、材质、光线、纹理、线条语言、色彩语言、构图语言和表面特征。

询问用户选择 `PERSON_ONLY`、`STYLE_ONLY`、`PERSON_AND_STYLE`、`PERSON_KEEP_STYLE_CHANGE` 或 `PERSON_AND_STYLE_ENHANCE`。对“换一种更好看”这类模糊表达不得擅自推断，需把歧义摆出来。

还要让用户为每个条目选择资产范围：`AVATAR`（脸部和头部特征）、`HALF_BODY`（头部、躯干、服装和上肢动作）、`FULL_BODY`（完整身体、脚部、服装比例和全身动作）、`PROPS`（带有 IP 特征但不出现人物的周边）或 `COMBINATION`（人物与周边同画面）。凡是涉及 `FULL_BODY` 的 prompt，输出比例必须为 `9:16`。`AVATAR`、`HALF_BODY`、`PROPS` 默认用 `1:1`；`COMBINATION` 只能在构图审核后选择 `1:1` 或 `9:16`。不得为了塞进方形网格而压缩全身角色。

`PROPS` 必须明确禁止人物、手、身体部位、人物剪影和“拿着该物件”的动作。周边可以继承人物的配色、图案、纹理、材质或标志符号，但必须独立出现。若画面出现人物，该条必须改为 `COMBINATION`，并在 Manifest 中拆分 `Character` 与 `Props`。

### 2. 编制并确认生成方案

在任何批量任务前先生成简短方案和 `sticker_manifest.json`。每项至少包含稳定的 `id`、`sequence`、`emotion`、`action`、`camera`、`asset_scope`、`aspect_ratio`、`source_mode`，以及可选的重生成备注。Manifest 是文件命名和后续替换的唯一来源，不能根据图片内容猜名字。

MVP 默认规划 9 枚严格 3×3 贴纸。方案要写明目标画风、视觉锚点、负面约束、透明背景、描边/撕纸边缘/阴影处理和样张子集。停在 Gate 01，直到用户确认或修改方案。

### 源图分辨率契约

生成模式固定为一张 3×3 源图，之后拆分为 9 个独立文件。`AVATAR`、`HALF_BODY` 和 `PROPS` 条目目标是 4K 级方形图（`1:1`）。不要写死某个像素值：先读取当前用户模型支持的尺寸，选择可用的最大方形输出。如果模型最高能力未达到 4K 级，必须报告实际尺寸，并回到 Gate 01 让用户确认后才能生成。`FULL_BODY` 内容在已批准的素材板方案中保持 `9:16` 构图。`COMBINATION` 采用 Manifest 中确认的比例。

高分辨率 3×3 源图必须保留到拆剪阶段。禁止先缩小到 1800×1800 或其他工作尺寸再裁切，否则会损失描边、阴影、撕纸边缘和纹理细节。记录源图分辨率和每枚原生裁切尺寸。

### 3. 先样张、后批量

先生成能代表整体方向的小批样张并展示审核。若用户拒绝，只修改其指出的方案字段后重做样张。样张确认被记录后，再由支持批处理的适配器一次生成其余 Manifest 项，保持同一组人物锚点和画风决策。

生成失败时保留任务 ID 和错误，明确告知用户，并询问是重试受影响的条目还是修改方案。局部重生成只更新指定 Manifest 项，默认不得整套重做。

### 生图提示词工程

将 `huashu-gpt-image` 的方法论作为提示词层使用，但不引入其中的渠道专属素材流程：

- 默认用精炼中文短句写 prompt。只有品牌、产品或专有风格名称本身是英文时才保留英文。禁止使用 `Subject:`、`Style:` 等伪分区标题。
- 填满三个槽位：主体、具体参考锚点和媒介。优先使用用户提供的参考图或熟知的设计师/品牌/媒介名称，不堆形容词。若某个风格名容易诱发 logo 或 nameplate，就改用结构化视觉语言，并明确禁止不需要的标记。
- 写 prompt 前先选模式：方向不确定用 `exploration`，方向已有但细节未定用 `hybrid`，方案已批准用 `execution`。探索模式先生成少量方向，选定后再切执行模式生成样张或批量。
- 只保留会改变画面的信息：姿态、表情、镜头、相对位置、配色、材质和技术尺寸。3×3 素材板只描述“虚拟网格”，明确禁止可见网格线、边框、定位标记和坐标文字；裁切定位交给 Alpha 包围盒。
- 每次 3×3 生图必须明确要求 9 枚独立贴纸、每格四周留透明间隔、不得出现额外图形或伪影、不得有内容跨格。任何一项不满足，都应先重生成素材板再拆剪。
- 每条 prompt 提交前跑五项检查：中文优先、长度信息密度合适、至少两个具体锚点或结构化替代、没有伪分区、没有可删除的形容词填充。任何一项失败都必须重写后才能生图。

提示词或结果失败时先诊断再重试：压缩形容词堆砌，改用参考图或结构化描述替代模糊风格，密集或含文字布局提高质量档位，删除未经核实的设计史信息；只有当前适配器无法满足透明度、规模或额度时才切换生成路径，并在任务结果中记录 fallback。

### 4. 批量质量审核

创建联系表，检查角色一致性、表情/动作可读性、镜头力度、角色内部的拼贴材质、描边、撕纸边缘、透明背景和无重叠的 3×3 对齐。在 Gate 02 暂停并记录决定。被拒条目可局部重生成。

### 5. 拆剪与导出

对每个获批贴纸先沿 Alpha 实际可见边缘取最小包围盒，再向外扩大 1px 透明 padding。主 PNG 使用扩张后的原生像素尺寸导出，绝不重采样。不得把整张 3×3 画面机械平均切九块，否则会截断纸张纤维、抗锯齿描边和阴影。输入为 PNG/JPG/WebP 时统一转 RGBA；已有 Alpha 要保留；无 Alpha 只有在背景移除适配器成功并报告后才能去背景。

项目参考拆剪脚本为 `3. develop/domn-image-ipsticker-generator/scripts/split_3x3.py`。它只用 3×3 排版确定虚拟格，再在每格内使用 Alpha 感知前景掩膜并保留最大连通前景块。默认 `--margin 1`（向外扩大一个源像素）和 `--threshold 1`（保留所有非零 Alpha 像素）；输出保持原生尺寸且绝不重采样。脚本输出 9 张 PNG 和 `split_manifest.json`，清单记录 detected/expanded 包围盒、尺寸、`padding_clipped` 及 `resampled: false`。若不透明伪影已与贴纸发生像素连接，应标记人工复核，不得静默删除。

```powershell
python scripts/split_3x3.py <source.png> <output-dir> --threshold 1 --margin 1
```

对于已经独立且带透明背景的单枚贴纸，使用 `3. develop/domn-image-ipsticker-generator/scripts/crop_alpha.py`：按完整非零 Alpha 包围盒裁切，向外增加 1px 透明 padding，保持原生尺寸，并写出旁侧 JSON 清单。

```powershell
python scripts/crop_alpha.py <sticker.png> <output.png> --padding 1 --threshold 1
```

文件名严格读取 Manifest，格式为 `{sequence}_{emotion}_{action}.png`。导出结构：

```text
output/
  stickers/          # 按扩张包围盒导出的原生尺寸 RGBA PNG
  preview/           # 获批的 3×3 或分组预览
  project/ip_sticker_master.json
  manifest/sticker_manifest.json
  package/            # 用户要求且工具支持时的 ZIP
```

## 数据与交付契约

Manifest 记录项目元数据和每枚贴纸的 `id`、`sequence`、`emotion`、`action`、`camera`、`asset_scope`、`aspect_ratio`、`source_mode`、包围盒、输出路径及处理参数。

质量审核界面必须在每个高成本转移前展示生成预览，让审核者检查角色一致性、表情与动作、镜头可读性、拼贴材质、描边、撕纸边缘、透明度、间距和意外重叠。最终交付可包含独立 PNG、批量 ZIP、预览 PNG 和 Manifest JSON；每个产物都必须列出实际路径和验证结果。

## 反馈与局部替换

预览后允许按三种范围反馈：全部素材、某一枚或某一条 Manifest 项。可修改角色一致性、画风、表情、镜头、撕纸边缘、描边和构图。局部重生成只更新选中的 Manifest 项。

## MVP 与扩展

MVP 包含：参考上传与解析、Gate 01、Manifest、样张审核、批量生成、Gate 02、3×3 联系表审核、原生尺寸 Alpha 裁切、透明 PNG、语义命名和预览。

只有实现和适配器确实存在时才启用扩展：智能间距、自动对齐、自动裁切、边缘检测、自动撕纸边缘/描边、批量替换、版本历史和 ZIP 导出。仅规划的能力不得当作已完成能力展示。

路线分三阶段：第一阶段完成上传、9 枚贴纸、3×3 预览、双 Gate、原生尺寸透明拆剪、命名和 Manifest；第二阶段加入局部重生成、版本和重新导出；第三阶段形成角色、画风、贴纸、周边和 Prompt 库，以及长期资产版本管理。

## 交付自检

- 两次人工确认均明确记录。
- 每个输出都映射到一个 Manifest 项，不猜文件名。
- 主独立文件保留扩张裁切后的原生尺寸，为 RGBA PNG 和透明背景。
- 预览和 Manifest 一并交付。
- 局部重生成不影响未选中的 Manifest 项。
- 失败、缺少工具和视觉分析不确定性对用户可见。
- `FULL_BODY` 条目使用 `9:16`；`PROPS` 条目不含人物；两项都从 Manifest 校验。
