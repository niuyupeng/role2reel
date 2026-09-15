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

## Trademarks and product facts

Role2Reel is not affiliated with, endorsed by, or sponsored by ByteDance, Dreamina, Jimeng, Seedance, OpenAI, or either community project above. Names and trademarks belong to their respective owners.

Video-model modes, limits, and interfaces change. Any provider-specific fact should be checked against the provider's current authoritative documentation or interface at the time of use.
