# Release snapshot

This file freezes the local `v0.4.0-alpha.2` release candidate and system snapshot `2026.08.30-rcf.1`, prepared on **2026-08-30**. It records a local candidate only: no tag, GitHub repository creation, push, release, or public plugin-marketplace publication was performed. The separate personal toolkit plugin was rebuilt locally as `0.13.0`; a new Codex task is required after any local reinstall to load the revised Skills.

## Frozen components

| Component | Packaged destination | Files | Aggregate SHA-256 |
|---|---|---:|---|
| Focus canonical Skill plus `$focus` alias | `plugins/rcf-focus/skills/` | 25 | `501f585edc6d6e5b008c706d48ec9a447a173178786e4b1267726f8c1e846097` |
| Address Skill and engine | `plugins/rcf-address/skills/` | 5 | `39e609f751209fda6ad73d93b31ea956ddabda5d964d483fcc8dc25ee92f803a` |
| Distill Skill and audit ledger | `plugins/rcf-distill/skills/` | 4 | `4d9cb5b616f15b66f72d046c366e78deded07eeba9bd51d89487bfff092d3beb` |
| Current theory and specifications | `docs/theory.zh-CN.md`, `docs/methodology/`, `docs/spec/`, `docs/dynamic-addressing/`, `docs/release-scope.md` | 11 | `4f6f2fe52ee1b21d918e687793ecc79cafed70ad3ecdf5f6b9566dc11936e18f` |
| Mathematics, AI, and philosophy concept notes | `docs/concepts/` | 4 | `d7c8c1946637289955e95fd1ea217bf5e77ae10e8d8724fb028c786f8c5131c8` |
| Philosophical lineage and comparison material | `docs/philosophy/`, `docs/comparisons/`, comparison and reference maps | 16 | `d68f70539e70a279c819b32b47aa133a3157d5fbdb1107ecc5d5fa6c3876faca` |
| Whole candidate tree, excluding this snapshot and generated caches | repository root | 123 | `1f4a3e74356920203865ad457e7e08f410dedcd90276522c52a4c2711863f078` |

## Aggregate algorithm

For each set:

1. enumerate regular files recursively;
2. exclude `.git/`, `__pycache__/`, `.pytest_cache/`, and `*.pyc`;
3. for the whole-tree aggregate, also exclude `RELEASE_SNAPSHOT.md` to avoid a self-referential hash;
4. compute SHA-256 for each file;
5. sort records ordinally as `<repository-relative-path>\t<file-sha256>` using `/` separators;
6. join records with `\n` and compute SHA-256 over the UTF-8 bytes.

## Source and authority boundary

The current public authority order is documented in [`docs/release-scope.md`](docs/release-scope.md). The candidate packages root theory v0.13, dynamics v0.18, multi-center specification v0.7-draft, dynamic addressing v0.12-draft, public text v0.7-draft, Focus Skill v0.18 with the `focus-constructive-2.0` state contract, Address Skill v0.6 with engine 0.5, Distill Skill v0.2 with the optional `distill-ledger-1.0` audit contract, three concept-note groups, three public plugins, examples, tests, curated historical lineage material, and GitHub community health files. Historical sidecar and two-stage states remain compatibility surfaces rather than the default workflow.

It intentionally excludes internal conversation inheritance records, workspace logs, private research ideas, machine state, local validation dependencies, temporary files, unpublished project data, and development caches. Historical source texts remain below the current theory and specification authority.

## Validation boundary

The candidate was accepted locally only after 21 repository tests, the 48-test Focus source suite, 16 toolkit productization/runtime tests, Address engine and Distill ledger self-tests, Skill validation, plugin validation, credential-pattern scanning, local-path scanning, cache/tracked-state checks, whitespace checks, and release-hash verification.

Passing these checks demonstrates packaging and recorded protocol consistency. Independent model runs comparing no Skill, the historical sidecar, and constructive Focus were not supplied; the checks do not prove the theory true, prove formal logical consistency, establish novelty, or demonstrate performance superiority.
