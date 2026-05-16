# CoopVecHW 转换指令与 OpBitcast 设计文档

## 一、概述

允许 `OpTypeCooperativeVectorHW` 类型用于以下 SPIR-V 转换指令和 OpBitcast。转换结果和输入向量分量数量相同，仅改变分量类型。

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
| Result Type | ops[0] | 目标 coopvecHW 类型 |
| Result `<id>` | ops[1] | 转换结果的 ID |
| Value | ops[2] | 输入 coopvecHW 向量 |

### 2.3 语义说明

- 转换指令对向量每个分量逐一执行类型转换
- OpBitcast 对向量每个分量逐一执行位重新解释
- 输出向量分量数量与输入向量相同

---

## 三、GLSL 目标接口

### 3.1 GLSL 转换语法

转换指令统一使用目标类型的构造函数：

```glsl
// 浮点→有符号整数 (OpConvertFToS)
coopvecHW<int, M> intVec = coopvecHW<int, Mu>(floatVec);

// 整数→浮点 (OpConvertSToF)
coopvecHW<float, M> floatVec = coopvecHW<float, Mu>(intVec);

// 无符号→有符号整数 (OpSConvert)
coopvecHW<int, M> signedVec = coopvecHW<int, Mu>(unsignedVec);
```

### 3.2 GLSL Bitcast 语法

当分量类型之间需要位重新解释时，使用 GLSL 内建函数：

```glsl
// float32→int32 位重解释
coopvecHW<int, M> intVec = floatBitsToInt(floatVec);

// int32→float32 位重解释
coopvecHW<float, M> floatVec = intBitsToFloat(intVec);

// float32→uint32 位重解释
coopvecHW<uint, M> uintVec = floatBitsToUint(floatVec);

// uint32→float32 位重解释
coopvecHW<float, M> floatVec = uintBitsToFloat(uintVec);
```

当 `bitcast_glsl_op` 返回空字符串时，退化为使用构造函数语法。

---

## 四、实现设计

### 4.1 需要修改的文件

| 文件 | 修改内容 |
|------|----------|
| `spirv_glsl.cpp` | 在 OpBitcast case 中添加 CoopVecHW 判断；OpSConvert/OpConvertSToF/OpUConvert/OpConvertUToF 和 OpConvertFToU/OpConvertFToS 已支持 CoopVecHW |
| `gen_test_spv.py` | 添加 `gen_coopvec_convert_test`、`gen_coopvec_bitcast32_test` |

### 4.2 已支持的转换指令（无需修改）

以下 case 块已在先前的实现中包含 `CoopVecHW` 判断：

**块 1**：`OpSConvert, OpConvertSToF, OpUConvert, OpConvertUToF`（spirv_glsl.cpp:13746）

```cpp
if (type.basetype == SPIRType::CoopMatHW || type.basetype == SPIRType::CoopVecHW)
{
    auto func = type_to_glsl_constructor(type);
    emit_unary_func_op(result_type, id, ops[2], func.c_str());
    break;
}
```

**块 2**：`OpConvertFToU, OpConvertFToS`（spirv_glsl.cpp:13771）

```cpp
if (type.basetype == SPIRType::CoopMatHW || type.basetype == SPIRType::CoopVecHW)
{
    auto func = type_to_glsl_constructor(type);
    emit_unary_func_op(result_type, id, ops[2], func.c_str());
    break;
}
```

**块 3**：`OpFConvert`（spirv_glsl.cpp:13788）——通用路径，通过 `type_to_glsl_constructor` 正确处理所有类型。

### 4.3 新增修改：OpBitcast（spirv_glsl.cpp:13798）

OpBitcast 原来仅判断 `CoopMatHW`，现扩展为同时支持 `CoopVecHW`：

