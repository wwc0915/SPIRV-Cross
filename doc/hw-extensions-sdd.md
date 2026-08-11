# HW 硬件扩展软件设计说明书

## 1. 总体软件功能

### 1.1 概述

SPIRV-Cross 新增对三个硬件（HW）神经网络扩展的支持，面向神经网络推理（NPU/GPU 硬件加速）场景：

| SPIR-V 扩展 | GLSL 扩展 | 功能域 |
|---|---|---|
| `SPV_HW_neural_shader` | `GL_HW_neural_shader` | 硬件协作矩阵运算 |
| `SPV_HW_neural_shader` | `GL_HW_neural_shader` | 硬件协作向量运算 |
| `SPV_HW_neural_shader` | `GL_HW_neural_shader` | 神经着色器（张量映射/异步拷贝/屏障/shuffle） |

**设计原则：** 仅 GLSL 后端实现真实指令发射；MSL/HLSL/CPP/Reflect 后端在 `compile()` 入口处快速拒绝，避免错误地将 GLSL 内建函数泄漏到非 GLSL 输出。

### 1.2 功能范围

1. **类型声明解析** — 解析 `OpTypeCooperativeMatrixHW`、`OpTypeCooperativeVectorHW`、`OpTypeTensorMapHW` 三种新类型指令
2. **协作矩阵运算** — 加载 / 存储 / 乘加 / 乘法 / 归约 / 长度查询（6 条指令）
3. **协作向量运算** — 加载 / 存储 / 矩阵乘 / 矩阵乘加（4 条指令）
4. **神经着色器** — 张量映射、cp-async 异步拷贝、barrier 屏障同步、shuffle 索引、字节重排、shuffle 填充下移（9 条指令）
5. **类型转换与 bitcast** — CoopMatHW/CoopVecHW 与标量类型间的转换、HW 类型间的 bitcast
6. **常量表达式** — CoopMatHW/CoopVecHW 常量的 GLSL 构造函数生成
7. **访问链索引** — CoopVecHW 分量的 `[]` 下标访问与字节偏移折叠
8. **变量依赖跟踪** — HW 加载/存储指令接入核心编译器的读写分析、接口变量检测、块级写跟踪
9. **后端拒绝机制** — 非 GLSL 后端 fail-fast 拒绝，抛出明确错误信息
10. **寄存器控制属性** — `OpSelectionMerge` 的 `SelectionControl` 掩码新增 `Relreg` 位；GLSL 后端在还原 `if` 语句前输出 `[[reg_control]]` 前缀

### 1.3 架构层次与数据流

```
SPIR-V 字节码
    │
    ▼
┌─ 解析层 (spirv_parser.cpp) ──────────────────────┐
│  OpTypeCooperativeMatrixHW  → SPIRType{CoopMatHW} │
│  OpTypeCooperativeVectorHW  → SPIRType{CoopVecHW} │
│  OpTypeTensorMapHW          → SPIRType{TensorMap} │
│  OpSelectionMerge           → SPIRBlock.reg_control│
└────────────────────────────────────────────────────┘
    │
    ▼
┌─ IR 层 (spirv_common.hpp) ───────────────────────┐
│  SPIRType::BaseType += CoopMatHW / CoopVecHW /    │
│                        TensorMap                  │
│  SPIRType::ext += coopMatHW / coopVecHW /         │
│                   tensorMap                       │
│  SPIRBlock += reg_control (Relreg 掩码)          │
└────────────────────────────────────────────────────┘
    │
    ▼
┌─ 核心编译器 (spirv_cross.cpp) ───────────────────┐
│  变量依赖跟踪: HW Load/Store 接入                  │
│  • read-dependency 注册                            │
│  • interface-variable 使用检测                     │
│  • access-chain 指针源归类                         │
│  • block-level 写跟踪                              │
└────────────────────────────────────────────────────┘
    │
    ├──────────────────┬───────────────┬──────────┐
    ▼                  ▼               ▼          ▼
┌─ GLSL 后端 ─────┐ ┌─ MSL ──────┐ ┌─ HLSL ───┐ ┌─ CPP/Reflect ─┐
│ type_to_glsl()  │ │ reject()   │ │ reject() │ │ reject()      │
│ emit_instruction│ │ (fail-fast)│ │          │ │               │
│ constant_*()    │ └────────────┘ └──────────┘ └───────────────┘
│ convert/bitcast │
│ access_chain    │
│ branch():       │
│  [[reg_control]]│
│ (完整实现)      │
└─────────────────┘
```

