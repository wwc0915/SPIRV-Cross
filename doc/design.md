# 添加扩展SPV_HW_neural_matrix
## coopmatHW
### 1. 枚举
```
OpExtension:
SPV_HW_neural_matrix

Capability:
6600-CooperativeMatrixHW

Cooperative Matrix Layout:
0-RowMajorHW
1-ColumnMajorHW

Cooperative Matrix Reduce Mask:
0x0-Row
0x1-Column

Cooperative Matrix Reduce CombineOp:
0x0-ReduceAdd
0x1-ReduceMin
0x2-ReduceMax
```
### 2. spv指令
#### 2.1 总览
```
6601-OpTypeCooperativeMatrixHW
6602-OpCooperativeMatrixLengthHW
6603-OpCooperativeMatrixLoadHW
6604-OpCooperativeMatrixStoreHW
6605-OpCooperativeMatrixMulAddHW
6606-OpCooperativeMatrixReduceHW
```
`Word Count + Opcode + Results + Operands`
1. word0的高16位是word count，表示总字数；word0的低16为opcode
2. 当存在时，Results是由指令创建的Result\<id\>或者Result Type，每个Result\<id\>始终为32位
3. 当存在时，Operands是由指令所使用的任何字面量、其他指令的Result\<id\>等。每个操作数始终为32位

#### 2.2.1 杂项指令
`OpCooperativeMatrixLengthHW`
返回mat可访问的组件数量
| 4 | opcode: 6602 | \<id\> Result Type | Result \<id\> | \<id\> Type
| -- | -- | -- | -- | -- |
+ Type 必须是 cooperative matrix 类型
+ Result Type 必须是 OpTypeInt

GLSL实现：
```
int(coopmatHW<T, M, K>(0).length())
```
SPIRV-Cross通过SPIRExpression生成内联表达式，无需额外变量声明。
#### 2.2.4 内存指令
1. `OpCooperativeMatrixLoadHW`

| 5+vars | opcode: 6603 | \<id\> Result Type | Result \<id\>| \<id\> Pointer | \<id\> srcMatrixShape | \<id\> srcMatrixOffset | \<id\> layout |
| -- | -- | -- | -- | -- | -- | -- | -- |

通过指针load一个cooperative matrix
+ Result Type是load对象的类型，它必须是coop mat类型
+ Pointer是一个指针，其类型必须是OpTypePoniter，其操作数为标量或者向量类型。如果声明了着色器功能，则该指针必须指向一个数组，且对指针的任何`ArrayStride`修饰都将被忽略
+ srcMatrixShape是读取ddr/share memory上矩阵的行和列
+ srcMatrixOffset表示从原矩阵第srcMatrixOffset[0]、第srcMatrixOffset[1]列开始读的一个矩阵
+ layout是Cooperative Matrix Layout，即读入矩阵的我排布方式

```
void coopMatLoadHW(coopmatHW<T, M, K> matA, T buf[], vec2 srcMatrixShape, vec2 srcMatrixOffset, MatrixLayout layout)
```
2. `OpCooperativeMatrixStoreHW`

| 4+vars | opcode: 6604 | \<id\> Pointer | \<id\> Object | \<id\> srcMatrixShape | \<id\> srcMatrixOffset | \<id\> layout |
| -- | -- | -- | -- | -- | -- | -- |

通过指针store一个coopmat
+ Pointer是一个指针，其类型必须是OpTypePointer，其类型操作数可以是标量或者向量类型。如果声明了着色器功能，则指针必须指向一个数组，且对指针的任何ArrayStride修饰符都将被忽略
+ Object是要储存的对象，其类型必须是OpCooperativeMatrixHW
+ srcMatrixShape是要写出到ddr/shareMemory的矩阵的行和列
+ srcMatrixOffset表示从原矩阵第srcMatrixOffset[0]、第srcMatrixOffset[1]列开始读的一个矩阵
+ layout是读入矩阵的排布方式，其值取自Cooperative Matrix Layout属性

```
void coopMatStoreHW(coopmatHW<T, M, K> matA, T buf[], vec2 srcMatrixShape, vec2 srcMatrixOffset, MatrixLayour layout)
```

详细设计文档：
- [OpCooperativeMatrixLoadHW 设计文档](op-cooperative-matrix-load-hw-design.md)
- [OpCooperativeMatrixStoreHW 设计文档](op-cooperative-matrix-store-hw-design.md)

