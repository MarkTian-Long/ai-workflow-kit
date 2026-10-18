# ai-workflow-kit

[中文](README.md) | **English**

Skills, SOPs, templates, and small tools organized by task. Choose what you want to accomplish, then follow the linked guide to take only what you need. A full Harness setup is not required.

## Choose by task

| What you want to accomplish | Recommended starting point | How to choose and what you get |
| --- | --- | --- |
| Frame a problem and compare options before deciding | [Structured analysis Skill](skills/structured-analysis-discussion/SKILL.md) | Use goals, constraints, and evidence to identify necessary conditions, counterexamples, unknowns, and proposed actions. |
| Save outcomes and hand work to the next conversation | [Conversation saving and handoff](sops/session-handoff.md) | Start with the short SOP; follow its link to the Skill when you need the full workflow, including multi-conversation closeout. |
| Create flow, role, architecture, or state diagrams | [Document diagram guide](docs/document-visuals.md) | Use examples to adapt an existing diagram, or the Skill to create, export, and check diagrams from new requirements. |
| Present findings in a readable comparison report | [HTML report template](templates/html-report/README.md) | Edit the report skeleton and open it in a desktop browser. This is a reading page, not an interactive product demo. |
| Convert an entire local document into Markdown | [Document conversion tool](scripts/document-conversion/README.md) | Convert PDF, Word, and other documents for reading and search. Not all layout is preserved; no OCR. |
| Extract only the PDF pages you need | [PDF page reader](scripts/pdf-on-demand/README.md) | Inspect the page index, then select pages to extract. This differs from whole-document conversion; no OCR. |
| Build an interactive product demo from requirements | [Requirements-to-demo SOP](sops/prd-to-demo.md) | Implement the agreed behaviors, check successful and exceptional paths in a browser, and identify simulated capabilities. |
| Bring web research back into the current project | [Web research handoff SOP](sops/web-research-to-local.md) | Gather decision-relevant evidence, check sources and counterexamples, then merge verified findings into the project's authoritative materials. |

## Using an asset

Read an SOP directly or adapt its task request. For a Skill, first ask your AI assistant to read the selected `SKILL.md` explicitly and try it on a small task. If installation is needed, copy only the complete selected Skill directory to a location supported by the host. For templates, diagrams, and scripts, keep the entire selected directory and the root [LICENSE](LICENSE), then follow its instructions.

Independent use does not mean every item has a separate download package or no dependencies. Preserve and review any existing Skill with the same name before applying an adaptation. File presence, discovery, selection, and successful execution are separate checks. The analysis Skill's `validating` status means its benefits are still being observed; it is not a host enable/disable switch. The host's effective rules and the user's current authorization take priority. This repository grants no tools or permissions and does not automatically install content or enable background scheduling.

For long-term collaboration rules, task files, and recovery foundations, see [harness-starter](https://github.com/MarkTian-Long/harness-starter). Keep personal preferences and machine adaptations in your private layer. Pin a commit when adopting an asset and check its dependencies and local rules.

This page provides an English overview. Most linked Skills, SOPs, and detailed guides currently use Chinese; the scripts and file paths are the same in either language.

## Maintenance and publication

Maintainers first use the [asset selection and deduplication rules](sops/asset-selection.md) to reuse existing evaluations and determine how an asset relates to existing entry points. Then use the [publication preparation tool](scripts/asset-sync/README.md) for approved snapshots. Ordinary users do not need to run the publication tool.

Assets are stored under `skills/`, `sops/`, `templates/`, `diagrams/`, and `scripts/`; these storage types are not homepage categories. Guides, Skills, and examples for the same task share one recommended entry point. Explain the choices there rather than adding a row for each format.

This repository receives reviewed publication snapshots. Each asset has one authoritative editing source and is exported through an explicit catalog. Make revisions at that source first. Merge authorized remote revisions before publishing again; do not overwrite them with an old snapshot. Record any source reconciliation still pending. Before adding an asset or destination, check provenance, redistribution rights, dependencies, and data scope. Routine changes within approved scope can be published after applicable checks. Unchanged content produces no empty commit; missing sources do not imply deletion.

Personal profiles, account settings, customer materials, actual reports, logs, and the publisher's internal catalog are excluded. File counts, publication counts, and passing checks do not establish long-term benefits.

Original content is provided under the [MIT License](LICENSE). Third-party dependencies retain their respective licenses. See [ATTRIBUTION](ATTRIBUTION.md) for provenance and [VALIDATION](VALIDATION.md) for actual checks and limitations.
