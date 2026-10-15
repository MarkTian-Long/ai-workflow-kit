# Provenance and maintenance

## Current method sources

The validating workflow absorbs concepts rather than executing external frameworks:

| Source | Frozen commit | License | Absorbed concept |
| --- | --- | --- | --- |
| `stanford-oval/storm` | `fb951af7744dab086e34962e9bc6fe878e145f83` | MIT | multi-perspective questions, evidence curation, structure before conclusion |
| `stanfordnlp/dspy` | `4ed377ee9110e912d4f5e1be43b317b87455053c` | MIT | frozen tasks and metrics for comparing candidate methods |
| `promptfoo/promptfoo` | `679e7ecb64a2e09042b009b549b81dc0d0b983bb` | MIT | evaluation matrices across method, model, reasoning, quality, time, and cost |

The upstream entries above are concept provenance only; upstream code and frameworks are not runtime dependencies.

## Validation and transfer boundary

Status remains `validating`: this method is available for scoped use, while effectiveness and downstream benefit remain under observation. This local governance label is not a host enable/disable switch. Private task receipts are omitted; counts do not authorize promotion or prove recipient adoption. Derive necessary parts, relationships and conditions before selecting solutions; mixed tasks use the method only for unresolved analysis. The current shared source includes the bounded correction; no private validation history is redistributed.

## Upgrade and downgrade

Review upstream only when a real task exposes a gap, a frozen source materially changes, a license or security boundary changes, or two validation rounds show no net benefit. Stars are a discovery signal, not an adoption gate.

For an upgrade:

1. freeze the new version or commit;
2. inspect the relevant diff, license, dependencies, network behavior, telemetry, and data flow;
3. compare the revised method on eligible frozen tasks;
4. preserve the previous SKILL.md as the rollback baseline until validation closes.

Narrow or downgrade when the trigger over-matches, perspectives repeat one another, user correction or rework does not fall, or time, token, coordination, privacy, or maintenance cost rises without decision value. Retire when no real consumer remains or an existing governed mechanism fully covers the result.

Do not install the source frameworks, upload internal material, change global model defaults, or promote multi-agent execution merely because this skill references those projects.
