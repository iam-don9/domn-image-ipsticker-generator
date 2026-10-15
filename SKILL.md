---
name: domn-image-ipsticker-generator
description: |
  Turn IP character references into a reviewable batch of transparent sticker PNGs. Use for consistent character stickers, 3x3 sticker sheets, semantic filenames, and native-size alpha-edge crops. Requires approval before batch generation and before cropping.
trigger-words: [IP sticker, character stickers, sticker sheet, batch stickers, transparent stickers, 贴纸, 表情贴纸, IP形象, 贴纸素材库, 批量生成贴纸]
---

# IP Sticker Asset Production

Use this Skill as a gated production workflow for reference analysis, prompt planning, image generation, review, alpha-edge cropping, naming, and delivery. Do not claim an image, background removal, or ZIP exists unless a connected tool actually produced it.

## Operating contract

- **Module:** the workflow module exposes a small interface: reference input, generation brief, approval decisions, and export request.
- **Interface:** callers must know the current state, required approval, accepted inputs, output paths, manifest IDs, and error mode; they do not need internal prompt assembly or crop calculations.
- **Implementation:** hide reference parsing, prompt construction, grid placement, edge padding, RGBA conversion, and package assembly behind the interface.
- **Depth:** prefer one deep orchestration module with few state-changing operations over many shallow pass-through steps.
- **Adapter:** use an adapter for the actual image generator, background remover, and archive writer. If only one implementation exists, keep the seam conceptual and do not add a speculative abstraction.
- Return structured artifacts and errors; do not bury a failed job or silently retry it.

## State machine and gates

Maintain exactly one current state and record transitions:

`INIT -> REFERENCE_UPLOADED -> REFERENCE_ANALYZED -> GENERATION_PLAN_CREATED -> WAITING_USER_CONFIRMATION -> SAMPLE_GENERATING -> SAMPLE_REVIEW -> WAITING_SAMPLE_APPROVAL -> BATCH_GENERATING -> BATCH_GENERATED -> QUALITY_CHECK -> WAITING_FINAL_APPROVAL -> CROPPING -> EXPORTING -> NAMING -> PACKAGING -> COMPLETED`

Gate 01 is `WAITING_USER_CONFIRMATION`. Show and obtain explicit confirmation for character reference, style reference, whether style changes, target style, asset scope (`AVATAR`, `HALF_BODY`, `FULL_BODY`, `PROPS`, or `COMBINATION`), aspect ratio, sticker type, 3x3 layout, background, outline, torn edge, single-sticker size, and quantity. Without approval, do not start batch generation.

Gate 02 is `WAITING_FINAL_APPROVAL`. After batch generation, pause and show a preview. Obtain explicit confirmation for character consistency, expression, camera/readability, collage treatment, outline, torn edge, transparency, and 3x3 alignment. Without approval, do not import for cropping or export individual assets.

Never take these shortcuts: `REFERENCE_ANALYZED -> BATCH_GENERATING`, `SAMPLE_REVIEW -> BATCH_GENERATING` without sample approval, or `BATCH_GENERATED -> CROPPING` without final approval.

## Workflow

### 1. Inspect the reference

Confirm that a readable image exists. Analyze two independent dimensions and state uncertainty:

- Character: identity, face shape, eyes, mouth, ears, hair/fur, body ratio, palette, clothing, accessories, signature features, personality.
- Style: medium, rendering, material, lighting, texture, line language, color language, composition language, and surface characteristics.

Ask whether the user wants `PERSON_ONLY`, `STYLE_ONLY`, `PERSON_AND_STYLE`, `PERSON_KEEP_STYLE_CHANGE`, or `PERSON_AND_STYLE_ENHANCE`. Do not infer a style change from a vague request; surface the ambiguity.

Also ask which asset scope applies to each entry: `AVATAR` (face and head features), `HALF_BODY` (head, torso, clothing, and upper-limb action), `FULL_BODY` (complete body, feet, clothing proportions, and full-body action), `PROPS` (an object carrying IP traits but no person), or `COMBINATION` (character and props together). Any prompt involving `FULL_BODY` must use a `9:16` output ratio. `AVATAR`, `HALF_BODY`, and `PROPS` default to `1:1`; `COMBINATION` is `1:1` or `9:16` only after composition review. Do not squeeze a full-body character into a square merely to fit a grid.

