---
name: structured-analysis-discussion
description: Frame consequential open-ended decisions, research, or diagnosis before choosing solutions when alternative problem structures, perspectives, or counterarguments matter. Exclude short factual answers, personal preferences, and deterministic execution; in mixed tasks, apply only to the unresolved analysis.
---

# Structured Analysis Discussion

Status: `validating` (the method remains under evaluation; this is a lifecycle label, not a host enable/disable switch). Use in a host depends on installation, discovery and actual invocation.

Use this skill to improve decision quality without running or installing STORM, DSPy, Promptfoo, or another external framework.

## Route the task

Apply the workflow when either condition holds:

- the question is open-ended, has multiple reasonable interpretations, and the conclusion affects a real decision; or
- research or diagnosis could miss a material requirement, stakeholder, counterargument, dependency, or unknown because the problem structure or the basis for a proposed solution is unresolved.

If neither condition holds, continue normally and do not add process for completeness. In mixed analysis/execution tasks, apply this workflow only to the unresolved analysis; continue clearly specified, authorized work. Preserve fixed user choices rather than replacing the requested product or scope.

## Work toward a decision-ready answer

1. Separate the desired outcome, current problem, and proposed solution; preserve fixed user choices, deliverable, and authority boundaries. Freeze the decision, success criteria, and one to three questions that must be answered.
2. Before recommending solutions, choose a decomposition suited to the problem and identify necessary capabilities or parts, their relationships, dependencies, and conditions. Treat the structure as a hypothesis to check, not an exhaustive model. Choose two to four perspectives only when they can change the conclusion; include the strongest credible counterargument or overlooked consumer. Do not reuse a case-specific checklist as the default structure or create Agent roles merely to simulate disagreement.
3. Gather only decision-relevant evidence. Keep verified facts, public evidence, analysis, recommendations, and unknowns distinct; look for evidence that could falsify the leading view.
4. Before drafting, check how each viable option covers the necessary conditions, including gaps and deliberate tradeoffs. Organize consensus, disagreement, unknowns, and evidence or events that would change the conclusion. For diagnosis, distinguish existing coverage, execution omissions, actual mechanism gaps, and insufficient evidence; revise at the lowest sufficient level. When maintaining reusable guidance, state the transferable relation and conditions, then check another task type or counterexample within its stated scope.
5. Lead with the answer and required decision or action. Put research process and production detail after the reader path.
6. Stop expanding when new perspectives repeat existing claims, available evidence cannot change the decision, or merge and context costs exceed expected value.

Use subagents only when the task can be split into genuinely independent evidence tracks and current instructions authorize delegation. Give each the minimum context; keep shared-control writing and final arbitration with the coordinating agent.

## Validate rather than assume benefit

For the first three substantive eligible tasks, state briefly in the final handoff that this validating skill was used and record, where the current workspace already has a control plane:

- trigger reason and task type;
- material perspective or unknown found beyond a direct-answer baseline;
- major omission, user correction, or structural rework;
- wall-clock and observable token/cost proxy when available;
- extra coordination or maintenance burden.

Do not create a new log for a short task. Do not claim effectiveness from invocation count alone.

After three eligible tasks, retain or narrow the trigger only if evidence shows decision-relevant additions or reduced rework without material quality, time, permission, or maintenance regression. If it repeatedly over-triggers, adds no new evidence, or increases merge/context cost, narrow the description or disable implicit invocation. Remove the skill when no active consumer remains and preserve the retirement reason in the applicable control plane.

Read [references/provenance-and-maintenance.md](references/provenance-and-maintenance.md) only when reviewing the method's sources, version, promotion, upgrade, downgrade, or retirement.
