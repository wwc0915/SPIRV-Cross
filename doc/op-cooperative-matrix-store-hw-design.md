# OpCooperativeMatrixStoreHW 设计文档

## 一、概述

`OpCooperativeMatrixStoreHW` 是 SPV_HW_neural_matrix 扩展中的指令，用于将硬件优化的协作矩阵（Cooperative Matrix）存储到内存。与 `OpCooperativeMatrixLoadHW` 互为逆操作，支持将矩阵写入到指定内存位置的子区域。

---

## 二、SPIR-V 指令规范

### 2.1 指令编码

| 字段 | 值 |
|------|-----|
| Opcode | 6503 |
| Word Count | 4+vars |
| hasResult | false |
| hasResultType | false |

**指令格式**:
```
| Word Count | Opcode: 6503 | <id> Pointer | <id> Object | <id> srcMatrixShape | <id> srcMatrixOffset | <id> layout |
```

### 2.2 操作数说明

| 操作数 | 位置 | 描述 |
|--------|------|------|
| Pointer | ops[0] | 指向标量/向量数组的指针 (`OpTypePointer`)，其类型操作数可以是标量或向量类型。如果声明了着色器功能，则指针必须指向一个数组，且对指针的任何 `ArrayStride` 修饰符都将被忽略 |
| Object | ops[1] | 要存储的合作矩阵，其类型必须是 `OpTypeCooperativeMatrixHW` |
| srcMatrixShape | ops[2] | vec2，要写出到 ddr/sharedMemory 的矩阵的行数和列数 |
| srcMatrixOffset | ops[3] | vec2，从目标矩阵第 srcMatrixOffset[0] 行、第 srcMatrixOffset[1] 列开始写入 |
| layout | ops[4] | `CooperativeMatrixLayoutHW` 枚举常量 (0=RowMajorHW, 1=ColumnMajorHW) |

---

## 三、与 LoadHW 的对比

| 特性 | LoadHW (6502) | StoreHW (6503) |
|------|---------------|----------------|
| Result | 有 (返回加载的矩阵) | 无 |
| Result Type | ops[0] | 无 |
| Pointer | ops[2] | ops[0] |
| Object | 无 | ops[1] |
| srcMatrixShape | ops[3] | ops[2] |
| srcMatrixOffset | ops[4] | ops[3] |
| layout | ops[5] | ops[4] |
| Word Count | 5+vars | 4+vars |
| 数据流 | 内存 -> 矩阵 | 矩阵 -> 内存 |

---

## 四、GLSL 目标接口

### 4.1 GLSL 函数签名

```glsl
void coopMatStoreHW(
    coopmatHW<T, M, K> mat,           // 输入矩阵
    T buf[],                           // 目标数据缓冲区
    uvec2 srcMatrixShape,             // 目标矩阵形状 (rows, cols)
    uvec2 srcMatrixOffset,            // 写入偏移 (row_offset, col_offset)
    uint layout                        // 布局方式
);
```

### 4.2 layout 常量映射

| SPIR-V 常量值 | GLSL 常量名 |
|---------------|-------------|
| 0 | `gl_CooperativeMatrixLayoutRowMajorHW` |
| 1 | `gl_CooperativeMatrixLayoutColumnMajorHW` |

---

## 五、实现设计

### 5.1 需要修改的文件

| 文件 | 修改内容 | 状态 |
|------|----------|------|
| `spirv.h` | Op 枚举、hasResult/hasResultType | 已有 |
| `spirv.hpp` | Op 枚举、hasResult/hasResultType | 已有 |
| `spirv_cross.cpp` | Store 追踪 (L823, L3468) | 已有 |
| `spirv_glsl.cpp` | `emit_instruction` 中添加 case | 已实现 |

注意：`spirv.h`/`spirv.hpp`/`spirv_cross.cpp` 中 OpCooperativeMatrixStoreHW 的定义和追踪逻辑已经存在，只需在 GLSL 后端添加代码生成。

### 5.2 spirv_glsl.cpp 实现

