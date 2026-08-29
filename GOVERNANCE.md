# Governance

## Project status

Recursive Partial-Order Multi-Center Dynamic Field Theory is currently a single-maintainer personal research project. Publication invites examination and contribution; it does not transfer final release authority or imply that every proposed extension will enter the canonical theory.

## Roles

- **Maintainer:** freezes authoritative versions, accepts or rejects changes, manages releases and moderation, and preserves version lineage.
- **Contributors:** may submit counterexamples, evidence, documentation, tests, implementations, comparisons, and narrowly scoped proposals.
- **Community participants:** may ask questions and discuss applications without representing their interpretation as an official project position.

The current maintainer is [`qq783840671-png`](https://github.com/qq783840671-png).

## Decision rules

Changes are assessed by layer:

1. documentation corrections require source and link accuracy;
2. implementation changes require tests and compatibility analysis;
3. protocol changes require an invariant and migration audit;
4. theory changes require a defined scope, contradiction or evidence analysis, affected-document map, and explicit version transition;
5. license, governance, or publication changes require an explicit maintainer decision.

Consensus is welcome but not guaranteed. The maintainer may decline a change because it is unsupported, out of scope, duplicative, unsafe, incompatible with the current contract, or too costly to maintain. Rejection of a contribution is not a declaration that its underlying idea is false.

## Canonical status and history

The authority order for this candidate is defined in [`docs/release-scope.md`](docs/release-scope.md). Historical documents and rejected proposals remain useful evidence but do not silently override the current root theory, specifications, or release boundary.

## Contribution licensing

By submitting a contribution, you represent that you have the right to submit it and agree that the accepted contribution may be distributed under this repository's [CC BY-NC 4.0 license](LICENSE). Do not submit material that requires an incompatible license or contains private third-party content.

## Future governance

If sustained external maintenance develops, governance may be versioned to add reviewers, release roles, appeal paths, or a steering structure. Such a change must be explicit and must not rewrite the decision history of earlier releases.
