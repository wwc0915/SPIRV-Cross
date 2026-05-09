# OpCooperativeVectorMatrixMulHW 设计文档

## 一、概述

`OpCooperativeVectorMatrixMulHW` 是 SPV_HW_cooperative_vector 扩展中的指令，用于协作向量与矩阵相乘（无偏移）。

---

## 二、SPIR-V 指令规范

### 2.1 指令编码

| 字段 | 值 |
|------|-----|
| Opcode | 6612 |
| Word Count | 5+ |

**指令格式**:
```
| Word Count | Opcode: 6612 | <id> Result Type | Result <id> | <id> Vector | <id> Matrix |
```

### 2.2 操作数说明

| 操作数 | 类型 | 描述 |
|--------|------|------|
| Result Type | `<id>` | 结果类型，必须是 `OpTypeCooperativeVectorHW` 类型 |
| Result `<id>` | `<id>` | 结果协作向量 ID |
| Vector | `<id>` | 输入协作向量 |
| Matrix | `<id>` | 输入协作矩阵 |

### 2.3 关联枚举定义

**Capability**:
```cpp
CapabilityCooperativeVectorHW = 6607
```

---

## 三、GLSL 目标接口

### 3.1 GLSL 扩展声明

```glsl
#extension GL_HW_cooperative_vector : require
```

### 3.2 GLSL 函数签名

```glsl
void coopVecMatMulHW(out coopvecHW m, coopvecHW v, coopmatHW mi);
```

---

## 四、用例

### 4.1 基本用例：向量矩阵乘法

**GLSL 输出** (SPIRV-Cross 生成):
```glsl
#version 450
#extension GL_HW_cooperative_vector : require

layout(local_size_x = 16) in;

void main() {
    coopvecHW<float, 16u> vec;
    coopVecLoadHW(vec, data._m0[0u]);
    coopvecHW<float, 16u> result;
    coopVecMatMulHW(result, vec, mat);
}
```

---

## 五、实现设计

### 5.1 需要修改的文件

| 文件 | 修改内容 |
|------|----------|
| `spirv.h` / `spirv.hpp` | 已有 Op 枚举、HasResultAndType |
| `spirv_glsl.cpp` | 添加 `emit_instruction` case |

### 5.2 spirv_glsl.cpp 设计

```cpp
case OpCooperativeVectorMatrixMulHW:
{
    if (length < 4)
        SPIRV_CROSS_THROW("Not enough operands for OpCooperativeVectorMatrixMulHW.");

    uint32_t result_type = ops[0];
    uint32_t id = ops[1];
    uint32_t vector = ops[2];
    uint32_t matrix = ops[3];

    emit_uninitialized_temporary_expression(result_type, id);

    statement("coopVecMatMulHW(", to_expression(id), ", ",
              to_expression(vector), ", ",
              to_expression(matrix), ");");

    break;
}
```

---

## 六、实现检查清单

- [x] `spirv.h` / `spirv.hpp` — 已有枚举定义
- [x] `spirv_glsl.cpp` — 添加 `emit_instruction` case
- [x] `gen_test_spv.py` — 添加测试生成函数