### 1.4 新增 SPIR-V 指令一览

| 指令 | Opcode | 扩展 | 有结果 | 有结果类型 |
|---|---|---|---|---|
| `OpTypeCooperativeMatrixHW` | 6601 | neural_matrix | ✓ | ✗ |
| `OpCooperativeMatrixLengthHW` | 6602 | neural_matrix | ✓ | ✓ |
| `OpCooperativeMatrixLoadHW` | 6603 | neural_matrix | ✓ | ✓ |
| `OpCooperativeMatrixStoreHW` | 6604 | neural_matrix | ✗ | ✗ |
| `OpCooperativeMatrixMulAddHW` | 6605 | neural_matrix | ✓ | ✓ |
| `OpCooperativeMatrixReduceHW` | 6606 | neural_matrix | ✓ | ✓ |
| `OpTypeCooperativeVectorHW` | 6608 | cooperative_vector | ✓ | ✗ |
| `OpCooperativeVectorLoadHW` | 6609 | cooperative_vector | ✓ | ✓ |
| `OpCooperativeVectorStoreHW` | 6610 | cooperative_vector | ✗ | ✗ |
| `OpCooperativeVectorMatrixMulAddHW` | 6611 | cooperative_vector | ✓ | ✓ |
| `OpCooperativeVectorMatrixMulHW` | 6612 | cooperative_vector | ✓ | ✓ |
| `OpTypeTensorMapHW` | 6613 | neural_shader | ✓ | ✗ |
| `OpCpAsyncTensorGlobalSharedHW` | 6614 | neural_shader | ✗ | ✗ |
| `OpCpAsyncCommitGroupHW` | 6615 | neural_shader | ✗ | ✗ |
| `OpCpAsyncWaitGroupHW` | 6616 | neural_shader | ✗ | ✗ |
| `OpBarrierArriveHW` | 6617 | neural_shader | ✗ | ✗ |
| `OpBarrierWaitHW` | 6618 | neural_shader | ✗ | ✗ |
| `OpShuffleIndexHW` | 6619 | neural_shader | ✓ | ✓ |
| `OpBytePermuteHW` | 6620 | neural_shader | ✓ | ✓ |
| `OpShuffleFillDownHW` | 6621 | neural_shader | ✓ | ✓ |

新增 Capability：`CapabilityCooperativeMatrixHW = 6600`、`CapabilityCooperativeVectorHW = 6607`。`SPV_HW_neural_shader` 无 Capability，仅通过 `OpExtension` 声明。

> **注：** 寄存器控制属性 `Relreg` 不新增 SPIR-V 指令，仅复用既有 `OpSelectionMerge`（opcode 247）的 `Selection Control` 掩码新增一位 `SpvSelectionControlRelregMask = 0x00000004`（`SpvSelectionControlRelregShift = 2`）。该位与 `Flatten`/`DontFlatten` 位级正交，可组合使用，`hasResult = false`，`hasResultType = false`。

---

## 2. 新增数据结构

### 2.1 SPIRType::BaseType 枚举新增 (`spirv_common.hpp`)

```cpp
enum BaseType {
    ...                      // 既有类型
    CoopMatHW,               // 硬件协作矩阵类型
    CoopVecHW,               // 硬件协作向量类型
    TensorMap,               // 张量映射类型
    ...
};
```

### 2.2 SPIRType::ext 联合体新增 (`spirv_common.hpp`)

