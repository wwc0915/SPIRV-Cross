# OpCooperativeMatrixReduceHW 设计文档

## 一、概述

`OpCooperativeMatrixReduceHW` 是 SPV_HW_neural_shader 扩展中的规约指令，用于对协作矩阵进行行/列规约计算（Add/Min/Max）。规约结果广播到矩阵的每个元素上。

---

## 二、SPIR-V 指令规范

### 2.1 指令编码

| 字段 | 值 |
|------|-----|
| Opcode | 6505 |
| Word Count | 6 |
| hasResult | true |
| hasResultType | true |

**指令格式**:
```
| 6 | opcode: 6505 | <id> Result Type | Result <id> | <id> Matrix | <id> reduceMask | <id> combineOp |
```

### 2.2 操作数说明

| 操作数 | 位置 | 描述 |
|--------|------|------|
| Result Type | ops[0] | 结果类型，必须是 `OpTypeCooperativeMatrixHW` 类型 |
| Result `<id>` | ops[1] | 规约结果的合作矩阵 ID |
| Matrix | ops[2] | 输入矩阵，类型必须是 `OpTypeCooperativeMatrixHW` |
| reduceMask | ops[3] | 规约掩码常量：0x0=Row，0x1=Column |
| combineOp | ops[4] | 规约操作常量：0x0=ReduceAdd，0x1=ReduceMin，0x2=ReduceMax |

### 2.3 关联枚举

**Cooperative Matrix Reduce Mask**:
```cpp
Row    = 0x0  // 按行规约
Column = 0x1  // 按列规约
```

**Cooperative Matrix Reduce CombineOp**:
```cpp
ReduceAdd = 0x0  // 求和
ReduceMin = 0x1  // 最小值
ReduceMax = 0x2  // 最大值
```

### 2.4 语义说明

- 对输入矩阵按 reduceMask 指定的维度进行规约
- 规约操作由 combineOp 指定（Add/Min/Max）
- 规约结果广播到输出矩阵的每个元素上
- 输出矩阵形状与输入矩阵相同（M×N）

---

## 三、GLSL 目标接口

### 3.1 GLSL 函数签名

```glsl
void coopMatReduceHW(
    out coopmatHW<T, M, N> matO,    // 输出矩阵（规约结果广播）
    coopmatHW<T, M, N> mat,         // 输入矩阵
    uint reduceMask,                 // 规约掩码
    uint combineOp                   // 规约操作
);
```

### 3.2 reduceMask 常量映射

| SPIR-V 常量值 | GLSL 常量名 |
|---------------|-------------|
| 0x0 | `gl_CooperativeMatrixReduceRowHW` |
| 0x1 | `gl_CooperativeMatrixReduceColumnHW` |

### 3.3 combineOp 常量映射

| SPIR-V 常量值 | GLSL 常量名 |
|---------------|-------------|
| 0x0 | `gl_CooperativeMatrixReduceAddHW` |
| 0x1 | `gl_CooperativeMatrixReduceMinHW` |
| 0x2 | `gl_CooperativeMatrixReduceMaxHW` |

---

## 四、实现设计

### 4.1 需要修改的文件

| 文件 | 修改内容 |
|------|----------|
| `spirv.h` | 添加 `SpvOpCooperativeMatrixReduceHW = 6505`、hasResult/hasResultType、名称字符串 |
| `spirv.hpp` | 添加 `OpCooperativeMatrixReduceHW = 6505`、hasResult/hasResultType、名称字符串 |
| `spirv_glsl.cpp` | 添加 `emit_instruction` case |
| `gen_test_spv.py` | 添加 `gen_reduce_test` |

### 4.2 spirv_glsl.cpp 实现

在 `OpCooperativeMatrixStoreHW` case 之前插入：

```cpp
case OpCooperativeMatrixReduceHW:
{
    if (length < 5)
        SPIRV_CROSS_THROW("Not enough operands for OpCooperativeMatrixReduceHW.");

    uint32_t result_type = ops[0];
    uint32_t id = ops[1];
    uint32_t matrix = ops[2];
    uint32_t reduce_mask_id = ops[3];
    uint32_t combine_op_id = ops[4];

    emit_uninitialized_temporary_expression(result_type, id);

    auto &mask_const = get<SPIRConstant>(reduce_mask_id);
    auto &op_const = get<SPIRConstant>(combine_op_id);
    uint32_t mask_val = mask_const.scalar();
    uint32_t op_val = op_const.scalar();

    const char *mask_str;
    switch (mask_val)
    {
    case 0: mask_str = "gl_CooperativeMatrixReduceRowHW"; break;
    case 1: mask_str = "gl_CooperativeMatrixReduceColumnHW"; break;
    default: mask_str = to_expression(reduce_mask_id).c_str(); break;
    }

    const char *op_str;
    switch (op_val)
    {
    case 0: op_str = "gl_CooperativeMatrixReduceAddHW"; break;
    case 1: op_str = "gl_CooperativeMatrixReduceMinHW"; break;
    case 2: op_str = "gl_CooperativeMatrixReduceMaxHW"; break;
    default: op_str = to_expression(combine_op_id).c_str(); break;
    }

    statement("coopMatReduceHW(", to_expression(id), ", ",
              to_expression(matrix), ", ",
              mask_str, ", ",
              op_str, ");");

    break;
}
```

---

## 五、测试用例

### 5.1 Row ReduceAdd 测试

**期望 GLSL 输出**:
```glsl
coopmatHW<float, 16u, 16u> result;
coopMatReduceHW(result, matA, gl_CooperativeMatrixReduceRowHW, gl_CooperativeMatrixReduceAddHW);
```

### 5.2 Column ReduceMax 测试

**期望 GLSL 输出**:
```glsl
coopmatHW<float, 16u, 16u> result;
coopMatReduceHW(result, matA, gl_CooperativeMatrixReduceColumnHW, gl_CooperativeMatrixReduceMaxHW);
```

---

## 六、实现检查清单

- [ ] `spirv.h` — 添加 `SpvOpCooperativeMatrixReduceHW = 6505`
- [ ] `spirv.hpp` — 添加 `OpCooperativeMatrixReduceHW = 6505`
- [ ] `spirv_glsl.cpp` — 添加 `emit_instruction` case
- [ ] `gen_test_spv.py` — 添加 `gen_reduce_test`
- [ ] 构建并通过测试
