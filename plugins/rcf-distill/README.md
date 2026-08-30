# RCF Distill

本插件封装 `distill-conversation-ideas` Skill。它把长对话或零碎讨论中的稳定中心、决定、约束、假设、冲突、剩余和来源，保守地合并到一个唯一知识主文件。

最小调用：

```text
沉淀这段对话：先找到项目唯一知识主文件，再把可复用内容按证据状态合并进去。
```

它不会把推断伪装成用户决定，也不会为了整理得漂亮而抹去冲突和未决问题。参见[最小示例](../../examples/distill/README.md)。

Distill v0.2 还提供可选的 `distill-ledger-1.0` 审计助手，用于持久化、压缩来源、争议或高风险合并。助手只验证模型声明的分类计划并记录应用／延后结果，不自行判断语义或改写母稿。

```bash
python plugins/rcf-distill/skills/distill-conversation-ideas/scripts/distill_ledger.py self-test
```