```cpp
union {
    struct {
        uint32_t component_type_id;   // 分量元素类型 ID
        uint32_t rows_id;             // 行数常量 ID
        uint32_t cols_id;             // 列数常量 ID
        uint32_t use_id;              // 用途标识（可选，0=A/B/Accumulator）
    } coopMatHW;
    struct {
        uint32_t component_type_id;   // 分量元素类型 ID
        uint32_t component_count_id;  // 分量个数常量 ID
    } coopVecHW;
    struct {
        uint32_t dimensions;          // 维度数 (1/2/3/4)
    } tensorMap;
} ext;
```

### 2.3 SPIRBlock::reg_control 字段新增 (`spirv_common.hpp`)

```cpp
struct SPIRBlock : IVariant {
    Terminator terminator = Unknown;
    Merge merge = MergeNone;
    Hints hint = HintNone;
    bool reg_control = false;   // OpSelectionMerge Relreg 掩码置位时为真
    // ...
};
```

- **设计说明：** 既有 `SPIRBlock::hint` 是单值枚举（`HintFlatten`/`HintDontFlatten` 互斥），无法同时表达 "flatten + reg_control"。`reg_control` 语义上与展平无关，因此采用独立布尔字段，与 `hint` 位级正交、可组合。

---

## 3. 新增函数详细描述

### 3.1 解析层 — `spirv_parser.cpp`

#### `Parser::parse()` — HW 类型声明分支

**函数签名：** `void Parser::parse(const Instruction &instruction)`（既有函数，新增 case 分支）

**所属文件：** `spirv_parser.cpp`

**新增 case：**

##### `case OpTypeCooperativeMatrixHW` (行 793–811)

- **功能：** 解析 `OpTypeCooperativeMatrixHW` 类型声明指令，创建 `SPIRType` 并填充 HW 矩阵字段。
- **关键逻辑：**
  1. 创建 `SPIRType`，设 `basetype = SPIRType::CoopMatHW`，记录 `op`
  2. 填充 `ext.coopMatHW`：
     - `component_type_id = ops[1]`（分量元素类型 ID）
     - `rows_id = ops[2]`（行数常量 ID）
     - `cols_id = ops[3]`（列数常量 ID）
     - `use_id = (length > 4) ? ops[4] : 0`（用途标识，可选操作数）
  3. 设 `parent_type = ops[1]`，从分量类型复制 `width`（位宽）

##### `case OpTypeCooperativeVectorHW` (行 813–828)

- **功能：** 解析 `OpTypeCooperativeVectorHW` 类型声明指令。
- **关键逻辑：**
  1. 创建 `SPIRType`，设 `basetype = SPIRType::CoopVecHW`
  2. 填充 `ext.coopVecHW`：
     - `component_type_id = ops[1]`
     - `component_count_id = ops[2]`
  3. 设 `parent_type = ops[1]`，复制 `width`

##### `case OpTypeTensorMapHW` (行 830–840)

- **功能：** 解析 `OpTypeTensorMapHW` 类型声明指令。
- **关键逻辑：** 设 `basetype = SPIRType::TensorMap`，`ext.tensorMap.dimensions = ops[1]`，设 `self = id`。

##### `case OpSelectionMerge` — Relreg 掩码解析 (行 1242–1245)

- **功能：** 在既有 `OpSelectionMerge` 解析分支中，检测新增的 `SpvSelectionControlRelregMask` 位。
- **关键逻辑：** 既有逻辑按 `ops[1]` 设置 `current_block->hint`（`HintFlatten`/`HintDontFlatten`）；新增 `if (ops[1] & SpvSelectionControlRelregMask) current_block->reg_control = true;`。该位与 flatten/dont_flatten 正交，不互斥，因此独立于 `hint` 检测。

---

### 3.2 核心编译器 — `spirv_cross.cpp`

以下均为既有函数中新增的 switch case，使 HW 指令接入变量依赖分析框架。

#### 3.2.1 `Compiler::analyze_variable_cache()` — 读依赖注册 (行 372–388)

