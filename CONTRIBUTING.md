# Contributing

Thank you for helping examine this philosophy–method–engineering project. The most useful contribution is not agreement with the framework but a precise improvement, reproduction, contradiction, counterexample, or boundary correction.

中文说明：欢迎提交可复现缺陷、理论反例、证据挑战、文档修订和测试。请明确你修改的是哲学命题、方法规范、运行协议、程序实现还是经验主张；不要用程序测试冒充哲学证明，也不要用观点分歧冒充程序缺陷。

## Choose a contribution channel

- **Runtime or Skill failure:** reproducible Focus, Address, Distill, packaging, test, or execution behavior.
- **Theory or evidence challenge:** contradiction, counterexample, scope confusion, attribution error, or unsupported claim.
- **Documentation problem:** broken link, stale diagram, translation, accessibility, or navigation issue.
- **Discussion:** interpretation, application idea, broad comparison, or a question without an actionable defect.
- **Security:** follow [SECURITY.md](SECURITY.md); do not publish details.

Blank issues are disabled so that each report carries the evidence needed for its layer.

## Before opening an issue

1. Read the [current release scope](docs/release-scope.md) and confirm the authoritative version.
2. State the task-relative field contract or the exact theoretical claim, not only a broad topic.
3. Include the smallest task, quotation, address, state, source, or reproduction that exposes the problem.
4. Distinguish expected behavior, observed behavior, contrary evidence, and proposed repair.
5. Remove private conversations, credentials, unpublished manuscripts, personal data, and unrelated workspace files.

Historical texts may be challenged as historical records, but they do not override the current authority order unless the issue also shows a current inheritance defect.

## Pull requests

Keep a pull request focused on one closure gap. The pull request template asks for target layer, evidence, invariant impact, compatibility, validation, and publication safety.

For theory changes, include:

- exact proposition and scope;
- contradiction, counterexample, source, or ambiguity;
- affected-document and terminology map;
- whether the old version is corrected, narrowed, rejected, or retained historically;
- any implementation and migration consequences.

For implementation changes, include tests for the changed behavior and preserve the following invariants unless the proposal explicitly versions them:

- explicit-only constructive Focus invocation with no Focus-specific permission gate;
- normal parent-task authorization and safety boundaries;
- one evidence-backed current center, one next structural decision, and preserved peer interfaces;
- necessary-predecessor and join legality;
- candidate, potential, realized, failed, and no-address distinctions;
- selected-center versus complete-field closure;
- observation evidence, residual history, `Fold`, and historical `Unwind` semantics;
- legacy schema compatibility where claimed.

## Validation

```bash
python -m py_compile plugins/rcf-focus/skills/recursive-center-field-dynamics/scripts/focus_runtime.py plugins/rcf-focus/skills/recursive-center-field-dynamics/scripts/field_state.py plugins/rcf-address/skills/recursive-field-addressing/scripts/address_engine.py
python plugins/rcf-address/skills/recursive-field-addressing/scripts/address_engine.py self-test
python -m unittest discover -s tests -p "test_*.py" -v
python -m unittest discover -s plugins/rcf-focus/skills/recursive-center-field-dynamics/tests -p "test_*.py" -v
```

Theory-only changes still require link, version, terminology, authority, and downstream consistency checks. Code tests do not prove philosophical or empirical claims.

## Claims, conduct, and licensing

- Mark definitions or implemented protocol behavior `[D]`, hypotheses `[H]`, and unresolved questions `[O]` where those labels are used.
- Follow the [Code of Conduct](CODE_OF_CONDUCT.md).
- By submitting material, you represent that you may submit it and agree that accepted contributions may be distributed under [CC BY-NC 4.0](LICENSE).
- The project is source-available and non-commercial, not OSI-approved open source.

Maintainer decisions follow [GOVERNANCE.md](GOVERNANCE.md). A declined contribution may still contain a valuable idea; rejection means only that it did not close the current repository contract.
