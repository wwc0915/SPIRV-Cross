# OpCooperativeMatrixMulAddHW 设计文档

## 一、概述

`OpCooperativeMatrixMulAddHW` 是 SPV_HW_neural_matrix 扩展中的算术指令，用于执行硬件优化的矩阵乘加操作。矩阵 A 与矩阵 B 相乘，然后逐元素加上矩阵 C，结果写入累积器矩阵。适用于神经网络推理中的矩阵乘加加速场景。

---

## 二、SPIR-V 指令规范

### 2.1 指令编码

| 字段 | 值 |
|------|-----|
| Opcode | 6504 |
| Word Count | 6+variable |
| hasResult | true |
| hasResultType | true |

**指令格式**:
```
| Word Count | Opcode: 6504 | <id> Result Type | Result <id> | <A> | <B> | <C> |
```

### 2.2 操作数说明

| 操作数 | 位置 | 描述 |
|--------|------|------|
| Result Type | ops[0] | 结果类型，必须是 `OpTypeCooperativeMatrixHW` 类型，且用途为 `MatrixAccumulatorHW` |
| Result `<id>` | ops[1] | 结果的合作矩阵 ID |
| A | ops[2] | 左操作数矩阵，类型必须是 `OpTypeCooperativeMatrixHW` |
| B | ops[3] | 右操作数矩阵，类型必须是 `OpTypeCooperativeMatrixHW` |
| C | ops[4] | 加数矩阵，类型必须是 `OpTypeCooperativeMatrixHW`，用途为 `MatrixAccumulatorHW` |

### 2.3 语义说明

- 矩阵 A (M×K) 与矩阵 B (K×N) 相乘，得到 M×N 的中间结果
- 将中间结果逐元素加上矩阵 C (M×N)
- Result Type 必须是一个具有 M 行和 N 列的协作矩阵类型，其用途必须是 `MatrixAccumulatorHW`
- 操作的顺序取决于实现方式
- 浮点运算的内部精度由客户端 API 定义
- 如果存在 `Matrix{A,B,C}SignedComponentsHW` 操作数，则相应矩阵操作数的元素将 sign-extended 到结果类型的精度，否则将零扩展

---

## 三、GLSL 目标接口

### 3.1 GLSL 函数签名

```glsl
void coopmatMulAddHW(
    out coopmatHW<T1, M, N> matO,    // 输出矩阵 (out 参数)
    coopmatHW<T, M, K> matA,         // 左操作数矩阵
    coopmatHW<T, K, N> matB,         // 右操作数矩阵
    coopmatHW<T1, M, N> matC         // 累积器矩阵
);
```

注意：SPIR-V 中有 Result Type 和 Result `<id>`，但在 GLSL 中通过 `out` 参数传递结果，与 `coopMatLoadHW` 的映射模式一致。

