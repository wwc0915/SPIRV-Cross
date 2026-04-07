# SPIRV-Cross 添加新 Op 流程指南

本文档以 **NVIDIA Cooperative Vector (GL_NV_cooperative_vector)** 扩展的实现为例，介绍在 SPIRV-Cross 中添加新 SPIR-V 操作码的完整流程和注意事项。

---

## 一、整体流程概览

添加新 Op 需要修改多个文件，流程如下：

```
SPIR-V 二进制
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│ 1. spirv.h / spirv.hpp                                  │
│    - 定义 Op 枚举值、Capability、常量枚举               │
└─────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│ 2. spirv_common.hpp                                     │
│    - SPIRType::BaseType 添加新类型                      │
│    - SPIRType::ext 联合体添加类型元数据                 │
└─────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│ 3. spirv_parser.cpp                                     │
│    - 解析 Type Op，创建 SPIRType 对象                   │
│    - 设置类型属性和依赖关系                             │
└─────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│ 4. spirv_cross.cpp                                      │
│    - 数据依赖追踪（Load/Store 的读写注册）              │
│    - 变量访问分析                                       │
└─────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│ 5. spirv_glsl.cpp / spirv_msl.cpp / spirv_hlsl.cpp     │
│    - emit_instruction() 中添加 case 分支                │
│    - type_to_glsl() 中处理类型名称                      │
│    - 常量名称映射表                                     │
│    - 扩展要求声明                                       │
└─────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│ 6. 测试                                                 │
│    - shaders/ 添加测试 shader                           │
│    - reference/ 添加期望输出                            │
└─────────────────────────────────────────────────────────┘
```

---

## 二、详细步骤

### Step 1: spirv.h / spirv.hpp — Op 枚举和 Capability 定义

**文件位置**: 项目根目录的 `spirv.h` (C) 和 `spirv.hpp` (C++)