For `PROPS`, explicitly prohibit people, hands, body parts, silhouettes, and holding actions. The prop may inherit the character's palette, pattern, texture, material, or signature symbol, but must stand alone. If a person appears, classify the entry as `COMBINATION` and split `Character` and `Props` in the manifest.

### 2. Build and confirm the generation plan

Produce a concise plan and a `sticker_manifest.json` before any batch job. Each entry has a stable `id`, `sequence`, `emotion`, `action`, `camera`, `asset_scope`, `aspect_ratio`, `source_mode`, and optional regeneration notes. The manifest is the sole source for filenames and later replacement; image content must never be used to guess names.

The default MVP plan is nine stickers in a strict 3x3 grid. Each plan states the target style, visual anchors, prompt exclusions, transparent-background requirement, outline/torn-edge/shadow treatment, and the sample subset. Stop at Gate 01 until the user approves or edits the plan.

### Source resolution contract

Generation always uses one 3x3 source sheet that is later split into nine individual files. Target a 4K-class square image (`1:1`) for `AVATAR`, `HALF_BODY`, and `PROPS` entries. Do not hard-code one pixel value: inspect the current user model's supported sizes and select its largest available square output. If the model's maximum does not reach 4K class, report the actual size and return to Gate 01 for approval before generating. `FULL_BODY` content uses `9:16` composition within the approved sheet plan. `COMBINATION` follows the ratio approved in the manifest.

Keep the high-resolution 3x3 source through cropping. Do not downscale to 1800x1800 or another working size before extraction, because that discards outline, shadow, torn-edge, and texture detail. Record source resolution and each native crop dimension.

### 3. Generate a sample, then the batch

Generate a small representative sample first and present it for visual review. If the user rejects it, revise only the plan fields they identify and regenerate the sample. Once sample approval is recorded, generate the remaining manifest entries in one batch where the adapter supports batching. Preserve the same character anchors and style decisions across all entries.

On generation failure, preserve the failed job ID and error, report it, and ask whether to retry the affected entry or revise the plan. Local regeneration must update only the requested manifest entry; never regenerate the whole set by default.

### Prompt engineering for image generation

Apply the `huashu-gpt-image` method as a prompt-writing layer, without importing its channel-specific asset workflow:

- Write prompts as concise Chinese sentences by default. Use English only for an intrinsic brand, product, or named style. Do not use pseudo-sections such as `Subject:` or `Style:`.
- Fill three slots: subject, a concrete reference anchor, and medium. Prefer a supplied reference image or a well-known designer/brand/medium over adjective piles. If a style name is likely to produce a logo or nameplate, replace it with structural visual language and explicitly forbid unwanted marks.
- Choose a mode before writing: `exploration` for uncertain direction, `hybrid` for a direction with open details, or `execution` for an approved plan. For exploration, generate a small set of directions, select one, then switch to execution before the sample or batch.
- Keep only information that changes the image: pose, expression, camera, relative placement, palette, material, layer treatment, and technical size. For a 3x3 sheet, describe a virtual grid but forbid visible grid lines, borders, registration marks, and coordinate labels; let content bounding boxes determine crop placement.
- For every 3x3 prompt, explicitly require nine independent stickers, transparent breathing room around every cell, no extra graphics or artifacts, and no content crossing cell boundaries. Regenerate the source sheet before cropping if any condition fails.
- Run this five-point checkpoint before submitting each prompt: Chinese-first language, information-dense length, at least two concrete anchors or a structured substitute, no pseudo-sections, and no removable adjective padding. A failed check blocks generation until the prompt is rewritten.

When a prompt or output fails, diagnose the failure before retrying: shorten adjective-heavy text, replace a vague style with a reference image or structural description, increase quality for dense or text-bearing layouts, remove unverified historical claims, and switch generation paths only when the current adapter cannot meet transparency, scale, or quota requirements. Record the chosen fallback in the job result.

### 4. Review the batch

