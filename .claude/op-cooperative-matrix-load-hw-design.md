# OpCooperativeMatrixLoadHW 设计文档

## 一、概述

`OpCooperativeMatrixLoadHW` 是 SPV_HW_neural_shader 扩展中的指令，用于从内存加载硬件优化的协作矩阵（Cooperative Matrix）。相比 KHR 标准的 CooperativeMatrixLoad，它增加了对子矩阵区域加载的支持，适用于神经网络推理场景。

---

## 二、SPIR-V 指令规范

### 2.1 指令编码

| 字段 | 值 |
|------|-----|
| Opcode | 6502 |
| Word Count | 5+vars |

**指令格式**:
```
| Word Count | Opcode: 6502 | <id> Result Type | Result <id> | <id> Pointer | <id> srcMatrixShape | <id> srcMatrixOffset | <id> layout |
```

### 2.2 操作数说明

| 操作数 | 类型 | 描述 |
|--------|------|------|
| Result Type | `<id>` | 结果类型，必须是 `OpTypeCooperativeMatrixHW` 类型 |
| Result `<id>` | `<id>` | 加载结果的合作矩阵 ID |
| Pointer | `<id>` | 指向标量/向量数组的指针 (`OpTypePointer`) |
| srcMatrixShape | `<id>` | vec2 类型，表示源矩阵的行数和列数 |
| srcMatrixOffset | `<id>` | vec2 类型，表示从源矩阵的哪个位置开始读取 (行偏移, 列偏移) |
| layout | `<id>` | `CooperativeMatrixLayoutHW` 枚举常量 |

### 2.3 关联枚举定义

**Capability**:
```cpp
CapabilityCooperativeMatrixHW = 6600  // 自定义 capability
```

**CooperativeMatrixLayoutHW**:
```cpp
enum CooperativeMatrixLayoutHW {
    RowMajorHW = 0,      // 行主序
    ColumnMajorHW = 1,   // 列主序
};
```

---

## 三、GLSL 目标接口

### 3.1 GLSL 扩展声明

```glsl
#extension GL_HW_neural_shader : require
```

### 3.2 GLSL 函数签名

```glsl
// 加载子矩阵
void coopMatLoadHW(
    out coopmatHW<T, M, K> mat,      // 输出矩阵
    T buf[],                          // 源数据缓冲区
    uvec2 srcMatrixShape,            // 源矩阵形状 (rows, cols)
    uvec2 srcMatrixOffset,           // 起始偏移 (row_offset, col_offset)
    uint layout                       // 布局方式
);
```

### 3.3 类型表示

```glsl
// 硬件协作矩阵类型
template<typename T, uint M, uint K>
coopmatHW {
    // 内部实现由硬件定义
};
```

---

## 四、用例

### 4.1 基本用例：加载整个矩阵

**GLSL 输入**:
```glsl
#version 450
#extension GL_HW_neural_shader : require

layout(local_size_x = 16) in;

layout(binding = 0) buffer MatrixBuffer {
    float data[];
};

void main() {
    // 定义 16x16 的协作矩阵
    coopmatHW<float, 16, 16> matA;

    // 加载整个 16x16 矩阵，从 (0, 0) 开始
    coopMatLoadHW(matA, data, uvec2(16, 16), uvec2(0, 0), gl_RowMajorHW);

    // 使用 matA...
}
```

**SPIR-V 表示** (伪代码):
```
%mat_type = OpTypeCooperativeMatrixHW %float %uint_16 %uint_16 %MatrixUseMatrixAHW
%matA = OpVariable %mat_ptr_type Function

%shape = OpConstantComposite %v2uint %uint_16 %uint_16
%offset = OpConstantComposite %v2uint %uint_0 %uint_0
%layout = OpConstant %uint 0  ; RowMajorHW

%loaded = OpCooperativeMatrixLoadHW %mat_type %data_ptr %shape %offset %layout
OpStore %matA %loaded
```

**GLSL 输出** (SPIRV-Cross 生成):
```glsl
#version 450
#extension GL_HW_neural_shader : require

layout(local_size_x = 16) in;

layout(binding = 0) buffer MatrixBuffer {
    float data[];
};

void main() {
    coopmatHW<float, 16, 16> matA;
    coopMatLoadHW(matA, data, 16u, 16u, 0u, 0u, gl_RowMajorHW);

    // 使用 matA...
}
```

