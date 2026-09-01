# Copy-paste shot prompt contract

The final delivery remains a paste-ready text block. Do not replace it with a table, JSON dump, explanatory paragraph, or provider-specific wrapper.

Every block uses this order:

```text
shot1｜
景别与运镜：
拍摄方式：
画面与动线：
【00:01-00:05】:（拍摄机位）（具体画面内容）
```

The local `shotN` label may restart inside each provider generation segment, while a project workbook keeps the original stable shot ID separately. When several segment prompts are concatenated for review, mark that export as allowing local restarts; a single segment must still have increasing labels. Time-code lines are ordered, non-overlapping, and contiguous within the block. Use one-based display time (`00:01`) when the delivery contract says so; store numeric seconds in the timing plan. In a per-shot clock the first time line begins at the declared display origin; when preserving an upstream segment-relative clock, declare that offset and keep it consistent rather than silently renumbering the source. Every end must be greater than its start, and the last end must equal the block's editorial duration when the block is on a per-shot clock.

`景别与运镜` names shot scale and motivated camera behavior. `拍摄方式` declares the practical or generated capture method, including any long-generation/short-trim instruction. `画面与动线` describes observable blocking, screen direction, state change, sound-relevant action, and the ending handoff. Time-coded lines describe atomic beats, not a prose summary or a list of intentions.

Keep nonverbal beats when the audience can read them. Do not add dialogue merely to fill a time range. If dialogue is present, preserve natural breath and listener reaction. If an action contains contact or force, show cause, approach, contact, result, and recovery across the current block or an explicitly linked neighboring block.

No placeholder, unbound character, invented asset, unexplained reference-image inheritance, or unresolved hard timing conflict may enter a production-locked block. The mechanical auditor checks syntax, timing continuity, duplicate labels, and obvious unfinished text; it cannot judge whether the image is good, the actor is playable, or the story meaning is preserved.
