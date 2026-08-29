# Reproducible example: open-source defect repair

This repository carries three compatibility layers:

- the current v0.18 constructive live loop in `focus_runtime.py`;
- the historical two-stage state path in the same runtime, retained for validation, resumption, and migration;
- the legacy schema-2.2 helper in `field_state.py`, retained for historical reproduction.

During defect repair, Focus may frame several irreducible concerns, for example functional correctness, compatibility, and delivery evidence. It selects one current center, returns one necessary next frontier, and preserves the others as peer interfaces instead of mixing all concerns into one queue.

```text
parent defect-repair task executes normally
  → observe actual reads, writes, tools and validation
  → reconstruct contract, actual centers, order and joins
  → derive evidence-bound realized addresses
  → fold selected-center and complete-field closure separately
  → append the compact field note
```

The example is a protocol demonstration, not a universal taxonomy of software engineering. The runtime derives addresses; the user or agent remains responsible for the semantic quality of the proposed contract, relations, centers, evidence, and failure conditions.

## Run the current tests

```sh
python -m unittest discover -s plugins/rcf-focus/skills/recursive-center-field-dynamics/tests -p "test_*.py" -v
python -m unittest discover -s tests -p "test_*.py" -v
```

The source suite covers constructive decisions, knowledge deltas, dependency invalidation, version branches, reclosure, evidence gates, candidate/legal address separation, typed centers and joins, plus historical sidecar and two-stage compatibility.

The public smoke test continues to exercise the legacy helper because that surface remains part of this release's compatibility boundary. New integrations should use `focus_runtime.py` with `init --mode constructive → frame → decide／expand／execute → ingest-delta／assess-impact → fold／unwind`.
