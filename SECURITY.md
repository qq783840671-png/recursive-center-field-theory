# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| `0.3.0-alpha.2` | Yes, while it is the current public candidate |
| `0.1.0-alpha.3` and earlier | No; retained for historical reproduction only |

This policy covers executable scripts, plugin packaging, repository automation, and examples. Disagreement with a philosophical or methodological claim is not a security vulnerability; use the theory-challenge issue form instead.

## Reporting a vulnerability

Do not open a public issue for credentials, arbitrary code execution, unsafe path handling, command injection, unintended remote writes, permission bypasses, or private-data exposure.

After the repository is published, use GitHub's private vulnerability reporting page:

```text
https://github.com/qq783840671-png/recursive-center-field-theory/security/advisories/new
```

If private reporting is not yet enabled or the page is unavailable, contact the maintainer through the contact method shown on the [maintainer's GitHub profile](https://github.com/qq783840671-png) and disclose only that a private security channel is needed. Do not send exploit details through a public issue or discussion.

Include:

- affected version and file;
- impact and realistic attack conditions;
- minimal reproduction or proof of concept;
- whether credentials or personal data may already be exposed;
- suggested mitigation, if known.

The maintainer will acknowledge a usable private report when received, assess scope, prepare a fix and regression test where practical, and coordinate disclosure. No fixed response-time guarantee is made for this personal research project.

## Security boundaries

- The plugins are local Skills and scripts, not a hosted security boundary.
- Focus can alter structural navigation inside an already authorized parent task, but it cannot grant permissions or expand task scope; operating-system permissions, sandboxing, review, and user judgment remain authoritative.
- Passing repository tests proves recorded behavior under tested inputs; it does not certify the project for high-risk or adversarial deployment.