### 4.2 高级用例：分块加载大矩阵

**场景**: 从一个 64x64 的大矩阵中加载 16x16 的子块，用于矩阵分块乘法。

**GLSL 输入**:
```glsl
#version 450
#extension GL_HW_neural_shader : require

layout(local_size_x = 16, local_size_y = 4) in;

layout(binding = 0) buffer InputMatrix {
    float input[64 * 64];  // 64x64 矩阵
};

layout(binding = 1) buffer OutputMatrix {
    float output[64 * 64];
};

void main() {
    // 当前 workgroup 处理的子块位置
    uint blockRow = gl_WorkGroupID.y;  // 0-3
    uint blockCol = gl_WorkGroupID.x;  // 0-3

    // 计算子块偏移
    uint rowOffset = blockRow * 16;
    uint colOffset = blockCol * 16;

    coopmatHW<float, 16, 16> block;

    // 从大矩阵的指定位置加载 16x16 子块
    coopMatLoadHW(
        block,
        input,
        uvec2(64, 64),           // 源矩阵是 64x64
        uvec2(rowOffset, colOffset),  // 子块起始位置
        gl_RowMajorHW
    );

    // 处理 block...
}
```

**SPIR-V 表示** (关键部分):
```
; 类型定义
%mat16x16 = OpTypeCooperativeMatrixHW %float %uint_16 %uint_16 %MatrixUseMatrixAHW

; 常量
%src_shape = OpConstantComposite %v2uint %uint_64 %uint_64

; 动态偏移计算
%block_row = OpAccessChain %uint_ptr %gl_WorkGroupID %uint_1
%row_val = OpLoad %uint %block_row
%row_offset = OpIMul %uint %row_val %uint_16

%block_col = OpAccessChain %uint_ptr %gl_WorkGroupID %uint_0
%col_val = OpLoad %uint %block_col
%col_offset = OpIMul %uint %col_val %uint_16

%offset = OpCompositeConstruct %v2uint %row_offset %col_offset

; 加载操作
%block = OpCooperativeMatrixLoadHW %mat16x16 %input_ptr %src_shape %offset %layout_row_major
```

### 4.3 用例：矩阵乘法加速

**场景**: 实现 C = A * B 的分块矩阵乘法。

**GLSL 输入**:
```glsl
#version 450
#extension GL_HW_neural_shader : require

layout(local_size_x = 16, local_size_y = 16) in;

layout(binding = 0) buffer MatrixA { float A[128 * 64]; };
layout(binding = 1) buffer MatrixB { float B[64 * 128]; };
layout(binding = 2) buffer MatrixC { float C[128 * 128]; };

void main() {
    const uint M = 128, K = 64, N = 128;
    const uint TM = 16, TK = 16, TN = 16;

    uint row = gl_WorkGroupID.y * TM;
    uint col = gl_WorkGroupID.x * TN;

    // 累加器矩阵
    coopmatHW<float, 16, 16> acc;
    coopMatLoadHW(acc, C, uvec2(M, N), uvec2(row, col), gl_RowMajorHW);

    // 分块矩阵乘法
    for (uint k = 0; k < K; k += TK) {
        coopmatHW<float, 16, 16> matA, matB;

        // 加载 A 的 16x16 子块
        coopMatLoadHW(matA, A, uvec2(M, K), uvec2(row, k), gl_RowMajorHW);

        // 加载 B 的 16x16 子块
        coopMatLoadHW(matB, B, uvec2(K, N), uvec2(k, col), gl_RowMajorHW);

        // 硬件矩阵乘加
        acc = coopMatMulAddHW(matA, matB, acc);
    }

    // 存储 C 的子块
    coopMatStoreHW(acc, C, uvec2(M, N), uvec2(row, col), gl_RowMajorHW);
}
```

### 4.4 用例：列主序矩阵加载

**场景**: 加载列主序存储的矩阵数据。

**GLSL 输入**:
```glsl
#version 450
#extension GL_HW_neural_shader : require

layout(binding = 0) buffer ColMajorMatrix {
    float data[256];  // 16x16 列主序存储
};

void main() {
    coopmatHW<float, 16, 16> mat;

    // 使用列主序布局加载
    coopMatLoadHW(mat, data, uvec2(16, 16), uvec2(0, 0), gl_ColumnMajorHW);
}
```

