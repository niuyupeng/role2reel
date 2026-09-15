# Third-Party Notices

Role2Reel includes independently implemented material and the explicitly identified adaptation below. Repositories listed as design-only references have no copied source code, prose, prompt examples, templates, test cases, or assets bundled.

## Design references (not bundled)

### Seedance 2.5 Video Director

- Source: <https://github.com/liyue-aigc/seedance-2-5-video-director>
- Reviewed commit: `ad0e68ba6ce24fb9ae9c67c9276061cef37663f1`
- License: MIT
- Copyright (c) 2026 liyue-aigc

Design ideas reviewed included task-mode routing, reference-asset role contracts, continuity locks, causal timelines, and layered validation. Role2Reel independently re-expresses these at a provider-neutral level and deliberately omits copied product-limit tables and provider examples.

### Video Storyboard Generator

- Source: <https://github.com/OYYH-Apple/video-storyboard-generator>
- Reviewed commit: `4ccbe8abd80b9a44da43024aec11b2aa41b2bbb4`
- License: MIT
- Copyright (c) 2024 Video Storyboard Generator Contributors

Design ideas reviewed included modular storyboard fields, stable character/asset descriptions, output depth choices, and multi-layer continuity review. Role2Reel does not inherit universal duration, camera-movement, narration, framing-density, onboarding, or auto-save rules.

## Additional design review: natural dialogue (2026-09-15)