- **功能：** 将 `OpCooperativeMatrixLoadHW`、`OpCooperativeVectorLoadHW` 与 `OpLoad`/`OpImageRead` 同组处理，注册 `ops[2]`（指针操作数）的后备变量为 `dependee`。
- **条件：** 跳过 Function 存储类和 Image/Subpass 类型。

#### 3.2.2 接口变量使用检测 (行 822–837)

- **功能：** 检测 HW Store 指令对接口变量的写入。
- **关键逻辑：**
  - `OpCooperativeVectorStoreHW`：指针为 `args[0]`（与 `OpStore` 一致）
  - `OpCooperativeMatrixStoreHW`：指针为 `args[0]`，指令操作数布局为 `(Pointer, Object, srcShape, srcOffset, layout, [MemOps])`，遵循标准 SPIR-V store 约定（Pointer 在前，Object 在后）

#### 3.2.3 access-chain 指针源归类 (行 921–944)

- **功能：** 将 `OpCooperativeMatrixLoadHW`、`OpCooperativeVectorLoadHW` 加入 `OpAccessChain`/`OpLoad`/`OpPtrAccessChain` 组，使其指针操作数被识别为变量源。

#### 3.2.4 `Compiler::CfgBuilder` — 块级写跟踪 (行 3477–3505)

- **功能：** 将 `OpCooperativeMatrixStoreHW`、`OpCooperativeVectorStoreHW` 加入 `OpStore` 处理路径。
- **关键逻辑：**
  - 所有三个 opcode（OpStore、OpCooperativeMatrixStoreHW、OpCooperativeVectorStoreHW）的指针操作数均在 `args[0]`，遵循标准 SPIR-V store 约定
  - 更新 `accessed_variables_to_block`
  - 根据指针是否为裸变量（vs access chain）选择 `complete_write` 或 `partial_write`
  - 对指针和 Object 值均调用 `notify_variable_access`

---

### 3.3 GLSL 后端 — `spirv_glsl.hpp` / `spirv_glsl.cpp`

#### 3.3.1 `CompilerGLSL::reject_hw_neural_extensions()` (行 640–652)

- **声明：** `spirv_glsl.hpp:1001` — `void reject_hw_neural_extensions();`
- **功能：** 在非 GLSL 后端的 `compile()` 入口处快速拒绝 HW 扩展，抛出明确错误。
- **关键逻辑（双重检测）：**
  1. 遍历 `ir.declared_extensions`，若任一扩展名以 `"SPV_HW_"` 前缀开头则抛异常
  2. 遍历 `ir.declared_capabilities`，若存在 `CapabilityCooperativeMatrixHW` 或 `CapabilityCooperativeVectorHW` 则抛异常
- **设计原因：** `SPV_HW_neural_shader` 无 Capability（仅 `OpExtension` 声明），靠前缀检测捕获；矩阵/向量测试可能仅声明 Capability，靠 Capability 检测捕获。两者并集覆盖所有声明方式。
- **调用点：** `spirv_msl.cpp:1584`、`spirv_hlsl.cpp:6769`、`spirv_cpp.cpp:314`、`spirv_reflect.cpp:274`（各后端 `compile()` 首行）

#### 3.3.2 `CompilerGLSL::type_to_glsl()` — HW 类型渲染 (行 16760–16779)

- **功能：** 将 `SPIRType` 的 HW BaseType 转为 GLSL 类型字符串。
- **分支：**

| BaseType | 要求扩展 | 输出格式 | 示例 |
|---|---|---|---|
| `CoopMatHW` | `GL_HW_neural_shader` | `coopmatHW<CompT, rowsU, colsU>` | `coopmatHW<float, 16u, 16u>` |
| `CoopVecHW` | `GL_HW_neural_shader` | `coopvecHW<CompT, countU>` | `coopvecHW<float, 128u>` |
| `TensorMap` | `GL_HW_neural_shader` | `tensorMap<dims>D` | `tensorMap2D` |

