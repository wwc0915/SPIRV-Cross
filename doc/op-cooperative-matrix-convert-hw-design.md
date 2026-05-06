# CoopMatHW 转换指令与 OpBitcast 设计文档

## 一、概述

允许 `OpTypeCooperativeMatrixHW` 类型用于以下 SPIR-V 转换指令和 OpBitcast。转换结果和输入矩阵形状相同（M×N），仅改变分量类型。

**支持的转换指令**：
- OpConvertFToU、OpConvertFToS（浮点→整数）
- OpConvertSToF、OpConvertUToF（整数→浮点）
- OpSConvert、OpUConvert（整数→整数，位宽变化）
- OpFConvert（浮点→浮点，位宽变化）

**OpBitcast 约束**：结果类型和值类型必须具有相同的分量数量以及每个分量的相同位数。

---

## 二、SPIR-V 指令规范

### 2.1 指令格式

所有转换指令和 OpBitcast 的格式为：

```
| 4 | opcode | <id> Result Type | Result <id> | <id> Value |
```

### 2.2 操作数说明

| 操作数 | 位置 | 描述 |
|--------|------|------|
| Result Type | ops[0] | 目标 coopmatHW 类型 |
| Result `<id>` | ops[1] | 转换结果的 ID |
| Value | ops[2] | 输入 coopmatHW 矩阵 |

### 2.3 语义说明

- 转换指令对矩阵每个分量逐一执行类型转换
- OpBitcast 对矩阵每个分量逐一执行位重新解释
- 输出矩阵形状与输入矩阵相同（M×N）

---

## 三、GLSL 目标接口

### 3.1 GLSL 转换语法

所有转换和 bitcast 统一使用目标类型的构造函数：

```glsl
// 浮点→有符号整数
coopmatHW<int, M, N> intMat = coopmatHW<int, Mu, Nu>(floatMat);

// 整数→浮点
coopmatHW<float, M, N> floatMat = coopmatHW<float, Mu, Nu>(intMat);

// 无符号→有符号整数
coopmatHW<int, M, N> signedMat = coopmatHW<int, Mu, Nu>(unsignedMat);

// Bitcast（浮点→整数，位重新解释）
coopmatHW<int, M, N> intMat = coopmatHW<int, Mu, Nu>(floatMat);
```

---

## 四、实现设计

### 4.1 需要修改的文件

| 文件 | 修改内容 |
|------|----------|
| `spirv_glsl.cpp` | 在 4 个转换/bitcast case 块中添加 CoopMatHW 早期判断 |
| `gen_test_spv.py` | 添加 `gen_convert_test` |

### 4.2 spirv_glsl.cpp 实现

在以下 4 个 case 块中，当 `result_type` 的 basetype 为 `SPIRType::CoopMatHW` 时，直接使用构造函数输出：

**块 1**：`OpSConvert, OpConvertSToF, OpUConvert, OpConvertUToF`
**块 2**：`OpConvertFToU, OpConvertFToS`
**块 3**：`OpFConvert`（已有路径正确，使用 `emit_unary_func_op` + `type_to_glsl_constructor`）
**块 4**：`OpBitcast`

统一处理逻辑：
```cpp
if (get<SPIRType>(result_type).basetype == SPIRType::CoopMatHW)
{
    auto func = type_to_glsl_constructor(get<SPIRType>(result_type));
    emit_unary_func_op(result_type, id, ops[2], func.c_str());
    break;
}
```

---

## 五、测试用例

### 5.1 ConvertFToS（浮点→整数）

**期望 GLSL 输出**：
```glsl
coopmatHW<int, 16u, 16u> result_ftos = coopmatHW<int, 16u, 16u>(matF);
```

### 5.2 ConvertSToF（整数→浮点）

**期望 GLSL 输出**：
```glsl
coopmatHW<float, 16u, 16u> result_stof = coopmatHW<float, 16u, 16u>(result_ftos);
```

### 5.3 OpBitcast（浮点→整数位重解释）

**期望 GLSL 输出**：
```glsl
coopmatHW<int, 16u, 16u> result_bitcast = coopmatHW<int, 16u, 16u>(matF);
```
