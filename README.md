# Recursive Partial-Order Multi-Center Dynamic Field Theory

[简体中文](README.zh-CN.md) · local release candidate `v0.4.0-alpha.2` · system snapshot `2026.08.30-rcf.1` · not uploaded · personal non-commercial sharing

> Focus participates while Codex performs the parent task: it forms one current projection, drives a necessary frontier, revises obsolete closure when evidence changes, and preserves version lineage.

This repository publishes a developing philosophy–method–engineering system. It forms task-relative fields, distinguishes a multi-center complete field from one compact main-center view, reconstructs necessary partial order from actual work, assigns evidence-bound dynamic addresses, and maintains later versions through evidence, residuals, folding, and lineage.

It is a personal research project and testable engineering prototype—not a natural law, complete ontology, or commercial service. The publication goal is to make definitions, implementations, tests, limits, and lineage inspectable and criticizable.

## Current system

| Layer | Public artifact | Status |
|---|---|---|
| Root framework | [Recursive Center Partial-Order Dynamic Field Theory](docs/methodology/递归中心偏序动力场域论.md) | `v0.13`, philosophy-method prototype |
| Dynamics specification | [Recursive Center-Field Partial-Order Dynamics](docs/spec/递归中心场偏序动力模型.md) | `v0.18`, candidate discrete-event model |
| Multi-center specification | [Recursive Partial-Order Multi-Center Dynamic Field Theory](docs/spec/递归偏序多中心动态场域论.md) | `v0.7-draft` |
| Dynamic addressing | [Field-relative Recursive Dynamic Addressing](docs/dynamic-addressing/递归动态寻址理论.md) | `v0.12-draft`; experimental engine included |
| Public introduction | [Recursive Center-Field Theory](docs/theory.zh-CN.md) | `v0.7-draft` |

See [release scope and evidence boundaries](docs/release-scope.md) for authority order, implemented subsets, and open gaps.

### Two different kinds of potential

- Latent frontier `P_t^latent`: a calibrated legal address already exists, but the current parent contract does not require opening it this round; if unrealized it normally remains `[◇]`.
- Latent residual `Λ_t`: an inactive difference record whose binding may be a legal address, an address candidate, or `unaddressed`; it is not an address and never carries `[◇]`.

In short, `P_t^latent` means “the position is known; defer it,” while `Λ_t` means “a difference is known; its position or disposition is not settled.”

## Three Codex plugins

- **RCF Focus** maintains a live task field through `FORM → DRIVE → REVISE → FOLD`, changes the next action when a structural difference exists, invalidates obsolete closure, and preserves versions and branches.
- **RCF Address** generates, registers, queries, and audits field-relative, versioned, reopenable structural addresses.
- **RCF Distill** conservatively merges durable claims, decisions, conflicts, residuals, and provenance into one canonical knowledge file.

Address v0.6 is backed by the `0.5-experimental` persisted-state engine. Distill v0.2 adds an optional `distill-ledger-1.0` audit helper for persisted, compacted, disputed, or high-risk merges; the model still owns semantic comparison and the actual minimum edit.

The Focus plugin also packages the `$focus` invocation alias. All three plugins contain local Skills and scripts only; they add no connector, hosted service, MCP server, or authentication dependency.

After publication, the marketplace can be added with:

```bash
codex plugin marketplace add qq783840671-png/recursive-center-field-theory
```

This is currently a local candidate, so the remote path may remain unavailable until a separate upload is authorized.

## Start here

- [Documentation map](docs/README.md)
- [Focus constructive runtime](plugins/rcf-focus/README.md)
- [Dynamic-address protocol](docs/dynamic-addressing/动态地址生成与运动协议.md)
- [Open-source defect-repair example](examples/open-source-defect-repair/README.md)
- [Mathematics, AI, and philosophy concept notes](docs/concepts/README.md)
- [Comparison guide](docs/comparisons/README.md)

## Claims and limits

- `[D]` marks definitions or protocol behavior backed by current code and tests.
- `[H]` marks hypotheses requiring comparison or empirical evaluation.
- `[O]` marks open questions.

The v0.18 runtime implements constructive framing and next-frontier decisions, typed knowledge deltas, dependency-scoped invalidation, immutable closure versions and branches, dynamic addresses, recursive fold/unwind, and separation of selected-center closure from complete-field closure. Historical sidecar and two-stage states remain supported for import and audit. The runtime does not yet implement automatic domain-truth discovery, a complete multi-center lifecycle, cross-task panorama recomposition, automatic reprojection, or proven performance gains.

The project does not claim state of the art, universal outperformance, automatic recovery of true causality, lossless inversion of higher-dimensional reality, a solved general planner, or a proven cross-scale ontology. Mathematical and physical comparisons are structural references, not ontological proof.

## Repository map

```text
docs/                 theory, specifications, concepts, lineage, comparisons
plugins/              three independent Codex plugins
.agents/plugins/      repository marketplace manifest
examples/             reproducible usage paths
tests/                public contracts and example validation
RELEASE_SNAPSHOT.md   frozen sources, file counts, and hashes
release-manifest.json machine-readable component and compatibility matrix
```

## Participation and community

The project welcomes reproducible defects, theoretical counterexamples, evidence challenges, documentation corrections, and bounded engineering improvements. Open participation does not mean every proposal enters the canonical theory; theory, protocol, implementation, and empirical claims have different evidence requirements.

- [Contribution guide](CONTRIBUTING.md)
- [Code of conduct](CODE_OF_CONDUCT.md)
- [Support and channel routing](SUPPORT.md)
- [Security policy](SECURITY.md)
- [Governance](GOVERNANCE.md)

Use Discussions for interpretation, application ideas, and open comparison. Use the typed issue forms for reproducible failures, theory challenges, and documentation defects. Never post credentials, private conversations, unpublished manuscripts, or vulnerability details in a public issue.

## License and citation

Shared under [CC BY-NC 4.0](LICENSE): attribution is required and commercial use is not permitted. It is a source-available, non-commercial release rather than OSI-approved open-source software. Cite it with [CITATION.cff](CITATION.cff).