- **关键逻辑：** 从 `ext` 联合体读取分量类型 ID 和维度常量，递归调用 `type_to_glsl(component_type)` 获取分量类型字符串，行/列/个数从常量 ID 经 `evaluate_constant_u32()` 读取，支持普通常量和特化常量（`OpSpecConstant`、`OpSpecConstantOp`）。

#### 3.3.3 `CompilerGLSL::constant_expression()` — HW 常量构造 (行 6072–6146)

- **功能：** 生成 CoopMatHW/CoopVecHW 常量的 GLSL 构造表达式。
- **关键逻辑：**
  1. 从 `ext` 获取分量类型，递归确定分量 BaseType（Float/Half/Int/UInt/Short/UShort）
  2. 遍历 `c.vector_size()` 个分量值
  3. 按分量类型调用 `convert_float_to_string` / `convert_half_to_string` / `convert_to_string`（含 int16/uint16 后缀）
  4. 输出 `type(v0, v1, ...)` 形式
  5. 不支持的分量类型抛 `SPIRV_CROSS_THROW`

#### 3.3.4 `CompilerGLSL::access_chain_internal()` — CoopVecHW 分量访问 (行 10728–10742)

- **功能：** 处理 CoopVecHW 类型的 `[]` 下标访问，降级到分量标量类型。
- **关键逻辑：**
  1. 发射 `[index]` 下标
  2. 降级到 `parent_type`（分量类型）
  3. 清除 `is_packed` / `physical_type` 标记

#### 3.3.5 `access_chain_internal` (flatten/offset 变体) — CoopVecHW 字节偏移 (行 11364–11385)

- **功能：** 在 flatten 模式下计算 CoopVecHW 分量访问的字节偏移。
- **关键逻辑：**
  - 若 index 为常量：折叠 `index * (width / 8)` 到字节偏移
  - 若 index 为动态值：发射 `index * (stride / word_stride) +` 表达式；若 stride 不能被 word_stride 整除则抛异常

#### 3.3.6 类型转换与 bitcast (行 13785–13888)

在既有 `OpSConvert` / `OpConvertSToF` / `OpUConvert` / `OpConvertUToF` / `OpConvertFToU` / `OpConvertFToS` / `OpBitcast` 的 case 中新增 CoopMatHW/CoopVecHW 早返回分支。

- **标量转换（OpSConvert 等）：** 若结果类型为 HW 类型，发射构造函数调用 `type_to_glsl_constructor(type)(arg)`，跳过标量转换路径。
- **OpBitcast（行 13849–13880）：**
  - 若结果和参数**均为** HW 类型：在**分量类型**上查找 `bitcast_glsl_op(out_component, in_component)`；若为同宽整数间 bitcast（返回标量构造函数名如 `"int"`），改用目标 HW 类型构造函数（避免 `int(coopmatHW<...>)` 非法表达式）；若存在命名 bitcast 操作（如 `floatBitsToInt`）则发射该操作；否则用构造函数
  - 若仅结果为 HW 类型：用构造函数 `type_to_glsl_constructor(type)(arg)`

#### 3.3.7 `CompilerGLSL::emit_instruction()` — HW 指令发射 (行 15567–15893)

以下为 `emit_instruction()` 中新增的所有 HW case 分支：

##### `OpCooperativeMatrixLengthHW` (行 15567–15576)

- **GLSL 输出：** `type(res).type(arg)(0).length())`
- **功能：** 查询 HW 协作矩阵的元素个数。结果从 `ops[2]` 的形状类型构造。

##### `OpCooperativeMatrixLoadHW` (行 15578–15603)

- **GLSL 输出：** `coopMatLoadHW(id, ptr, srcShape, srcOffset, <layout>);`
- **功能：** 从内存加载 HW 协作矩阵。
- **关键逻辑：**
  - layout 常量 0 → `gl_CooperativeMatrixLayoutRowMajorHW`，否则 → `gl_CooperativeMatrixLayoutColumnMajorHW`
  - 调用 `register_read(id, ptr)` 注册读依赖