在 `emit_instruction()` 函数中，`OpCooperativeMatrixLoadHW` case 之后插入：

```cpp
case OpCooperativeMatrixStoreHW:
{
    if (length < 5)
        SPIRV_CROSS_THROW("Not enough operands for OpCooperativeMatrixStoreHW.");

    uint32_t ptr = ops[0];
    uint32_t object = ops[1];
    uint32_t src_shape = ops[2];
    uint32_t src_offset = ops[3];
    uint32_t layout_id = ops[4];

    auto expr = to_expression(ptr);
    auto &layout_const = get<SPIRConstant>(layout_id);
    bool is_column_major = layout_const.scalar() != 0;

    statement("coopMatStoreHW(", to_expression(object), ", ", expr, ", ",
              to_expression(src_shape), ", ",
              to_expression(src_offset), ", ",
              is_column_major ? "gl_CooperativeMatrixLayoutColumnMajorHW"
                              : "gl_CooperativeMatrixLayoutRowMajorHW", ");");

    register_write(object);
    break;
}
```

---

## 六、测试用例

### 6.1 基本 Store 测试（行主序）

**SPIR-V 输入** (通过 gen_test_spv.py `gen_store_test` 生成):
```
%matA = OpCooperativeMatrixLoadHW %coopmatA_t %ptr %dim16 %dim0 %c0
OpCooperativeMatrixStoreHW %ptr %matA %dim16 %dim0 %c0
```

**期望 GLSL 输出**:
```glsl
coopmatHW<float, 16u, 16u> matA;
coopMatLoadHW(matA, data._m0[0u], uvec2(16u), uvec2(0u), gl_CooperativeMatrixLayoutRowMajorHW);
coopMatStoreHW(matA, data._m0[0u], uvec2(16u), uvec2(0u), gl_CooperativeMatrixLayoutRowMajorHW);
```

### 6.2 列主序 Store 测试

**期望输出**:
```glsl
coopMatStoreHW(mat, data._m0[0u], uvec2(16u), uvec2(0u), gl_CooperativeMatrixLayoutColumnMajorHW);
```

### 6.3 带偏移的 Store 测试

**期望输出**:
```glsl
coopMatStoreHW(mat, data._m0[0u], uvec2(64u), uvec2(16u, 32u), gl_CooperativeMatrixLayoutRowMajorHW);
```

### 6.4 矩阵乘法后 Store 的完整用例

**GLSL 场景**:
```glsl
#version 450
#extension GL_HW_neural_matrix : require

layout(local_size_x = 16, local_size_y = 16) in;

layout(binding = 0) buffer MatrixA { float A[128 * 64]; };
layout(binding = 1) buffer MatrixB { float B[64 * 128]; };
layout(binding = 2) buffer MatrixC { float C[128 * 128]; };

void main() {
    const uint M = 128, K = 64, N = 128;

    uint row = gl_WorkGroupID.y * 16;
    uint col = gl_WorkGroupID.x * 16;

    coopmatHW<float, 16, 16> acc;
    coopMatLoadHW(acc, C, uvec2(M, N), uvec2(row, col), gl_CooperativeMatrixLayoutRowMajorHW);

    for (uint k = 0; k < K; k += 16) {
        coopmatHW<float, 16, 16> matA, matB;
        coopMatLoadHW(matA, A, uvec2(M, K), uvec2(row, k), gl_CooperativeMatrixLayoutRowMajorHW);
        coopMatLoadHW(matB, B, uvec2(K, N), uvec2(k, col), gl_CooperativeMatrixLayoutRowMajorHW);
        acc = coopMatMulAddHW(matA, matB, acc);
    }

    // 存储计算结果
    coopMatStoreHW(acc, C, uvec2(M, N), uvec2(row, col), gl_CooperativeMatrixLayoutRowMajorHW);
}
```

---

## 七、测试生成

使用 `gen_test_spv.py` 生成测试 SPIR-V：

```bash
# 生成 Store 测试
python3 gen_test_spv.py test_hw_store.spv

# 运行 spirv-cross 验证输出
./spirv-cross test_hw_store.spv
```
