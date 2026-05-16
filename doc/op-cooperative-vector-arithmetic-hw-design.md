# CoopVecHW 算术指令设计文档

## 一、概述

允许 `OpTypeCooperativeVectorHW` 类型用于 SPIR-V 算术指令和 GLSL.std.450 扩展指令。这些指令对向量的每个分量逐一执行运算。

**支持的 SPIR-V 算术指令**：

| 指令 | 操作 | 分量类型要求 |
|------|------|-------------|
| OpFNegate | -a | 浮点 |
| OpSNegate | -a | 有符号整数 |
| OpFAdd | a + b | 浮点 |
| OpIAdd | a + b | 整数 |
| OpFSub | a - b | 浮点 |
| OpISub | a - b | 整数 |
| OpFMul | a * b | 浮点 |
| OpIMul | a * b | 整数 |
| OpFDiv | a / b | 浮点 |
| OpSDiv | a / b | 有符号整数 |
| OpUDiv | a / b | 无符号整数 |
| OpVectorTimesScalar | a * s | 浮点 |

**支持的 GLSL.std.450 扩展指令**：
FMin, UMin, SMin, NMin, FMax, UMax, SMax, NMax, FClamp, UClamp, SClamp, NClamp, Step, Exp, Log, Tanh, Atan, Fma

---

## 二、指令格式

### 2.1 一元算术指令

```
| 4 | opcode | <id> Result Type | Result <id> | <id> Operand |
```

### 2.2 二元算术指令

```
| 5 | opcode | <id> Result Type | Result <id> | <id> Operand1 | <id> Operand2 |
```

### 2.3 OpVectorTimesScalar

```
| 5 | 143 | <id> Result Type | Result <id> | <id> Vector | <id> Scalar |
```

### 2.4 GLSL.std.450 扩展指令（以 FMin 为例）

```
| 6+ | 12 | <id> Result Type | Result <id> | <id> Set | literal Opcode | <id> args... |
```

---

## 三、GLSL 目标接口

### 3.1 算术运算符

所有算术指令直接映射到 GLSL 运算符重载：

```glsl
coopvecHW<float, 16u> a, b;

// 一元
coopvecHW<float, 16u> neg = -a;

// 二元
coopvecHW<float, 16u> sum = a + b;
coopvecHW<float, 16u> diff = a - b;
coopvecHW<float, 16u> prod = a * b;
coopvecHW<float, 16u> quot = a / b;

// 向量×标量
coopvecHW<float, 16u> scaled = a * 2.0;
```

### 3.2 GLSL.std.450 内建函数

```glsl
coopvecHW<float, 16u> r;
r = min(a, b);
r = max(a, b);
r = clamp(a, b, c);
r = fma(a, b, c);
r = step(a, b);
r = exp(a);
r = log(a);
r = tanh(a);
r = atan(a);
```

---

## 四、实现设计

### 4.1 无需修改 spirv_glsl.cpp

CoopVecHW 算术指令**无需任何代码修改**即可正常工作。原因如下：

1. **算术运算符指令**（OpFAdd、OpFMul 等）使用 `GLSL_BOP`/`GLSL_UOP` 宏，这些宏调用通用的 `emit_binary_op`/`emit_unary_op` 函数。这些函数只生成 GLSL 表达式（如 `a + b`、`-a`），不涉及类型特定的逻辑。

2. **OpVectorTimesScalar** 使用 `GLSL_BOP(*)` 宏，生成 `a * s` 表达式。

3. **GLSL.std.450 浮点指令**（FMin、FMax、FClamp、Fma、Exp、Log、Tanh、Atan、Step）使用 `emit_binary_func_op`/`emit_unary_func_op`/`emit_trinary_func_op`，生成 `min(a, b)`、`exp(a)` 等函数调用，不涉及类型转换。

4. **类型匹配**：当操作数类型与结果类型相同时（CoopVecHW 算术的典型场景），`emit_binary_op_cast` 中的 `binary_op_bitcast_helper` 会跳过类型转换，直接使用原始表达式。

### 4.2 整数运算的 GLSL.std.450 指令

对于整数分量的 GLSL.std.450 指令（UMin、SMin、UMax、SMax、UClamp、SClamp），这些使用 `emit_binary_func_op_cast` 路径。当分量类型已经匹配时，不需要额外转换。如果需要转换（例如有符号/无符号不匹配），CoopVecHW 类型的 `basetype` 为 `CoopVecHW`，不等于 `int_type` 或 `uint_type`，可能导致转换逻辑异常。在实际使用中，这类操作通常不需要跨符号类型转换。

### 4.3 需要修改的文件

| 文件 | 修改内容 |
|------|----------|
| `gen_test_spv.py` | 添加算术指令 opcode 常量、`gen_coopvec_arith_test` 函数 |

---

## 五、测试用例

### 5.1 测试文件

| 文件名 | 生成函数 | 覆盖范围 |
|--------|----------|----------|
| `test_hw_coopvec_arith.spv` | `gen_coopvec_arith_test` | FAdd、FSub、FMul、FNegate、VectorTimesScalar、FMin、FMax、Fma |

### 5.2 OpFAdd（浮点加法）

**期望 GLSL 输出**：
```glsl
coopvecHW<float, 16u> _20 = _17 + _18;
```

### 5.3 OpFSub（浮点减法）

**期望 GLSL 输出**：
```glsl
coopVecStoreHW(_17 - _18, data._m0[0u]);
```

### 5.4 OpFMul（浮点乘法）

**期望 GLSL 输出**：
```glsl
coopVecStoreHW(_17 * _18, data._m0[0u]);
```

### 5.5 OpFNegate（浮点取反）

**期望 GLSL 输出**：
```glsl
coopVecStoreHW(-_17, data._m0[0u]);
```

### 5.6 OpVectorTimesScalar（向量乘标量）

**期望 GLSL 输出**：
```glsl
coopVecStoreHW(_17 * 2.0, data._m0[0u]);
```

### 5.7 GLSLstd450FMin

**期望 GLSL 输出**：
```glsl
coopVecStoreHW(min(_17, _18), data._m0[0u]);
```

### 5.8 GLSLstd450FMax

**期望 GLSL 输出**：
```glsl
coopVecStoreHW(max(_17, _18), data._m0[0u]);
```

### 5.9 GLSLstd450Fma

**期望 GLSL 输出**：
```glsl
coopVecStoreHW(fma(_17, _18, _20), data._m0[0u]);
```

---

## 六、与 CoopMatHW 算术指令的对比

| 维度 | CoopMatHW | CoopVecHW |
|------|-----------|-----------|
| 实现方式 | 相同——使用通用 GLSL 发射路径 | 相同 |
| 需要代码修改 | 否 | 否 |
| GLSL 运算符 | `+`, `-`, `*`, `/`, 一元 `-` | 相同 |
| OpVectorTimesScalar | 支持 | 支持 |
| GLSL.std.450 浮点指令 | 支持 | 支持 |
| GLSL.std.450 整数指令 | 支持（相同限制） | 支持（相同限制） |

两者完全一致：算术指令通过 GLSL 运算符重载和内建函数自然支持，无需任何 SPIRV-Cross 代码修改。