---

## 五、实现设计

### 5.1 需要修改的文件

| 文件 | 修改内容 |
|------|----------|
| `spirv.h` / `spirv.hpp` | 添加 Op 枚举、Capability、Layout 枚举 |
| `spirv_common.hpp` | 添加 `CoopMatHW` 到 `SPIRType::BaseType`，扩展 `ext` 联合体 |
| `spirv_parser.cpp` | 解析 `OpTypeCooperativeMatrixHW` 类型 |
| `spirv_cross.cpp` | 在 Load/Store 追踪处添加新 Op |
| `spirv_glsl.cpp` | 添加 GLSL 代码生成逻辑 |
| `spirv_msl.cpp` | (可选) 添加 MSL 后端支持 |

### 5.2 spirv_common.hpp 设计

```cpp
// SPIRType::BaseType 新增
enum BaseType {
    // ... 现有类型
    CoopMatHW,    // 硬件协作矩阵类型

    // Keep internal types at the end.
    // ...
};

// SPIRType::ext 联合体新增
union {
    // ... 现有结构

    struct
    {
        uint32_t component_type_id;   // 组件类型
        uint32_t rows_id;             // 行数
        uint32_t cols_id;             // 列数
        uint32_t use_id;              // 矩阵用途 (MatrixA/MatrixB/Accumulator)
    } coopMatHW;
} ext;
```

### 5.3 spirv_parser.cpp 设计

```cpp
case OpTypeCooperativeMatrixHW:
{
    uint32_t id = ops[0];
    auto &type = set<SPIRType>(id, op);

    type.basetype = SPIRType::CoopMatHW;
    type.op = op;
    type.ext.coopMatHW.component_type_id = ops[1];  // 组件类型
    type.ext.coopMatHW.rows_id = ops[2];            // 行数
    type.ext.coopMatHW.cols_id = ops[3];            // 列数
    type.ext.coopMatHW.use_id = ops[4];             // 用途

    // 设置父类型和位宽
    type.parent_type = ops[1];
    auto &component_type = get<SPIRType>(ops[1]);
    type.width = component_type.width;
    break;
}
```

### 5.4 spirv_glsl.cpp 设计

```cpp
// 常量名称映射表
static const GlslConstantNameMapping CoopMatHWLayoutNames[] = {
    DEF_GLSL_MAPPING(RowMajorHW),
    DEF_GLSL_MAPPING(ColumnMajorHW),
};

// emit_instruction() 中的处理
case OpCooperativeMatrixLoadHW:
{
    uint32_t result_type = ops[0];
    uint32_t id = ops[1];
    uint32_t ptr = ops[2];
    uint32_t src_shape = ops[3];
    uint32_t src_offset = ops[4];
    uint32_t layout = ops[5];

    emit_uninitialized_temporary_expression(result_type, id);

    string layout_expr = to_pretty_expression_if_int_constant(
        layout, std::begin(CoopMatHWLayoutNames), std::end(CoopMatHWLayoutNames));

    statement("coopMatLoadHW(", to_expression(id), ", ",
              to_expression(ptr), ", ",
              to_expression(src_shape), ".x, ", to_expression(src_shape), ".y, ",
              to_expression(src_offset), ".x, ", to_expression(src_offset), ".y, ",
              layout_expr, ");");

    register_read(id, ptr, false);
    break;
}

// type_to_glsl() 中的类型名称生成
if (type.op == OpTypeCooperativeMatrixHW)
{
    require_extension_internal("GL_HW_neural_shader");

    string component_type_str = type_to_glsl(get<SPIRType>(type.ext.coopMatHW.component_type_id));
    string rows = to_expression(type.ext.coopMatHW.rows_id);
    string cols = to_expression(type.ext.coopMatHW.cols_id);

    return join("coopmatHW<", component_type_str, ", ", rows, ", ", cols, ">");
}
```

### 5.5 spirv_cross.cpp 设计

在变量依赖追踪处添加：

```cpp
// analyze_variable_cache / register_control_dependent_expression
case OpCooperativeMatrixLoadHW:
case OpCooperativeMatrixLoadKHR:
case OpLoad:
    // ... 同样的处理逻辑

// preprocessing_pre_op_handler
case OpCooperativeMatrixLoadHW:
case OpCooperativeMatrixLoadKHR:
case OpLoad:
{
    if (length < 3) return false;
    uint32_t ptr = args[2];
    auto *var = compiler.maybe_get_backing_variable(ptr);
    // ... 资源访问处理
    break;
}
```