- [blader/humanizer](https://github.com/blader/humanizer), reviewed `SKILL.md` at commit `9862685f575c65a8247f90369951df1b3416e3d6`; repository LICENSE: MIT, Copyright (c) 2025 Siqi Chen. Consulted concepts: sample-led editing, preserving supported uncertainty, and identifying unprompted defenses. No source text, examples or executable code incorporated. Its punctuation bans and blanket pattern triggers are not adopted.
- [spuvr/humanizer](https://github.com/spuvr/humanizer), reviewed `SKILL.md` at commit `0d5a8cf82bc36232b79afafd4993ca4f8226c8bd`. Repository license API returned 404 during review; redistribution permission not verified. Consulted only general ideas about redundant explanation and reader inference. No files or prose copied. Its fixed punctuation limits, default opinionated voice and unsupported specificity are not adopted.

The resulting `references/natural-dialogue-repair.md` is independently worded for Chinese scene-level editing. No external install, dependency execution, detector validation or demonstrated artistic improvement is implied.

## Incorporated MIT-licensed material

### anti-defensive-writing-Skill — scoped film adaptation

Source: <https://github.com/Adkid-Zephyr/anti-defensive-writing-Skill>

Reviewed commit: `102c8b21acf5eda3a0aef3d9779a65db646c8980`.
Source file: `skills/anti-defensive-writing/SKILL.md` (Chinese, read in full).
Adapted section: `references/natural-dialogue-repair.md`, “anti-defensive-writing-Skill 的影视适配”.
Adaptation changes: paper-centric narrative organization becomes scene focus and causal editing; no blanket ban on acknowledging defeat, no suppressed negative evidence, no changes to author-approved outcomes or factual reporting. The original skill is not globally installed or executed.

MIT License

Copyright (c) 2026 Adkid-Zephyr

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

If a future contribution incorporates or adapts third-party material, it must identify the exact files or sections, preserve required copyright and license notices, and update this document.

## Story-prose design comparison (2026-09-15)

The following source files were read for design comparison, not installed or executed. GitHub repository metadata reported MIT for all five repositories below. No new upstream prose, examples, assets, or code are bundled in `references/story-prose-craft.md`; its wording and demonstration are independently authored. License metadata is not a quality rating.

| Source and reviewed revision | File inspected | Adopted idea / excluded prescription |
|---|---|---|
| [Adkid-Zephyr/anti-defensive-writing-Skill](https://github.com/Adkid-Zephyr/anti-defensive-writing-Skill), `102c8b21acf5eda3a0aef3d9779a65db646c8980` | `skills/anti-defensive-writing/SKILL.md`, full | Extend the existing scoped adaptation to story-body review; exclude selective reporting and compulsory victory. Existing MIT adaptation notice above remains applicable. |
| [blader/humanizer](https://github.com/blader/humanizer), `9862685f575c65a8247f90369951df1b3416e3d6` | `SKILL.md`, targeted sections on staging, voice and workflow | Diagnose paragraph-level repetition and reader-unprompted contrast; do not import punctuation bans or automatic one-pattern judgments. |
| [greyhaven-ai/claude-code-config](https://github.com/greyhaven-ai/claude-code-config), `d093a5a93cf483ed055b2a4fefcad3456ffd855d` | `grey-haven-plugins/creative-writing/skills/creative-writing/references/fiction-writing.md`, full | Distinguish scene from summary, response from event, and viewpoint knowledge; reject universal act percentages, adjective quotas and mandatory disaster. |
| [xcrrr/claude-skills](https://github.com/xcrrr/claude-skills), `145342ceff6318d2f5ffe8f95473fecc8b27d1e9` | `skills/writing/storyteller/SKILL.md`, full | Let immediate reader interest and selective detail guide attention; do not require wounds, heroic transformation, a fixed sensory count or two functions per line. |
| [d-wwei/great-writer](https://github.com/d-wwei/great-writer), `266bfd6ec26e5dedd23cd4b569e034b50b58d463` | `modes/creative-writing.md`, full | Genre-sensitive prose review and narrator-specific observation; exclude always-action openings, universal phrase blacklists and removal of user audience constraints. |

Additional search screening, not full skill audits: `gtmagents/gtm-agents` storytelling is product-marketing/CTA oriented and was not adopted; `AliDujie/storytelling-with-data` concerns data presentation; `Zzzeen2552/storytelling-mastery-skill` was not accepted on its “master” positioning alone. A search hit under NVIDIA/SkillSpector was a test fixture containing instruction-override text, not a writing-method recommendation, and was excluded. Search coverage is not an exhaustive inventory of GitHub. Self-authored demonstrations and structural tests do not establish measured artistic improvement.

## Expanded writing review: titles, fiction, screenplay and content (2026-09-15)

This pass extends the earlier story-writing review rather than claiming to have searched every repository. Three authorized AI reviewers inspected the project draft independently for naming, fiction and screenplay concerns, then re-read the revised draft. They are not real-world professional authors, award recipients or human acceptance reviewers. Private manuscripts and review artifacts are not distributed with this skill.

- [JeroTan/novel-writer-english — namecraft](https://github.com/JeroTan/novel-writer-english/blob/6d836f23281e240eed36d50529424e086c8ff42d/src/skills/writing-techniques/namecraft/SKILL.md): full file read by title reviewer and main editor. GitHub metadata reports MIT. Independently apply naming purpose, tone, canon fit and spoiler checks; omit fantasy generators, English sound prescriptions and compulsory candidate counts.
- [wgwtest/novel-writing](https://github.com/wgwtest/novel-writing/tree/c57b5c6b35d30d692a06c7fe9cc030bd4ea7af14/novel-writing): fiction reviewer read full `SKILL.md` and `references/revision-checklist.md`; main editor read the latter in full. GitHub metadata reports MIT. Independently apply reader anchoring and concrete location/problem/consequence review; do not import its full production infrastructure or chapter quotas.
- [ComposioHQ/awesome-claude-skills — content-research-writer](https://github.com/ComposioHQ/awesome-claude-skills/blob/be2a406907dbc61b73e6827ded415c96139d13a2/content-research-writer/SKILL.md): main editor read full file. License metadata was null; redistribution permission not confirmed. General concepts reviewed: source-grounded hooks, section feedback and author voice. No source wording, examples or templates copied; sample numbers and attributed quotes are not treated as verified evidence. Do not impose CTA or informational-article format on biographies.
- [kaigani/codeywood — screenplay-writer](https://github.com/kaigani/codeywood/blob/01f28c9d3927a69db4384b42621f9101de35859e/skills/core/screenplay-writer/SKILL.md): screenplay reviewer and main editor read full file. License was not verified; main editor's metadata check also returned null. General concepts reviewed: visible action and character-specific read-through. No text or templates copied. Reject universal winners-per-exchange, paragraph-per-shot, page-to-minute timing and a prohibition on needed structural revision.
- [hesreallyhim/naming-fork](https://github.com/hesreallyhim/naming-fork/tree/56e05a7c2c63cbaf118b1902bcc557fe09436c4c): title reviewer read `SKILL.md`, `anti-patterns.md` and `evaluation.md`, with MIT license observed; main editor confirmed metadata and revision. Reviewed as a contrast case: brand naming and literary titles are different deliverables. No source material bundled. Do not import domain/trademark work, English length limits, numerical rankings, mandatory waiting or claims that AI cannot invent names.

The new title and cross-character review sections in `references/story-prose-craft.md` are independently worded. Behavioral observations came from actual draft review, not upstream popularity or automated text-pattern scores. No broader empirical writing-quality improvement has been established.

## Recursive revision design review (2026-09-15)

[justinwetch/Skill-RSI](https://github.com/justinwetch/Skill-RSI), repository main observed at `6baf57e9e37d80431ec7132fca71bad251cdcc30`: reviewed README sections describing a baseline, localized challenger, comparison evidence and retained history. This is conceptual design comparison, not installation, execution, a source-code audit, or measured validation of Role2Reel. GitHub's license endpoint returned 404; redistribution permission was not established. No upstream text, examples, templates or code are included. `references/recursive-story-revision.md` is independently authored. Do not assume the author's unresolved acronym “RIS” names this project. Do not import unattended runs, numerical source quotas, model judges as human acceptance, or automatic publication of private manuscripts.

Follow-up after the author confirmed RSI (2026-09-15): read the complete [HOW_IT_WORKS.md](https://github.com/justinwetch/Skill-RSI/blob/6baf57e9e37d80431ec7132fca71bad251cdcc30/docs/HOW_IT_WORKS.md) at the same pinned revision. The independently written writing adaptation adds stable-task regression protection, inconclusive outcomes, and scoped failure memory. This supersedes the unresolved-acronym status above, not its historical review record. No upstream code or wording is bundled, and no Skill RSI software run or independent quality comparison is claimed. License permission remains unverified.

## Trademarks and product facts

Role2Reel is not affiliated with, endorsed by, or sponsored by ByteDance, Dreamina, Jimeng, Seedance, OpenAI, or the community projects above. Names and trademarks belong to their respective owners.

Video-model modes, limits, and interfaces change. Any provider-specific fact should be checked against the provider's current authoritative documentation or interface at the time of use.