```cpp
if (get<SPIRType>(result_type).basetype == SPIRType::CoopMatHW ||
    get<SPIRType>(result_type).basetype == SPIRType::CoopVecHW)
{
    auto &arg_type = expression_type(arg);
    if (arg_type.basetype == SPIRType::CoopMatHW || arg_type.basetype == SPIRType::CoopVecHW)
    {
        const SPIRType &out_type = get<SPIRType>(result_type);
        const SPIRType &out_component = get<SPIRType>(
            out_type.basetype == SPIRType::CoopMatHW
                ? out_type.ext.coopMatHW.component_type_id
                : out_type.ext.coopVecHW.component_type_id);
        const SPIRType &in_component = get<SPIRType>(
            arg_type.basetype == SPIRType::CoopMatHW
                ? arg_type.ext.coopMatHW.component_type_id
                : arg_type.ext.coopVecHW.component_type_id);
        auto op = bitcast_glsl_op(out_component, in_component);
        if (!op.empty())
        {
            emit_unary_func_op(result_type, id, arg, op.c_str());
            break;
        }
    }
    auto func = type_to_glsl_constructor(get<SPIRType>(result_type));
    emit_unary_func_op(result_type, id, arg, func.c_str());
    break;
}
```

**关键设计点**：
- 根据类型（CoopMatHW 或 CoopVecHW）选择正确的 `component_type_id` 路径，因为两者的扩展结构不同：
  - CoopMatHW：`ext.coopMatHW.component_type_id`
  - CoopVecHW：`ext.coopVecHW.component_type_id`
- 先尝试 `bitcast_glsl_op` 获取专门的 bitcast 函数（如 `floatBitsToInt`），如果不存在则回退到构造函数语法

---

## 五、测试用例

### 5.1 测试文件

| 文件名 | 生成函数 | 覆盖范围 |
|--------|----------|----------|
| `test_hw_coopvec_convert.spv` | `gen_coopvec_convert_test` | OpConvertFToS、OpConvertSToF、OpBitcast |
| `test_hw_coopvec_bitcast32.spv` | `gen_coopvec_bitcast32_test` | float32↔int32、float32↔uint32 bitcast |

### 5.2 ConvertFToS（浮点→整数）

**输入 SPIR-V**：
```
%vecF = OpCooperativeVectorLoadHW %coopvecF %ptr_elem
%result_ftos = OpConvertFToS %coopvecI %vecF
```

**期望 GLSL 输出**：
```glsl
coopvecHW<int, 16u> result_ftos = coopvecHW<int, 16u>(vecF);
```

### 5.3 ConvertSToF（整数→浮点）

**输入 SPIR-V**：
```
%result_stof = OpConvertSToF %coopvecF %result_ftos
```

**期望 GLSL 输出**：
```glsl
coopvecHW<float, 16u> result_stof = coopvecHW<float, 16u>(result_ftos);
```

### 5.4 OpBitcast float→int（位重解释）

**输入 SPIR-V**：
```
%result_bitcast = OpBitcast %coopvecI %vecF
```

**期望 GLSL 输出**：
```glsl
coopvecHW<int, 16u> result_bitcast = floatBitsToInt(vecF);
```

### 5.5 OpBitcast float32→uint32

**期望 GLSL 输出**：
```glsl
coopvecHW<uint, 16u> result_f2u = floatBitsToUint(vecF);
```

### 5.6 OpBitcast uint32→float32

**期望 GLSL 输出**：
```glsl
coopvecHW<float, 16u> result_u2f = uintBitsToFloat(result_f2u);
```

---

## 六、与 CoopMatHW 转换指令的对比

| 维度 | CoopMatHW | CoopVecHW |
|------|-----------|-----------|
| 转换指令支持 | OpConvertFToU/S、OpConvertSToF/OpToF、OpSConvert/UConvert、OpFConvert | 相同 |
| OpBitcast 支持 | 使用 `ext.coopMatHW.component_type_id` | 使用 `ext.coopVecHW.component_type_id` |
| 类型形状 | M×N 矩阵，行数×列数 | M 分量向量 |
| GLSL 类型 | `coopmatHW<T, Mu, Nu>` | `coopvecHW<T, Mu>` |
| GLSL 构造函数 | `coopmatHW<int, Mu, Nu>(floatMat)` | `coopvecHW<int, Mu>(floatVec)` |

两者的转换逻辑完全一致：统一使用目标类型构造函数或 `bitcast_glsl_op` 内建函数，区别仅在于类型维度和扩展结构路径。
