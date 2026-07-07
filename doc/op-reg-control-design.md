# [[reg_control]] 设计文档

## 一、概述

在 SPIR-V 的 `OpSelectionMerge` 指令的 `Selection Control` 字面量掩码上新增一个枚举位 `Relreg`。
当该位被置位时，GLSL 后端在还原 `if` 语句前输出硬件属性 `[[reg_control]]`，用于提示编译器对该
选择结构进行寄存器控制。

### 1.1 期望 GLSL 输出

```glsl
[[reg_control]] if (idx == 0) {
    producer();
} else {
    consumer();
}
```

`[[reg_control]]` 与 `if` 处于同一行，是一个独立于 `flatten`/`dont_flatten` 的硬件属性，
不走 `GL_EXT_control_flow_attributes` 扩展，也不需要新增 SPIR-V Capability 或变量类型。

---

## 二、指令格式

`OpSelectionMerge`（opcode 247）本身格式不变，仅 `Selection Control` 掩码新增一位：

```
| Word Count | Opcode | <id> Merge Block | Selection Control |
| 3          | 247    | Merge Block <id> | Selection Control |
```

`SelectionControl` 掩码：

| 名称 | 值 | 说明 |
|------|----|------|
| `SelectionControlMaskNone` | 0 | 默认 |
| `SelectionControlFlattenMask` | 0x00000001 | 强展平（既有） |
| `SelectionControlDontFlattenMask` | 0x00000002 | 禁展平（既有） |
| `SelectionControlRelregMask` | 0x00000004 | 寄存器控制（新增） |

- `Relreg` 与 `Flatten`/`DontFlatten` 在位级正交，可组合使用。
- `hasResult = false`，`hasResultType = false`，与既有 `OpSelectionMerge` 一致。

---

## 三、实现设计

### 3.1 需要修改的文件

| 文件 | 修改内容 |
|------|----------|
| `spirv.h` / `spirv.hpp` | `SelectionControlShift` 新增 `RelregShift = 2`；`SelectionControlMask` 新增 `RelregMask = 0x00000004` |
| `spirv_common.hpp` | `SPIRBlock` 新增 `bool reg_control = false;` 字段（与 `hint` 正交，独立于 flatten/branch） |
| `spirv_parser.cpp` | `OpSelectionMerge` 解析分支中，检测 `SelectionControlRelregMask` 并置位 `current_block->reg_control` |
| `spirv_glsl.cpp` | `branch(from, cond, true_block, false_block)` 在发射 `if` 语句前，若 `from_block.reg_control` 为真，将 `[[reg_control]] ` 前缀拼接到 `if` 行 |
| `gen_test_spv.py` | 新增 `gen_reg_control_test`，构造带 `Relreg` 掩码的 `OpSelectionMerge` + `OpBranchConditional` 的 if-else 结构 |

本特性复用既有 `OpSelectionMerge` / 选择分支的解析与控制流骨架，仅新增一个掩码位与一个布尔字段，
**不需要**修改 `spirv_cross.cpp`、`spirv_hlsl.cpp`、`spirv_msl.cpp`（GLSL 专属硬件属性）。

### 3.2 字段选择：独立布尔 vs `Hints` 枚举

既有 `SPIRBlock::hint` 是单值枚举（`HintFlatten`/`HintDontFlatten` 互斥），无法同时表达
"flatten + reg_control"。`reg_control` 语义上与展平无关，因此采用独立布尔字段 `reg_control`，
与 `hint` 位级正交，可组合。

### 3.3 解析（spirv_parser.cpp）

```cpp
case OpSelectionMerge:
{
    // ... 既有 next_block / merge / flatten / dont_flatten 处理 ...

    if (length >= 2)
    {
        if (ops[1] & SelectionControlFlattenMask)
            current_block->hint = SPIRBlock::HintFlatten;
        else if (ops[1] & SelectionControlDontFlattenMask)
            current_block->hint = SPIRBlock::HintDontFlatten;
        if (ops[1] & SelectionControlRelregMask)
            current_block->reg_control = true;
    }
    break;
}
```

### 3.4 指令发射（spirv_glsl.cpp）

在 `CompilerGLSL::branch(BlockID, uint32_t cond, BlockID true_block, BlockID false_block)` 中，
发射 `if` 语句时按需拼接前缀，保证 `[[reg_control]]` 与 `if` 同行：

```cpp
auto prefix = from_block.reg_control ? "[[reg_control]] " : "";

if (true_block_needs_code)
{
    statement(prefix, "if (", to_expression(cond), ")");
    // ...
}
else if (false_block_needs_code)
{
    statement(prefix, "if (!", to_enclosed_expression(cond), ")");
    // ...
}
```

- 不调用 `require_extension_internal`：`[[reg_control]]` 是硬件自定义属性，不属于 `GL_EXT_control_flow_attributes`。
- `emit_block_hints()` 仍只处理 flatten/branch/unroll，不受影响。

---

## 四、测试用例

### 4.1 测试文件

| 文件名 | 生成函数 | 覆盖范围 |
|--------|----------|----------|
| `test_hw_reg_control.spv` | `gen_reg_control_test` | 带 `Relreg` 掩码的 `OpSelectionMerge` + `OpBranchConditional` if-else，两个分支分别写入不同值 |

测试 SPV 结构：声明输入/输出 SSBO（uint 元素）；entry 块从输入 buffer load `idx`，
计算 `idx == 0`；`OpSelectionMerge %merge, 0x4`（Relreg）；`OpBranchConditional` 跳到
true/false 块；true 块写 `1u`，false 块写 `2u`；merge 块 `OpReturn`。
条件来自 buffer 加载，确保 if-else 结构在 GLSL 输出中保留。

### 4.2 期望 GLSL 输出

```glsl
#version 450
layout(local_size_x = 16, local_size_y = 1, local_size_z = 1) in;

void main()
{
    uint _10 = input._m0[0u];
    [[reg_control]] if (_10 == 0u)
    {
        output._m0[0u] = 1u;
    }
    else
    {
        output._m0[0u] = 2u;
    }
}
```

---

## 五、参考

- [总体设计文档](design.md) — `## [[reg_control]]` 章节
- 既有 `OpSelectionMerge` 解析：`spirv_parser.cpp` `case OpSelectionMerge`
- 既有选择属性发射：`spirv_glsl.cpp` `emit_block_hints` / `branch`