##### `OpCooperativeVectorLoadHW` (行 15605–15622)

- **GLSL 输出：** `coopVecLoadHW(id, ptr, offset);`
- **功能：** 从内存加载 HW 协作向量。调用 `register_read`。

##### `OpCooperativeVectorMatrixMulAddHW` (行 15624–15643)

- **GLSL 输出：** `coopVecMatMulAddHW(id, vector, matrix, bias);`
- **功能：** HW 协作向量与矩阵的乘加运算（带 bias）。

##### `OpCooperativeVectorMatrixMulHW` (行 15645–15662)

- **GLSL 输出：** `coopVecMatMulHW(id, vector, matrix);`
- **功能：** HW 协作向量与矩阵的乘法（无 bias）。

##### `OpCooperativeMatrixMulAddHW` (行 15664–15702)

- **GLSL 输出：** `coopMatMulAddHW(id, a, b, c);` 或 `coopMatMulHW(id, a, b);`
- **功能：** HW 协作矩阵乘加 / 乘法。
- **关键逻辑：** 若 `ops[4]`（C 操作数）为 `OpUndef` 或 null 常量，则省略 C，发射 `coopMatMulHW`；否则发射 `coopMatMulAddHW`。

##### `OpCooperativeMatrixReduceHW` (行 15704–15731)

- **GLSL 输出：** `coopMatReduceHW(matrix, <mask>, <op>);`
- **功能：** HW 协作矩阵归约。
- **关键逻辑：**
  - mask 常量 0 → `gl_CooperativeMatrixReduceRowHW`，否则 → `gl_CooperativeMatrixReduceColumnHW`
  - op 常量 0/1/2 → `Add` / `Min` / `Max`

##### `OpCooperativeMatrixStoreHW` (行 15733–15755)

- **GLSL 输出：** `coopMatStoreHW(object, ptr, srcShape, srcOffset, <layout>);`
- **功能：** 将 HW 协作矩阵存储到内存。调用 `register_write(object)`。

##### `OpCooperativeVectorStoreHW` (行 15757–15771)

- **GLSL 输出：** `coopVecStoreHW(object, ptr, offset);`
- **功能：** 将 HW 协作向量存储到内存。调用 `register_write`。

##### `OpCpAsyncTensorGlobalSharedHW` (行 15773–15787)

- **GLSL 输出：** `cp_async_tensor_global_shared(dstPtr, tensorMap, coord);`
- **功能：** 张量映射的 global↔shared 异步拷贝。要求 `GL_HW_neural_shader`。维度从类型推断，不发射到 GLSL。

##### `OpCpAsyncCommitGroupHW` (行 15789–15794)

- **GLSL 输出：** `cp_async_commit_group();`
- **功能：** 提交一组 cp-async 操作。无操作数。

##### `OpCpAsyncWaitGroupHW` (行 15796–15805)

- **GLSL 输出：** `cp_async_wait_group(n);`
- **功能：** 等待 cp-async 组完成，`ops[0]` 为等待阈值 N。

##### `OpBarrierArriveHW` (行 15807–15817)

- **GLSL 输出：** `barrier_arrive(barrierId, barrierN);`
- **功能：** 到达屏障（非阻塞）。

##### `OpBarrierWaitHW` (行 15819–15829)

- **GLSL 输出：** `barrier_wait(barrierId, barrierN);`
- **功能：** 等待屏障。

##### `OpShuffleIndexHW` (行 15831–15848)

- **GLSL 输出：** `shufidx(value, index)`
- **功能：** 硬件 shuffle 索引操作。若两操作数均可 forward 则转发，继承依赖。

##### `OpBytePermuteHW` (行 15850–15870)

- **GLSL 输出：** `bytePrmt(src0, src1, mask)`
- **功能：** 字节重排。从全部 3 个操作数继承依赖。

##### `OpShuffleFillDownHW` (行 15872–15893)

- **GLSL 输出：** `shuffle_fill_down(src, fill, shift)`
- **功能：** shuffle 填充下移。从全部 3 个操作数继承依赖。

