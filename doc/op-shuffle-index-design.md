# OpShuffleIndex 设计文档

## 一、概述

`OpShuffleIndex`（opcode 6478）是一个 warp/simdgroup 内的线程数据交换指令：将 `Index` 线程的 `val` 数据广播/赋值到当前线程，返回交换后的值。

### 1.1 GLSL 函数签名

```glsl
int32_t shufidx(int32_t val, int32_t idx);
```

- `val`：当前线程持有的待交换数据，类型 `OpTypeInt(32-bit signed)`。
- `idx`：源 thread 索引，类型 `int32`，范围 `0-31`。
- 返回值：来自 `idx` 线程的 `val`，类型与 `val` 相同。

不需要新增 SPIR-V Capability，也不需要新增变量类型。

---

## 二、指令格式

```
| Word Count | Opcode | <id> Result Type | Result <id> | <id> Value | <id> Index |
| 5          | 6478   | Result Type <id> | Result <id> | Value <id> | Index <id> |
```

- `hasResult = true`，`hasResultType = true`
- Result Type 必须是 `OpTypeInt(32-bit signed)`
- Value 是要交换的数据，类型必须匹配 Result Type
- Index 是源 thread 索引，类型为 int32（范围 0-31），类型必须匹配 Result Type

`Word Count + Opcode + Results + Operands`：
1. word0 高 16 位为 word count，低 16 位为 opcode
2. Results = Result Type + Result `<id>`（各 32 位）
3. Operands = Value `<id>` + Index `<id>`（各 32 位）

---

## 三、实现设计

### 3.1 需要修改的文件

| 文件 | 修改内容 |
|------|----------|
| `spirv.h` / `spirv.hpp` | 添加 `OpShuffleIndex = 6478` 枚举、`HasResultAndType`（均 true）、名称字符串 |
| `spirv_glsl.cpp` | `emit_instruction()` 添加 case，生成 `shufidx(...)` 内联表达式 |
| `gen_test_spv.py` | 添加 opcode 常量、`gen_shuffle_index_test`、main dispatch |

本指令操作标量 `OpTypeInt` 类型，复用既有类型系统，因此**不需要**修改 `spirv_common.hpp`、`spirv_parser.cpp`、`spirv_cross.cpp`。

### 3.2 指令发射

`OpShuffleIndex` 产生标量 int 结果，按二元函数调用内联发射：

```cpp
case OpShuffleIndex:
{
    if (length < 4)
        SPIRV_CROSS_THROW("Not enough operands for OpShuffleIndex.");

    uint32_t result_type = ops[0];
    uint32_t id = ops[1];
    uint32_t value = ops[2];
    uint32_t index = ops[3];

    bool forward = should_forward(value) && should_forward(index);
    emit_op(result_type, id,
            join("shufidx(", to_expression(value), ", ", to_expression(index), ")"), forward);
    inherit_expression_dependencies(id, value);
    inherit_expression_dependencies(id, index);
    break;
}
```

- 使用 `emit_op` 将结果注册为可内联表达式（与 `OpCooperativeMatrixReduceHW` 等一致）。
- `should_forward` 决定是否内联（无副作用函数，可内联）。
- `inherit_expression_dependencies` 保证操作数表达式在结果之前被刷新。

---

## 四、测试用例

### 4.1 测试文件

| 文件名 | 生成函数 | 覆盖范围 |
|--------|----------|----------|
| `test_hw_shuffle_index.spv` | `gen_shuffle_index_test` | `OpShuffleIndex` 标量调用，结果写入输出 buffer |

测试 SPV 结构：声明 signed int 类型、输出 SSBO、常量 `val=5` / `idx=2`，调用 `OpShuffleIndex` 得到 `result`，再 `OpStore` 到输出 buffer。

### 4.2 期望 GLSL 输出

```glsl
output._m0[0] = shufidx(5, 2);
```

---

## 五、参考

- [总体设计文档](design.md) — `## OpShuffleIndex` 章节
- 同类 intrinsic 实现：cp-async 指令（[cp-async-design.md](cp-async-design.md)）
