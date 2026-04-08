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
#### 2.2.4 内存指令
1. `OpCooperativeMatrixLoadHW`

| 5+vars | opcode: 6502 | \<id\> Result Type | Result \<id\>| \<id\> Pointer | \<id\> srcMatrixShape | \<id\> srcMatrixOffset | \<id\> layout |
| -- | -- | -- | -- | -- | -- | -- | -- |

通过指针load一个cooperative matrix
+ Result Type是load对象的类型，它必须是coop mat类型
+ Pointer是一个指针，其类型必须是OpTypePoniter，其操作数为标量或者向量类型。如果声明了着色器功能，则该指针必须指向一个数组，且对指针的任何`ArrayStride`修饰都将被忽略
+ srcMatrixShape是ddr/share memory上矩阵的行和列
+ srcMatrixOffset是从原矩阵第srcMatrixOffset[0]、第srcMatrixOffset[1]列开始读的一个矩阵
+ layout是Cooperative Matrix Layout，即读入矩阵的我排布方式

```
void coopMatLoadHW(coopmatHW<T, M, K> matA, T buf[], vec2 srcMatrixShape, vec2 srcMatrixOffset, MatrixLayout layout)
```
