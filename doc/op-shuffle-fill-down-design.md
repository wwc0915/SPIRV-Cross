# OpShuffleFillDown 设计文档

## 一、概述

`OpShuffleFillDown`（opcode 6480）将 `src` 与 `fill` 的数据在 warp lane 间向下 shuffle：lane `i` 取 lane `i+shift` 的 `src` 值，越界的 lane 用 `fill` 填充。

### 1.1 GLSL 函数签名

```glsl
uint32_t shuffle_fill_down(uint32_t src, uint32_t fill, int32_t shift);
```

- `src`：源数据，类型 `OpTypeInt(32-bit unsigned)`。
- `fill`：填充数据，类型同 `src`。
- `shift`：向下移位的量（粒度 32-bit），范围 `0-31`，类型 `OpTypeInt(32-bit signed)`。
- 返回值：shuffle down 后的 32-bit 无符号整数。

不需要新增 SPIR-V Capability，也不需要新增变量类型。

---

## 二、指令格式

```
| Word Count | Opcode | <id> Result Type | Result <id> | <id> Src | <id> Fill | <id> Shift |
| 6          | 6480   | Result Type <id> | Result <id> | Src <id> | Fill <id> | Shift <id> |
```

- `hasResult = true`，`hasResultType = true`
- Result Type 必须是 `OpTypeInt(32-bit unsigned)`
- Src / Fill 类型必须匹配 Result Type
- Shift 类型为 `OpTypeInt(32-bit signed)`

`Word Count + Opcode + Results + Operands`：
1. word0 高 16 位为 word count，低 16 位为 opcode
2. Results = Result Type + Result `<id>`
3. Operands = Src `<id>` + Fill `<id>` + Shift `<id>`

> 注意：与前两个 op 不同，`Shift` 是 **signed** int，`Result/Src/Fill` 是 **unsigned** int。

---

## 三、实现设计

### 3.1 需要修改的文件

| 文件 | 修改内容 |
|------|----------|
| `spirv.h` / `spirv.hpp` | 添加 `OpShuffleFillDown = 6480` 枚举、`HasResultAndType`（均 true）、名称字符串 |
| `spirv_glsl.cpp` | `emit_instruction()` 添加 case，生成 `shuffle_fill_down(...)` 内联表达式 |
| `gen_test_spv.py` | 添加 opcode 常量、`gen_shuffle_fill_down_test`、main dispatch |

本指令操作标量 `OpTypeInt` 类型，复用既有类型系统，**不需要**修改 `spirv_common.hpp`、`spirv_parser.cpp`、`spirv_cross.cpp`。

### 3.2 指令发射

`OpShuffleFillDown` 为三元函数调用，按内联表达式发射：

```cpp
case OpShuffleFillDown:
{
    if (length < 5)
        SPIRV_CROSS_THROW("Not enough operands for OpShuffleFillDown.");

    uint32_t result_type = ops[0];
    uint32_t id = ops[1];
    uint32_t src = ops[2];
    uint32_t fill = ops[3];
    uint32_t shift = ops[4];

    bool forward = should_forward(src) && should_forward(fill) && should_forward(shift);
    emit_op(result_type, id,
            join("shuffle_fill_down(", to_expression(src), ", ", to_expression(fill), ", ",
                 to_expression(shift), ")"),
            forward);
    inherit_expression_dependencies(id, src);
    inherit_expression_dependencies(id, fill);
    inherit_expression_dependencies(id, shift);
    break;
}
```

---

## 四、测试用例

### 4.1 测试文件

| 文件名 | 生成函数 | 覆盖范围 |
|--------|----------|----------|
| `test_hw_shuffle_fill_down.spv` | `gen_shuffle_fill_down_test` | `OpShuffleFillDown` 标量调用，结果写入输出 buffer |

测试 SPV 结构：同时声明 unsigned int 与 signed int 类型、输出 SSBO（unsigned 元素）、
常量 `src=0xCAFEBABE` / `fill=0x11111111`（unsigned）与 `shift=1`（signed），
调用 `OpShuffleFillDown` 得到 `result`，再 `OpStore` 到输出 buffer。

### 4.2 期望 GLSL 输出

```glsl
output._m0[0u] = shuffle_fill_down(3405691582u, 286331153u, 1);
```

（`0xCAFEBABE = 3405691582`，`0x11111111 = 286331153`）

---

## 五、参考

- [总体设计文档](design.md) — `## OpShuffleFillDown` 章节
- 同类 intrinsic 实现：[op-shuffle-index-design.md](op-shuffle-index-design.md)
