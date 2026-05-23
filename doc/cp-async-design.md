# CpAsync 与 TensorMap 设计文档

## 一、概述

新增 `TensorMap` 变量类型和 `cp-async` 系列同步指令，用于支持异步内存拷贝和屏障操作。

### 1.1 新增变量类型

| GLSL 类型 | SPIR-V 指令 | Opcode |
|-----------|------------|--------|
| tensorMap1D | OpTypeTensorMap (dimensions=1) | 6466 |
| tensorMap2D | OpTypeTensorMap (dimensions=2) | 6466 |
| tensorMap3D | OpTypeTensorMap (dimensions=3) | 6466 |
| tensorMap4D | OpTypeTensorMap (dimensions=4) | 6466 |

### 1.2 新增 Intrinsic 指令

| GLSL 函数签名 | SPIR-V 指令 | Opcode |
|--------------|------------|--------|
| void cp_async_tensor_global_shared(shared int[] dstMem, tensorMapXD tensorSharp, ivecX coord) | OpCpAsyncTensorGlobalShared | 6470 |
| void cp_async_commit_group() | OpCpAsyncCommitGroup | 6474 |
| void cp_async_wait_group(int N) | OpCpAsyncWaitGroup | 6475 |
| void barrier_arrive(int id, int n) | OpBarrierArrive | 6476 |
| void barrier_wait(int id, int n) | OpBarrierWait | 6477 |

不需要新增 SPIR-V Capability。

---

## 二、指令格式

### 2.1 OpTypeTensorMap（类型声明）

```
| 3 | 6466 | Result <id> | dimensions (literal: 1/2/3/4) |
```

- hasResult = true, hasResultType = false
- dimensions: 1 ~ 4，表示张量映射的维度

### 2.2 OpCpAsyncTensorGlobalShared（异步拷贝）

```
| 4+ | 6470 | <id> dstMem | <id> tensorMap | <id> coord |
```

- hasResult = false, hasResultType = false
- dstMem: 目标共享内存指针
- tensorMap: TensorMap 变量（tensorMap1D/2D/3D/4D）
- coord: 坐标，类型与维度匹配（int / ivec2 / ivec3 / ivec4）

### 2.3 OpCpAsyncCommitGroup（提交异步组）

```
| 1 | 6474 |
```

- hasResult = false, hasResultType = false

### 2.4 OpCpAsyncWaitGroup（等待异步组）

```
| 2 | 6475 | <id> N |
```

- hasResult = false, hasResultType = false
- N: 等待的组数

### 2.5 OpBarrierArrive / OpBarrierWait（屏障同步）

```
| 3 | 6476/6477 | <id> barrier_id | <id> barrier_n |
```

- hasResult = false, hasResultType = false
- barrier_id: 屏障标识
- barrier_n: 屏障参与数量

---

## 三、实现设计

### 3.1 需要修改的文件

| 文件 | 修改内容 |
|------|----------|
| `spirv_common.hpp` | 添加 `SPIRType::TensorMap` basetype 和 `ext.tensorMap.dimensions` 字段 |
| `spirv.h` / `spirv.hpp` | 添加 opcode 定义（6466-6477）、HasResultAndType、名称字符串 |
| `spirv_parser.cpp` | 添加 `OpTypeTensorMap` 解析，设置 basetype=TensorMap，存储 dimensions |
| `spirv_glsl.cpp` | 添加 `type_to_glsl` 的 TensorMap case 和 5 条指令的 GLSL 发射 |

### 3.2 类型发射

```cpp
case SPIRType::TensorMap:
    return join("tensorMap", type.ext.tensorMap.dimensions, "D");
```

根据 dimensions 值（1/2/3/4）生成 `tensorMap1D` / `tensorMap2D` / `tensorMap3D` / `tensorMap4D`。

### 3.3 指令发射

所有 cp-async 指令均为 void 返回，直接 `statement()` 输出函数调用：

- `OpCpAsyncTensorGlobalShared` → `cp_async_tensor_global_shared(dstMem, tensorMap, coord);`
- `OpCpAsyncCommitGroup` → `cp_async_commit_group();`
- `OpCpAsyncWaitGroup` → `cp_async_wait_group(N);`
- `OpBarrierArrive` → `barrier_arrive(id, n);`
- `OpBarrierWait` → `barrier_wait(id, n);`

---

## 四、测试用例

### 4.1 测试文件

| 文件名 | 生成函数 | 覆盖范围 |
|--------|----------|----------|
| `test_hw_cp_async.spv` | `gen_cp_async_test` | TensorMap1D/2D 类型、cp_async_tensor_global_shared、cp_async_commit_group、cp_async_wait_group、barrier_arrive、barrier_wait |

### 4.2 OpCpAsyncTensorGlobalShared（1D）

**期望 GLSL 输出**：
```glsl
cp_async_tensor_global_shared(data._m0[0u], tensorMap1D _20, 0u);
```

### 4.3 OpCpAsyncTensorGlobalShared（2D）

**期望 GLSL 输出**：
```glsl
cp_async_tensor_global_shared(data._m0[0u], tensorMap2D _21, ivec2(0));
```

### 4.4 OpCpAsyncCommitGroup

**期望 GLSL 输出**：
```glsl
cp_async_commit_group();
```

### 4.5 OpCpAsyncWaitGroup

**期望 GLSL 输出**：
```glsl
cp_async_wait_group(0);
```

### 4.6 OpBarrierArrive

**期望 GLSL 输出**：
```glsl
barrier_arrive(0, 1);
```

### 4.7 OpBarrierWait

**期望 GLSL 输出**：
```glsl
barrier_wait(0, 1);
```

---

## 五、完整 GLSL 输出示例

```glsl
#version 450
layout(local_size_x = 16, local_size_y = 1, local_size_z = 1) in;

void main()
{
    cp_async_tensor_global_shared(data._m0[0u], tensorMap1D _20, 0u);
    cp_async_tensor_global_shared(data._m0[0u], tensorMap2D _21, ivec2(0));
    cp_async_commit_group();
    cp_async_wait_group(0);
    barrier_arrive(0, 1);
    barrier_wait(0, 1);
}
```
