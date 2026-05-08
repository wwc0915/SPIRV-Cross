# OpCooperativeVectorLoadHW 设计文档

## 一、概述

`OpCooperativeVectorLoadHW` 是 SPV_HW_cooperative_vector 扩展中的指令，用于从内存加载硬件优化的协作向量（Cooperative Vector）。

---

## 二、SPIR-V 指令规范

### 2.1 指令编码

| 字段 | 值 |
|------|-----|
| Opcode | 6609 |
| Word Count | 4+ |

**指令格式**:
```
| Word Count | Opcode: 6609 | <id> Result Type | Result <id> | <id> Pointer |
```

### 2.2 操作数说明

| 操作数 | 类型 | 描述 |
|--------|------|------|
| Result Type | `<id>` | 结果类型，必须是 `OpTypeCooperativeVectorHW` 类型 |
| Result `<id>` | `<id>` | 加载结果的协作向量 ID |
| Pointer | `<id>` | 指向标量/向量元素类型数组的指针 (`OpTypePointer`)，存储类别必须是 CrossWorkGroup、Workgroup、StorageBuffer 或 PhysicalStorageBuffer |

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
void coopVecLoadHW(out coopvecHW<T, M> vec, T buf[]);
```

---

## 四、用例

### 4.1 基本用例：加载协作向量

**GLSL 输入**:
```glsl
#version 450
#extension GL_HW_cooperative_vector : require

layout(local_size_x = 16) in;

layout(binding = 0) buffer VecData {
    float data[256];
};

void main() {
    coopvecHW<float, 16> vec;
    coopVecLoadHW(vec, data);
}
```

**GLSL 输出** (SPIRV-Cross 生成):
```glsl
#version 450
#extension GL_HW_cooperative_vector : require

layout(local_size_x = 16) in;

layout(binding = 0) buffer VecData {
    float data[];
};

void main() {
    coopvecHW<float, 16u> vec;
    coopVecLoadHW(vec, data._m0[0u]);
}
```

---

## 五、实现设计

### 5.1 需要修改的文件

| 文件 | 修改内容 |
|------|----------|
| `spirv.h` / `spirv.hpp` | 添加 Op 枚举、HasResultAndType |
| `spirv_cross.cpp` | 添加 Load 追踪（2处） |
| `spirv_glsl.cpp` | 添加 `emit_instruction` case |

### 5.2 spirv_cross.cpp 设计

将 `OpCooperativeVectorLoadHW` 添加到与 `OpCooperativeMatrixLoadHW` 相同的变量依赖追踪位置（2处）：

1. `analyze_variable_cache` / `register_control_dependent_expression` 中的读依赖注册
2. `CfgBuilder` 中的访问链处理

### 5.3 spirv_glsl.cpp 设计

```cpp
// emit_instruction() 中的处理
case OpCooperativeVectorLoadHW:
{
    if (length < 3)
        SPIRV_CROSS_THROW("Not enough operands for OpCooperativeVectorLoadHW.");

    uint32_t result_type = ops[0];
    uint32_t id = ops[1];
    uint32_t ptr = ops[2];

    emit_uninitialized_temporary_expression(result_type, id);

    auto expr = to_expression(ptr);
    statement("coopVecLoadHW(", to_expression(id), ", ", expr, ");");

    register_read(id, ptr, false);
    break;
}
```

---

## 六、实现检查清单

- [x] `spirv.h` — 添加 `SpvOpCooperativeVectorLoadHW = 6609`
- [x] `spirv.hpp` — 添加 `OpCooperativeVectorLoadHW = 6609`
- [x] `spirv.hpp` — 更新 InstructionDB 的 `hasResult`/`hasResultType`
- [x] `spirv_cross.cpp` — 添加 Load 追踪（2处）
- [x] `spirv_glsl.cpp` — 添加 `emit_instruction` case
