# OpCooperativeVectorStoreHW 设计文档

## 一、概述

`OpCooperativeVectorStoreHW` 是 SPV_HW_cooperative_vector 扩展中的指令，用于将协作向量存储到内存。

---

## 二、SPIR-V 指令规范

### 2.1 指令编码

| 字段 | 值 |
|------|-----|
| Opcode | 6610 |
| Word Count | 3+ |

**指令格式**:
```
| Word Count | Opcode: 6610 | <id> Pointer | <id> Object |
```

### 2.2 操作数说明

| 操作数 | 类型 | 描述 |
|--------|------|------|
| Pointer | `<id>` | 指向标量/向量元素类型数组的指针 (`OpTypePointer`)，存储类别必须是 CrossWorkGroup、Workgroup、StorageBuffer 或 PhysicalStorageBuffer |
| Object | `<id>` | 要存储的协作向量 (`OpTypeCooperativeVectorHW`) |

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
void coopVecStoreHW(coopvecHW<T, M> vec, out T buf[]);
```

---

## 四、用例

### 4.1 基本用例：加载后存储

**GLSL 输出** (SPIRV-Cross 生成):
```glsl
#version 450
#extension GL_HW_cooperative_vector : require

layout(local_size_x = 16) in;

layout(binding = 0) buffer Data {
    float data[];
};

void main() {
    coopvecHW<float, 16u> vec;
    coopVecLoadHW(vec, data._m0[0u]);
    coopVecStoreHW(vec, data._m0[0u]);
}
```

### 4.2 完整用例：加载、计算、存储

**GLSL 输出** (SPIRV-Cross 生成):
```glsl
void main() {
    coopvecHW<float, 16u> vec;
    coopVecLoadHW(vec, data._m0[0u]);
    coopmatHW<float, 16u, 16u> mat;
    coopMatLoadHW(mat, data._m0[0u], uvec2(16u), uvec2(0u), gl_CooperativeMatrixLayoutRowMajorHW);
    coopvecHW<float, 16u> result;
    coopVecMatMulHW(result, vec, mat);
    coopVecStoreHW(result, data._m0[0u]);
}
```

---

## 五、实现设计

### 5.1 需要修改的文件

| 文件 | 修改内容 |
|------|----------|
| `spirv.h` / `spirv.hpp` | 已有 Op 枚举、HasResultAndType |
| `spirv_cross.cpp` | 已有 Store 追踪（2处：analyze_variable_cache + CfgBuilder） |
| `spirv_glsl.cpp` | 添加 `emit_instruction` case |

### 5.2 spirv_cross.cpp 设计

已有实现，与 `OpCooperativeMatrixStoreHW` 共享相同的写入追踪逻辑：
1. `analyze_variable_cache` — 注册写入依赖
2. `CfgBuilder` — 追踪通过 access chain 的部分写入

### 5.3 spirv_glsl.cpp 设计

```cpp
case OpCooperativeVectorStoreHW:
{
    if (length < 2)
        SPIRV_CROSS_THROW("Not enough operands for OpCooperativeVectorStoreHW.");

    uint32_t ptr = ops[0];
    uint32_t object = ops[1];

    auto expr = to_expression(ptr);
    statement("coopVecStoreHW(", to_expression(object), ", ", expr, ");");

    register_write(object);
    break;
}
```

注意：SPIR-V 格式为 `Pointer, Object`，而 GLSL 函数签名为 `void coopVecStoreHW(vec, buf)`，即参数顺序与 SPIR-V 相同（Object 在前，Pointer 在后）。

---

## 六、实现检查清单

- [x] `spirv.h` / `spirv.hpp` — 已有枚举定义
- [x] `spirv_cross.cpp` — 已有 Store 追踪（2处）
- [x] `spirv_glsl.cpp` — 添加 `emit_instruction` case
- [x] `gen_test_spv.py` — 已有测试生成（matmul / matmuladd 测试中包含 StoreHW）
