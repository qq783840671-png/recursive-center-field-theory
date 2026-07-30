# Contributing

This project is an early protocol and Skill. The most useful contribution is a reproducible case that shows where the current field, center, partial order, address, execution gate, or residual audit succeeds or fails.

Before opening an issue or pull request:

1. state the root goal F0 and acceptance condition;
2. include the smallest task or state file that reproduces the behavior;
3. distinguish expected legal frontier, actual output, and any residual that was omitted or misclassified;
4. remove private conversations, credentials, unpublished manuscripts, and unrelated workspace files;
5. run the public tests when changing the Skill, protocol, schema, helper, or example.

```bash
python -m py_compile plugins/rcf-focus/skills/recursive-center-field-dynamics/scripts/field_state.py plugins/rcf-address/skills/recursive-field-addressing/scripts/address_engine.py
python plugins/rcf-address/skills/recursive-field-addressing/scripts/address_engine.py self-test
python -m unittest discover -s tests -p "test_*.py" -v
python -m unittest discover -s plugins/rcf-focus/skills/recursive-center-field-dynamics/tests -p "test_*.py" -v
```

Definitions and protocol rules should be marked `[D]`; performance or generality claims should remain `[H]` until controlled evidence supports them; unresolved questions should be marked `[O]`.

Do not silently change the explicit-invocation boundary, root-goal semantics, partial-order legality gate, `[◇] → Execute → Audit → [+]` rule, residual history, or schema compatibility. Explain any proposed change to those invariants and add a regression case.
