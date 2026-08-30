# Distill 最小示例

输入是一段长对话，其中混合了已确认决定、临时设想、互相冲突的说法和以后再处理的问题。

建议调用：

```text
沉淀这段对话到项目唯一知识主文件：
保留来源，区分已确认决定、工作假设和开放问题；
若新内容与旧内容冲突，不要静默覆盖，先登记冲突和剩余。
```

理想输出不是另一份聊天摘要，而是对已有主文件的保守合并：

```text
稳定中心与边界
已确认决定
可复用方法
证据与来源
冲突和被替代版本
未决剩余与重新激活条件
```

Distill 只维护知识，不替代 Focus 的复杂任务建模，也不替代 Address 的结构赋址。

对需要持久化审计的合并，可以先让模型形成候选计划，再用账本验证并保存 `ADD / REFINE / REPLACE / CONTRADICT / NOOP` 分类：

```bash
python plugins/rcf-distill/skills/distill-conversation-ideas/scripts/distill_ledger.py self-test
```

该自检证明账本约束可运行，不证明模型选择的语义分类正确。
