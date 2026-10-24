# Bounded fault diagnosis

Use within analysis steps 2–4 when the cause is unclear across components, data/configuration propagation may be wrong, or previous fixes failed. Use the smallest relevant part; this is not a required sequence for every bug. Restore current use through a known safe workaround when authorized, then continue only the persistent repair within scope. A known local defect can be fixed directly.

## Locate the first divergence

Choose one failing example and, when useful, a nearby working case. State the expected and actual behavior, the input and environment that matter, and whether the failure reproduces. Keep an intermittent or unavailable reproduction explicitly uncertain.

Follow the relevant data, state or configuration through the implicated boundaries: for example, input → parsing → normalization → service → rendering. Compare what enters and leaves each boundary and locate the earliest evidenced divergence. Do not inspect unrelated components merely to complete a diagram.

Add temporary observations only where existing evidence cannot distinguish the candidates. Prefer types, counts, status, presence/absence, or a synthetic input. Do not dump environment variables, credentials, request bodies or customer content. A configuration key being present does not establish that its value is valid. Remove temporary instrumentation when it has no remaining consumer; retain necessary findings in the existing task record.

## Test a discriminating hypothesis

Write one falsifiable explanation at a time: “If X changes at boundary Y, observation Z should differ; if Z does not differ, reject or revise X.” Select the smallest probe or reversible change that separates it from a plausible alternative. A temporary probe is not automatically the final repair.

Do not combine unrelated fixes in that experiment. A successful change supports only the behavior actually tested; identify the implicated cause and affected scope from evidence rather than from the number of failed attempts. If the result contradicts the hypothesis, update the explanation before trying another patch. Missing evidence can justify one targeted observation or a concrete blocker; it does not prove an architectural defect.

## Repair and stop

Apply the smallest sufficient persistent repair, then rerun the original failing example and the neighboring behavior that could plausibly regress. Use existing checks when suitable; do not run the whole system solely for a fresh completion claim. A workaround, passing probe, persistent repair and deployment are separate results.

Report what failed, the evidenced divergence, the change, and the behavior actually verified. Stop when the scoped goal and required checks pass. Any further investigation needs an unresolved requirement, observed failure or specific risk.

Counterexample: if one editable label is wrong and its intended text is specified, change and check that label directly. No boundary map, hypothesis report or root-cause gate is needed.
