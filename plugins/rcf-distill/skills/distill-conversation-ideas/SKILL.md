---
name: distill-conversation-ideas
description: "Use when the user says 沉淀／沉淀一下 or asks to preserve ideas from a long or compacted conversation. Extract durable decisions, constraints, evidence boundaries, relations, and open questions; merge them safely into one canonical project knowledge file without turning inference into fact."
---

# Distill

## Quick start

Accept `Use Distill: preserve the durable decisions and unresolved questions from this conversation.` Locate the canonical project destination, make the minimum safe merge, then report what was retained, merged, revised, or left uncertain. Ask for a destination only when no unambiguous project route exists.

## Outcome and ownership

Turn conversation into the minimum sufficient knowledge future work must inherit. Preserve the durable center, dependencies, evidence boundaries, provenance, and unresolved edges; discard conversational noise.

Distill owns preservation intent and the canonical knowledge destination. It does not execute the original domain task. Use ordinary semantic relations by default; delegate to Address only when field-relative identity or migration materially affects the merge.

An explicit `沉淀` request authorizes this workflow. Do not add an F0 checkpoint unless scope, destination, or a high-risk target would materially change the write.

## Internal center

Recover, but hide by default:

`source scope → durable center → decisions/dependencies/boundaries/evidence/residuals → one canonical route → minimum merge → audited knowledge version`

The center is not a frequency list. Retain only material that changes future reasoning or work. Keep independent ideas incomparable and unresolved relevant material open; never force it into a settled conclusion.

## Efficient workflow

1. **Scope once.** Use the current conversation unless the user names other sources. Treat compacted summaries as secondary records labeled `来自对话摘要`; never reconstruct missing turns or quotations.
2. **Extract before loading the destination.** Convert the source once into a small candidate set: durable center, atomic decisions/ideas, dependencies, evidence boundaries, conflicts, residuals, and only decision-linked next actions. Drop greetings, coordination, generic explanation, repetition, abandoned scaffolding, and raw process logs.
3. **Route narrowly.** Use an explicit file first, then an established inheritance router, then a clearly canonical project-memory file. Search filenames/headings before opening large files. Never scan unrelated directories or place project knowledge in the Skill folder.
4. **Read only what governs the merge.** Read the router plus the target schema and relevant topic/neighbor sections. Read the whole destination only when its structure, cross-file uniqueness, or duplicate risk cannot otherwise be verified.
5. **Normalize candidates.** Record only supported fields: idea/decision, why it matters, status, basis, relations, and material open edge.
6. **Compare semantically.** Classify each candidate as `ADD`, `REFINE`, `REPLACE`, `CONTRADICT`, or `NOOP`; do not append wording variants of an existing idea.
7. **Merge minimally.** Keep one semantic idea in one canonical main file. Preserve meaningful revision relations; never blend conflict into false consensus or overwrite source evidence.
8. **Audit.** Re-read the changed section and verify claim status, basis, retained requirements/negative results, duplicate handling, route correctness, and minimal file scope.

If no durable candidate survives, write nothing and report `NO_DURABLE_UPDATE`. If no canonical destination can be resolved, show the compact candidate preview and ask one concise path question. For a thesis, final manuscript, submission file, core specification, or similarly high-risk target, present the proposed patch and obtain confirmation before writing.

## Atomic knowledge record

Use the destination's schema. Otherwise use this compact form and omit empty fields:

```markdown
### <idea title>

- Idea/decision: ...
- Why it matters: ...
- Status: 用户明确 | 已验证 | 工作假设 | 模型推断 | 待确认 | 已替代 | 已否定
- Basis: <turn/file/paper/experiment/来自对话摘要>
- Relations: refines | contradicts | replaces | depends on | applies to ...
- Open edge: ...
```

Do not create a dated section when the item belongs under an existing topic. A superseded idea may remain only when its history explains the current state.

## Claim and provenance rules

- Prefer specific, hard-to-reconstruct, decision-relevant, reusable material.
- Keep user requirements, verified findings, hypotheses, model inference, and unresolved questions in distinct statuses.
- Never promote repetition, assistant inference, or a compacted summary into verification.
- Preserve the source/basis whenever available; do not invent quotations or certainty.
- Synchronize an inheritance entry only when the merge changes what future maintainers must know.

## State and token discipline

- Extract and deduplicate the conversation once; carry atomic candidate IDs instead of repeating source paragraphs.
- Reuse an already resolved router and unchanged destination schema across the same task.
- Use targeted search and sectional reads before full-file loading.
- Edit only the smallest relevant section and do not generate parallel notes, process documents, or per-invocation dated copies.
- Keep internal candidates, rejected noise, and duplicate comparisons hidden unless requested.

These rules reduce representation and I/O cost without weakening provenance, canonical routing, or claim boundaries.

## Compact report

After writing, return:

1. the most important retained ideas;
2. a link to the canonical destination and changed section;
3. counts or a short list of `ADD/REFINE/REPLACE/CONTRADICT/NOOP` outcomes;
4. uncertainties caused by compaction or incomplete evidence.

Never report only “file updated,” and never claim a write when none occurred.
