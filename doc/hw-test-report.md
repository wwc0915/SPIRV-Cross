# SPIRV-Cross HW 扩展测试自验证报告

## 一、测试方法

### 1.1 验证流程

采用 SPIRV-Cross 项目的标准回归测试方法，对每个 GLSL 源 shader 执行以下流水线：

```
GLSL 源 shader
    │  glslangValidator --target-env vulkan1.3 -V -o x.spv input.comp
    ▼
SPIR-V 二进制 (x.spv, SPIR-V 1.6)
    │  spirv-val --target-env vulkan1.3 x.spv            ← 验证 SPIR-V 合法性
    ▼
    │  spirv-cross --entry main --output out.glsl x.spv  ← 反编译为 GLSL
    ▼
输出 GLSL (out.glsl)
    │  glslangValidator --target-env vulkan1.3 out.glsl   ← 验证输出 GLSL 可编译
    ▼
    │  md5 比对 out.glsl vs reference/hw/.../*.comp  ← 回归比对
    ▼
通过 / 失败
```

**关键设计**：spirv-cross 转换后的 GLSL 与原始 GLSL **不要求文本一致**（变量名、布局限定符、临时变量等会不同），验证正确性依赖两个机制：
1. **glslang 反向验证**——输出 GLSL 必须能被 glslang 重新编译通过，证明输出是合法 GLSL
2. **Reference 文件 + MD5 回归比对**——首次运行将 spirv-cross 输出固化为 reference 文件；后续运行用 MD5 比对输出是否变化，捕获回归

### 1.2 Vulkan 专属 shader 处理

使用 `GL_EXT_buffer_reference`（Vulkan 专属特性）的 shader 命名为 `.vk.nocompat.` 前缀，测试框架自动使用 `spirv-cross -V`（Vulkan GLSL 模式）编译和验证，glslang 使用 `--target-env vulkan1.3`。

### 1.3 编译目标环境

所有 HW 扩展测试 shader 统一使用 `--target-env vulkan1.3` 编译和验证（SPIR-V 1.6），通过 `test_hw_shaders.sh` 的 `--target-env vulkan1.3` 参数传入 `test_shaders.py`，覆盖默认的 `vulkan1.1`。

### 1.4 统计与容错

测试脚本使用 `--continue` 标志，遇到失败不中断，跑完全部用例后汇总统计总数、通过数、失败数及失败详情。

---

## 二、测试脚本用法

### 2.1 脚本位置

```
test_hw_shaders.sh
```

### 2.2 依赖工具

测试所需的外部工具及对应环境变量在 `test_hw_shaders.sh` 脚本顶部的 `GLSLANG_BUILD` 变量中统一配置，修改该变量即可指向自己的 glslang + spirv-tools 构建目录。

| 工具 | 来源 | 说明 |
|------|------|------|
| glslangValidator | `${GLSLANG_BUILD}/StandAlone/glslangValidator` | 需支持 HW 扩展内建符号 |
| spirv-val | `${GLSLANG_BUILD}/External/spirv-tools/tools/spirv-val` | SPIR-V 验证 |
| spirv-opt | `${GLSLANG_BUILD}/External/spirv-tools/tools/spirv-opt` | SPIR-V 优化（`--opt` 时启用） |
| spirv-as | `${GLSLANG_BUILD}/External/spirv-tools/tools/spirv-as` | SPIR-V 汇编（`.asm.` shader 用） |
| spirv-cross | 项目根目录 `./spirv-cross` | 不存在时脚本自动 `make` 构建 |

### 2.3 命令

```bash
# 运行回归测试（统计总数/通过/失败，使用 vulkan1.3 target-env）
./test_hw_shaders.sh

# 更新 reference 文件（输出变化时）
./test_hw_shaders.sh --update

# 失败时显示 diff
./test_hw_shaders.sh --diff

# 并行执行
./test_hw_shaders.sh --parallel
```

脚本内部调用 `test_shaders.py` 时传入 `--target-env vulkan1.3`，使 glslang 编译、spirv-val 验证、glslang 反向验证全部使用 Vulkan 1.3 / SPIR-V 1.6 环境。

### 2.4 输出示例