#### 3.3.8 `CompilerGLSL::branch()` — `[[reg_control]]` 前缀发射 (行 17550–17580)

- **功能：** 在还原 `if`/`if-else` 语句前，按 `from_block.reg_control` 和 `from_block.hint` 决定属性前缀，使其与 `if` 同行。
- **关键逻辑：**
  - 若 `reg_control` 为真：`require_extension_internal("GL_HW_neural_shader")`，设 `prefix = "[[reg_control]] "`。
  - 若同时存在 `HintFlatten`/`HintDontFlatten`：
    - `reg_control` 为真时：合并为单个属性 `[[flatten, reg_control]]` 或 `[[branch, reg_control]]`，并 `require_extension_internal("GL_EXT_control_flow_attributes")`（glslang 不接受分开的 `[[flatten]] [[reg_control]]`）
    - `reg_control` 为假时：走原有 `emit_block_hints()` 宏路径
  - true 分支需代码时：`statement(prefix, "if (", to_expression(cond), ")");`
  - 仅 false 分支需代码时：`statement(prefix, "if (!", to_enclosed_expression(cond), ")");`
- **设计说明：** `[[reg_control]]` 属于 `GL_HW_neural_shader` 扩展，不属于 `GL_EXT_control_flow_attributes`。但当 `reg_control` 与 flatten/branch hint 共存时，glslang 要求合并为单个 `[[flatten, reg_control]]` 属性说明符（逗号分隔），此时同时需要两个扩展。非 GLSL 后端无需修改（GLSL 专属硬件属性）。

---

### 3.4 其他后端 — reject 调用

各后端 `compile()` 首行调用 `reject_hw_neural_extensions()`：

| 后端 | 文件 | 行号 |
|---|---|---|
| MSL | `spirv_msl.cpp` | 1584 |
| HLSL | `spirv_hlsl.cpp` | 6769 |
| CPP | `spirv_cpp.cpp` | 314 |
| Reflect | `spirv_reflect.cpp` | 274 |

GLSL 后端 `CompilerGLSL::compile()` **不调用** reject，保留完整指令发射。

---

## 4. 新增 GLSL 符号

### 4.1 类型

| GLSL 类型 | 对应 SPIRType | 说明 |
|---|---|---|
| `coopmatHW<CompT, rowsU, colsU>` | CoopMatHW | 硬件协作矩阵 |
| `coopvecHW<CompT, countU>` | CoopVecHW | 硬件协作向量 |
| `tensorMap1D` / `2D` / `3D` / `4D` | TensorMap | 张量映射 |

### 4.2 函数

| GLSL 函数 | 来源指令 |
|---|---|
| `coopMatLoadHW` | OpCooperativeMatrixLoadHW |
| `coopMatStoreHW` | OpCooperativeMatrixStoreHW |
| `coopMatMulAddHW` | OpCooperativeMatrixMulAddHW |
| `coopMatMulHW` | OpCooperativeMatrixMulAddHW (无 C) |
| `coopMatReduceHW` | OpCooperativeMatrixReduceHW |
| `coopVecLoadHW` | OpCooperativeVectorLoadHW |
| `coopVecStoreHW` | OpCooperativeVectorStoreHW |
| `coopVecMatMulAddHW` | OpCooperativeVectorMatrixMulAddHW |
| `coopVecMatMulHW` | OpCooperativeVectorMatrixMulHW |
| `cp_async_tensor_global_shared` | OpCpAsyncTensorGlobalSharedHW |
| `cp_async_commit_group` | OpCpAsyncCommitGroupHW |
| `cp_async_wait_group` | OpCpAsyncWaitGroupHW |
| `barrier_arrive` | OpBarrierArriveHW |
| `barrier_wait` | OpBarrierWaitHW |
| `shufidx` | OpShuffleIndexHW |
| `bytePrmt` | OpBytePermuteHW |
| `shuffle_fill_down` | OpShuffleFillDownHW |

### 4.3 常量