这些文件通常来自 [SPIRV-Headers](https://github.com/KhronosGroup/SPIRV-Headers)，如果新 Op 是 Khronos 标准的一部分，更新 Headers 即可。如果是厂商扩展，可能需要手动添加。

**需要添加的内容**:

1. **Capability 枚举**:
```cpp
// spirv.hpp ~line 1189
CapabilityCooperativeVectorNV = 5394,
CapabilityCooperativeVectorTrainingNV = 5435,
```

2. **常量枚举** (如果 Op 使用新的枚举类型):
```cpp
// spirv.hpp ~line 1578
enum CooperativeVectorMatrixLayout {
    CooperativeVectorMatrixLayoutRowMajorNV = 0,
    CooperativeVectorMatrixLayoutColumnMajorNV = 1,
    CooperativeVectorMatrixLayoutInferencingOptimalNV = 2,
    CooperativeVectorMatrixLayoutTrainingOptimalNV = 3,
};
```

3. **Op 枚举**:
```cpp
// spirv.hpp ~line 2082
OpTypeCooperativeVectorNV = 5288,
OpCooperativeVectorMatrixMulNV = 5289,
OpCooperativeVectorOuterProductAccumulateNV = 5290,
OpCooperativeVectorReduceSumAccumulateNV = 5291,
OpCooperativeVectorMatrixMulAddNV = 5292,
OpCooperativeVectorLoadNV = 5302,
OpCooperativeVectorStoreNV = 5303,
```

4. **Op 属性函数** (`InstructionDB` 中的 `GetResultType` / `HasResult`):
```cpp
// spirv.hpp ~line 2921
case OpTypeCooperativeVectorNV: *hasResult = true; *hasResultType = false; break;
case OpCooperativeVectorMatrixMulNV: *hasResult = true; *hasResultType = true; break;
case OpCooperativeVectorOuterProductAccumulateNV: *hasResult = false; *hasResultType = false; break;
// ... 其他 ops
```

**注意**: `spirv.h` 和 `spirv.hpp` 需要保持同步，前者是 C 风格带 `Spv` 前缀，后者是 C++ 风格在 `spv` 命名空间中。

---

### Step 2: spirv_common.hpp — SPIRType 扩展

**文件位置**: `spirv_common.hpp`

为新的类型定义内部表示。

**需要修改的内容**:

1. **SPIRType::BaseType 枚举** — 添加新的基础类型:
```cpp
// spirv_common.hpp ~line 576
enum BaseType
{
    // ... 现有类型
    Sampler,
    AccelerationStructure,
    RayQuery,
    CoopVecNV,    // <-- 新增类型

    // Keep internal types at the end.
    ControlPointArray,
    // ...
};
```

2. **SPIRType::ext 联合体** — 添加类型元数据存储:
```cpp
// spirv_common.hpp ~line 636
union
{
    struct
    {
        uint32_t use_id;
        uint32_t rows_id;
        uint32_t columns_id;
        uint32_t scope_id;
    } cooperative;

    struct                           // <-- 新增结构体
    {
        uint32_t component_type_id;  // 组件类型 ID
        uint32_t component_count_id; // 组件数量 ID
    } coopVecNV;

    struct
    {
        uint32_t type;
        uint32_t rank;
        uint32_t shape;
    } tensor;
} ext;
```

---

### Step 3: spirv_parser.cpp — 解析 Op 创建内部类型

**文件位置**: `spirv_parser.cpp`

在 `Parser::parse()` 函数的 `switch` 语句中添加类型解析逻辑。

**示例代码** (`OpTypeCooperativeVectorNV`):
```cpp
// spirv_parser.cpp ~line 759
case OpTypeCooperativeVectorNV:
{
    uint32_t id = ops[0];
    auto &type = set<SPIRType>(id, op);

    type.basetype = SPIRType::CoopVecNV;    // 设置 BaseType
    type.op = op;                            // 保存原始 Op
    type.ext.coopVecNV.component_type_id = ops[1];   // 组件类型
    type.ext.coopVecNV.component_count_id = ops[2];  // 组件数量
    type.parent_type = ops[1];               // 设置父类型用于类型推导

    // 某些操作（如 SMax）需要检查组件的位宽
    auto component_type = get<SPIRType>(type.ext.coopVecNV.component_type_id);
    type.width = component_type.width;
    break;
}
```

**要点**:
- 使用 `set<SPIRType>(id, op)` 创建类型对象
- 设置 `basetype` 用于类型判断
- 设置 `parent_type` 用于类型继承/推导
- 复制必要的属性（如 `width`）到新类型

---

### Step 4: spirv_cross.cpp — 基础 Compiler 中的数据依赖追踪

**文件位置**: `spirv_cross.cpp`

基础 `Compiler` 类需要知道新 Op 的 Load/Store 行为，以便正确追踪变量依赖。

**需要修改的位置**:

1. **`analyze_variable_cache`** — 注册 Load 操作的依赖:
```cpp
// spirv_cross.cpp ~line 377
case OpLoad:
case OpCooperativeMatrixLoadKHR:
case OpCooperativeVectorLoadNV:   // <-- 添加
case OpImageRead:
{
    auto *var = maybe_get_backing_variable(args[2]);
    if (var && var->storage != StorageClassFunction)
    {
        // ...
        var->dependees.push_back(id);
    }
    break;
}
```

2. **`variable_access_heuristic`** — 检测变量读取:
```cpp
// spirv_cross.cpp ~line 4391
case OpCopyObject:
case OpLoad:
case OpCooperativeVectorLoadNV:    // <-- 添加
case OpCooperativeMatrixLoadKHR:
    if (ops[2] == var)
        return true;
    break;
```

3. **`preprocessing_pre_op_handler`** — 预处理阶段检测资源访问:

Load 操作:
```cpp
// spirv_cross.cpp ~line 5527
case OpLoad:
case OpCooperativeMatrixLoadKHR:
case OpCooperativeVectorLoadNV:    // <-- 添加
{
    if (length < 3) return false;
    uint32_t ptr = args[2];
    auto *var = compiler.maybe_get_backing_variable(ptr);
    // ... 资源访问处理
    break;
}
```

Store 操作:
```cpp
// spirv_cross.cpp ~line 5605
case OpStore:
case OpImageWrite:
case OpAtomicStore:
case OpCooperativeMatrixStoreKHR:
case OpCooperativeVectorStoreNV:   // <-- 添加
{
    if (length < 1) return false;
    uint32_t ptr = args[0];
    auto *var = compiler.maybe_get_backing_variable(ptr);
    if (var && (var->storage == StorageClassUniform || ...))
    {
        access_potential_resource(var->self);
    }
    break;
}
```

---

### Step 5: spirv_glsl.cpp — GLSL 后端代码生成

**文件位置**: `spirv_glsl.cpp`

这是最重要的部分，需要在多个位置添加代码。

#### 5.1 常量名称映射表

如果 Op 使用特殊的枚举常量，需要定义名称映射：

```cpp
// spirv_glsl.cpp ~line 55
struct GlslConstantNameMapping
{
    uint32_t value;
    const char *alias;
};

#define DEF_GLSL_MAPPING(x) { x, "gl_" #x }

static const GlslConstantNameMapping CoopVecComponentTypeNames[] = {
    DEF_GLSL_MAPPING(ComponentTypeFloat16NV),
    DEF_GLSL_MAPPING(ComponentTypeFloat32NV),
    DEF_GLSL_MAPPING(ComponentTypeSignedInt8NV),
    // ... 其他组件类型
};

static const GlslConstantNameMapping CoopVecMatrixLayoutNames[] = {
    DEF_GLSL_MAPPING(CooperativeVectorMatrixLayoutRowMajorNV),
    DEF_GLSL_MAPPING(CooperativeVectorMatrixLayoutColumnMajorNV),
    // ... 其他布局
};
```

#### 5.2 emit_instruction() — 添加 Op 处理

在 `emit_instruction()` 函数的 switch 语句中添加 case：

```cpp
// spirv_glsl.cpp ~line 15904
case OpCooperativeVectorLoadNV:
{
    uint32_t result_type = ops[0];
    uint32_t id = ops[1];

    // 创建未初始化的临时变量
    emit_uninitialized_temporary_expression(result_type, id);

    // 发出 GLSL 函数调用
    statement("coopVecLoadNV(", to_expression(id), ", ",
              to_expression(ops[2]), ", ", to_expression(ops[3]), ");");

    // 注册读取操作
    register_read(id, ops[2], false);
    break;
}

case OpCooperativeVectorStoreNV:
{
    uint32_t id = ops[0];
    statement("coopVecStoreNV(", to_expression(ops[2]), ", ",
              to_expression(id), ", ", to_expression(ops[1]), ");");
    register_write(ops[2]);
    break;
}

case OpCooperativeVectorMatrixMulAddNV:
{
    uint32_t result_type = ops[0];
    uint32_t id = ops[1];

    emit_uninitialized_temporary_expression(result_type, id);

    std::string stmt = "coopVecMatMulAddNV(";
    for (uint32_t i = 2; i < length; i++)
    {
        // 特殊处理：某些参数需要转换为 GLSL 常量名
        if (i == 3 || i == 6 || i == 9)  // 组件类型参数
        {
            stmt += to_pretty_expression_if_int_constant(
                ops[i], std::begin(CoopVecComponentTypeNames),
                std::end(CoopVecComponentTypeNames));
        }
        else if (i == 12)  // 布局参数
        {
            stmt += to_pretty_expression_if_int_constant(
                ops[i], std::begin(CoopVecMatrixLayoutNames),
                std::end(CoopVecMatrixLayoutNames));
        }
        else
        {
            stmt += to_expression(ops[i]);
        }

        if (i < length - 1) stmt += ", ";
    }
    stmt += ");";
    statement(stmt);
    break;
}
```

**关键函数**:
- `emit_uninitialized_temporary_expression()` — 创建输出变量
- `to_expression()` — 获取操作数的 GLSL 表达式
- `to_pretty_expression_if_int_constant()` — 将整数常量转换为 GLSL 名称
- `statement()` — 输出一行代码
- `register_read()` / `register_write()` — 追踪变量访问

#### 5.3 type_to_glsl() — 类型名称生成

```cpp
// spirv_glsl.cpp ~line 16994
if (type.op == OpTypeCooperativeVectorNV)
{
    require_extension_internal("GL_NV_cooperative_vector");
    if (!options.vulkan_semantics)
        SPIRV_CROSS_THROW("Cooperative vector NV only available in Vulkan.");

    std::string component_type_str = type_to_glsl(get<SPIRType>(type.ext.coopVecNV.component_type_id));

    return join("coopvecNV<", component_type_str, ", ",
                to_expression(type.ext.coopVecNV.component_count_id), ">");
}
```

#### 5.4 数组访问处理

如果类型支持索引访问（如 `vec[5]`），需要在 `access_chain` 相关代码中处理：

```cpp
// spirv_glsl.cpp ~line 10761
// Arrays and OpTypeCooperativeVectorNV (aka fancy arrays)
else if (!type->array.empty() || type->op == OpTypeCooperativeVectorNV)
{
    // 处理数组式访问
}
```

---

### Step 6: spirv_msl.cpp — MSL 后端（可选）

如果目标包括 Metal，需要在 MSL 后端添加类似处理。

**预处理检测** (`OpCodePreprocessor`):
```cpp
// spirv_msl.hpp ~line 1403
struct OpCodePreprocessor : OpcodeHandler
{
    // ...
    bool uses_cooperative_matrix = false;
};
```

```cpp
// spirv_msl.cpp ~line 19242
case OpCooperativeMatrixLoadKHR:
case OpCooperativeMatrixMulAddKHR:
case OpCooperativeMatrixLengthKHR:
    uses_cooperative_matrix = true;
    break;
```

**头文件包含**:
```cpp
// spirv_msl.cpp ~line 1934
if (preproc.uses_cooperative_matrix)
{
    if (!msl_options.supports_msl_version(3, 1))
        SPIRV_CROSS_THROW("Cooperative matrices require MSL 3.1 or later.");
    add_header_line("#include <metal_simdgroup_matrix>");
}
```

**emit_instruction()** — 类似 GLSL，但使用 MSL 语法。

---

### Step 7: 添加测试

**测试 Shader 目录结构**:
```
shaders/
├── comp/
│   └── cooperative-vec-nv.spv16.vk.nocompat.comp    # 输入 GLSL
├── shaders-msl/
│   └── ...                                           # MSL 测试
└── shaders-hlsl/
    └── ...                                           # HLSL 测试

reference/
├── shaders/
│   └── comp/
│       └── cooperative-vec-nv.spv16.vk.nocompat.comp.vk  # 期望输出
└── opt/
    └── ...                                                 # 优化版本
```

**测试文件命名规范**:
- 文件名包含关键特性标记：`vk` (Vulkan), `spv16` (SPIR-V 1.6), `nocompat` (非兼容模式)
- 后缀表示目标语言：`.vk` (GLSL Vulkan), `.msl` (Metal), `.hlsl` (HLSL)

**运行测试**:
```bash
# 完整测试
./test_shaders.sh

# 单独测试 GLSL
python3 test_shaders.py shaders --spirv-cross ./spirv-cross

# 更新 reference
./update_test_shaders.sh
```

---

## 三、注意事项

### 1. Op 分类

- **Type Op** (如 `OpTypeCooperativeVectorNV`): 在 `spirv_parser.cpp` 中解析，创建 `SPIRType`
- **Operation Op** (如 `OpCooperativeVectorLoadNV`): 在各后端的 `emit_instruction()` 中处理

### 2. 常见遗漏点

| 遗漏 | 后果 |
|------|------|
| 忘记在 `spirv_cross.cpp` 注册 Load/Store | 变量依赖分析错误，可能导致不正确的优化 |
| 忘记 `require_extension_internal()` | 生成的代码缺少 `#extension` 声明 |
| 忘记处理 `parent_type` | 类型推导失败 |
| `spirv.h` 和 `spirv.hpp` 不同步 | C/C++ API 行为不一致 |

### 3. 类型系统

- 使用 `SPIRType::BaseType` 进行类型判断
- 使用 `SPIRType::ext` 存储类型的额外信息
- 设置 `type.width` 以支持位宽相关的操作

### 4. 代码风格

```bash
# 格式化代码
./format_all.sh
```

使用项目根目录的 `.clang-format` 配置。

### 5. 测试覆盖

- 添加正向测试（正常使用）
- 添加边界测试（特殊情况）
- 考虑不同 shader stage (comp, frag, vert)
- 考虑优化和非优化版本 (`reference/` 和 `reference/opt/`)

---

## 四、快速检查清单

添加新 Op 时，按此清单检查：

- [ ] `spirv.h` / `spirv.hpp` — Op 枚举、Capability、常量枚举、InstructionDB
- [ ] `spirv_common.hpp` — BaseType、ext 联合体
- [ ] `spirv_parser.cpp` — 类型解析
- [ ] `spirv_cross.cpp` — Load/Store 依赖追踪（3 处）
- [ ] `spirv_glsl.cpp`:
  - [ ] 常量名称映射表
  - [ ] `emit_instruction()` case
  - [ ] `type_to_glsl()` 类型名称
  - [ ] `require_extension_internal()` 扩展声明
  - [ ] 数组/访问链处理（如适用）
- [ ] `spirv_msl.cpp` — MSL 后端（如需要）
- [ ] `spirv_hlsl.cpp` — HLSL 后端（如需要）
- [ ] 测试 shader 和 reference 文件
- [ ] 代码格式化 (`./format_all.sh`)

---

## 五、参考资源

- [SPIRV-Headers](https://github.com/KhronosGroup/SPIRV-Headers) — SPIR-V 指令集定义
- [SPIRV-Tools](https://github.com/KhronosGroup/SPIRV-Tools) — SPIR-V 汇编/反汇编工具
- [glslang](https://github.com/KhronosGroup/glslang) — GLSL 到 SPIR-V 编译器
- [SPIRV-Cross Wiki](https://github.com/KhronosGroup/SPIRV-Cross/wiki) — 官方文档