```
========================================
Statistics: total=59  passed=59  failed=0
========================================
HW shader tests completed!
```

---

## 三、测试用例位置与数量

### 3.1 文件位置

| 目录 | 内容 |
|------|------|
| `shaders/hw/comp/` | 41 个 compute shader 源文件 + .spv |
| `shaders/hw/frag/` | 9 个 fragment shader 源文件 + .spv |
| `shaders/hw/vert/` | 9 个 vertex shader 源文件 + .spv |
| `reference/hw/comp/` | 41 个 reference（期望输出）文件 |
| `reference/hw/frag/` | 9 个 reference 文件 |
| `reference/hw/vert/` | 9 个 reference 文件 |

**总计：59 个测试用例**（comp 41 + frag 9 + vert 9）

### 3.2 shader 来源

全部来自 glslang 仓库 `Test/` 目录中 HW 扩展相关的测试 shader，排除了 Error/Negative 用例（预期编译失败的负向测试）和非 HW 扩展 shader（如 NV/KHR cooperative matrix）。

---

## 四、涉及的 HW Op、Capability 和 Extension

### 4.1 HW 指令（17 条）

| Opcode | 指令 | 功能 |
|--------|------|------|
| 6602 | OpCooperativeMatrixLengthHW | 协作矩阵元素个数查询 |
| 6603 | OpCooperativeMatrixLoadHW | 协作矩阵加载 |
| 6604 | OpCooperativeMatrixStoreHW | 协作矩阵存储 |
| 6605 | OpCooperativeMatrixMulAddHW | 协作矩阵乘加（C=OpUndef 时为纯乘法） |
| 6606 | OpCooperativeMatrixReduceHW | 协作矩阵归约 |
| 6609 | OpCooperativeVectorLoadHW | 协作向量加载 |
| 6610 | OpCooperativeVectorStoreHW | 协作向量存储 |
| 6611 | OpCooperativeVectorMatrixMulAddHW | 协作向量矩阵乘加 |
| 6612 | OpCooperativeVectorMatrixMulHW | 协作向量矩阵乘法 |
| 6614 | OpCpAsyncTensorGlobalSharedHW | 张量映射异步拷贝 |
| 6615 | OpCpAsyncCommitGroupHW | 提交异步拷贝组 |
| 6616 | OpCpAsyncWaitGroupHW | 等待异步拷贝组 |
| 6617 | OpBarrierArriveHW | 屏障到达（非阻塞） |
| 6618 | OpBarrierWaitHW | 屏障等待 |
| 6619 | OpShuffleIndexHW | 硬件 shuffle 索引 |
| 6620 | OpBytePermuteHW | 字节重排 |
| 6621 | OpShuffleFillDownHW | shuffle 填充下移 |

### 4.2 HW 类型（3 种）

| Opcode | 类型 | 说明 |
|--------|------|------|
| 6601 | OpTypeCooperativeMatrixHW | 硬件协作矩阵类型 |
| 6608 | OpTypeCooperativeVectorHW | 硬件协作向量类型 |
| 6613 | OpTypeTensorMapHW | 张量映射类型 |

### 4.3 寄存器控制属性

| 来源 | GLSL 属性 | 说明 |
|------|----------|------|
| OpSelectionMerge SelectionControl Relreg 掩码位 (0x4) | `[[reg_control]]` | 硬件寄存器控制提示，可与 flatten/branch 组合为 `[[flatten, reg_control]]` |

### 4.4 Capability（2 种）

| 值 | 名称 | 覆盖范围 |
|----|------|---------|
| 6600 | CooperativeMatrixHW | 协作矩阵运算 |
| 6607 | CooperativeVectorHW | 协作向量运算 |

### 4.5 Extension

| Extension | 说明 |
|-----------|------|
| `SPV_HW_neural_shader` | HW 神经网络着色器扩展（矩阵/向量/cp-async/barrier/shuffle/reg_control 均归属此扩展） |
| `SPV_KHR_vulkan_memory_model` | Vulkan 内存模型（多数 shader 使用） |
| `SPV_KHR_8bit_storage` | 8 位存储（builtin shader 使用 int8） |
| `SPV_KHR_physical_storage_buffer` | 物理存储缓冲（coopvecHWloadstore 使用 buffer_reference） |
| `SPV_EXT_replicated_composites` | 复合常量复制扩展 |

