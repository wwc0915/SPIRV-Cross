# HW 扩展后端拒绝 设计文档

## 一、概述

`design.md` 中新增的 SPV 扩展均为 GLSL 专属硬件扩展：

| 扩展 (OpExtension) | Capability | GLSL 扩展 | 覆盖范围 |
|--------------------|------------|-----------|----------|
| `SPV_HW_neural_matrix` | `CooperativeMatrixHW = 6600` | `GL_HW_neural_matrix` | coopmatHW 类型与指令 |
| `SPV_HW_cooperative_vector` | `CooperativeVectorHW = 6607` | `GL_HW_cooperative_vector` | coopvecHW 类型与指令 |
| `SPV_HW_neural_shader` | （无 capability） | `GL_HW_neural_shader` | cp-async / shuffle / TensorMap |

这些扩展只在 GLSL 后端有对应的 intrinsic 实现。当用户把含有这些扩展/capability 的
SPIR-V 二进制转成非 GLSL 语言（MSL、HLSL、C++、Reflect）时，应当给出明确的错误提示，
而不是静默生成错误的代码（HW 指令会通过 `default` 分支落入基类 `CompilerGLSL::emit_instruction`，
把 GLSL intrinsic 写进 MSL/HLSL 输出）。

---

## 二、检测机制

非 GLSL 后端在 `compile()` 入口处调用 `CompilerGLSL::reject_hw_neural_extensions()`，遍历：

1. `ir.declared_extensions`：任何以 `SPV_HW_` 为前缀的扩展字符串 → 抛错。
2. `ir.declared_capabilities`：`CapabilityCooperativeMatrixHW (6600)` 或 `CapabilityCooperativeVectorHW (6607)` → 抛错。

两者取并集：

- `SPV_HW_neural_shader` 只声明 `OpExtension`（无 capability）→ 由扩展前缀检测命中。
- `SPV_HW_neural_matrix` / `SPV_HW_cooperative_vector` 的测试只声明 `OpCapability 6600`/`6607`
  （未声明 `OpExtension`）→ 由 capability 检测命中。
- 任意一种声明方式都能被捕获，无需修改既有测试。

> 该检测在 `compile()` 最开始执行，早于任何类型/指令发射，保证 fail-fast。

---

## 三、实现设计

### 3.1 需要修改的文件

| 文件 | 修改 |
|------|------|
| `spirv_glsl.hpp` | `CompilerGLSL` 新增 `void reject_hw_neural_extensions();` 声明 |
| `spirv_glsl.cpp` | 实现该方法：遍历 `declared_extensions` / `declared_capabilities` 并 `SPIRV_CROSS_THROW` |
| `spirv_msl.cpp` / `spirv_hlsl.cpp` / `spirv_cpp.cpp` / `spirv_reflect.cpp` | 各自 `compile()` 入口处调用 `reject_hw_neural_extensions()` |

GLSL 后端（`CompilerGLSL::compile()`）不调用此方法，保持原有行为。

### 3.2 核心实现

```cpp
void CompilerGLSL::reject_hw_neural_extensions()
{
    for (auto &ext : ir.declared_extensions)
        if (ext.rfind("SPV_HW_", 0) == 0)
            SPIRV_CROSS_THROW(ext + " extension is only supported by the GLSL backend.");

    for (auto &cap : ir.declared_capabilities)
        if (cap == CapabilityCooperativeMatrixHW || cap == CapabilityCooperativeVectorHW)
            SPIRV_CROSS_THROW("HW neural matrix/vector capability is only supported by the GLSL backend.");
}
```

- `ext.rfind("SPV_HW_", 0) == 0` 为 C++11 起始字符串匹配惯用法。
- capability 名取自 `spirv.hpp`（`using namespace spv;` 已生效）。

### 3.3 调用点

```cpp
string CompilerMSL::compile()       { reject_hw_neural_extensions(); /* ... */ }
string CompilerHLSL::compile()      { reject_hw_neural_extensions(); /* ... */ }
string CompilerCPP::compile()       { reject_hw_neural_extensions(); /* ... */ }
string CompilerReflection::compile(){ reject_hw_neural_extensions(); /* ... */ }
```

---

## 四、测试用例

### 4.1 覆盖矩阵

| 输入 SPV | 目标后端 | 期望 |
|----------|----------|------|
| `test_hw_cp_async.spv`（SPV_HW_neural_shader） | `--msl` / `--hlsl` | 抛错，提示 `SPV_HW_neural_shader ... only supported by the GLSL backend.` |
| `test_hw_length.spv`（cap 6600） | `--msl` | 抛错，提示 `HW neural matrix/vector capability ... only supported by the GLSL backend.` |
| `test_hw_coopvec.spv`（cap 6607） | `--msl` | 同上 |
| `test_hw_cp_async.spv` | 默认 GLSL | 正常输出 |
| `test_hw_reg_control.spv`（无 HW 扩展/cap） | `--msl` | 正常输出（无误报） |

### 4.2 期望错误输出示例

```
SPIRV-Cross threw an exception: SPV_HW_neural_shader extension is only supported by the GLSL backend.
```

---

## 五、参考

- [总体设计文档](design.md) — 各 HW 扩展章节
- 既有扩展/capability 解析：`spirv_parser.cpp` `case OpCapability` / `case OpExtension`
- 既有后端错误模式：`spirv_glsl.cpp` `find_static_extensions()` 中 `SPIRV_CROSS_THROW`
