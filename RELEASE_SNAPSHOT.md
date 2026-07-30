# Release snapshot

This release candidate freezes a local source snapshot taken on **2026-07-19**. The development Skills may continue changing after this point; those changes are not part of `v0.1.0-alpha.3` unless a new snapshot is explicitly prepared.

## Frozen components

| Component | Packaged destination | Files | Aggregate SHA-256 |
|---|---|---:|---|
| Focus Skill | `plugins/rcf-focus/skills/recursive-center-field-dynamics/` | 8 | `b835d3cf906297ac539e2b207ff0969282cb743b7b2c35c9a07f0de97e2d930e` |
| Address Skill and engine | `plugins/rcf-address/skills/recursive-field-addressing/` | 5 | `9cee66b92436009ae5eed69688c99b67f9f81b1eb76716435face874aa68de2f` |
| Distill Skill | `plugins/rcf-distill/skills/distill-conversation-ideas/` | 2 | `2501d4678037551d7359463a755189b7e343f2f6cab6bcb4f75d1c6d91aee901` |
| Dynamic-addressing source set | `docs/dynamic-addressing/` | 4 | source aggregate `6cb2e229ff6571e4d7c00e3b695aa2085bebc4885d996834e02c6910dd316f51` |
| Curated formal philosophy source set | `docs/methodology/`, `docs/philosophy/`, `docs/comparisons/` | 14 | source aggregate `ce2c77ba3f4024798661e1458a291dcd2926e75d7e048db70aa15964b7229e1e` |

The dynamic-addressing packaged README differs from its source hash only because local private-path links were rewritten to public repository links. Several philosophy files are similarly renamed or routed into public folders without changing their source text.

## Aggregate algorithm

For each source set:

1. exclude `__pycache__/` and `*.pyc`;
2. compute SHA-256 for every included file;
3. sort records as `<relative-path>\t<file-sha256>`;
4. join records with `\n`;
5. compute SHA-256 of the UTF-8 record list.

## Included theory boundary

The public theory snapshot includes the root theory and methodology, the complete public draft, philosophical lineage and comparison matrix, seven formal source texts, the public `主义主义` comparison data, and the complete recursive dynamic-addressing theory directory.

It intentionally excludes private research Ideas, conversation inheritance logs, maintenance workspaces, state JSON, unpublished project data, local absolute paths, Python caches, and temporary files.

## Release boundary

This file records a **local release candidate**, not a GitHub publication. Preparing, committing, creating the remote repository, and pushing are separate actions.
