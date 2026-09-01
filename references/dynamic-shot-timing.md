# Dynamic shot timing

Dynamic timing is a production contract, not a fixed-length formatting trick. Estimate each shot from what the audience must be able to see, hear, understand, and feel, then keep the editorial cut length separate from the provider's generation length.

## Three clocks

- **Performance clock**: the time a person, object, line, reaction, or camera move needs to happen credibly.
- **Editorial clock**: the time the finished cut holds the shot. It may include a readable reveal, a reaction, a transition, or a deliberate hold.
- **Provider clock**: the duration requested from a video model. It may be longer than the editorial shot and later trimmed; it must never stretch a short action into a different dramatic event.

Never impose a universal 3-second, 5-second, or provider-default shot length. A shot can be shorter than a model's minimum generation duration when the delivery record explicitly declares long-generation/short-trim. A long spoken thought or physical consequence must not be compressed merely to fit a template.

## Hard floor

For each shot, record the following lower bounds in seconds:

1. `dialogue_floor`: measured or estimated natural speech plus breath where audible;
2. `action_floor`: prepare or judge → approach → contact/trigger → force/state change → recovery/end;
3. `visual_floor`: enough time to identify space, subjects, text, or a decisive prop;
4. `camera_floor`: time for the declared pan, track, rack, crane, or reveal to complete;
5. `performance_hold`: comprehension, involuntary response, or aftermath that would otherwise be cut off.

`hard_floor = max(dialogue_floor, action_floor, visual_floor, camera_floor, performance_hold)` for sequential duties. For simultaneous duties, document the overlap and calculate the longest causal path rather than blindly adding every component. Use:

`recommended_duration = hard_floor + rhythm_slack + evidence_adjustment`.

If the requested target is below the hard floor, emit `DURATION_INFEASIBLE` and propose a narrow repair: shorten the duty, split the shot, change the camera task, or move information to a neighboring shot. Do not silently speed-ramp dialogue or erase the result of contact.

## Beat and relation fields

Declare whether dialogue, action, visual reveal, and reaction are `sequential`, `parallel`, `mixed`, `voiceover`, or `none`. State the shot's beat duty and its `state_in`/`state_out`. A slow reveal may have no dialogue; a dialogue shot may stay on the listener. Add `REACTION_MISSING`, `READABILITY_TOO_SHORT`, `ACTION_UNDERCRANKED`, `DIALOGUE_TOO_FAST`, `SPLIT_RECOMMENDED`, or `RELATION_UNCLEAR` when the evidence shows a risk.

## Evidence and calibration

Keep the source evidence visible. Use these weights only as priors, never as automatic truth: `final_cut 1.00`, `director_approved 0.85`, `edited_accepted 0.70`, `planned 0.25`, `rejected 0.00`. A user-uploaded planned or re-estimated board is useful evidence but is not a final-cut measurement. Mark low evidence as `CALIBRATION_LOW_EVIDENCE` and request human confirmation for production lock.

## Timing handoff

The timing plan owns editorial duration, generation duration, floors, evidence, flags, and confidence. The paste-ready prompt owns only the executable shot description and time-coded beats. The downstream provider adapter may choose a compliant generation duration and trim plan, but may not rewrite plot, character behavior, shot duty, or upstream timing rationale.

Use [copy-paste-prompt-contract.md](copy-paste-prompt-contract.md) for the fixed Chinese output shape and [workbook-delivery-profile.md](workbook-delivery-profile.md) for the spreadsheet layout.