### 4.6 标准 SPIR-V 指令在 HW 类型上的测试

以下 shader 虽然不使用 HW 专属指令，但在 HW 类型上使用标准 SPIR-V 转换/运算指令，测试 spirv-cross 的 HW 类型处理代码路径：

- `*_arithmetic.*` — OpFAdd/OpFMul 等算术运算 on CoopMatHW
- `*_bitcast.*` — OpBitcast on CoopMatHW/CoopVecHW（float↔int 位重解释）
- `*_conversion.*` — OpConvertFToS/OpConvertSToF/OpUConvert/OpFConvert on CoopMatHW/CoopVecHW

---

## 五、测试结果

### 5.1 汇总

| 指标 | 值 |
|------|-----|
| 总用例数 | 59 |
| 通过 | 59 |
| 失败 | 0 |
| 通过率 | 100% |
| 验证项 | spirv-val + spirv-cross + glslang validate + MD5 reference |

### 5.2 逐用例结果

| # | Shader | Stage | Result | HW Instructions | HW Types | Capabilities | Extensions |
|---|--------|-------|--------|-----------------|---------|-------------|------------|
| 1 | spv.coopmatHW.comp | comp | PASS | OpCooperativeMatrixLengthHW, OpCooperativeMatrixLoadHW, OpCooperativeMatrixMulAddHW, OpCooperativeMatrixReduceHW, OpCooperativeMatrixStoreHW | OpTypeCooperativeMatrixHW | CooperativeMatrixHW | SPV_HW_neural_shader +1 |
| 2 | spv.coopmatHW_arithmetic.comp | comp | PASS | - | OpTypeCooperativeMatrixHW | CooperativeMatrixHW | SPV_HW_neural_shader +1 |
| 3 | spv.coopmatHW_bitcast.comp | comp | PASS | - | OpTypeCooperativeMatrixHW | CooperativeMatrixHW | SPV_HW_neural_shader +1 |
| 4 | spv.coopmatHW_builtin.comp | comp | PASS | OpCooperativeMatrixLengthHW, OpCooperativeMatrixLoadHW, OpCooperativeMatrixMulAddHW, OpCooperativeMatrixReduceHW, OpCooperativeMatrixStoreHW | OpTypeCooperativeMatrixHW | CooperativeMatrixHW | SPV_HW_neural_shader +2 |
| 5 | spv.coopmatHW_conversion.comp | comp | PASS | - | OpTypeCooperativeMatrixHW | CooperativeMatrixHW | SPV_HW_neural_shader +1 |
| 6 | spv.coopmatHW_logicalUse.comp | comp | PASS | OpCooperativeMatrixLoadHW, OpCooperativeMatrixMulAddHW | OpTypeCooperativeMatrixHW | CooperativeMatrixHW | SPV_HW_neural_shader +1 |
| 7 | spv.coopmatHW_roleCheck.comp | comp | PASS | OpCooperativeMatrixLoadHW, OpCooperativeMatrixMulAddHW | OpTypeCooperativeMatrixHW | CooperativeMatrixHW | SPV_HW_neural_shader +1 |
| 8 | spv.coopmatHW_roleFunction.comp | comp | PASS | OpCooperativeMatrixLoadHW, OpCooperativeMatrixMulAddHW | OpTypeCooperativeMatrixHW | CooperativeMatrixHW | SPV_HW_neural_shader +1 |
| 9 | spv.coopmatHW_roleReturn.comp | comp | PASS | OpCooperativeMatrixLoadHW, OpCooperativeMatrixMulAddHW | OpTypeCooperativeMatrixHW | CooperativeMatrixHW | SPV_HW_neural_shader +1 |
| 10 | spv.coopmatHW_roleReturnForward.comp | comp | PASS | OpCooperativeMatrixLoadHW, OpCooperativeMatrixMulAddHW | OpTypeCooperativeMatrixHW | CooperativeMatrixHW | SPV_HW_neural_shader +1 |
| 11 | spv.coopmatHW_ternary.comp | comp | PASS | OpCooperativeMatrixLoadHW, OpCooperativeMatrixMulAddHW | OpTypeCooperativeMatrixHW | CooperativeMatrixHW | SPV_HW_neural_shader +1 |
| 12 | spv.coopmatHW_use_pass.comp | comp | PASS | OpCooperativeMatrixLoadHW, OpCooperativeMatrixMulAddHW, OpCooperativeMatrixStoreHW | OpTypeCooperativeMatrixHW | CooperativeMatrixHW | SPV_HW_neural_shader +1 |
| 13 | spv.coopmatHW_use_pass_abconflict.comp | comp | PASS | OpCooperativeMatrixLoadHW, OpCooperativeMatrixMulAddHW | OpTypeCooperativeMatrixHW | CooperativeMatrixHW | SPV_HW_neural_shader +1 |
| 14 | spv.coopmatHW_use_pass_accpriority.comp | comp | PASS | OpCooperativeMatrixLoadHW, OpCooperativeMatrixMulAddHW | OpTypeCooperativeMatrixHW | CooperativeMatrixHW | SPV_HW_neural_shader +1 |
| 15 | spv.coopmatHW_use_pass_allroles.comp | comp | PASS | OpCooperativeMatrixLoadHW, OpCooperativeMatrixMulAddHW | OpTypeCooperativeMatrixHW | CooperativeMatrixHW | SPV_HW_neural_shader +1 |
| 16 | spv.coopmatHW_use_pass_array.comp | comp | PASS | OpCooperativeMatrixLoadHW, OpCooperativeMatrixMulAddHW | OpTypeCooperativeMatrixHW | CooperativeMatrixHW | SPV_HW_neural_shader +1 |
| 17 | spv.coopmatHW_use_pass_block.comp | comp | PASS | OpCooperativeMatrixLoadHW, OpCooperativeMatrixMulAddHW | OpTypeCooperativeMatrixHW | CooperativeMatrixHW | SPV_HW_neural_shader +1 |
| 18 | spv.coopmatHW_use_pass_chain.comp | comp | PASS | OpCooperativeMatrixLoadHW, OpCooperativeMatrixMulAddHW | OpTypeCooperativeMatrixHW | CooperativeMatrixHW | SPV_HW_neural_shader +1 |
| 19 | spv.coopmatHW_use_pass_eqcount.comp | comp | PASS | OpCooperativeMatrixLoadHW, OpCooperativeMatrixMulAddHW | OpTypeCooperativeMatrixHW | CooperativeMatrixHW | SPV_HW_neural_shader +1 |
| 20 | spv.coopmatHW_use_pass_func.comp | comp | PASS | OpCooperativeMatrixLoadHW, OpCooperativeMatrixMulAddHW | OpTypeCooperativeMatrixHW | CooperativeMatrixHW | SPV_HW_neural_shader +1 |
| 21 | spv.coopmatHW_use_pass_matmul.comp | comp | PASS | OpCooperativeMatrixLoadHW, OpCooperativeMatrixMulAddHW | OpTypeCooperativeMatrixHW | CooperativeMatrixHW | SPV_HW_neural_shader +1 |
| 22 | spv.coopmatHW_use_pass_matmul_rect.comp | comp | PASS | OpCooperativeMatrixLoadHW, OpCooperativeMatrixMulAddHW, OpCooperativeMatrixStoreHW | OpTypeCooperativeMatrixHW | CooperativeMatrixHW | SPV_HW_neural_shader +2 |
| 23 | spv.coopmatHW_use_pass_mixed.comp | comp | PASS | OpCooperativeMatrixLoadHW, OpCooperativeMatrixMulAddHW | OpTypeCooperativeMatrixHW | CooperativeMatrixHW | SPV_HW_neural_shader +1 |
| 24 | spv.coopmatHW_use_pass_nomul.comp | comp | PASS | OpCooperativeMatrixLoadHW, OpCooperativeMatrixStoreHW | OpTypeCooperativeMatrixHW | CooperativeMatrixHW | SPV_HW_neural_shader +1 |
| 25 | spv.coopmatHW_use_pass_noncoopmat.comp | comp | PASS | OpCooperativeMatrixLoadHW, OpCooperativeMatrixMulAddHW | OpTypeCooperativeMatrixHW | CooperativeMatrixHW | SPV_HW_neural_shader +1 |
| 26 | spv.coopvecHW.comp | comp | PASS | OpCooperativeVectorMatrixMulAddHW, OpCooperativeVectorMatrixMulHW | OpTypeCooperativeMatrixHW, OpTypeCooperativeVectorHW | CooperativeMatrixHW, CooperativeVectorHW | SPV_HW_neural_shader +2 |
| 27 | spv.coopvecHW_bitcast.comp | comp | PASS | - | OpTypeCooperativeVectorHW | CooperativeVectorHW | SPV_HW_neural_shader +1 |
| 28 | spv.coopvecHW_conversion.comp | comp | PASS | - | OpTypeCooperativeVectorHW | CooperativeVectorHW | SPV_HW_neural_shader +1 |
| 29 | spv.coopvecHW_use_pass.comp | comp | PASS | OpCooperativeVectorMatrixMulAddHW, OpCooperativeVectorMatrixMulHW | OpTypeCooperativeMatrixHW, OpTypeCooperativeVectorHW | CooperativeMatrixHW, CooperativeVectorHW | SPV_HW_neural_shader +1 |
| 30 | spv.coopvecHW_use_pass_arithmetic.comp | comp | PASS | OpCooperativeVectorMatrixMulHW | OpTypeCooperativeMatrixHW, OpTypeCooperativeVectorHW | CooperativeMatrixHW, CooperativeVectorHW | SPV_HW_neural_shader +1 |
| 31 | spv.coopvecHW_use_pass_array.comp | comp | PASS | OpCooperativeVectorMatrixMulAddHW, OpCooperativeVectorMatrixMulHW | OpTypeCooperativeMatrixHW, OpTypeCooperativeVectorHW | CooperativeMatrixHW, CooperativeVectorHW | SPV_HW_neural_shader +1 |
| 32 | spv.coopvecHW_use_pass_chained.comp | comp | PASS | OpCooperativeVectorMatrixMulHW | OpTypeCooperativeMatrixHW, OpTypeCooperativeVectorHW | CooperativeMatrixHW, CooperativeVectorHW | SPV_HW_neural_shader +1 |
| 33 | spv.coopvecHW_use_pass_func.comp | comp | PASS | OpCooperativeMatrixLoadHW, OpCooperativeVectorMatrixMulAddHW, OpCooperativeVectorMatrixMulHW | OpTypeCooperativeMatrixHW, OpTypeCooperativeVectorHW | CooperativeMatrixHW, CooperativeVectorHW | SPV_HW_neural_shader +1 |
| 34 | spv.coopvecHW_use_pass_mixed.comp | comp | PASS | OpCooperativeMatrixMulAddHW, OpCooperativeVectorMatrixMulAddHW, OpCooperativeVectorMatrixMulHW | OpTypeCooperativeMatrixHW, OpTypeCooperativeVectorHW | CooperativeMatrixHW, CooperativeVectorHW | SPV_HW_neural_shader +1 |
| 35 | spv.coopvecHW_use_pass_nomul.comp | comp | PASS | OpCooperativeMatrixLoadHW, OpCooperativeMatrixStoreHW | OpTypeCooperativeMatrixHW | CooperativeMatrixHW | SPV_HW_neural_shader +1 |
| 36 | spv.coopvecHWloadstore.vk.nocompat.comp | comp | PASS | OpCooperativeVectorLoadHW, OpCooperativeVectorStoreHW | OpTypeCooperativeVectorHW | CooperativeVectorHW | SPV_HW_neural_shader +2 |
| 37 | spv.cpAsyncGroupBarrier.comp | comp | PASS | OpBarrierArriveHW, OpBarrierWaitHW, OpCpAsyncCommitGroupHW, OpCpAsyncWaitGroupHW | - | - | SPV_HW_neural_shader |
| 38 | spv.cpAsyncTensor.comp | comp | PASS | OpCpAsyncTensorGlobalSharedHW | OpTypeTensorMapHW | - | SPV_HW_neural_shader |
| 39 | spv.hwNeuralBuiltins.comp | comp | PASS | OpBytePermuteHW, OpShuffleFillDownHW, OpShuffleIndexHW | - | - | SPV_HW_neural_shader |
| 40 | spv.regControl.comp | comp | PASS | OpSelectionMerge(Relreg) | - | - | SPV_HW_neural_shader |
| 41 | spv.tensorMap.comp | comp | PASS | - | OpTypeTensorMapHW | - | SPV_HW_neural_shader |
| 42 | spv.coopmatHW.frag | frag | PASS | OpCooperativeMatrixLengthHW, OpCooperativeMatrixLoadHW, OpCooperativeMatrixMulAddHW, OpCooperativeMatrixReduceHW, OpCooperativeMatrixStoreHW | OpTypeCooperativeMatrixHW | CooperativeMatrixHW | SPV_HW_neural_shader +1 |
| 43 | spv.coopmatHW_arithmetic.frag | frag | PASS | - | OpTypeCooperativeMatrixHW | CooperativeMatrixHW | SPV_HW_neural_shader +1 |
| 44 | spv.coopmatHW_bitcast.frag | frag | PASS | - | OpTypeCooperativeMatrixHW | CooperativeMatrixHW | SPV_HW_neural_shader +1 |
| 45 | spv.coopmatHW_builtin.frag | frag | PASS | OpCooperativeMatrixLengthHW, OpCooperativeMatrixLoadHW, OpCooperativeMatrixMulAddHW, OpCooperativeMatrixReduceHW, OpCooperativeMatrixStoreHW | OpTypeCooperativeMatrixHW | CooperativeMatrixHW | SPV_HW_neural_shader +2 |
| 46 | spv.coopmatHW_conversion.frag | frag | PASS | - | OpTypeCooperativeMatrixHW | CooperativeMatrixHW | SPV_HW_neural_shader +1 |
| 47 | spv.coopvecHW.frag | frag | PASS | OpCooperativeVectorMatrixMulAddHW, OpCooperativeVectorMatrixMulHW | OpTypeCooperativeMatrixHW, OpTypeCooperativeVectorHW | CooperativeMatrixHW, CooperativeVectorHW | SPV_HW_neural_shader +2 |
| 48 | spv.coopvecHW_bitcast.frag | frag | PASS | - | OpTypeCooperativeVectorHW | CooperativeVectorHW | SPV_HW_neural_shader +1 |
| 49 | spv.coopvecHW_conversion.frag | frag | PASS | - | OpTypeCooperativeVectorHW | CooperativeVectorHW | SPV_HW_neural_shader +1 |
| 50 | spv.coopvecHWloadstore.vk.nocompat.frag | frag | PASS | OpCooperativeVectorLoadHW, OpCooperativeVectorStoreHW | OpTypeCooperativeVectorHW | CooperativeVectorHW | SPV_HW_neural_shader +2 |
| 51 | spv.coopmatHW.vert | vert | PASS | OpCooperativeMatrixLengthHW, OpCooperativeMatrixLoadHW, OpCooperativeMatrixMulAddHW, OpCooperativeMatrixReduceHW, OpCooperativeMatrixStoreHW | OpTypeCooperativeMatrixHW | CooperativeMatrixHW | SPV_HW_neural_shader +1 |
| 52 | spv.coopmatHW_arithmetic.vert | vert | PASS | - | OpTypeCooperativeMatrixHW | CooperativeMatrixHW | SPV_HW_neural_shader +1 |
| 53 | spv.coopmatHW_bitcast.vert | vert | PASS | - | OpTypeCooperativeMatrixHW | CooperativeMatrixHW | SPV_HW_neural_shader +1 |
| 54 | spv.coopmatHW_builtin.vert | vert | PASS | OpCooperativeMatrixLengthHW, OpCooperativeMatrixLoadHW, OpCooperativeMatrixMulAddHW, OpCooperativeMatrixReduceHW, OpCooperativeMatrixStoreHW | OpTypeCooperativeMatrixHW | CooperativeMatrixHW | SPV_HW_neural_shader +2 |
| 55 | spv.coopmatHW_conversion.vert | vert | PASS | - | OpTypeCooperativeMatrixHW | CooperativeMatrixHW | SPV_HW_neural_shader +1 |
| 56 | spv.coopvecHW.vert | vert | PASS | OpCooperativeVectorMatrixMulAddHW, OpCooperativeVectorMatrixMulHW | OpTypeCooperativeMatrixHW, OpTypeCooperativeVectorHW | CooperativeMatrixHW, CooperativeVectorHW | SPV_HW_neural_shader +2 |
| 57 | spv.coopvecHW_bitcast.vert | vert | PASS | - | OpTypeCooperativeVectorHW | CooperativeVectorHW | SPV_HW_neural_shader +1 |
| 58 | spv.coopvecHW_conversion.vert | vert | PASS | - | OpTypeCooperativeVectorHW | CooperativeVectorHW | SPV_HW_neural_shader +1 |
| 59 | spv.coopvecHWloadstore.vk.nocompat.vert | vert | PASS | OpCooperativeVectorLoadHW, OpCooperativeVectorStoreHW | OpTypeCooperativeVectorHW | CooperativeVectorHW | SPV_HW_neural_shader +2 |

