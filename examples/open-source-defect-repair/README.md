# Reproducible example: open-source defect repair

This example constructs and executes one bounded recursive center-field state. It is a demonstration of the protocol, not a universal taxonomy of software engineering.

The deterministic motion chain is:

```text
FIELD_FORM → SURVEY → GLOBAL_EXPAND → FOCUS → COMPRESS → EXECUTE → INVALIDATE
```

Only `EXECUTE` realizes a task address. Global Expansion and Focus create legal potential addresses marked `[◇]`. The last motion deliberately invalidates the executed patch to demonstrate evidence-driven propagation and atomic state revision.

## Parent field and first branch layer

```text
F0:A  Receive and delimit the defect
  A1 functional error
  A2 performance regression
  A3 compatibility problem
→ F0:B  Reproduce and form evidence
  B1 local environment
  B2 continuous integration
  B3 user environment
→ F0:C  Locate the first structural cause
  C1 data path
  C2 state transition
  C3 interface contract
→ F0:D  Complete the repair
  D1 local patch
  D2 structural modification
  D3 compatibility strategy
→ F0:E  Validate and deliver
  E1 regression test
  E2 integration test
  E3 review and merge
```

The parent center is the A–E functional closure. The selected object path is `F0:A1 → B1 → C3 → D1 → E1`; unselected branches remain represented as legal potential addresses.

## Focus child field

`GLOBAL_EXPAND` opens `F0:C3` as child field `CF-F0-C3-v1`. `FOCUS` then constructs this local route:

```text
CF-F0-C3-v1:A2  Capture a response mismatch
→ B3  Restore the shared invariant
→ C3  Locate a compatibility or version-contract violation
→ D1  Adapt the caller
→ E3  Run the integration regression
```

Its F0-facing address is:

```text
F0:C3.2.3.3.1.3[◇]
```

The address stays `[◇]` throughout this example. `COMPRESS` preserves `F0:C3` as a reopenable interface whose `reopen_address` is `CF-F0-C3-v1`; it does not pretend that the focused route has executed.

## Run the current executable gate

The A–E and C3 structures above are the narrative example. The frozen helper now requires evidence-bound graph claims and validated child-field opening proofs, so the public smoke test deliberately uses a minimal one-node field to demonstrate the current formation/confirmation boundary without fabricating deeper evidence.

```sh
python -m unittest tests.test_public_example -v
```

The test verifies that a new field begins at `FIELD_FORMATION_REQUIRED`, an early Global motion is rejected atomically, a validated candidate changes the decision to `F0_CONFIRMATION_REQUIRED`, explicit confirmation records an `F0_CONFIRM` event, and the resulting schema-2.2 state validates.

The frozen Focus source tests cover the deeper address-motion, child-opening proof, invalidation, version-branching, no-address, and rollback rules:

```sh
python -m unittest discover -s plugins/rcf-focus/skills/recursive-center-field-dynamics/tests -p "test_*.py" -v
```

```sh
python -m unittest discover -s tests -p "test_*.py" -v
```

Tests resolve the packaged helper at `plugins/rcf-focus/skills/recursive-center-field-dynamics/scripts/field_state.py`. Maintainers can test the same public artifacts against a frozen development helper without editing or copying the Skill:

```text
RCF_FIELD_STATE_HELPER=/absolute/path/to/field_state.py
```

Set that environment variable using the syntax of the current shell, then run the same unittest command. CI runs the packaged helper on both Windows and Linux with Python 3.11.