#### 2.2.5 算数指令
`OpCooperativeMatrixMulAddHW`
矩阵A与矩阵B相乘，然后逐元素加上矩阵C。操作的顺序取决于实现方式。浮点运算的内部精度由客户端API定义。如果存在Matrix{A,B,C}SignedComponentsHW操作数，则相应矩阵操作数的元素将sign-extended到结果类型的精度，否则将零扩展。

| 6+variable | opcode:6605 | \<id\> Result Type | Result \<id\> | \<id\> A | \<id\> B | \<id\> C |
| -- | -- | -- | -- | -- | -- | -- |

+ Result Type必须是一个具有M行和N列的协作矩阵类型
+ A是M行、K列的协作矩阵，数据类型为T
+ B是K行、N列的协作矩阵，数据类型为T
+ C是M行、N列的协作矩阵，数据类型为T1

```
void coopmatMulAddHW(out coopmatHW<T1, M, N> matO, coopmatHW<T, M, K> matA, coopmatHW<T, K, N> matB, coopmatHW<T1, M, N> matC)
```

详细设计文档：
- [OpCooperativeMatrixMulAddHW 设计文档](op-cooperative-matrix-muladd-hw-design.md)

另外，不新增`OpCooperativeMatrixMulHw`,只是把`OpCooperativeMatrixMulAddHW`的C设为None
| 6+variable | opcode:6504 | \<id\> Result Type | Result \<id\> | \<id\> A | \<id\> B | \<id\> None |
| -- | -- | -- | -- | -- | -- | -- |
函数签名：
```
void coopmatMulHW(out coopmatHW<T1, M, N> matO, coopmatHW<T, M, K> matA, coopmatHW<T, K, N> matB)
```

详细设计文档：
- [coopmatMulHW 设计文档](op-cooperative-matrix-mul-hw-design.md)

#### 2.2.6 规约指令
`OpCooperativeMatrixReduceHW`
对一个数据类型T，M行N列的矩阵进行规约计算，输出的数据类型是T，M行N列的矩阵。输出结果是广播到矩阵的每个参数上的。

| 5 variable | opcode:6606 | \<id\> Result Type | Result \<id\> | \<id\> reduceMask | \<id\> combineOp |
| -- | -- | -- | -- | -- | -- |

允许协作矩阵类型用于以下算术指令:
+ OpSNegate and OpFNegate
+ OpIAdd, OpFAdd, OpISub, OpFSub, OpFMul, OpIMul, OpFDiv, OpSDiv, and OpUDiv
+ 如果它们的Component类型合适：
    + OpF指令可以用于组件类型为浮点类型的协作矩阵
    + OpI、OpS和OpU指令可以用于组件类型为整数类型的协作矩阵
+ 单目算术指令对协作矩阵的各个元素进行操作，双目算术指令对类型必须匹配的一对协作矩阵的各个元素进行操作
+ 允许协作矩阵类型用于OpMatrixTimesScalar

函数签名
```
coopmatHW<T, M, N> coopMatReduceHW(coopmat<T, M, N> mat, int reduceMask, int combineOp)
```

详细设计文档：
- [OpCooperativeMatrixReduceHW 设计文档](op-cooperative-matrix-reduce-hw-design.md)
#### 2.2.7 转换指令
允许协作矩阵类型用于以下转换指令（如果分量类型合适）:OpConvertFToU、OpConvertFToS、OpConvertSToF、OpConvertUToF、OpUConvert、OpSConvert、OpFConvert。结果类型和值类型必须具有相同的分量数量。

允许协作矩阵类型用于OpBitcast。结果类型和值类型必须具有相同的分量数量以及每个分量的相同位数。

---

## coopvecHW
### 3.1 Enumerants
| 分类 | 名称 | 值 | 说明 |
| -- | -- | -- | -- |
| OpExtension | SPV_HW_cooperative_vector | | |
| Capability | CooperativeVectorHW | 6607 | 启用协作向量类型以及操作这些类型的指令 |
| Cooperative Vector Matrix Layout | RowMajorHW | 0 | 矩阵行由内存中连续的元素构成 |
| | ColumnMajorHW | 1 | 矩阵的列由内存中连续的元素构成 |
| Component Type | SignedInt8HW | 0 | |
| | SignedInt16HW | 1 | |
| | SignedInt32HW | 2 | |
| | Float16HW | 3 | |
| | Float32HW | 4 | |

