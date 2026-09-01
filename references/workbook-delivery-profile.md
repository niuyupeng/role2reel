# Workbook delivery profile

Use the workbook as the review and audit surface; use the text export as the direct handoff to a video model.

## Core sheets

1. **最终可复制提示词** — one row per shot, with a formula-generated five-field block in the exact copy-paste contract. Keep stable source shot ID, generation segment, local label, editorial duration, and provider duration in visible columns.
2. **镜头时长与逐秒节拍** — dialogue/action/visual/camera/reaction floors, hard floor, recommendation, editorial and provider clocks, relation, evidence level, confidence, flags, and manual confirmation.
3. **连续性与素材锁定** — character, wardrobe, prop, location, axis, lighting, sound bridge, source asset revision, state handoff, and explicit unknowns. Unknown assets remain unknown; they are not filled from nearby rows.
4. **审校与修订记录** — source evidence, author decision, conflict, repair, before/after, and lock status.

Keep **关键帧图片提示词（按需）** only for shots that need a first/last frame or composition check. Keep **复杂动作预演（按需）** for collision, combat, vehicle, mechanical, transformation, or multi-person occlusion risks. These sheets are not mandatory for every shot.

## Workbook rules

- The source storyboard's original shot numbers and omitted/deleted IDs remain visible; do not renumber away a gap without author approval.
- Editorial total and provider generation total are separate totals. A provider segment can be longer than its cut because the output will be trimmed.
- Preserve source plot, dialogue, character relations, and scene order. “Re-estimated” means timing has been reconsidered, not that story content may be invented.
- A plan or re-estimated workbook without final-cut measurements or recorded audio is low-evidence. Mark it and leave a human confirmation field.
- Formula cells may compose the final block, but the exported text must be opened and audited as text as well.
- Before delivery, render representative top and bottom ranges of every sheet, inspect for clipped text or formula errors, reopen the exported workbook, and run the copy-paste auditor on the text export.
