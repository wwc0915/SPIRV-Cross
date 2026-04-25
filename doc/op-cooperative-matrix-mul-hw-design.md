# coopmatMulHW 设计文档

## 一、概述

`coopmatMulHW` 是纯矩阵乘法函数，通过复用 `OpCooperativeMatrixMulAddHW`（opcode 6504）指令实现。当该指令的 C 操作数为 `OpUndef`（表示 None）时，SPIRV-Cross 将其映射为 `coopmatMulHW` 调用，而非 `coopmatMulAddHW`。

不新增 SPIR-V opcode，仅通过操作数语义区分。

---

## 二、SPIR-V 指令格式

与 MulAdd 相同的 opcode 6504，区别仅在于 C 操作数为 `OpUndef`：

```
| 6 | opcode:6504 | <id> Result Type | Result <id> | <id> A | <id> B | <id> C(OpUndef) |
```

+ C 操作数为 `<id>` 指向一个 `OpUndef` 值，表示无加法操作
+ SPIRV-Cross 通过 `maybe_get<SPIRUndef>(ops[4])` 检测是否为 None

**设计说明**：SPIR-V 中 `<id>` 不能为 0（会导致解析失败），因此使用 `OpUndef` 作为 None 标记。SPIR-V 生成器需为目标矩阵类型创建一个 `OpUndef` 并作为 C 传入。

---

## 三、GLSL 目标接口

```glsl
void coopmatMulHW(
    out coopmatHW<T1, M, N> matO,    // 输出矩阵
    coopmatHW<T, M, K> matA,         // 左操作数矩阵
    coopmatHW<T, K, N> matB          // 右操作数矩阵
);
```

---

## 四、实现设计

### 4.1 修改文件

| 文件 | 修改内容 |
|------|----------|
| `spirv_glsl.cpp` | 在 `OpCooperativeMatrixMulAddHW` case 中检查 C 是否为 `OpUndef` |

### 4.2 spirv_glsl.cpp 修改

在现有 `OpCooperativeMatrixMulAddHW` case 中，检测 C 是否为 `OpUndef`：

```cpp
case OpCooperativeMatrixMulAddHW:
{
    if (length < 4)
        SPIRV_CROSS_THROW("...");

    uint32_t result_type = ops[0];
    uint32_t id = ops[1];
    uint32_t a = ops[2];
    uint32_t b = ops[3];

    emit_uninitialized_temporary_expression(result_type, id);

    if (length >= 5 && maybe_get<SPIRUndef>(ops[4]) == nullptr)
    {
        uint32_t c = ops[4];
        statement("coopmatMulAddHW(", to_expression(id), ", ",
                  to_expression(a), ", ",
                  to_expression(b), ", ",
                  to_expression(c), ");");
    }
    else
    {
        statement("coopmatMulHW(", to_expression(id), ", ",
                  to_expression(a), ", ",
                  to_expression(b), ");");
    }

    break;
}
```

---

## 五、测试用例

### 5.1 Mul 测试（C=OpUndef）

**SPIR-V 操作**:
```
%undef = OpUndef %coopmatAcc_t
%matA  = OpCooperativeMatrixLoadHW ...
%matB  = OpCooperativeMatrixLoadHW ...
%result = OpCooperativeMatrixMulAddHW %coopmatAcc_t %matA %matB %undef
OpCooperativeMatrixStoreHW %ptr %result ...
```

**期望 GLSL 输出**:
```glsl
coopmatHW<float, 16u, 16u> result;
coopmatMulHW(result, matA, matB);
```

### 5.2 MulAdd 测试（C=有效矩阵）保持不变

```glsl
coopmatMulAddHW(result, matA, matB, matC);
```

---

## 六、实现检查清单

- [x] `spirv_glsl.cpp` — 修改 `OpCooperativeMatrixMulAddHW` case，检测 `OpUndef`
- [x] `gen_test_spv.py` — 添加 `gen_mul_test`（使用 `OpUndef` 作为 C）
- [x] 构建并通过测试