### 3.2 指令
| 分类 | 指令 | Opcode | 说明 |
| -- | -- | -- | -- |
| Type-Declaration Instructions | OpTypeCooperativeVectorHW | 6608 | 声明协作向量类型 |
| Memory Instructions | OpCooperativeVectorLoadHW | 6609 | 从内存加载协作向量 |
| | OpCooperativeVectorStoreHW | 6610 | 将协作向量存储到内存 |
| Cooperative Vector Instructions | OpCooperativeVectorMatrixMulAddHW | 6611 | 协作向量矩阵乘加 |
| | OpCooperativeVectorMatrixMulHW | 6612 | 协作向量矩阵乘法 |

#### 3.2.1 类型定义指令
`OpTypeCooperativeVectorHW`
声明一个新的协作向量类型，其包含请求的标量类型的Component Count个组件
+ Component Type组件类型必须是标量数值类型
+ Component Count必须是一个具有标量32位整数类型的常量指令

SPV格式：
| Word Count | Opcode | Result \<id\> | \<id\> Component Type | \<id\> Component Count |
| -- | -- | -- | -- | -- |
| 4 | 6608 | Result \<id\> | Component Type \<id\> | Component Count \<id\> |

GLSL类型声明：
```glsl
coopvecHW<T, M> vecA;
```

详细设计文档：
- [OpTypeCooperativeVectorHW 设计文档](op-type-cooperative-vector-hw-design.md)

#### 3.2.2 内存指令

##### OpCooperativeVectorLoadHW
通过指针load一个cooperative vector。
+ Result Type是加载对象的类型。它必须是协作向量类型。
+ Pointer是一个指针。其类型必须是OpTypePointer，其Type操作数是一个具有标量或者向量元素类型的数组类型。指针的存储类别必须是CrossWorkGroup、Workgroup、StorageBuffer或PhysicalStorageBuffer。对指针的任何ArrayStride装饰符都将被忽略。

SPV格式：
| Word Count | Opcode | \<id\> Result Type | Result \<id\> | \<id\> Pointer |
| -- | -- | -- | -- | -- |
| 4+ | 6609 | Result Type \<id\> | Result \<id\> | Pointer \<id\> |

GLSL函数签名：
```glsl
void coopVecLoadHW(out coopvecHW<T, M> vec, T buf[]);
```

详细设计文档：
- [OpCooperativeVectorLoadHW 设计文档](op-cooperative-vector-load-hw-design.md)

##### OpCooperativeVectorStoreHW
通过指针store一个cooperative vector。

SPV格式：
| Word Count | Opcode | \<id\> Pointer | \<id\> Object |
| -- | -- | -- | -- |
| 3+ | 6610 | Pointer \<id\> | Object \<id\> |

GLSL函数签名：
```glsl
void coopVecStoreHW(out coopvecHW<T, M> vec, T buf[]);
```

详细设计文档：
- [OpCooperativeVectorStoreHW 设计文档](op-cooperative-vector-store-hw-design.md)

#### 3.2.3 算数指令

##### OpCooperativeVectorMatrixMulAddHW
协作向量与矩阵相乘后逐元素加上偏移向量。

SPV格式：
| Word Count | Opcode | \<id\> Result Type | Result \<id\> | \<id\> Vector | \<id\> Matrix | \<id\> Bias |
| -- | -- | -- | -- | -- | -- | -- |
| 6+ | 6611 | Result Type \<id\> | Result \<id\> | Vector \<id\> | Matrix \<id\> | Bias \<id\> |

GLSL函数签名：
```glsl
void coopVecMatMulAddHW(out coopvecHW m, coopvecHW v, coopmatHW mi, coopvecHW b);
```

##### OpCooperativeVectorMatrixMulHW
协作向量与矩阵相乘（无偏移）。

SPV格式：
| Word Count | Opcode | \<id\> Result Type | Result \<id\> | \<id\> Vector | \<id\> Matrix |
| -- | -- | -- | -- | -- | -- |
| 5+ | 6612 | Result Type \<id\> | Result \<id\> | Vector \<id\> | Matrix \<id\> |

GLSL函数签名：
```glsl
void coopVecMatMulHW(out coopvecHW m, coopvecHW v, coopmatHW mi);
```
