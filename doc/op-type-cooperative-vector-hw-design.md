# OpTypeCooperativeVectorHW 设计文档

## 一、概述

`OpTypeCooperativeVectorHW` 是 SPV_HW_cooperative_vector 扩展中的类型声明指令，用于声明一个新的协作向量类型，其包含请求的标量类型的 Component Count 个组件。

---

## 二、SPIR-V 指令规范

### 2.1 指令编码

| 字段 | 值 |
|------|-----|
| Opcode | 6608 |
| Word Count | 4 |

**指令格式**:
```
| Word Count | Opcode: 6608 | Result <id> | <id> Component Type | <id> Component Count |
```

### 2.2 操作数说明

| 操作数 | 类型 | 描述 |
|--------|------|------|
| Result `<id>` | `<id>` | 声明的协作向量类型 ID |
| Component Type | `<id>` | 组件类型，必须是标量数值类型 |
| Component Count | `<id>` | 组件数量，必须是具有标量32位整数类型的常量指令 |

### 2.3 关联枚举定义

**Capability**:
```cpp
CapabilityCooperativeVectorHW = 6607
```

**Component Type**:
```cpp
enum ComponentTypeHW {
    SignedInt8HW  = 0,
    SignedInt16HW = 1,
    SignedInt32HW = 2,
    Float16HW     = 3,
    Float32HW     = 4,
};
```

---

## 三、GLSL 目标接口

### 3.1 GLSL 扩展声明

```glsl
#extension GL_HW_cooperative_vector : require
```

### 3.2 GLSL 类型声明

```glsl
// 硬件协作向量类型
coopvecHW<T, M> vecA;
```

---

## 四、实现设计

### 4.1 需要修改的文件

| 文件 | 修改内容 |
|------|----------|
| `spirv.h` / `spirv.hpp` | 添加 Op 枚举、Capability、HasResultAndType |
| `spirv_common.hpp` | 添加 `CoopVecHW` 到 `SPIRType::BaseType`，扩展 `ext` 联合体 |
| `spirv_parser.cpp` | 解析 `OpTypeCooperativeVectorHW` 类型 |
| `spirv_glsl.cpp` | 添加 GLSL 代码生成逻辑（type_to_glsl、常量处理、转换指令） |

### 4.2 spirv_common.hpp 设计

```cpp
// SPIRType::BaseType 新增
enum BaseType {
    // ... 现有类型
    CoopMatHW,
    CoopVecHW,    // 硬件协作向量类型
    // ...
};

// SPIRType::ext 联合体新增
union {
    // ... 现有结构

    struct
    {
        uint32_t component_type_id;   // 组件类型ID
        uint32_t component_count_id;  // 组件数量ID
    } coopVecHW;
} ext;
```

### 4.3 spirv_parser.cpp 设计

```cpp
case OpTypeCooperativeVectorHW:
{
    uint32_t id = ops[0];
    auto &type = set<SPIRType>(id, op);
    type.basetype = SPIRType::CoopVecHW;
    type.op = op;
    type.ext.coopVecHW.component_type_id = ops[1];
    type.ext.coopVecHW.component_count_id = ops[2];
    type.parent_type = ops[1];
    type.self = id;
    auto &component_type = get<SPIRType>(type.ext.coopVecHW.component_type_id);
    type.width = component_type.width;
    break;
}
```

### 4.4 spirv_glsl.cpp 设计

```cpp
// type_to_glsl() 中的类型名称生成
case SPIRType::CoopVecHW:
{
    require_extension_internal("GL_HW_cooperative_vector");
    string component_type_str = type_to_glsl(get<SPIRType>(type.ext.coopVecHW.component_type_id));
    string count = to_expression(type.ext.coopVecHW.component_count_id);
    return join("coopvecHW<", component_type_str, ", ", count, ">");
}

// constant_expression() 中的常量处理（与CoopMatHW同模式）
case SPIRType::CoopVecHW:
{
    // 格式: coopvecHW<T, M>(value0, value1, ...)
}

// 转换指令（OpSConvert/OpUConvert/OpFConvert等）
// CoopVecHW与CoopMatHW共用同一处理分支
if (type.basetype == SPIRType::CoopMatHW || type.basetype == SPIRType::CoopVecHW)
```

---

## 五、测试用例

### 5.1 测试方式

通过 `gen_test_spv.py` 生成测试 SPIR-V 二进制，使用 C++ API（Parser + CompilerGLSL）验证编译输出。

### 5.2 测试 Shader

**GLSL输入**：
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

**期望输出**：
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

## 六、实现检查清单

- [x] `spirv.h` — 添加 `SpvOpTypeCooperativeVectorHW = 6608`
- [x] `spirv.hpp` — 添加 `OpTypeCooperativeVectorHW = 6608`
- [x] `spirv.hpp` — 添加 Capability `CapabilityCooperativeVectorHW = 6607`
- [x] `spirv.hpp` — 更新 InstructionDB 的 `hasResult`/`hasResultType`
- [x] `spirv_common.hpp` — 添加 `CoopVecHW` 到 BaseType
- [x] `spirv_common.hpp` — 扩展 `ext` 联合体
- [x] `spirv_parser.cpp` — 添加类型解析
- [x] `spirv_glsl.cpp` — 添加 `type_to_glsl` 处理
- [x] `spirv_glsl.cpp` — 添加常量处理
- [x] `spirv_glsl.cpp` — 添加转换指令支持