Create a contact sheet and run the final quality checklist. Check identity consistency, expression/action legibility, camera strength, collage material inside the character, outline quality, torn-paper edge, transparent background, and non-overlapping 3x3 alignment. Pause at Gate 02 and record the decision. Rejected entries may be selectively regenerated before proceeding.

### 5. Crop and export

For each approved sticker, trace the actual visible Alpha edge, expand it outward by exactly 1px transparent padding, then crop the resulting box including outline, torn edge, and shadow. Export at native pixel dimensions; never resample. Do not mechanically divide the 3x3 sheet or crop exactly at the visible edge, because that clips paper fibers, anti-aliased outlines, and shadows. Normalize PNG/JPG/WebP inputs to RGBA; preserve existing alpha and remove a non-transparent background only when the configured adapter can do so and reports success.

The project reference splitter is `3. develop/domn-image-ipsticker-generator/scripts/split_3x3.py`. It uses the 3x3 layout only to establish virtual cells, then applies an alpha-aware foreground mask and keeps the largest connected foreground component per cell. Defaults are `--margin 1` (one source-pixel outward expansion) and `--threshold 1` (include every non-zero alpha pixel); output is native-size with no resampling. The script writes nine PNGs and `split_manifest.json`, which records detected/expanded boxes, dimensions, `padding_clipped`, and `resampled: false`. Opaque artifacts physically connected to a sticker must be reported for review rather than silently removed.

```powershell
python scripts/split_3x3.py <source.png> <output-dir> --threshold 1 --margin 1
```

For one already-isolated transparent sticker, use `3. develop/domn-image-ipsticker-generator/scripts/crop_alpha.py`. It crops the complete non-zero Alpha bounding box, adds exactly 1px transparent padding, preserves native dimensions, and writes a sidecar JSON manifest:

```powershell
python scripts/crop_alpha.py <sticker.png> <output.png> --padding 1 --threshold 1
```

Use the manifest to name files exactly `{sequence}_{emotion}_{action}.png`. Export:

```text
output/
  stickers/          # individual native-size RGBA PNGs
  preview/           # approved 3x3 or sticker previews
  manifest/sticker_manifest.json
  package/            # optional ZIP when requested and supported
```

## Data and delivery contract

The manifest contains project metadata and one record per sticker with `id`, `sequence`, `emotion`, `action`, `camera`, `asset_scope`, `aspect_ratio`, `source_mode`, bounding box, output path, and processing parameters.

The quality-review interface must expose the generated preview before each costly transition. The reviewer can judge identity consistency, expression and action, camera readability, collage material, outline, torn edge, transparency, spacing, and accidental overlap. The final delivery can include individual PNGs, a batch ZIP, preview PNGs, and Manifest JSON; each artifact must be listed with its actual path and verification result.


## Feedback and local replacement

After preview, accept feedback at three scopes: all assets, one sticker, or one entry. Supported corrections include character identity, style, expression, camera, torn edge, outline, and composition. A local regeneration updates only the selected manifest entry.

## MVP versus extensions

MVP: reference upload and analysis, Gate 01, manifest, sample review, batch generation, Gate 02, 3x3 contact-sheet review, native-size alpha-edge crop, transparent PNG export, semantic naming, and preview.

Extensions only when the implementation and adapter are available: smart spacing, auto-align, auto-crop, edge detection, torn-edge/outline generation, batch replacement, version history, and ZIP export. Do not present an extension as complete when it is only planned.

Roadmap: Phase 1 covers upload, nine-sticker generation, 3x3 preview, approval gates, native-size transparent crop, naming, and Manifest. Phase 2 adds local regeneration, versioning, and re-export. Phase 3 adds character/style/sticker/prop/prompt libraries and long-term asset version control.

## Delivery checklist

- Both approval decisions are explicit and recorded.
- Every output maps to one manifest entry; no guessed filenames.
- Primary individual files preserve the expanded crop's native dimensions, are RGBA PNGs, and are transparent.
- Preview and Manifest are delivered together.
- Partial regeneration preserves unaffected manifest entries.
- Failures, missing tools, and uncertain visual analysis are visible to the user.
- `FULL_BODY` entries use `9:16`; `PROPS` entries contain no person; these fields are verified from the manifest.
