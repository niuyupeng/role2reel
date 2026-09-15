# Story–character–dialogue round trip

Use this route when the author wants a coherent story built through specialized
stages, or wants natural dialogue without losing the story during model handoff.
For a single typo or a narrow line edit, use only the applicable local contract.

## Establish the job and protect the author's contribution

Separate the requested deliverable from ideas discussed in supplied notes.
Meeting suggestions, technical hypotheses, commercial possibilities, and old
assistant proposals are not current decisions. Preserve attribution and uncertainty
with [humanization.md](humanization.md). Unknown tool names remain unresolved.

For an end-to-end story, record a compact brief using
[story-workflow.yaml](../assets/templates/story-workflow.yaml): premise, desired
audience experience, duration, ending, principal characters, production constraints,
author-protected beats, and permitted changes. Keep protected content identifiable
by source revision and beat/line ID, not by a vague instruction to retain the tone.
Protect its dramatic function as well as its wording where applicable.

Do not merge separate briefs. A two-minute demonstration and an existing longer
film can have different casts, lengths, endings, and approval states.

## Check story capacity before adding material

List the active characters, locations, conflicts, setups, and payoffs. For each
addition, ask which existing beat it serves and what screen time, explanation,
transition, or unresolved obligation it introduces. Estimate speech, action,
comprehension, and holds rather than dividing duration by word count alone.

When the story is overloaded, offer a concrete tradeoff: remove or combine a
function, simplify a subplot, or ask to extend the duration. Do not silently delete
an author-protected joke, emotional transition, or unresolved ending. There is no
universal cast limit or compulsory plot formula. A new character is not the default
solution to an underdeveloped conflict.

## Coordinate modules with explicit handoffs

| Stage | Input | Output and boundary |
|---|---|---|
| Story structure | Brief and supplied facts | Provisional causal outline, missing motivations, capacity risks; new biography remains a proposal |
| Character development | Outline demands and existing canon | Applicable locked/approved character sources; contradictions returned to author, not rewritten silently |
| Return to story | Outline plus approved character resources | Revised scene goals, choices, causes and consequences, with a localized change map |
| Dialogue surface | Locked scene state and relevant character evidence | Candidate wording for named turns only; no new plot, knowledge, speakers, or off-screen actions |
| Scene reintegration | Chosen candidate and exact current source | Updated scene plus continuity and read-aloud review; downstream artifacts invalidated where changed |

Use [life-paths.md](life-paths.md) when consequential prehistory must be created,
[character-engine.md](character-engine.md) for its compilation and retrieval, and
[scene-dialogue.md](scene-dialogue.md) for playable exchanges. Do not replace these
with a second biography system. An outline may pose questions before a biography
is approved; it must not canonize an unapproved answer.

Do not send an entire long biography to a surface-polishing model by default.
Retrieve the exact approved cognition, relationship, knowledge, and expression
evidence relevant to the turns. Insufficient evidence is an unresolved input, not
permission to invent a personality. Judge richness by causal and dramatic usefulness, not page or character count;
a figurative request for “forty pages/forty thousand characters” is not a quota. There is no
default length minimum. Preserve content-sufficiency review and separate
author approval before formal canon compilation.

## Local dialogue adapter

For the executable local extraction/reintegration helper, read [dialogue-local-workbench.md](dialogue-local-workbench.md). Use it to reduce repeated copying and stale-source merges; still perform the semantic and whole-scene reviews below.

Use [dialogue-handoff.yaml](../assets/templates/dialogue-handoff.yaml) when a
different model, skill, or manual copy/paste step polishes dialogue. This is a data
contract, not a promise that any external service is installed or has been called.
An unavailable adapter may produce a labeled manual handoff packet; it must not
claim an external result. Keep private story material local unless the authorized
workflow includes transmission to that service.

The packet contains:

- exact source file, revision and SHA-256; scene, beat, and turn IDs;
- only the target turns as editable text, with speaker and recipient fixed;
- enough preceding and following context to resolve pronouns, interruptions,
  shared knowledge, and the next response, marked read-only;
