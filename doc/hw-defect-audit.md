# HW 扩展代码缺陷审查报告

基于 `dev0811` 分支 riflebird 提交历史和当前代码审查。

---

## 一、已修复缺陷（来自 commit 历史）

| # | Commit | 缺陷出处 | 描述 | 严重程度 | 修改说明 | 是否改正 |
|---|--------|----------|------|----------|----------|----------|
| 1 | e5bd5b42 | `spirv_glsl.cpp` `type_to_glsl` | GLSL 扩展名写成了 SPIR-V 扩展名：`require_extension_internal("SPV_HW_neural_shader")` 应为 `GL_HW_neural_shader` | 高 | 改为 `GL_HW_neural_shader` | ✅ |
| 2 | a8c185ca | `spirv_glsl.cpp` `constant_expression` | `coopmatHW<float,16,16>(100.0f)` 作为立即数传给 `coopMatStore` 时抛 `"Invalid constant expression basetype"`，因为 `SPIRType::CoopMatHW` 未在 `constant_expression` 的 basetype switch 中处理 | 高 | 新增 CoopMatHW 分支，按组件类型渲染标量值 | ✅ |
| 3 | bf6d00bc | `spirv_glsl.cpp` `OpCooperativeMatrixReduceHW` | `coopMatReduceHW` 返回 `coopmatHW<T,M,N>`，但实现用了 void out-param 模式（`statement` + `emit_uninitialized_temporary_expression`），未生成返回值赋值 | 高 | 改为 `emit_op` 生成 `coopMatReduceHW(...)` 返回表达式 | ✅ |
| 4 | 26e2d8f9 | `spirv_glsl.cpp` `OpCooperativeMatrixMulAddHW` | `coopmatMulHW`（无 C 矩阵）只检测 `OpUndef`，漏检 `OpConstantNull`，导致传入 `OpConstantNull` 时错误生成 `coopMatMulAddHW` | 中 | 增加 `maybe_get<SPIRConstant>` + `constant_is_null()` 检测 | ✅ |
| 5 | b4fd083c | `spirv_glsl.cpp` `OpBitcast` | CoopMatHW 间 OpBitcast（如 float16→int16）错误使用 `coopmatHW` 构造函数，应使用 `float16BitsToInt16` 等 bitcast 函数 | 高 | 提取双方组件类型，用 `bitcast_glsl_op()` 查找正确函数 | ✅ |
| 6 | 52798fb2 | `spirv_glsl.cpp` `access_chain_internal` | CoopVecHW 类型未在 access chain 中处理，`vec[i]` 索引无法生成，`OpCompositeExtract/Insert` 崩溃 | 高 | 在 `access_chain_internal` 和 `flattened_access_chain_offset` 中新增 CoopVecHW 分支 | ✅ |
| 7 | fa6d5b2d | `spirv_glsl.cpp` `OpCooperativeMatrixMulAddHW` | 函数名大小写错误：`coopmatMulAddHW`/`coopmatMulHW` 应为 `coopMatMulAddHW`/`coopMatMulHW` | 中 | 统一改为驼峰 `coopMat` 前缀 | ✅ |
| 8 | fa6d5b2d | `spirv_glsl.cpp` `spirv_cross.cpp` `OpCooperativeMatrixStoreHW` | 操作数顺序错误：代码按 `(Object, Pointer)` 读取，实际 SPIR-V 定义为 `(Pointer, Object)`，导致变量依赖追踪指向错误 ID | 高 | 全部 3 处（emit、interface tracking、scope analysis）统一为 `args[0]=Pointer, args[1]=Object` | ✅ |
| 9 | fa6d5b2d | `spirv_glsl.cpp` `OpBitcast` | 同宽整数 CoopMatHW/CoopVecHW 间 bitcast（如 int16→uint16）错误使用标量 bitcast 函数而非类型构造函数 | 中 | 增加 `integral_cast && same_size_cast` 判断，走构造函数路径 | ✅ |
| 10 | fa6d5b2d | `spirv_glsl.cpp` `type_to_glsl` | 矩阵维度用 `get_constant().scalar()` 读取，不支持 spec constant 维度，spec constant 场景崩溃 | 高 | 改为 `evaluate_constant_u32()` | ✅ |
| 11 | fa6d5b2d | `spirv_glsl.cpp` `reg_control` | `reg_control` 未声明所需扩展，且与 `flatten`/`branch` hint 共存时生成两个独立 attribute 而非合并形式 | 中 | 声明 `GL_HW_neural_shader`，与 hint 合并为 `[[flatten, reg_control]]` | ✅ |
| 12 | f30b819d | `spirv_glsl.cpp` `OpCooperativeMatrixLoadHW/StoreHW` | layout 操作数用 `get<SPIRConstant>` 强转，当 layout 为三目运算符（`OpSelect`/`OpSpecConstantOp`）时抛 `bad_cast` 异常 | 高 | 新增 `to_coopmat_layout_expression()` 处理常量/spec-constant-ternary/运行时表达式三种情况 | ✅ |
| 13 | f30b819d | `spirv_glsl.cpp` `reject_hw_neural_extensions` | 扩展检测用 `rfind("SPV_HW_", 0)` 前缀匹配，过于宽泛，可能误拒未来其他 `SPV_HW_*` 扩展 | 低 | 改为精确匹配 `ext == "SPV_HW_neural_shader"` | ✅ |

---

## 二、当前代码中仍存在的缺陷

| # | 缺陷出处 | 描述 | 严重程度 | 修改说明 | 是否改正 |
|---|----------|------|----------|----------|----------|
| 14 | `spirv_glsl.cpp:15613` `OpCooperativeMatrixLengthHW` | 缺少 length 检查。其他 HW 指令都有 `if (length < N)` 保护，此处直接访问 `ops[0]`/`ops[1]`/`ops[2]`，若 SPIR-V 指令长度不足 3 会越界 | 中 | 添加 `if (length < 3) SPIRV_CROSS_THROW(...)` | ❌ 未修 |
| 15 | `spirv_glsl.cpp:15760` `OpCooperativeMatrixReduceHW` | `reduce_mask_id` 和 `combine_op_id` 用 `get<SPIRConstant>` 强转，与 layout bug（#12）同一模式。若 mask/op 为 `OpSelect`/`OpSpecConstantOp` 会抛 `bad_cast` | 高 | 参考 `to_coopmat_layout_expression` 模式改为 `maybe_get` + 验证 | ❌ 未修 |
| 16 | `spirv_glsl.cpp:15765` `OpCooperativeMatrixReduceHW` | mask 只判断 `== 0` 否则一律当 Column，op 只判断 `0/1` 否则一律当 Max。未校验 mask 范围（应为 0-1）和 op 范围（应为 0-2），越界值静默走错枚举 | 低 | 增加 range 校验 + `SPIRV_CROSS_THROW` | ❌ 未修 |
| 17 | `spirv_glsl.cpp:15817` `OpCpAsyncTensorGlobalSharedHW` | 未调用 `register_write(dst_ptr)`，与 `OpCooperativeMatrixStoreHW`/`OpCooperativeVectorStoreHW` 不一致。store 类指令应注册写入以正确追踪变量作用域 | 低 | 添加 `register_write(dst_ptr)` | ❌ 未修 |