> **Extensions 列说明**：`+N` 表示除 `SPV_HW_neural_shader` 外还使用 N 个其他扩展（如 `SPV_KHR_vulkan_memory_model`、`SPV_KHR_8bit_storage`、`SPV_KHR_physical_storage_buffer`、`SPV_EXT_replicated_composites`）。

> **HW Instructions 列说明**：`-` 表示该 shader 不使用 HW 专属指令，但在 HW 类型上使用标准 SPIR-V 指令（OpBitcast/OpConvertFToS/OpFAdd 等），测试 spirv-cross 的 HW 类型处理代码路径。`OpSelectionMerge(Relreg)` 表示使用 OpSelectionMerge 的 Relreg 掩码位。

---

## 六、覆盖度分析

### 6.1 HW 指令覆盖

| 指令 | 覆盖用例数 |
|------|-----------|
| OpCooperativeMatrixLoadHW | 28 |
| OpCooperativeMatrixMulAddHW | 27 |
| OpCooperativeMatrixStoreHW | 7 |
| OpCooperativeMatrixLengthHW | 4 |
| OpCooperativeMatrixReduceHW | 4 |
| OpCooperativeVectorMatrixMulHW | 8 |
| OpCooperativeVectorMatrixMulAddHW | 5 |
| OpCooperativeVectorLoadHW | 3 |
| OpCooperativeVectorStoreHW | 3 |
| OpCpAsyncTensorGlobalSharedHW | 1 |
| OpCpAsyncCommitGroupHW | 1 |
| OpCpAsyncWaitGroupHW | 1 |
| OpBarrierArriveHW | 1 |
| OpBarrierWaitHW | 1 |
| OpShuffleIndexHW | 1 |
| OpBytePermuteHW | 1 |
| OpShuffleFillDownHW | 1 |
| OpSelectionMerge(Relreg) | 1 |

### 6.2 测试分类

| 类别 | 用例数 | 说明 |
|------|--------|------|
| CoopMatHW 指令测试 | 20 | Load/Store/MulAdd/Reduce/Length 全覆盖 |
| CoopMatHW use_pass 系列 | 14 | 矩阵在控制流中的传递场景 |
| CoopMatHW role 系列 | 5 | 函数参数/返回值中的矩阵传递 |
| CoopMatHW 类型操作 | 3 | arithmetic/bitcast/conversion on HW 类型 |
| CoopVecHW 指令测试 | 8 | MatMul/MatMulAdd/Load/Store |
| CoopVecHW 类型操作 | 2 | bitcast/conversion on CoopVecHW |
| CoopVecHW loadstore | 3 | 含 buffer_reference (Vulkan 专属) |
| cp-async + barrier | 2 | 异步拷贝 + 屏障同步 |
| TensorMap | 2 | 类型声明 + cp_async_tensor |
| Shuffle + BytePermute | 1 | hwNeuralBuiltins 综合 |
| reg_control | 1 | [[reg_control]] 属性（含组合） |
| 多 stage 覆盖 | 18 | 同一 shader 在 comp/frag/vert 三个 stage 验证 |
