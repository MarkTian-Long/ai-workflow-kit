---
name: structured-analysis-discussion
description: Frame consequential open-ended decisions, research, or diagnosis before choosing solutions when alternative problem structures, perspectives, or counterarguments matter. Exclude short factual answers, personal preferences, and deterministic execution; in mixed tasks, apply only to the unresolved analysis.
---

# Structured Analysis Discussion

Status: `enabled`. Use on matching tasks; effectiveness evidence is recorded separately.

Use this skill to improve decision quality without running or installing STORM, DSPy, Promptfoo, or another external framework.

## Route the task

Apply the workflow when either condition holds:

- the question is open-ended, has multiple reasonable interpretations, and the conclusion affects a real decision; or
- research or diagnosis could miss a material requirement, stakeholder, counterargument, dependency, or unknown because the problem structure or the basis for a proposed solution is unresolved.

If neither condition holds, continue normally and do not add process for completeness. In mixed analysis/execution tasks, apply this workflow only to the unresolved analysis; continue clearly specified, authorized work. Preserve fixed user choices rather than replacing the requested product or scope.

## Work toward a decision-ready answer

1. Separate the desired outcome, current problem, and proposed solution; preserve fixed user choices, deliverable, and authority boundaries. Freeze the decision, success criteria, and one to three questions that must be answered.
2. Before recommending solutions, choose a decomposition suited to the problem and identify necessary capabilities or parts, their relationships, dependencies, and conditions. Treat the structure as a hypothesis to check, not an exhaustive model. When context or relationships could change the decision, orient the reader with a compact overview visualization that locates the current question or feature before local detail; choose a form suited to those relationships and mark unknowns. Choose two to four perspectives only when they can change the conclusion; include the strongest credible counterargument or overlooked consumer. Do not reuse a case-specific checklist as the default structure or create Agent roles merely to simulate disagreement.
3. Gather only decision-relevant evidence. Keep verified facts, public evidence, analysis, recommendations, and unknowns distinct; look for evidence that could falsify the leading view.
4. Before drafting, check how each viable option covers the necessary conditions, including gaps and deliberate tradeoffs. Organize consensus, disagreement, unknowns, and evidence or events that would change the conclusion. For diagnosis, distinguish existing coverage, execution omissions, actual mechanism gaps, and insufficient evidence; revise at the lowest sufficient level. When maintaining reusable guidance, state the transferable relation and conditions, then check another task type or counterexample within its stated scope.
5. Lead with the answer and required decision or action. Put research process and production detail after the reader path.
6. Stop expanding when new perspectives repeat existing claims, available evidence cannot change the decision, or merge and context costs exceed expected value.

When workflow structure or upstream/downstream dependencies could change a diagnosis or product/feature decision, including cross-role handoffs and human/AI/system collaboration, read [references/process-and-interaction-analysis.md](references/process-and-interaction-analysis.md) during steps 2–4. Reconstruct the evidenced current interactions, distinguish actual from required inputs/outputs, and inspect conditions on connections as well as activities. Use branches, joins, feedback and repeated interactions when supported; do not force a serial chain or make drawing a prerequisite for every analysis. Keep hypothetical and proposed flows distinct from current facts.

For technical faults with unclear causes across components or repeated failed fixes, read [references/fault-diagnosis.md](references/fault-diagnosis.md) during steps 2–4. Use a bounded boundary trace and a falsifiable hypothesis; a known single-point fix or authorized recovery remains direct execution.

Use subagents only when the task can be split into genuinely independent evidence tracks and current instructions authorize delegation. Give each the minimum context; keep shared-control writing and final arbitration with the coordinating agent.

## Validate rather than assume benefit

Continue using this enabled Skill within its stated scope. Authorized installation or improvement and the required checks are sufficient for ongoing use; do not wait for a task count, fixed observation window or a separate promotion approval. An explicit temporary trial keeps only its stated scope and end condition.

When a real task supplies a concrete useful finding, failure, user correction or added burden, record that observation in the task's existing record when relevant. Separate correct triggering/execution, method help and the actual decision or delivery result; do not claim benefit from invocation counts or passing checks alone. Do not create per-use logs for short tasks.

For actual over-triggering, repeated omissions, poor results or unnecessary coordination cost, correct execution or propose a narrower method, merge or disable under the applicable authority. Preserve sources and rollback; do not automatically delete the Skill or broaden its trigger. Missing long-term benefit evidence alone does not suspend its use.

Read [references/provenance-and-maintenance.md](references/provenance-and-maintenance.md) only when reviewing the method's sources, version, promotion, upgrade, downgrade, or retirement.