| GLSL 常量 | 值 | 用途 |
|---|---|---|
| `gl_CooperativeMatrixLayoutRowMajorHW` | 0 | 矩阵布局：行主序 |
| `gl_CooperativeMatrixLayoutColumnMajorHW` | 1 | 矩阵布局：列主序 |
| `gl_CooperativeMatrixReduceRowHW` | 0 | 归约掩码：行 |
| `gl_CooperativeMatrixReduceColumnHW` | 1 | 归约掩码：列 |
| `gl_CooperativeMatrixReduceAddHW` | 0 | 归约操作：加法 |
| `gl_CooperativeMatrixReduceMinHW` | 1 | 归约操作：最小值 |
| `gl_CooperativeMatrixReduceMaxHW` | 2 | 归约操作：最大值 |

### 4.4 属性

| GLSL 属性 | 来源 | 说明 |
|---|---|---|
| `[[reg_control]]` | `OpSelectionMerge` 的 `Relreg` 掩码位 | 硬件寄存器控制提示，置于 `if` 语句同行，要求 `GL_HW_neural_shader` 扩展；与 `flatten`/`branch` hint 共存时合并为 `[[flatten, reg_control]]` / `[[branch, reg_control]]`，同时要求 `GL_EXT_control_flow_attributes` |

---

## 5. 设计说明

### 5.1 后端拒绝策略

HW 扩展仅 GLSL 后端支持。非 GLSL 后端在 `compile()` 入口调用 `reject_hw_neural_extensions()`，采用**双重检测**：

1. **扩展名前缀检测**：`SPV_HW_` 前缀覆盖 `SPV_HW_neural_shader`（无 Capability）
2. **Capability 检测**：`CapabilityCooperativeMatrixHW` / `CapabilityCooperativeVectorHW` 覆盖仅声明 Capability 的场景

这确保无论 SPIR-V 用扩展还是 Capability 声明 HW 功能，非 GLSL 后端都能 fail-fast 拒绝。

### 5.2 常量映射内联解析

layout / reduce 等 GLSL 常量在代码中使用内联三元表达式（`const == 0 ? RowMajor : ColumnMajor`）解析，而非查表。这与部分设计文档描述的 `CoopMatHWLayoutNames[]` 查表方案不同，实际实现更简洁。

### 5.3 乘加/乘法统一处理

`OpCooperativeMatrixMulAddHW` 同时处理乘加和乘法：若第三操作数 C 为 `OpUndef` 或 null，省略 C 发射 `coopMatMulHW`，否则发射 `coopMatMulAddHW`。减少了独立乘法指令的需要。

### 5.4 bitcast 分量类型查找

HW 类型间的 `OpBitcast` 在**分量类型**（而非 HW 类型本身）上查找 `bitcast_glsl_op`，因为 GLSL bitcast 内建函数定义在标量类型上。若存在命名操作则发射，否则回退到构造函数。

### 5.5 寄存器控制属性的独立性与组合发射

`Relreg` 复用既有 `OpSelectionMerge` 指令，不新增 SPIR-V 指令、Capability 或扩展声明，仅新增一个掩码位与一个 `SPIRBlock::reg_control` 布尔字段。该属性语义上与展平无关，故不并入互斥的 `hint` 枚举，而以独立布尔字段表达，使其与 `flatten`/`dont_flatten` 位级正交、可组合。

GLSL 后端在 `branch()` 中发射 `[[reg_control]]` 前缀，并 `require_extension_internal("GL_HW_neural_shader")`。当 `reg_control` 与 `flatten`/`branch` hint 共存时，合并为 `[[flatten, reg_control]]` 或 `[[branch, reg_control]]` 单个属性说明符（逗号分隔），同时要求 `GL_EXT_control_flow_attributes` 扩展——因为 glslang 不接受分开的 `[[flatten]] [[reg_control]]` 两个属性说明符。`spirv_cross.cpp`、`spirv_hlsl.cpp`、`spirv_msl.cpp` 均无需修改。
