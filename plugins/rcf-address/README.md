# RCF Address

本插件封装 `recursive-field-addressing` Skill 和实验性地址引擎。它根据场、根目标契约、功能位置、必要根路径、递归路径、模态、证据和版本生成可审计的动态地址。

最小调用：

```text
用 RCF Address：为这套结构赋址，检查合法性，并列出潜在、禁止和当前无地址的项目。
```

地址字符串只是导航入口，不是结构正确性的证明。使用前应先形成足以支持赋址的场契约和必要偏序。参见[动态寻址理论](../../docs/dynamic-addressing/README.md)和[最小示例](../../examples/address/README.md)。