---

## 六、测试用例

### 6.1 测试文件结构

```
shaders/
└── comp/
    └── cooperative-matrix-hw-load.spv16.vk.nocompat.comp

reference/
└── shaders/
    └── comp/
        └── cooperative-matrix-hw-load.spv16.vk.nocompat.comp.vk
```

### 6.2 测试 Shader

**shaders/comp/cooperative-matrix-hw-load.spv16.vk.nocompat.comp**:
```glsl
#version 450
#extension GL_HW_neural_shader : require

layout(local_size_x = 16) in;

layout(binding = 0) buffer MatrixData {
    float data[256];
};

void main() {
    coopmatHW<float, 16, 16> mat;

    // 测试基本加载
    coopMatLoadHW(mat, data, uvec2(16, 16), uvec2(0, 0), gl_RowMajorHW);

    // 测试带偏移加载
    coopmatHW<float, 16, 16> mat2;
    coopMatLoadHW(mat2, data, uvec2(32, 32), uvec2(8, 8), gl_ColumnMajorHW);
}
```

### 6.3 期望输出

**reference/shaders/comp/cooperative-matrix-hw-load.spv16.vk.nocompat.comp.vk**:
```glsl
#version 450
#extension GL_HW_neural_shader : require

layout(local_size_x = 16) in;

layout(binding = 0) buffer MatrixData {
    float data[];
};

void main() {
    coopmatHW<float, 16, 16> mat;
    coopMatLoadHW(mat, data, 16u, 16u, 0u, 0u, gl_RowMajorHW);

    coopmatHW<float, 16, 16> mat2;
    coopMatLoadHW(mat2, data, 32u, 32u, 8u, 8u, gl_ColumnMajorHW);
}
```

---

## 七、与 KHR 版本的差异对比

| 特性 | KHR (OpCooperativeMatrixLoadKHR) | HW (OpCooperativeMatrixLoadHW) |
|------|-----------------------------------|--------------------------------|
| 源矩阵形状 | 固定，通过 Stride 控制 | 动态，通过 srcMatrixShape 指定 |
| 子矩阵偏移 | 不支持 | 支持 srcMatrixOffset |
| 布局方式 | RowMajor/ColumnMajor | RowMajorHW/ColumnMajorHW |
| Stride 参数 | 必需 | 隐式计算（基于形状和布局） |
| 适用场景 | 通用 GPU 计算 | 神经网络推理加速 |

---

## 八、注意事项

1. **扩展依赖**: 需要先声明 `GL_HW_neural_shader` 扩展
2. **Vulkan 语义**: 仅在 Vulkan 环境下可用
3. **内存对齐**: 源数据缓冲区应满足硬件对齐要求
4. **边界检查**: srcMatrixOffset + 矩阵尺寸不应超出 srcMatrixShape 范围
5. **Workgroup 同步**: 多个 workitem 协作加载时需确保同步

---

## 九、实现检查清单

- [ ] `spirv.h` — 添加 `SpvOpCooperativeMatrixLoadHW = 6502`
- [ ] `spirv.hpp` — 添加 `OpCooperativeMatrixLoadHW = 6502`
- [ ] `spirv.hpp` — 添加 Capability `CapabilityCooperativeMatrixHW`
- [ ] `spirv.hpp` — 添加 Layout 枚举
- [ ] `spirv.hpp` — 更新 InstructionDB 的 `hasResult`/`hasResultType`
- [ ] `spirv_common.hpp` — 添加 `CoopMatHW` 到 BaseType
- [ ] `spirv_common.hpp` — 扩展 `ext` 联合体
- [ ] `spirv_parser.cpp` — 添加类型解析
- [ ] `spirv_cross.cpp` — 添加 Load 追踪 (3 处)
- [ ] `spirv_glsl.cpp` — 添加常量映射表
- [ ] `spirv_glsl.cpp` — 添加 `emit_instruction` case
- [ ] `spirv_glsl.cpp` — 添加 `type_to_glsl` 处理
- [ ] `spirv_msl.cpp` — (可选) MSL 后端
- [ ] 测试 shader 和 reference 文件
- [ ] 代码格式化 (`./format_all.sh`)
