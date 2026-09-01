# Atomic shot gate

Decide whether a storyboard row is one executable shot or a deliberately designed shot cluster before estimating duration. A longer row is not automatically wrong, and a short row is not automatically atomic.

## Atomicity test

An `ATOMIC_PASS` row has one dominant audience task, one continuous camera/geography contract, one main causal path, and one ending state that the next shot can inherit. Its internal beats may still include preparation, a line, a look, contact, or a brief hold.

Mark `SPLIT_REQUIRED` when the row contains independent camera locations or axes, unrelated cause/result chains, a hidden location change, a subject switch that needs a new audience task, or an action whose contact and result cannot remain readable in one view. Mark `SPLIT_RECOMMENDED` when the row is technically possible but its reaction, joke, reveal, or physical consequence would be clearer as separate cuts.

Mark `CLUSTER_APPROVAL_REQUIRED` when the author intentionally wants one continuous shot or one provider generation unit to carry multiple beats. Record the beat sequence, camera continuity, start/end state, why a cut would harm the intended effect, and the author's explicit decision. Do not stretch a cluster to fit a template; split it or obtain the approval.

## Cause and consequence

For a physical action, keep the readable path `prepare or decide → approach → contact or trigger → force/state change → recovery/result`. For a performance beat, keep `stimulus → comprehension → involuntary response → chosen mask or tactic → visible residue`. A line can share a shot with an action, but it must not make the audience miss the listener's understanding or the object's result.

Only after this gate should the timing plan calculate hard floors and provider duration. `SPLIT_REQUIRED` and unapproved `CLUSTER_APPROVAL_REQUIRED` block production lock; `SPLIT_RECOMMENDED` stays visible as a repair decision rather than being silently ignored.

Use [source-truth-gate.md](source-truth-gate.md) first and record the outcome in [shot-readiness-review.yaml](../assets/templates/shot-readiness-review.yaml).
