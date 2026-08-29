# Release snapshot

This file freezes the local `v0.4.0-alpha.1` release candidate and system snapshot `2026.08.29-rcf.1`, prepared on **2026-08-29**. It records a local candidate only: no commit, tag, GitHub repository creation, push, release, or public plugin-marketplace publication was performed. The separate personal toolkit plugin was rebuilt and reinstalled locally as `0.12.0+codex.20260829151605`.

## Frozen components

| Component | Packaged destination | Files | Aggregate SHA-256 |
|---|---|---:|---|
| Focus canonical Skill plus `$focus` alias | `plugins/rcf-focus/skills/` | 25 | `501f585edc6d6e5b008c706d48ec9a447a173178786e4b1267726f8c1e846097` |
| Address Skill and engine | `plugins/rcf-address/skills/` | 5 | `15ce9fa3febd26d2757b14dae31d8e9c876c0fb36424e84b3333a51168637b5d` |
| Distill Skill | `plugins/rcf-distill/skills/` | 2 | `8376b628250dc951834c3a965655934fba85cebab2e1b7102bfd5d94e6d4c5b3` |
| Current theory and specifications | `docs/theory.zh-CN.md`, `docs/methodology/`, `docs/spec/`, `docs/dynamic-addressing/`, `docs/release-scope.md` | 11 | `5f7165f0c25d8558a6c418a1c6ca39faf7543844bbd238e6f99ff07b7a825991` |
| Mathematics, AI, and philosophy concept notes | `docs/concepts/` | 4 | `d7c8c1946637289955e95fd1ea217bf5e77ae10e8d8724fb028c786f8c5131c8` |
| Philosophical lineage and comparison material | `docs/philosophy/`, `docs/comparisons/`, comparison and reference maps | 16 | `c4fd90a8ba4d421b15f54f67559025074fe82c5da31620f7db259913eaedb96b` |
| Whole candidate tree, excluding this snapshot and generated caches | repository root | 120 | `908faecf4dc4429e42ce902461749644b8969cb23d2acc8172541d0462da9b91` |

## Aggregate algorithm

For each set:

1. enumerate regular files recursively;
2. exclude `.git/`, `__pycache__/`, `.pytest_cache/`, and `*.pyc`;
3. for the whole-tree aggregate, also exclude `RELEASE_SNAPSHOT.md` to avoid a self-referential hash;
4. compute SHA-256 for each file;
5. sort records ordinally as `<repository-relative-path>\t<file-sha256>` using `/` separators;
6. join records with `\n` and compute SHA-256 over the UTF-8 bytes.

## Source and authority boundary

The current public authority order is documented in [`docs/release-scope.md`](docs/release-scope.md). The candidate packages root theory v0.13, dynamics v0.18, multi-center specification v0.7-draft, dynamic addressing v0.12-draft, public text v0.7-draft, Focus Skill v0.18 with the `focus-constructive-2.0` state contract, three concept-note groups, three public plugins, examples, tests, curated historical lineage material, and GitHub community health files for conduct, security, support, governance, issues, and pull requests. Historical sidecar and two-stage states remain compatibility surfaces rather than the default workflow.

It intentionally excludes internal conversation inheritance records, workspace logs, private research ideas, machine state, local validation dependencies, temporary files, unpublished project data, and development caches. Historical source texts remain below the current theory and specification authority.

## Validation boundary

The candidate was accepted locally only after repository unit tests, the 48-test Focus source suite, 10 productization tests, 15 behavior-contract definitions, Address engine self-test, Skill validation, plugin validation, relative-link checks, credential-pattern scanning, local-path scanning, cache/tracked-state checks, whitespace checks, and release-hash verification.

Passing these checks demonstrates packaging and recorded protocol consistency. Independent model runs comparing no Skill, the historical sidecar, and constructive Focus were not supplied; the checks do not prove the theory true, prove formal logical consistency, establish novelty, or demonstrate performance superiority.
