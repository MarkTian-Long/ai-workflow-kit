# ai-workflow-kit

[中文](README.md) | **English**

Small tools and methods for working with AI. Pick one for the task you want to complete; each can be used independently of a full Harness setup.

| What you want to do | Start here | Input and result |
| --- | --- | --- |
| Save conversation outcomes, archive, or hand work over | [session-closeout Skill](skills/session-closeout/SKILL.md) | A defined scope and task materials become checked artifact links, open items, and actual operation results. Native conversation tools are a conditional dependency. |
| Think through an open problem before deciding | [structured-analysis-discussion Skill](skills/structured-analysis-discussion/SKILL.md) | Goals, constraints, and evidence become necessary conditions, counterexamples, unknowns, and proposed actions. Use it for unresolved analysis. |
| Create document flow, handoff, sequence, state, or ER diagrams | [Document visuals Skill](skills/create-document-visuals/SKILL.md) · [Setup and usage](docs/document-visuals.md) | Editable sources, offline SVG/PNG, and geometry checks. Native families use a separate fixed local Mermaid engine. |
| Prepare a handoff without installing a Skill | [One-page handoff SOP](sops/session-handoff.md) | Check existing materials, adapt the request, and save a minimal handoff. |
| Make a report that is readable, comparable, and traceable | [HTML report template](templates/html-report/README.md) | Edit the blank template or synthetic example and open it in a desktop browser. Sections can be added or removed. |
| Explain steps, roles, or state changes | [Flowchart guide and examples](diagrams/flowcharts/README.md) | Three editable Mermaid diagrams and offline SVGs, with a creation SOP. Choose the relevant example. |
| Convert local documents into searchable Markdown | [Document conversion tool](scripts/document-conversion/README.md) | Explicit local input and Markdown output. Install the declared dependencies separately; no OCR. |
| Inspect a PDF by page, then extract selected pages | [PDF page reader](scripts/pdf-on-demand/README.md) | Local page index, page selections starting at 1, and low-text or no-text warnings. No OCR. |
| Build a local demo that can be reviewed against requirements | [Requirements-to-demo SOP](sops/prd-to-demo.md) | A requirements baseline, behavior mapping, real browser checks, and clear simulation boundaries. |
| Bring web research back into an ongoing task | [Web research handoff SOP](sops/web-research-to-local.md) | Define the decision, check sources and counterexamples, then merge verified results into the authoritative materials. |
| Publish approved local assets to GitHub on repeat runs | [Prepare snapshots from an explicit catalog](scripts/asset-sync/README.md) | Declare sources and destinations, freeze, compare, review, and read back the complete result. An authorized operator performs network writes. |

## Using an asset

Read an SOP directly. For templates, diagrams, and scripts, keep the entire selected directory and the root [LICENSE](LICENSE), then follow its instructions. For a Skill, first ask your agent to read the selected SKILL.md explicitly and try it in an isolated task. If installation is needed, copy only the complete selected Skill directory to a location supported by the host. Preserve and review any existing Skill with the same name before applying your adaptation.

The three Skills allow the host to select them when applicable. File presence, discovery, selection, and successful execution are separate checks. The analysis Skill's `validating` status means that method benefits are still being observed; it can be used within its stated scope. This label is not a host enable/disable switch. The host's effective rules and the user's current authorization take priority; these files do not grant tools or permissions.

This page provides an English overview. Most linked Skills, SOPs, and detailed guides currently use Chinese; the scripts and file paths remain the same in either language.

## Contents and maintenance

Assets are organized under `skills/`, `sops/`, `templates/`, `diagrams/`, and `scripts/`. Examples stay with their asset. Reusable requests usually remain in the relevant SOP or Skill.

This repository receives reviewed publication snapshots. Each asset has one authoritative editing source and is exported through an explicit catalog. Make revisions at that source first. Before adding an asset or destination, check provenance, redistribution rights, dependencies, and data scope. Routine changes within the approved scope can be published after the applicable checks. Unchanged content produces no empty commit; missing sources do not imply deletion; remote conflicts must be resolved first.

This repository does not automatically install its contents or enable background scheduling. Personal profiles, account settings, customer materials, actual reports, logs, and the publisher's internal catalog are excluded from the distributed source.

For basic collaboration rules, context routing, and file lifecycle management, start with [harness-starter](https://github.com/MarkTian-Long/harness-starter), then choose individual assets here as tasks require them. Keep personal preferences and machine adaptations in your own private layer. Pin a commit when adopting an asset and check its dependencies and local rules.

Maintainers can use the [asset selection SOP](sops/asset-selection.md) to reuse existing manual audits and real task evidence, adding only provenance, licensing, independent usage requirements, and publication differences. Counts of discovered files or published assets do not establish long-term benefit.

Original content is provided under the [MIT License](LICENSE). Third-party dependencies retain their respective licenses. See [ATTRIBUTION](ATTRIBUTION.md) for provenance and [VALIDATION](VALIDATION.md) for actual checks and limitations.
