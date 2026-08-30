# Changelog

All notable public-candidate changes are recorded here. Theory, Skill, plugin, release, and Git versions remain separate clocks; see [`release-manifest.json`](release-manifest.json) for their compatibility matrix.

## [0.4.0-alpha.2] - 2026-08-30

### Changed

- Bound Address Skill v0.6 to the existing `0.5-experimental` persisted-state engine and synchronized the public Schema from the stale 0.4 header.
- Added direct behavior tests for Address candidate/address separation and the existing engine self-test.
- Advanced Distill to v0.2 with an optional `distill-ledger-1.0` helper that validates declared `ADD / REFINE / REPLACE / CONTRADICT / NOOP` plans and records applied or deferred outcomes.
- Kept semantic extraction, canonical routing, comparison, and the actual minimum knowledge edit under model responsibility; the ledger does not infer meaning or prove truth.

### Evidence boundary

- Tests validate recorded state and audit invariants, including rejection of summary-to-verified promotion and incomplete finalization.
- No comparative advantage, automatic semantic equivalence, or automatic truth discovery is claimed.
- This remains a local candidate until the GitHub repository is created and pushed.

## [0.4.0-alpha.1] - 2026-08-29

### Changed

- Rebuilt Focus from a post-execution symbol/audit sidecar into a constructive live loop: `FORM → DRIVE → REVISE → FOLD`.
- Added one-next-decision enforcement, typed knowledge deltas, scoped dependency invalidation, parent-interface reopening, immutable closure versions, branches, and reclosure lineage.
- Restricted address generation to positions that perform navigation, constraint, evidence, memory, or reopening work; structurally empty invocations return `NOOP`.
- Preserved v0.17 sidecar and historical two-stage states as import and audit compatibility surfaces.
- Advanced the dynamics specification to v0.18, multi-center specification to v0.7-draft, and dynamic-addressing specification to v0.12-draft.

### Evidence boundary

- Source and packaging tests verify state transitions, invalidation, version lineage, and compatibility contracts.
- Independent model runs comparing no Skill, the old sidecar, and constructive Focus have not yet been supplied; no empirical performance advantage is claimed.
- This remains a local candidate. No commit, tag, push, GitHub Release, or marketplace publication is implied by this entry.

## [0.3.0-alpha.2] - 2026-08-26

### Fixed

- Restored the explicit symbols and ledger split between latent frontier `P_t^latent` and latent residual `Λ_t` in the public entry points.
- Corrected two legacy protocol sentences that incorrectly implied every `Λ_t` was already addressed or that `[◇]` could serve as a residual modality.
- Clarified that `Λ_t` may bind a legal address, a candidate address, or remain `unaddressed`, while never becoming an address itself.

### Evidence boundary

- This is a documentation and protocol-consistency patch. Root theory, dynamics, multi-center, dynamic-addressing, Focus runtime, and address-engine semantic versions are unchanged.
- The unified local toolkit advances to `0.11.1`; this remains a local candidate with no commit, tag, push, or GitHub Release.

## [0.3.0-alpha.1] - 2026-08-26

### Changed

- Replaced the default pre-action Focus gate with the v0.17 post-execution sidecar workflow.
- Focus now lets the parent task complete normally, observes the actual trace, reconstructs evidence-bound centers, order, joins and addresses, then appends a compact field note.
- Historical two-stage Focus states remain available only for validation, resumption, and migration.
- Advanced the root framework to v0.12, dynamics specification to v0.17, multi-center specification to v0.6-draft, and dynamic-addressing specification to v0.11-draft.
- Added a machine-readable release manifest and explicit compatibility matrix.

### Evidence boundary

- Realized reconstructed nodes require non-empty evidence tied to observed events.
- Runtime validation demonstrates recorded consistency; it does not prove domain truth, unique center recovery, ontological claims, or performance superiority.
- This remains a local candidate. No commit, tag, push, GitHub Release, or marketplace publication is implied by this entry.

## [0.2.0-alpha.1] - 2026-08-10

- Prepared the first full local theory–specification–plugin candidate with community governance, tests, public boundaries, and frozen hashes.
- This candidate was not committed or uploaded.
