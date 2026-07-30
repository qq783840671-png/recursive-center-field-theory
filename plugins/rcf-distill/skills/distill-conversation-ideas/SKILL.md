---
name: distill-conversation-ideas
description: Distill the durable center, decisions, constraints, hypotheses, residuals, open questions, and reusable methods from long, fragmented, or compacted conversations, then safely merge them into the one canonical project knowledge destination without losing provenance or turning inference into fact. Use when the user says “沉淀”“沉淀一下”, asks to 沉淀对话、整理或保存想法、把聊天内容写入文件、在上下文压缩前保留关键信息、合并多轮讨论结论，或维护持续演化的 idea/研究笔记。
---

# Distill

## Goal

Turn conversation into the minimum sufficient project knowledge that future work must inherit. Preserve the durable center, dependencies, evidence boundaries, and unresolved edges; discard conversational noise.

## Center-first model

Treat an explicit “沉淀” request as authorization to run the distillation workflow. Do not add a separate F0 confirmation gate unless scope or destination ambiguity would materially change what gets written.

Internally recover this compact structure before editing:

```text
A source scope
→ B durable center: what future work must retain
→ C decisions, dependencies, boundaries, evidence, and residuals
→ D one canonical knowledge route
→ E minimum merge and audit
→ A′ updated project knowledge version
```

The center is not a list of frequently repeated topics. Keep only items that affect future reasoning or work, and preserve necessary relations among them. Treat unresolved but relevant material as an open edge or residual; never force it into a settled conclusion. Keep this internal structure hidden unless the user asks to see it.

## Workflow

1. Set the source scope.
   - Use the current conversation unless the user names other threads, summaries, or files.
   - Treat a compacted conversation summary as a secondary record, not as verbatim dialogue. Mark material recoverable only from it as `来自对话摘要`.
   - Do not reconstruct missing turns or quotations.

2. Recover the durable center.
   - State internally, in one sentence, what a future maintainer must retain from this source.
   - Separate central decisions and constraints from supporting detail, open frontiers, genuine residuals, superseded ideas, and noise.
   - Preserve dependency, refinement, replacement, contradiction, and application relations when they affect meaning.
   - Do not impose a false linear order on independent ideas.

3. Resolve the destination.
   - Use the file explicitly named by the user.
   - Otherwise follow a clearly established inheritance document, knowledge router, or project writing route before guessing from filenames.
   - Keep one semantic idea in one canonical main file. Synchronize an inheritance entry only when the new material changes what future work must know.
   - If no router exists, inspect the current workspace for one clearly established ideas, research-notes, decisions, or project-memory file.
   - If there is no unambiguous destination, show the distilled preview and ask one concise question for the target path before writing.
   - Never place project knowledge inside the skill directory.

4. Read the destination before editing.
   - Preserve its language, structure, terminology, heading depth, identifiers, and ordering rules.
   - Search for semantic duplicates, earlier versions, conflicts, and cross-references.

5. Extract only durable items. Prefer material that is specific, difficult to reconstruct, decision-relevant, reusable, or likely to affect later work:
   - user goals, requirements, and non-negotiable constraints;
   - decisions and the reasons or tradeoffs behind them;
   - original ideas, hypotheses, models, definitions, and distinctions;
   - verified findings and their evidence boundary;
   - unresolved questions, counterexamples, risks, and rejected alternatives that still matter;
   - concrete next actions only when they follow from the retained ideas.

6. Remove noise.
   - Omit greetings, coordination chatter, generic explanations, repeated assistant paraphrases, abandoned scaffolding, and low-information process logs.
   - Do not retain a detail merely because it appeared often.
   - Do not silently delete a superseded idea when its history explains the current one; mark the relationship instead.

7. Normalize each retained idea as an atomic record containing as much as the evidence supports:
   - **Idea/decision:** one clear proposition;
   - **Why it matters:** effect on the project or later reasoning;
   - **Status:** one of `用户明确`, `已验证`, `工作假设`, `模型推断`, `待确认`, `已替代`, `已否定`;
   - **Basis:** source turn, named file, paper, experiment, or `来自对话摘要` when available;
   - **Relations:** refines, contradicts, replaces, depends on, or applies to another item;
   - **Open edge:** uncertainty or next validation, only if material.

8. Merge conservatively.
   - Keep one canonical entry for the same semantic idea.
   - Append genuinely new ideas.
   - Update an existing entry only when the new material clarifies, strengthens, narrows, contradicts, or supersedes it.
   - Preserve meaningful revision history with `replaces`, `refines`, or `contradicts`; never blend conflicting claims into a false consensus.
   - Use the smallest relevant edit. Do not rewrite unrelated sections.
   - Do not overwrite raw conversations or source evidence.
   - For a thesis, final manuscript, submission file, core project specification, or other high-stakes document, present the proposed patch and obtain confirmation before modifying it.

9. Verify after writing.
   - Re-read the changed section.
   - Check that every strong claim has the correct status and basis.
   - Check that no user requirement, negative result, or unresolved contradiction was converted into a settled conclusion.
   - Confirm that duplicates were merged without losing distinct meanings.
   - Confirm that unrelated files were untouched and any inheritance-entry synchronization was actually necessary.

## Default Markdown Shape

Use the destination's existing schema when present. Otherwise use this compact shape; omit empty fields:

```markdown
## <date or topic>

### <idea title>

- Idea/decision: ...
- Why it matters: ...
- Status: 用户明确 | 已验证 | 工作假设 | 模型推断 | 待确认 | 已替代 | 已否定
- Basis: ...
- Relations: ...
- Open edge: ...
```

Do not create a new dated section on every invocation when the content belongs under an existing topic.

## Reporting

After completion, show the result in the response as well as writing it to disk:

- list the most important retained ideas;
- link the destination file and identify the changed section;
- state whether entries were added, merged, refined, contradicted, or superseded;
- list any items left uncertain because the conversation was compacted or the evidence was incomplete.

Never report only that a file was updated.
