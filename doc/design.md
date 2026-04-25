# 添加扩展SPV_HW_neural_shader
## coopmatHW
### 1. 枚举
```
Capability:
CooperativeMatrixHW

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
6500-OpCooperativeMatrixLengthHW
6501-OpTypeCooperativeMatrixHW
6502-OpCooperativeMatrixLoadHW
6503-OpCooperativeMatrixStoreHW
6504-OpCooperativeMtrixMulAddHW
6505-OpCooperativeReduceHW
```
`Word Count + Opcode + Results + Operands`
1. word0的高16位是word count，表示总字数；word0的低16为opcode
2. 当存在时，Results是由指令创建的Result\<id\>或者Result Type，每个Result\<id\>始终为32位
3. 当存在时，Operands是由指令所使用的任何字面量、其他指令的Result\<id\>等。每个操作数始终为32位

#### 2.2.1 杂项指令
`OpCooperativeMatrixLengthHW`
返回mat可访问的组件数量
| 4 | opcode: 6500 | \<id\> Result Type | Result \<id\> | \<id\> Type
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

| 5+vars | opcode: 6502 | \<id\> Result Type | Result \<id\>| \<id\> Pointer | \<id\> srcMatrixShape | \<id\> srcMatrixOffset | \<id\> layout |
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

| 4+vars | opcode: 6503 | \<id\> Pointer | \<id\> Object | \<id\> srcMatrixShape | \<id\> srcMatrixOffset | \<id\> layout |
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

| 6+variable | opcode:6504 | \<id\> Result Type | Result \<id\> | \<id\> A | \<id\> B | \<id\> C |
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

| 5 variable | opcode:6505 | \<id\> Result Type | Result \<id\> | \<id\> reduceMask | \<id\> combineOp |
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