### 3.2 使用示例

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

    // 累积器矩阵
    coopmatHW<float, 16, 16> acc;
    coopMatLoadHW(acc, C, uvec2(M, N), uvec2(row, col), gl_CooperativeMatrixLayoutRowMajorHW);

    // 分块矩阵乘加
    for (uint k = 0; k < K; k += 16) {
        coopmatHW<float, 16, 16> matA, matB;
        coopMatLoadHW(matA, A, uvec2(M, K), uvec2(row, k), gl_CooperativeMatrixLayoutRowMajorHW);
        coopMatLoadHW(matB, B, uvec2(K, N), uvec2(k, col), gl_CooperativeMatrixLayoutRowMajorHW);
        coopmatHW<float, 16, 16> result;
        coopmatMulAddHW(result, matA, matB, acc);
        acc = result;
    }

    coopMatStoreHW(acc, C, uvec2(M, N), uvec2(row, col), gl_CooperativeMatrixLayoutRowMajorHW);
}
```

---

## 四、实现设计

### 4.1 需要修改的文件

| 文件 | 修改内容 |
|------|----------|
| `spirv.h` | 添加 `SpvOpCooperativeMatrixMulAddHW = 6504`、hasResult/hasResultType、名称字符串 |
| `spirv.hpp` | 添加 `OpCooperativeMatrixMulAddHW = 6504`、hasResult/hasResultType、名称字符串 |
| `spirv_glsl.cpp` | 添加 `emit_instruction` 中的 case 处理 |
| `gen_test_spv.py` | 添加 `gen_muladd_test` 测试生成函数 |

### 4.2 spirv_glsl.cpp 实现

在 `emit_instruction()` 函数中，`OpCooperativeMatrixStoreHW` case 之前插入：

```cpp
case OpCooperativeMatrixMulAddHW:
{
    if (length < 5)
        SPIRV_CROSS_THROW("Not enough operands for OpCooperativeMatrixMulAddHW.");

    uint32_t result_type = ops[0];
    uint32_t id = ops[1];
    uint32_t a = ops[2];
    uint32_t b = ops[3];
    uint32_t c = ops[4];

    emit_uninitialized_temporary_expression(result_type, id);

    statement("coopmatMulAddHW(", to_expression(id), ", ",
              to_expression(a), ", ",
              to_expression(b), ", ",
              to_expression(c), ");");

    break;
}
```

**关键设计决策**:
- 使用 `emit_uninitialized_temporary_expression` + `statement` 模式，与 `OpCooperativeMatrixLoadHW` 一致
- GLSL 函数为 `void` 返回类型，结果通过 `out` 参数传递
- Result `<id>` (ops[1]) 映射为 GLSL 的第一个参数（out 参数）
- 不需要 `register_read`，因为操作数都是寄存器中的 coopmat 变量，不涉及内存访问

---

## 五、测试用例

### 5.1 基本 MulAdd 测试

**SPIR-V 操作流程**:
```
%matA = OpCooperativeMatrixLoadHW %coopmatA_t %ptr %dim16 %dim0 %c0
%matB = OpCooperativeMatrixLoadHW %coopmatB_t %ptr %dim16 %dim0 %c0
%acc   = OpCooperativeMatrixLoadHW %coopmatAcc_t %ptr %dim16 %dim0 %c0
%result = OpCooperativeMatrixMulAddHW %coopmatAcc_t %matA %matB %acc
OpCooperativeMatrixStoreHW %ptr %result %dim16 %dim0 %c0
```

**期望 GLSL 输出**:
```glsl
coopmatHW<float, 16u, 16u> _16;
coopMatLoadHW(_16, data._m0[0u], uvec2(16u), uvec2(0u), gl_CooperativeMatrixLayoutRowMajorHW);
coopmatHW<float, 16u, 16u> _17;
coopMatLoadHW(_17, data._m0[0u], uvec2(16u), uvec2(0u), gl_CooperativeMatrixLayoutRowMajorHW);
coopmatHW<float, 16u, 16u> _18;
coopMatLoadHW(_18, data._m0[0u], uvec2(16u), uvec2(0u), gl_CooperativeMatrixLayoutRowMajorHW);
coopmatHW<float, 16u, 16u> _19;
coopmatMulAddHW(_19, _16, _17, _18);
coopMatStoreHW(_19, data._m0[0u], uvec2(16u), uvec2(0u), gl_CooperativeMatrixLayoutRowMajorHW);
```

### 5.2 测试生成

使用 `gen_test_spv.py` 生成测试 SPIR-V：

```bash
# 生成 MulAdd 测试
python3 gen_test_spv.py test_hw_muladd.spv

# 运行 spirv-cross 验证输出
./spirv-cross test_hw_muladd.spv
```

---

## 六、实现检查清单

- [ ] `spirv.h` — 添加 `SpvOpCooperativeMatrixMulAddHW = 6504`
- [ ] `spirv.h` — 添加 hasResult=true, hasResultType=true
- [ ] `spirv.h` — 添加名称字符串
- [ ] `spirv.hpp` — 添加 `OpCooperativeMatrixMulAddHW = 6504`
- [ ] `spirv.hpp` — 添加 hasResult=true, hasResultType=true
- [ ] `spirv.hpp` — 添加名称字符串
- [ ] `spirv_glsl.cpp` — 添加 `emit_instruction` case
- [ ] `gen_test_spv.py` — 添加 `gen_muladd_test`
- [ ] 构建并通过测试
