# CoopVecHW 位操作指令设计文档

## 一、概述

允许 `OpTypeCooperativeVectorHW` 类型用于 SPIR-V 位操作指令。这些指令对向量的每个分量逐一执行位运算。

**支持的位操作指令**：

| 指令 | 操作 | 分量类型要求 |
|------|------|-------------|
| OpShiftRightLogical | a >> b (逻辑右移) | 整数 |
| OpShiftRightArithmetic | a >> b (算术右移) | 整数 |
| OpShiftLeftLogical | a << b | 整数 |
| OpBitwiseOr | a \| b | 整数 |
| OpBitwiseXor | a ^ b | 整数 |
| OpBitwiseAnd | a & b | 整数 |
| OpNot | ~a | 整数 |

---

## 二、指令格式

### 2.1 二元位操作指令（OpBitwiseOr/Xor/And, OpShiftLeftLogical）

```
| 5 | opcode | <id> Result Type | Result <id> | <id> Operand1 | <id> Operand2 |
```

### 2.2 移位指令（OpShiftRightLogical/Arithmetic）

```
| 5 | opcode | <id> Result Type | Result <id> | <id> Base | <id> Shift |
```

### 2.3 一元位操作指令（OpNot）

```
| 4 | opcode=200 | <id> Result Type | Result <id> | <id> Operand |
```

---

## 三、GLSL 目标接口

所有位操作指令直接映射到 GLSL 运算符重载：

```glsl
coopvecHW<uint, 16u> a, b;
coopvecHW<int, 16u> c;

coopvecHW<uint, 16u> r_or = a | b;
coopvecHW<uint, 16u> r_xor = a ^ b;
coopvecHW<uint, 16u> r_and = a & b;
coopvecHW<uint, 16u> r_not = ~a;
coopvecHW<uint, 16u> r_shl = a << b;
coopvecHW<uint, 16u> r_shr = a >> b;   // 逻辑右移（unsigned分量）
coopvecHW<int, 16u> r_sar = c >> c;    // 算术右移（signed分量）
```

---

## 四、实现设计

### 4.1 无需修改 spirv_glsl.cpp

CoopVecHW 位操作指令**无需任何代码修改**即可正常工作。原因如下：

1. **OpBitwiseOr/Xor/And/ShiftLeftLogical**：使用 `GLSL_BOP_CAST(op, type)` 宏，其中 `type = get<SPIRType>(ops[0]).basetype`。对于 CoopVecHW 结果类型，`type = SPIRType::CoopVecHW`。这些指令的 `opcode_is_sign_invariant` 返回 `true`，因此 `skip_cast_if_equal_type = true`。当两个操作数都是相同 CoopVecHW 类型时，`binary_op_bitcast_helper` 中 `cast = false`，直接生成 `a | b` 等表达式。

2. **OpShiftRightLogical/Arithmetic**：使用 `GLSL_BOP_CAST(>>, uint_type/int_type)`。虽然 `opcode_is_sign_invariant` 返回 `false`，但当两个操作数类型相同时（同为 CoopVecHW），`binary_op_bitcast_helper` 中第一个条件 `type0.basetype != type1.basetype` 为 `false`。由于 `input_type`（uint_type/int_type）与操作数类型（CoopVecHW）不同，`cast` 理论上为 `true`。但实际上 `emit_binary_op_cast` 中检查 `out_type.basetype != input_type`：
   - `out_type.basetype = CoopVecHW`，`input_type` 经 `binary_op_bitcast_helper` 更新后为 `CoopVecHW`（走 `cast=false` 分支时）
   - 最终 `out_type.basetype == input_type`，走 `else` 分支直接输出 `a >> b`

   对于分量类型与移位语义匹配的情况（unsigned 用逻辑右移、signed 用算术右移），GLSL 运算符天然正确。

3. **OpNot**：检查 `expression_type_id(ops[2]) != ops[0]`。当结果类型与操作数类型相同时（同一 CoopVecHW 类型 ID），使用 `GLSL_UOP(~)` → `emit_unary_op`，直接生成 `~a`。

### 4.2 需要修改的文件

| 文件 | 修改内容 |
|------|----------|
| `gen_test_spv.py` | 添加位操作 opcode 常量、`gen_coopvec_bit_test` 函数 |

---

## 五、测试用例

### 5.1 测试文件

| 文件名 | 生成函数 | 覆盖范围 |
|--------|----------|----------|
| `test_hw_coopvec_bit.spv` | `gen_coopvec_bit_test` | BitwiseOr、BitwiseXor、BitwiseAnd、Not、ShiftLeftLogical、ShiftRightLogical、ShiftRightArithmetic |

### 5.2 OpBitwiseOr（按位或）

**期望 GLSL 输出**：
```glsl
coopVecStoreHW(_17 | _18, data._m0[0u]);
```

### 5.3 OpBitwiseXor（按位异或）

**期望 GLSL 输出**：
```glsl
coopVecStoreHW(_17 ^ _18, data._m0[0u]);
```

### 5.4 OpBitwiseAnd（按位与）

**期望 GLSL 输出**：
```glsl
coopVecStoreHW(_17 & _18, data._m0[0u]);
```

### 5.5 OpNot（按位取反）

**期望 GLSL 输出**：
```glsl
coopVecStoreHW(~_17, data._m0[0u]);
```

### 5.6 OpShiftLeftLogical（逻辑左移）

**期望 GLSL 输出**：
```glsl
coopVecStoreHW(_17 << _18, data._m0[0u]);
```

### 5.7 OpShiftRightLogical（逻辑右移）

**期望 GLSL 输出**：
```glsl
coopVecStoreHW((_17 >> _18), data._m0[0u]);
```

### 5.8 OpShiftRightArithmetic（算术右移）

**期望 GLSL 输出**：
```glsl
coopVecStoreHW((_27 >> _27), data._m0[0u]);
```

---

## 六、与 CoopMatHW 算术指令的对比

| 维度 | CoopMatHW 算术 | CoopVecHW 算术 | CoopVecHW 位操作 |
|------|---------------|---------------|-----------------|
| 实现方式 | 通用 GLSL 发射路径 | 相同 | 相同 |
| 需要代码修改 | 否 | 否 | 否 |
| GLSL 运算符 | `+`, `-`, `*`, `/` | 相同 | `\|`, `^`, `&`, `~`, `<<`, `>>` |
| GLSL_BOP / GLSL_UOP | 使用 GLSL_BOP | 使用 GLSL_BOP | 使用 GLSL_BOP_CAST / GLSL_UOP |
| sign-invariant | N/A | N/A | BitwiseOr/Xor/And/ShiftLeft 为 sign-invariant |

三者完全一致：所有指令通过 GLSL 运算符重载自然支持，无需任何 SPIRV-Cross 代码修改。