- the propositions, their certainty/ownership, current objective and tactic,
  character knowledge boundaries, relevant approved resource IDs, and required
  scene exit state;
- author-protected material, prohibited additions, and timing constraints.

Request the smallest useful candidate set, normally one rewrite and a reason for
any unresolved ambiguity. Keep a second option only for a meaningful creative
tradeoff. Do not routinely require slang, particles, stutters, catchphrases, short
sentences, or more jokes. They are choices governed by the person and situation.
Perform the nonverbal/mute pass where it applies. Longer necessary speech is valid.

Reject a candidate that changes a speaker, grants knowledge, reverses a motive,
adds an event, or breaks the response it must lead into, even if it sounds smooth.
Improving readability is not disabling safety or assuming a speculative model
mechanism. No model is the compulsory 'human-sounding' backend without relevant
comparative evidence.

## Reintegrate, then judge

1. Reopen the bound source. If its revision or hash changed, rebase the packet;
   do not paste a stale candidate into a newer draft.
2. Map each selected rewrite to its target turn. Show before/after and preserve
   all non-target material. If a neighboring change is necessary, identify it as
   a separate proposed edit, not a hidden collateral rewrite.
3. Re-read the complete affected scene and both boundary handoffs. Check speaker,
   facts, chronology, motivation, location, knowledge, props, callbacks, and entry/
   exit states. A new location obligation can invalidate later scenes too.
4. Read the scene aloud, not only the isolated line. Review response timing,
   emotional progression, playable subtext, and whether compression removed a
   necessary word or setup.
5. Record human choice separately from machine checks. Do not manufacture approval.
   For production-bound humanization, apply the existing source/ledger/draft audit
   and approval contract; this packet does not replace it. Update the downstream
   revision map so an old screenplay or storyboard cannot masquerade as the new one.

Limit revision rounds to a stated task budget. Stop when the author accepts the
specific revision, or when the permitted edits no longer address the remaining
issue. Report that issue and the required choice. 'Keep making it better' is not
permission for endless full-script rewrites or self-scored perfection.

## Complete the requested artifact

Before claiming this workflow was applied end-to-end, inventory what actually ran: source brief, causal framework, character evidence/development, story revision, localized wording candidates, reintegrated full draft, and whole-scene review. Cite actual artifacts. Mark missing stages as missing, not passed by invoking the skill's name. An exploratory draft may be useful without proving deep-biography completion or human acceptance.

For a request to generate a complete story, the framework is an intermediate checkpoint, not the final deliverable. Continue through character-supported choices, story drafting, localized dialogue polishing, and whole-scene reintegration unless a material author choice blocks progress. Missing consequential canon must remain a stated uncertainty; it must not be fabricated. An explicitly requested exploratory screenplay may use labeled scene-local proposals without claiming formal biography approval or canon compilation.

Keep a compact `character_depth_review` in the workflow record: outline needs, character evidence, consequential gaps, proposed repairs, and actual review status. Use the content-sufficiency criteria in life-paths.md; do not turn “rich” into a new numerical quota. Frame review checks capacity; character review checks causes; dialogue review checks playable expression; final review checks that changes survived reintegration. Success at one stage does not prove success at the next.

## Test the benefit, not the amount of process

Use [quality-gates.md](quality-gates.md) and the existing
[calibration record](../assets/templates/calibration-record.yaml). For this route,
compare the same source and permitted changes under the pinned current workflow
and the round-trip workflow. Add an external-adapter arm only if it actually ran;
record its backend/version, settings, context, prompts, human time, and cost when
available. Keep those differences visible rather than claiming a controlled model
comparison when several variables changed.

Hard failures include altered protected content, stale-source reintegration,
speaker/knowledge drift, and broken causal or spatial continuity. Blind human
review evaluates adoption, editing burden, read-aloud fluency, character
distinction, and scene effectiveness. No lint, template, or model self-score proves
that the updated workflow is stronger. FT-23–FT-25 in
[the behavioral cases](../tests/forward/cases.json) specify regressions for this
route; their existence does not mean those runs or human reviews have occurred.
