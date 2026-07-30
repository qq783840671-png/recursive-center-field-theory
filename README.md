# Recursive Center-Field Theory

[简体中文](README.zh-CN.md) · frozen release candidate `v0.1.0-alpha.3` · personal, non-commercial sharing

> Not a promise of one permanently correct center, but a way to keep forming, testing, and rebuilding centers.

This repository shares a developing philosophy-method framework and three usable Codex Skills. The common core is **Recursive Center-Field Partial-Order Dynamics**: form a task-relative field, recover a candidate load-bearing center and necessary partial order, open or compress recursive subfields, assign traceable dynamic addresses, act on legal frontiers, and let evidence or residuals revise the next version.

This is a personal research project, not a commercial service. The aim is to make the ideas inspectable, usable, criticizable, and easier for others to adapt in non-commercial work.

## One system, three entrances

| Entrance | What it offers | Current status |
|---|---|---|
| [Theory and methodology](docs/methodology/README.md) | Philosophy, field-center co-formation, necessary partial order, recursive motion, closure, and residual-driven revision | Formal public draft |
| [Dynamic addressing](docs/dynamic-addressing/README.md) | A method for generating and auditing field-relative, versioned, reopenable addresses | Theory `v0.1`; experimental engine included |
| [Codex plugins](#install-the-skills) | Focus, Address, and Distill as separately installable Skills | Frozen alpha snapshot |

The hierarchy is intentional:

```text
philosophy
→ Recursive Center-Field Partial-Order Dynamics methodology
→ dynamic addressing method
→ Focus / Address / Distill applications
→ evidence, residuals, and the next theory version
```

Focus is the flagship application. Address exposes the address-generation method as a computable tool. Distill is a smaller derived application for conservatively turning fragmented conversations into durable project knowledge.

## Install the Skills

After this repository is published on GitHub:

```bash
codex plugin marketplace add qq783840671-png/recursive-center-field-theory
```

Restart Codex, open Plugins, and install any of:

- **RCF Focus** — clarify, model, execute, audit, and reopen complex tasks;
- **RCF Address** — generate, register, query, and audit dynamic addresses;
- **RCF Distill** — merge durable conversational knowledge with provenance.

The plugins contain only local Skills and scripts. They add no connector, hosted service, MCP server, or authentication dependency.

## Start here

- Try [Focus with the public defect-repair example](examples/open-source-defect-repair/README.md).
- Read [how Address assigns a structural identity](docs/dynamic-addressing/动态地址生成与运动协议.md).
- See [a minimal Distill workflow](examples/distill/README.md).
- Compare the framework with adjacent methods in [the comparison guide](docs/comparisons/README.md).
- Browse the [complete documentation map](docs/README.md).

## Claims and limits

- `[D]` marks definitions and implemented protocol behavior.
- `[H]` marks hypotheses that still require comparison or empirical evaluation.
- `[O]` marks open questions.

The project does not claim state of the art, universal outperformance, automatic recovery of true causality, lossless infinite context, a solved general planner, or a proven universal ontology. Explicit structure may help some long-horizon tasks, but it can also stabilize a wrong field or center; the contracts, candidates, evidence, and residuals must remain auditable.

## Repository map

```text
docs/                 public theory, philosophy, addressing, and comparisons
plugins/              three independent Codex plugins
.agents/plugins/      repository marketplace manifest
examples/             reproducible usage paths
tests/                repository and public-example validation
assets/               overview and social-preview media
RELEASE_SNAPSHOT.md   frozen source boundary for this candidate
```

## Version boundary

The development Skills continue to evolve elsewhere. This candidate freezes the files listed in [RELEASE_SNAPSHOT.md](RELEASE_SNAPSHOT.md); later development changes do not silently alter this release candidate.

## License and citation

Shared under [CC BY-NC 4.0](LICENSE): attribution is required and commercial use is not permitted. This is therefore a source-available, non-commercial release rather than an OSI-approved open-source software release. Cite the project with [CITATION.cff](CITATION.cff).
