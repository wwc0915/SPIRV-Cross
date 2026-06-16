# OpBytePermute 设计文档

## 一、概述

`OpBytePermute`（opcode 6479）按字节粒度重排两个 32-bit 源数据：从 `Src0` 和 `Src1` 共 8 个字节中，按 `Mask` 选择 4 个字节拼接到输出。

### 1.1 GLSL 函数签名

```glsl
uint32_t bytePrmt(uint32_t src0, uint32_t src1, uint32_t mask);
```

- `src0`：源数据 0，类型 `OpTypeInt(32-bit unsigned)`。
- `src1`：源数据 1，类型同上。
- `mask`：选择掩码，决定哪些字节写入输出，范围 `0x0000-0x7777`，类型同上。
- 返回值：按 mask 重排得到的 32-bit 无符号整数。

不需要新增 SPIR-V Capability，也不需要新增变量类型。

---

## 二、指令格式

```
| Word Count | Opcode | <id> Result Type | Result <id> | <id> Src0 | <id> Src1 | <id> Mask |
| 6          | 6479   | Result Type <id> | Result <id> | Src0 <id> | Src1 <id> | Mask <id> |
```

- `hasResult = true`，`hasResultType = true`
- Result Type 必须是 `OpTypeInt(32-bit unsigned)`
- Src0 / Src1 / Mask 类型必须匹配 Result Type

`Word Count + Opcode + Results + Operands`：
1. word0 高 16 位为 word count，低 16 位为 opcode
2. Results = Result Type + Result `<id>`
3. Operands = Src0 `<id>` + Src1 `<id>` + Mask `<id>`

---

## 三、实现设计

### 3.1 需要修改的文件

| 文件 | 修改内容 |
|------|----------|
| `spirv.h` / `spirv.hpp` | 添加 `OpBytePermute = 6479` 枚举、`HasResultAndType`（均 true）、名称字符串 |
| `spirv_glsl.cpp` | `emit_instruction()` 添加 case，生成 `bytePrmt(...)` 内联表达式 |
| `gen_test_spv.py` | 添加 opcode 常量、`gen_byte_permute_test`、main dispatch |

本指令操作标量 `OpTypeInt` 类型，复用既有类型系统，**不需要**修改 `spirv_common.hpp`、`spirv_parser.cpp`、`spirv_cross.cpp`。

### 3.2 指令发射

`OpBytePermute` 为三元函数调用，按内联表达式发射：

```cpp
case OpBytePermute:
{
    if (length < 5)
        SPIRV_CROSS_THROW("Not enough operands for OpBytePermute.");

    uint32_t result_type = ops[0];
    uint32_t id = ops[1];
    uint32_t src0 = ops[2];
    uint32_t src1 = ops[3];
    uint32_t mask = ops[4];

    bool forward = should_forward(src0) && should_forward(src1) && should_forward(mask);
    emit_op(result_type, id,
            join("bytePrmt(", to_expression(src0), ", ", to_expression(src1), ", ", to_expression(mask), ")"),
            forward);
    inherit_expression_dependencies(id, src0);
    inherit_expression_dependencies(id, src1);
    inherit_expression_dependencies(id, mask);
    break;
}
```

---

## 四、测试用例

### 4.1 测试文件

| 文件名 | 生成函数 | 覆盖范围 |
|--------|----------|----------|
| `test_hw_byte_permute.spv` | `gen_byte_permute_test` | `OpBytePermute` 标量调用，结果写入输出 buffer |

测试 SPV 结构：声明 unsigned int 类型、输出 SSBO、常量
`src0=0x12345678` / `src1=0x9ABCDEF0` / `mask=0x7654`，调用 `OpBytePermute` 得到 `result`，再 `OpStore` 到输出 buffer。

### 4.2 期望 GLSL 输出

```glsl
output._m0[0u] = bytePrmt(305419896u, 2596069104u, 30292u);
```

（`0x12345678 = 305419896`，`0x9ABCDEF0 = 2596069104`，`0x7654 = 30292`）

---

## 五、参考

- [总体设计文档](design.md) — `## OpBytePermute` 章节
- 同类 intrinsic 实现：[op-shuffle-index-design.md](op-shuffle-index-design.md)
