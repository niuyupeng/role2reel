# Third-Party Notices

Role2Reel was independently implemented and independently worded. The following repositories were consulted as design references. No source code, prose, prompt examples, templates, test cases, or assets from them are included.

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

## Incorporated MIT-licensed material

None.

If a future contribution incorporates or adapts third-party material, it must identify the exact files or sections, preserve required copyright and license notices, and update this document.

## Trademarks and product facts

Role2Reel is not affiliated with, endorsed by, or sponsored by ByteDance, Dreamina, Jimeng, Seedance, OpenAI, or either community project above. Names and trademarks belong to their respective owners.

Video-model modes, limits, and interfaces change. Any provider-specific fact should be checked against the provider's current authoritative documentation or interface at the time of use.
