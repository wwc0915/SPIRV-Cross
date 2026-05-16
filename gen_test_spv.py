#!/usr/bin/env python3
"""
Generate SPIR-V binaries for OpCooperativeMatrixLoadHW and OpCooperativeMatrixLengthHW testing.
"""
import struct, sys

def word(val):
    return struct.pack('<I', val)

def inst(opcode, *operands):
    words = list(operands)
    wc = len(words) + 1
    return word((wc << 16) | opcode) + b''.join(word(w) for w in words)

def str_words(s):
    b = s.encode('ascii') + b'\x00'
    b += b'\x00' * ((4 - len(b) % 4) % 4)
    return [struct.unpack('<I', b[i:i+4])[0] for i in range(0, len(b), 4)]

# Opcodes
OpCapability = 17; OpExtInstImport = 11; OpMemoryModel = 14
OpEntryPoint = 15; OpExecutionMode = 16; OpName = 5
OpDecorate = 71; OpMemberDecorate = 72; OpTypeVoid = 19; OpTypeFloat = 22
OpTypeInt = 21; OpTypeVector = 23; OpTypeFunction = 33; OpTypePointer = 32
OpTypeStruct = 30; OpTypeRuntimeArray = 29; OpTypeCooperativeMatrixHW = 6601
OpVariable = 59; OpFunction = 54; OpFunctionEnd = 56; OpLabel = 248
OpReturn = 253; OpConstant = 43; OpConstantComposite = 44; OpConstantNull = 46; OpAccessChain = 65
OpCooperativeMatrixLoadHW = 6603; OpCooperativeMatrixLengthHW = 6602
OpCooperativeMatrixStoreHW = 6604; OpCooperativeMatrixMulAddHW = 6605
OpCooperativeMatrixReduceHW = 6606
OpTypeCooperativeVectorHW = 6608; OpCooperativeVectorLoadHW = 6609
OpCooperativeVectorStoreHW = 6610; OpCooperativeVectorMatrixMulAddHW = 6611
OpCooperativeVectorMatrixMulHW = 6612
OpConvertFToS = 110; OpConvertSToF = 111
OpConvertFToU = 109; OpConvertUToF = 112
OpSConvert = 114; OpUConvert = 113; OpFConvert = 115; OpBitcast = 124
OpStore = 62; OpLoad = 61; OpUndef = 1

StorageClassStorageBuffer = 12
DecorationBlock = 2; DecorationBinding = 33; DecorationDescriptorSet = 34
DecorationArrayStride = 35; DecorationOffset = 35

def gen_length_test(outfile):
    """Generate test for OpCooperativeMatrixLengthHW with output storage."""
    # IDs
    void_t = 1; func_t = 2; main_f = 3; uint_t = 4; v2uint_t = 5; float_t = 6
    float_ptr_sb = 7; rtarray_t = 8; block_t = 9; block_ptr_t = 10
    data_var = 11; label = 12; glsl_id = 13
    c16 = 14; c16b = 15; c0 = 16; c1 = 17
    dim16 = 18; dim0 = 19
    coopmatA = 20; coopmatB = 21
    ptr_elem = 22; matA = 23; matB = 24
    lenA = 25; lenB = 26

    # Output buffer for length results (int type)
    int_t = 27; int_ptr_sb = 28; rtarray_int = 29; out_block_t = 30; out_block_ptr_t = 31
    out_var = 32; ptr_out0 = 33; ptr_out1 = 34

    BOUND = 35

    out = b''
    # Header
    out += word(0x07230203) + word(0x00010600) + word(0) + word(BOUND) + word(0)
    # Capabilities
    out += inst(OpCapability, 1) + inst(OpCapability, 6600)
    # ExtInstImport
    sw = str_words("GLSL.std.450")
    out += word(((1 + len(sw) + 1) << 16) | OpExtInstImport) + word(glsl_id) + b''.join(word(w) for w in sw)
    # MemoryModel
    out += inst(OpMemoryModel, 0, 1)
    # EntryPoint
    en = str_words("main")
    out += word(((2 + len(en) + 1) << 16) | OpEntryPoint) + word(5) + word(main_f) + b''.join(word(w) for w in en)
    # ExecutionMode
    out += inst(OpExecutionMode, main_f, 17, 16, 1, 1)
    # Debug names
    for target, name in [(main_f, "main"), (data_var, "data"), (float_t, "float"),
                          (uint_t, "uint"), (int_t, "int"), (lenA, "lenA"), (lenB, "lenB"),
                          (out_var, "output")]:
        nw = str_words(name)
        out += word(((1 + len(nw) + 1) << 16) | OpName) + word(target) + b''.join(word(w) for w in nw)
    # Annotations - input buffer
    out += inst(OpDecorate, block_t, DecorationBlock)
    out += inst(OpMemberDecorate, block_t, 0, DecorationOffset, 0)
    out += inst(OpDecorate, rtarray_t, DecorationArrayStride, 4)
    out += inst(OpDecorate, data_var, DecorationBinding, 0)
    out += inst(OpDecorate, data_var, DecorationDescriptorSet, 0)
    # Annotations - output buffer
    out += inst(OpDecorate, out_block_t, DecorationBlock)
    out += inst(OpMemberDecorate, out_block_t, 0, DecorationOffset, 0)
    out += inst(OpDecorate, rtarray_int, DecorationArrayStride, 4)
    out += inst(OpDecorate, out_var, DecorationBinding, 1)
    out += inst(OpDecorate, out_var, DecorationDescriptorSet, 0)
    # Types
    out += inst(OpTypeVoid, void_t)
    out += inst(OpTypeFloat, float_t, 32)
    out += inst(OpTypeInt, uint_t, 32, 0)
    out += inst(OpTypeInt, int_t, 32, 1)  # signed int for LengthHW result
    out += inst(OpTypeVector, v2uint_t, uint_t, 2)
    out += inst(OpTypeFunction, func_t, void_t)
    out += inst(OpTypePointer, float_ptr_sb, StorageClassStorageBuffer, float_t)
    out += inst(OpTypePointer, int_ptr_sb, StorageClassStorageBuffer, int_t)
    out += inst(OpTypeRuntimeArray, rtarray_t, float_t)
    out += inst(OpTypeRuntimeArray, rtarray_int, int_t)
    out += inst(OpTypeStruct, block_t, rtarray_t)
    out += inst(OpTypeStruct, out_block_t, rtarray_int)
    out += inst(OpTypePointer, block_ptr_t, StorageClassStorageBuffer, block_t)
    out += inst(OpTypePointer, out_block_ptr_t, StorageClassStorageBuffer, out_block_t)
    # Constants
    out += inst(OpConstant, uint_t, c16, 16)
    out += inst(OpConstant, uint_t, c16b, 16)
    out += inst(OpConstant, uint_t, c0, 0)
    out += inst(OpConstant, uint_t, c1, 1)
    out += inst(OpConstantComposite, v2uint_t, dim16, c16, c16b)
    out += inst(OpConstantComposite, v2uint_t, dim0, c0, c0)
    # CoopMat types (UseA=0, UseB=1)
    out += inst(OpTypeCooperativeMatrixHW, coopmatA, float_t, c16, c16b, c0)
    out += inst(OpTypeCooperativeMatrixHW, coopmatB, float_t, c16, c16b, c1)
    # Variables
    out += inst(OpVariable, block_ptr_t, data_var, StorageClassStorageBuffer)
    out += inst(OpVariable, out_block_ptr_t, out_var, StorageClassStorageBuffer)
    # Function body
    out += inst(OpFunction, void_t, main_f, 0, func_t)
    out += inst(OpLabel, label)
    # AccessChain for input
    out += inst(OpAccessChain, float_ptr_sb, ptr_elem, data_var, c0, c0)
    # AccessChain for output[0] and output[1]
    out += inst(OpAccessChain, int_ptr_sb, ptr_out0, out_var, c0, c0)
    out += inst(OpAccessChain, int_ptr_sb, ptr_out1, out_var, c0, c1)
    # Load matrices
    out += inst(OpCooperativeMatrixLoadHW, coopmatA, matA, ptr_elem, dim16, dim0, c0)
    out += inst(OpCooperativeMatrixLoadHW, coopmatB, matB, ptr_elem, dim16, dim0, c1)
    # OpCooperativeMatrixLengthHW (result type is int)
    out += inst(OpCooperativeMatrixLengthHW, int_t, lenA, coopmatA)
    out += inst(OpCooperativeMatrixLengthHW, int_t, lenB, coopmatB)
    # Store length results to output buffer
    out += inst(OpStore, ptr_out0, lenA)
    out += inst(OpStore, ptr_out1, lenB)
    # Store matrices back to memory using OpCooperativeMatrixStoreHW
    out += inst(OpCooperativeMatrixStoreHW, ptr_elem, matA, dim16, dim0, c0)
    out += inst(OpCooperativeMatrixStoreHW, ptr_elem, matB, dim16, dim0, c1)
    out += inst(OpReturn)
    out += inst(OpFunctionEnd)
    # Update bound
    data = bytearray(out)
    struct.pack_into('<I', data, 12, BOUND)
    with open(outfile, 'wb') as f:
        f.write(bytes(data))
    print(f"Generated: {len(data)} bytes -> {outfile}")

def gen_store_test(outfile):
    """Generate test for OpCooperativeMatrixStoreHW with load-store roundtrip."""
    # IDs
    void_t = 1; func_t = 2; main_f = 3; uint_t = 4; v2uint_t = 5; float_t = 6
    float_ptr_sb = 7; rtarray_t = 8; block_t = 9; block_ptr_t = 10
    data_var = 11; label = 12; glsl_id = 13
    c16 = 14; c16b = 15; c0 = 16; c1 = 17
    dim16 = 18; dim0 = 19
    coopmatA = 20
    ptr_elem = 21; matA = 22

    BOUND = 23

    out = b''
    # Header
    out += word(0x07230203) + word(0x00010600) + word(0) + word(BOUND) + word(0)
    # Capabilities
    out += inst(OpCapability, 1) + inst(OpCapability, 6600)
    # ExtInstImport
    sw = str_words("GLSL.std.450")
    out += word(((1 + len(sw) + 1) << 16) | OpExtInstImport) + word(glsl_id) + b''.join(word(w) for w in sw)
    # MemoryModel
    out += inst(OpMemoryModel, 0, 1)
    # EntryPoint
    en = str_words("main")
    out += word(((2 + len(en) + 1) << 16) | OpEntryPoint) + word(5) + word(main_f) + b''.join(word(w) for w in en)
    # ExecutionMode
    out += inst(OpExecutionMode, main_f, 17, 16, 1, 1)
    # Debug names
    for target, name in [(main_f, "main"), (data_var, "data"), (float_t, "float"),
                          (uint_t, "uint"), (matA, "matA")]:
        nw = str_words(name)
        out += word(((1 + len(nw) + 1) << 16) | OpName) + word(target) + b''.join(word(w) for w in nw)
    # Annotations
    out += inst(OpDecorate, block_t, DecorationBlock)
    out += inst(OpMemberDecorate, block_t, 0, DecorationOffset, 0)
    out += inst(OpDecorate, rtarray_t, DecorationArrayStride, 4)
    out += inst(OpDecorate, data_var, DecorationBinding, 0)
    out += inst(OpDecorate, data_var, DecorationDescriptorSet, 0)
    # Types
    out += inst(OpTypeVoid, void_t)
    out += inst(OpTypeFloat, float_t, 32)
    out += inst(OpTypeInt, uint_t, 32, 0)
    out += inst(OpTypeVector, v2uint_t, uint_t, 2)
    out += inst(OpTypeFunction, func_t, void_t)
    out += inst(OpTypePointer, float_ptr_sb, StorageClassStorageBuffer, float_t)
    out += inst(OpTypeRuntimeArray, rtarray_t, float_t)
    out += inst(OpTypeStruct, block_t, rtarray_t)
    out += inst(OpTypePointer, block_ptr_t, StorageClassStorageBuffer, block_t)
    # Constants
    out += inst(OpConstant, uint_t, c16, 16)
    out += inst(OpConstant, uint_t, c16b, 16)
    out += inst(OpConstant, uint_t, c0, 0)
    out += inst(OpConstant, uint_t, c1, 1)
    out += inst(OpConstantComposite, v2uint_t, dim16, c16, c16b)
    out += inst(OpConstantComposite, v2uint_t, dim0, c0, c0)
    # CoopMat type (UseA=0)
    out += inst(OpTypeCooperativeMatrixHW, coopmatA, float_t, c16, c16b, c0)
    # Variables
    out += inst(OpVariable, block_ptr_t, data_var, StorageClassStorageBuffer)
    # Function body
    out += inst(OpFunction, void_t, main_f, 0, func_t)
    out += inst(OpLabel, label)
    # AccessChain
    out += inst(OpAccessChain, float_ptr_sb, ptr_elem, data_var, c0, c0)
    # Load matrix
    out += inst(OpCooperativeMatrixLoadHW, coopmatA, matA, ptr_elem, dim16, dim0, c0)
    # Store matrix back (RowMajor)
    out += inst(OpCooperativeMatrixStoreHW, ptr_elem, matA, dim16, dim0, c0)
    out += inst(OpReturn)
    out += inst(OpFunctionEnd)
    # Update bound
    data = bytearray(out)
    struct.pack_into('<I', data, 12, BOUND)
    with open(outfile, 'wb') as f:
        f.write(bytes(data))
    print(f"Generated: {len(data)} bytes -> {outfile}")

def gen_const_store_test(outfile):
    """Generate test for OpCooperativeMatrixStoreHW with a constant immediate value.

    Reproduces the bug where coopmatHW<float,16,16>(100.0f) used as an
    immediate value causes 'Invalid constant expression basetype' in
    constant_expression_vector.
    """
    # IDs
    void_t = 1; func_t = 2; main_f = 3; uint_t = 4; v2uint_t = 5; float_t = 6
    float_ptr_sb = 7; rtarray_t = 8; block_t = 9; block_ptr_t = 10
    data_var = 11; label = 12; glsl_id = 13
    c16 = 14; c16b = 15; c0 = 16; c1 = 17
    dim16 = 18; dim0 = 19
    coopmatA = 20
    ptr_elem = 21
    c100f = 22; mat_const = 23

    BOUND = 24

    out = b''
    # Header
    out += word(0x07230203) + word(0x00010600) + word(0) + word(BOUND) + word(0)
    # Capabilities
    out += inst(OpCapability, 1) + inst(OpCapability, 6600)
    # ExtInstImport
    sw = str_words("GLSL.std.450")
    out += word(((1 + len(sw) + 1) << 16) | OpExtInstImport) + word(glsl_id) + b''.join(word(w) for w in sw)
    # MemoryModel
    out += inst(OpMemoryModel, 0, 1)
    # EntryPoint
    en = str_words("main")
    out += word(((2 + len(en) + 1) << 16) | OpEntryPoint) + word(5) + word(main_f) + b''.join(word(w) for w in en)
    # ExecutionMode
    out += inst(OpExecutionMode, main_f, 17, 16, 1, 1)
    # Debug names
    for target, name in [(main_f, "main"), (data_var, "data"), (float_t, "float"),
                          (uint_t, "uint"), (mat_const, "mat_const")]:
        nw = str_words(name)
        out += word(((1 + len(nw) + 1) << 16) | OpName) + word(target) + b''.join(word(w) for w in nw)
    # Annotations
    out += inst(OpDecorate, block_t, DecorationBlock)
    out += inst(OpMemberDecorate, block_t, 0, DecorationOffset, 0)
    out += inst(OpDecorate, rtarray_t, DecorationArrayStride, 4)
    out += inst(OpDecorate, data_var, DecorationBinding, 0)
    out += inst(OpDecorate, data_var, DecorationDescriptorSet, 0)
    # Types
    out += inst(OpTypeVoid, void_t)
    out += inst(OpTypeFloat, float_t, 32)
    out += inst(OpTypeInt, uint_t, 32, 0)
    out += inst(OpTypeVector, v2uint_t, uint_t, 2)
    out += inst(OpTypeFunction, func_t, void_t)
    out += inst(OpTypePointer, float_ptr_sb, StorageClassStorageBuffer, float_t)
    out += inst(OpTypeRuntimeArray, rtarray_t, float_t)
    out += inst(OpTypeStruct, block_t, rtarray_t)
    out += inst(OpTypePointer, block_ptr_t, StorageClassStorageBuffer, block_t)
    # Constants
    out += inst(OpConstant, uint_t, c16, 16)
    out += inst(OpConstant, uint_t, c16b, 16)
    out += inst(OpConstant, uint_t, c0, 0)
    out += inst(OpConstant, uint_t, c1, 1)
    # float constant 100.0 (IEEE 754: 0x42C80000)
    out += inst(OpConstant, float_t, c100f, 0x42C80000)
    out += inst(OpConstantComposite, v2uint_t, dim16, c16, c16b)
    out += inst(OpConstantComposite, v2uint_t, dim0, c0, c0)
    # CoopMat type
    out += inst(OpTypeCooperativeMatrixHW, coopmatA, float_t, c16, c16b, c0)
    # CoopMat constant constructed from single scalar (splat)
    out += inst(OpConstantComposite, coopmatA, mat_const, c100f)
    # Variables
    out += inst(OpVariable, block_ptr_t, data_var, StorageClassStorageBuffer)
    # Function body
    out += inst(OpFunction, void_t, main_f, 0, func_t)
    out += inst(OpLabel, label)
    # AccessChain
    out += inst(OpAccessChain, float_ptr_sb, ptr_elem, data_var, c0, c0)
    # Store constant coopmat directly (immediate value)
    out += inst(OpCooperativeMatrixStoreHW, ptr_elem, mat_const, dim16, dim0, c0)
    out += inst(OpReturn)
    out += inst(OpFunctionEnd)
    # Update bound
    data = bytearray(out)
    struct.pack_into('<I', data, 12, BOUND)
    with open(outfile, 'wb') as f:
        f.write(bytes(data))
    print(f"Generated: {len(data)} bytes -> {outfile}")

def gen_muladd_test(outfile):
    """Generate test for OpCooperativeMatrixMulAddHW: load A, B, C, MulAdd, store result."""
    # IDs
    void_t = 1; func_t = 2; main_f = 3; uint_t = 4; v2uint_t = 5; float_t = 6
    float_ptr_sb = 7; rtarray_t = 8; block_t = 9; block_ptr_t = 10
    data_var = 11; label = 12; glsl_id = 13
    c16 = 14; c16b = 15; c0 = 16; c1 = 17
    dim16 = 18; dim0 = 19
    c2 = 28  # Accumulator use constant
    # CoopMat types: UseA=0, UseB=1, Accumulator=2
    coopmatA = 20; coopmatB = 21; coopmatAcc = 22
    ptr_elem = 23; matA = 24; matB = 25; matC = 26; result = 27

    BOUND = 29

    out = b''
    # Header
    out += word(0x07230203) + word(0x00010600) + word(0) + word(BOUND) + word(0)
    # Capabilities
    out += inst(OpCapability, 1) + inst(OpCapability, 6600)
    # ExtInstImport
    sw = str_words("GLSL.std.450")
    out += word(((1 + len(sw) + 1) << 16) | OpExtInstImport) + word(glsl_id) + b''.join(word(w) for w in sw)
    # MemoryModel
    out += inst(OpMemoryModel, 0, 1)
    # EntryPoint
    en = str_words("main")
    out += word(((2 + len(en) + 1) << 16) | OpEntryPoint) + word(5) + word(main_f) + b''.join(word(w) for w in en)
    # ExecutionMode
    out += inst(OpExecutionMode, main_f, 17, 16, 1, 1)
    # Debug names
    for target, name in [(main_f, "main"), (data_var, "data"), (float_t, "float"),
                          (uint_t, "uint"), (matA, "matA"), (matB, "matB"),
                          (matC, "matC"), (result, "result")]:
        nw = str_words(name)
        out += word(((1 + len(nw) + 1) << 16) | OpName) + word(target) + b''.join(word(w) for w in nw)
    # Annotations
    out += inst(OpDecorate, block_t, DecorationBlock)
    out += inst(OpMemberDecorate, block_t, 0, DecorationOffset, 0)
    out += inst(OpDecorate, rtarray_t, DecorationArrayStride, 4)
    out += inst(OpDecorate, data_var, DecorationBinding, 0)
    out += inst(OpDecorate, data_var, DecorationDescriptorSet, 0)
    # Types
    out += inst(OpTypeVoid, void_t)
    out += inst(OpTypeFloat, float_t, 32)
    out += inst(OpTypeInt, uint_t, 32, 0)
    out += inst(OpTypeVector, v2uint_t, uint_t, 2)
    out += inst(OpTypeFunction, func_t, void_t)
    out += inst(OpTypePointer, float_ptr_sb, StorageClassStorageBuffer, float_t)
    out += inst(OpTypeRuntimeArray, rtarray_t, float_t)
    out += inst(OpTypeStruct, block_t, rtarray_t)
    out += inst(OpTypePointer, block_ptr_t, StorageClassStorageBuffer, block_t)
    # Constants
    out += inst(OpConstant, uint_t, c16, 16)
    out += inst(OpConstant, uint_t, c16b, 16)
    out += inst(OpConstant, uint_t, c0, 0)
    out += inst(OpConstant, uint_t, c1, 1)
    out += inst(OpConstant, uint_t, c2, 2)
    out += inst(OpConstantComposite, v2uint_t, dim16, c16, c16b)
    out += inst(OpConstantComposite, v2uint_t, dim0, c0, c0)
    # CoopMat types: UseA=0 (MatrixA), UseB=1 (MatrixB), Accumulator=2
    out += inst(OpTypeCooperativeMatrixHW, coopmatA, float_t, c16, c16b, c0)    # 16x16 UseA
    out += inst(OpTypeCooperativeMatrixHW, coopmatB, float_t, c16, c16b, c1)    # 16x16 UseB
    out += inst(OpTypeCooperativeMatrixHW, coopmatAcc, float_t, c16, c16b, c2) # 16x16 Accumulator=2
    # Variables
    out += inst(OpVariable, block_ptr_t, data_var, StorageClassStorageBuffer)
    # Function body
    out += inst(OpFunction, void_t, main_f, 0, func_t)
    out += inst(OpLabel, label)
    # AccessChain
    out += inst(OpAccessChain, float_ptr_sb, ptr_elem, data_var, c0, c0)
    # Load matrices A, B, C
    out += inst(OpCooperativeMatrixLoadHW, coopmatA, matA, ptr_elem, dim16, dim0, c0)
    out += inst(OpCooperativeMatrixLoadHW, coopmatB, matB, ptr_elem, dim16, dim0, c0)
    out += inst(OpCooperativeMatrixLoadHW, coopmatAcc, matC, ptr_elem, dim16, dim0, c0)
    # MulAdd: result = A * B + C
    out += inst(OpCooperativeMatrixMulAddHW, coopmatAcc, result, matA, matB, matC)
    # Store result
    out += inst(OpCooperativeMatrixStoreHW, ptr_elem, result, dim16, dim0, c0)
    out += inst(OpReturn)
    out += inst(OpFunctionEnd)
    # Update bound
    data = bytearray(out)
    struct.pack_into('<I', data, 12, BOUND)
    with open(outfile, 'wb') as f:
        f.write(bytes(data))
    print(f"Generated: {len(data)} bytes -> {outfile}")

def gen_mul_test(outfile):
    """Generate test for coopmatMulHW via MulAddHW with C=OpUndef (None)."""
    # IDs
    void_t = 1; func_t = 2; main_f = 3; uint_t = 4; v2uint_t = 5; float_t = 6
    float_ptr_sb = 7; rtarray_t = 8; block_t = 9; block_ptr_t = 10
    data_var = 11; label = 12; glsl_id = 13
    c16 = 14; c16b = 15; c0 = 16; c1 = 17
    dim16 = 18; dim0 = 19
    c2 = 28
    coopmatA = 20; coopmatB = 21; coopmatAcc = 22
    ptr_elem = 23; matA = 24; matB = 25; result = 26
    undef_acc = 27  # OpUndef for accumulator type (None marker)

    BOUND = 29

    out = b''
    out += word(0x07230203) + word(0x00010600) + word(0) + word(BOUND) + word(0)
    out += inst(OpCapability, 1) + inst(OpCapability, 6600)
    sw = str_words("GLSL.std.450")
    out += word(((1 + len(sw) + 1) << 16) | OpExtInstImport) + word(glsl_id) + b''.join(word(w) for w in sw)
    out += inst(OpMemoryModel, 0, 1)
    en = str_words("main")
    out += word(((2 + len(en) + 1) << 16) | OpEntryPoint) + word(5) + word(main_f) + b''.join(word(w) for w in en)
    out += inst(OpExecutionMode, main_f, 17, 16, 1, 1)
    for target, name in [(main_f, "main"), (data_var, "data"), (float_t, "float"),
                          (uint_t, "uint"), (matA, "matA"), (matB, "matB"),
                          (result, "result")]:
        nw = str_words(name)
        out += word(((1 + len(nw) + 1) << 16) | OpName) + word(target) + b''.join(word(w) for w in nw)
    out += inst(OpDecorate, block_t, DecorationBlock)
    out += inst(OpMemberDecorate, block_t, 0, DecorationOffset, 0)
    out += inst(OpDecorate, rtarray_t, DecorationArrayStride, 4)
    out += inst(OpDecorate, data_var, DecorationBinding, 0)
    out += inst(OpDecorate, data_var, DecorationDescriptorSet, 0)
    out += inst(OpTypeVoid, void_t)
    out += inst(OpTypeFloat, float_t, 32)
    out += inst(OpTypeInt, uint_t, 32, 0)
    out += inst(OpTypeVector, v2uint_t, uint_t, 2)
    out += inst(OpTypeFunction, func_t, void_t)
    out += inst(OpTypePointer, float_ptr_sb, StorageClassStorageBuffer, float_t)
    out += inst(OpTypeRuntimeArray, rtarray_t, float_t)
    out += inst(OpTypeStruct, block_t, rtarray_t)
    out += inst(OpTypePointer, block_ptr_t, StorageClassStorageBuffer, block_t)
    out += inst(OpConstant, uint_t, c16, 16)
    out += inst(OpConstant, uint_t, c16b, 16)
    out += inst(OpConstant, uint_t, c0, 0)
    out += inst(OpConstant, uint_t, c1, 1)
    out += inst(OpConstant, uint_t, c2, 2)
    out += inst(OpConstantComposite, v2uint_t, dim16, c16, c16b)
    out += inst(OpConstantComposite, v2uint_t, dim0, c0, c0)
    out += inst(OpTypeCooperativeMatrixHW, coopmatA, float_t, c16, c16b, c0)
    out += inst(OpTypeCooperativeMatrixHW, coopmatB, float_t, c16, c16b, c1)
    out += inst(OpTypeCooperativeMatrixHW, coopmatAcc, float_t, c16, c16b, c2)
    # OpUndef for accumulator type (None marker)
    out += inst(OpUndef, coopmatAcc, undef_acc)
    out += inst(OpVariable, block_ptr_t, data_var, StorageClassStorageBuffer)
    out += inst(OpFunction, void_t, main_f, 0, func_t)
    out += inst(OpLabel, label)
    out += inst(OpAccessChain, float_ptr_sb, ptr_elem, data_var, c0, c0)
    out += inst(OpCooperativeMatrixLoadHW, coopmatA, matA, ptr_elem, dim16, dim0, c0)
    out += inst(OpCooperativeMatrixLoadHW, coopmatB, matB, ptr_elem, dim16, dim0, c0)
    # Mul with C = OpUndef (None) -> coopmatMulHW
    out += inst(OpCooperativeMatrixMulAddHW, coopmatAcc, result, matA, matB, undef_acc)
    out += inst(OpCooperativeMatrixStoreHW, ptr_elem, result, dim16, dim0, c0)
    out += inst(OpReturn)
    out += inst(OpFunctionEnd)
    data = bytearray(out)
    struct.pack_into('<I', data, 12, BOUND)
    with open(outfile, 'wb') as f:
        f.write(bytes(data))
    print(f"Generated: {len(data)} bytes -> {outfile}")

def gen_reduce_test(outfile):
    """Generate test for OpCooperativeMatrixReduceHW: load, reduce, store."""
    # IDs
    void_t = 1; func_t = 2; main_f = 3; uint_t = 4; v2uint_t = 5; float_t = 6
    float_ptr_sb = 7; rtarray_t = 8; block_t = 9; block_ptr_t = 10
    data_var = 11; label = 12; glsl_id = 13
    c16 = 14; c16b = 15; c0 = 16; c1 = 17
    dim16 = 18; dim0 = 19
    c2 = 28; c3 = 29  # constant 2 (Accumulator use), constant 3 (ReduceMax)
    coopmatAcc = 20
    ptr_elem = 21; matA = 22; result1 = 23; result2 = 24

    BOUND = 30

    out = b''
    out += word(0x07230203) + word(0x00010600) + word(0) + word(BOUND) + word(0)
    out += inst(OpCapability, 1) + inst(OpCapability, 6600)
    sw = str_words("GLSL.std.450")
    out += word(((1 + len(sw) + 1) << 16) | OpExtInstImport) + word(glsl_id) + b''.join(word(w) for w in sw)
    out += inst(OpMemoryModel, 0, 1)
    en = str_words("main")
    out += word(((2 + len(en) + 1) << 16) | OpEntryPoint) + word(5) + word(main_f) + b''.join(word(w) for w in en)
    out += inst(OpExecutionMode, main_f, 17, 16, 1, 1)
    for target, name in [(main_f, "main"), (data_var, "data"), (float_t, "float"),
                          (uint_t, "uint"), (matA, "matA"), (result1, "result1"),
                          (result2, "result2")]:
        nw = str_words(name)
        out += word(((1 + len(nw) + 1) << 16) | OpName) + word(target) + b''.join(word(w) for w in nw)
    out += inst(OpDecorate, block_t, DecorationBlock)
    out += inst(OpMemberDecorate, block_t, 0, DecorationOffset, 0)
    out += inst(OpDecorate, rtarray_t, DecorationArrayStride, 4)
    out += inst(OpDecorate, data_var, DecorationBinding, 0)
    out += inst(OpDecorate, data_var, DecorationDescriptorSet, 0)
    out += inst(OpTypeVoid, void_t)
    out += inst(OpTypeFloat, float_t, 32)
    out += inst(OpTypeInt, uint_t, 32, 0)
    out += inst(OpTypeVector, v2uint_t, uint_t, 2)
    out += inst(OpTypeFunction, func_t, void_t)
    out += inst(OpTypePointer, float_ptr_sb, StorageClassStorageBuffer, float_t)
    out += inst(OpTypeRuntimeArray, rtarray_t, float_t)
    out += inst(OpTypeStruct, block_t, rtarray_t)
    out += inst(OpTypePointer, block_ptr_t, StorageClassStorageBuffer, block_t)
    out += inst(OpConstant, uint_t, c16, 16)
    out += inst(OpConstant, uint_t, c16b, 16)
    out += inst(OpConstant, uint_t, c0, 0)
    out += inst(OpConstant, uint_t, c1, 1)
    out += inst(OpConstant, uint_t, c2, 2)
    out += inst(OpConstant, uint_t, c3, 3)
    out += inst(OpConstantComposite, v2uint_t, dim16, c16, c16b)
    out += inst(OpConstantComposite, v2uint_t, dim0, c0, c0)
    # Accumulator type (use=2)
    out += inst(OpTypeCooperativeMatrixHW, coopmatAcc, float_t, c16, c16b, c2)
    out += inst(OpVariable, block_ptr_t, data_var, StorageClassStorageBuffer)
    out += inst(OpFunction, void_t, main_f, 0, func_t)
    out += inst(OpLabel, label)
    out += inst(OpAccessChain, float_ptr_sb, ptr_elem, data_var, c0, c0)
    out += inst(OpCooperativeMatrixLoadHW, coopmatAcc, matA, ptr_elem, dim16, dim0, c0)
    # Reduce 1: Row ReduceAdd (mask=0, op=0)
    out += inst(OpCooperativeMatrixReduceHW, coopmatAcc, result1, matA, c0, c0)
    # Reduce 2: Column ReduceMax (mask=1, op=2)
    out += inst(OpCooperativeMatrixReduceHW, coopmatAcc, result2, matA, c1, c2)
    out += inst(OpCooperativeMatrixStoreHW, ptr_elem, result1, dim16, dim0, c0)
    out += inst(OpCooperativeMatrixStoreHW, ptr_elem, result2, dim16, dim0, c0)
    out += inst(OpReturn)
    out += inst(OpFunctionEnd)
    data = bytearray(out)
    struct.pack_into('<I', data, 12, BOUND)
    with open(outfile, 'wb') as f:
        f.write(bytes(data))
    print(f"Generated: {len(data)} bytes -> {outfile}")

def gen_convert_test(outfile):
    """Generate test for coopmatHW conversion: float->int (ConvertFToS), int->float (ConvertSToF), bitcast."""
    # IDs
    void_t = 1; func_t = 2; main_f = 3; uint_t = 4; v2uint_t = 5; float_t = 6; int_t = 7
    float_ptr_sb = 8; rtarray_t = 9; block_t = 10; block_ptr_t = 11
    data_var = 12; label = 13; glsl_id = 14
    c16 = 15; c16b = 16; c0 = 17; c1 = 18; c2 = 19
    dim16 = 20; dim0 = 21
    coopmatF = 22; coopmatI = 23
    ptr_elem = 24; matF = 25
    result_ftos = 26; result_stof = 27
    result_bitcast = 28

    BOUND = 29

    out = b''
    out += word(0x07230203) + word(0x00010600) + word(0) + word(BOUND) + word(0)
    out += inst(OpCapability, 1) + inst(OpCapability, 6600)
    sw = str_words("GLSL.std.450")
    out += word(((1 + len(sw) + 1) << 16) | OpExtInstImport) + word(glsl_id) + b''.join(word(w) for w in sw)
    out += inst(OpMemoryModel, 0, 1)
    en = str_words("main")
    out += word(((2 + len(en) + 1) << 16) | OpEntryPoint) + word(5) + word(main_f) + b''.join(word(w) for w in en)
    out += inst(OpExecutionMode, main_f, 17, 16, 1, 1)
    for target, name in [(main_f, "main"), (data_var, "data"), (float_t, "float"),
                          (int_t, "int"), (uint_t, "uint"),
                          (matF, "matF"), (result_ftos, "result_ftos"),
                          (result_stof, "result_stof"), (result_bitcast, "result_bitcast")]:
        nw = str_words(name)
        out += word(((1 + len(nw) + 1) << 16) | OpName) + word(target) + b''.join(word(w) for w in nw)
    out += inst(OpDecorate, block_t, DecorationBlock)
    out += inst(OpMemberDecorate, block_t, 0, DecorationOffset, 0)
    out += inst(OpDecorate, rtarray_t, DecorationArrayStride, 4)
    out += inst(OpDecorate, data_var, DecorationBinding, 0)
    out += inst(OpDecorate, data_var, DecorationDescriptorSet, 0)
    out += inst(OpTypeVoid, void_t)
    out += inst(OpTypeFloat, float_t, 32)
    out += inst(OpTypeInt, uint_t, 32, 0)
    out += inst(OpTypeInt, int_t, 32, 1)
    out += inst(OpTypeVector, v2uint_t, uint_t, 2)
    out += inst(OpTypeFunction, func_t, void_t)
    out += inst(OpTypePointer, float_ptr_sb, StorageClassStorageBuffer, float_t)
    out += inst(OpTypeRuntimeArray, rtarray_t, float_t)
    out += inst(OpTypeStruct, block_t, rtarray_t)
    out += inst(OpTypePointer, block_ptr_t, StorageClassStorageBuffer, block_t)
    out += inst(OpConstant, uint_t, c16, 16)
    out += inst(OpConstant, uint_t, c16b, 16)
    out += inst(OpConstant, uint_t, c0, 0)
    out += inst(OpConstant, uint_t, c1, 1)
    out += inst(OpConstant, uint_t, c2, 2)
    out += inst(OpConstantComposite, v2uint_t, dim16, c16, c16b)
    out += inst(OpConstantComposite, v2uint_t, dim0, c0, c0)
    out += inst(OpTypeCooperativeMatrixHW, coopmatF, float_t, c16, c16b, c0)
    out += inst(OpTypeCooperativeMatrixHW, coopmatI, int_t, c16, c16b, c2)
    out += inst(OpVariable, block_ptr_t, data_var, StorageClassStorageBuffer)
    out += inst(OpFunction, void_t, main_f, 0, func_t)
    out += inst(OpLabel, label)
    out += inst(OpAccessChain, float_ptr_sb, ptr_elem, data_var, c0, c0)
    out += inst(OpCooperativeMatrixLoadHW, coopmatF, matF, ptr_elem, dim16, dim0, c0)
    # ConvertFToS: float -> int
    out += inst(OpConvertFToS, coopmatI, result_ftos, matF)
    # ConvertSToF: int -> float
    out += inst(OpConvertSToF, coopmatF, result_stof, result_ftos)
    # Bitcast: float -> int (reinterpret)
    out += inst(OpBitcast, coopmatI, result_bitcast, matF)
    out += inst(OpCooperativeMatrixStoreHW, ptr_elem, result_stof, dim16, dim0, c0)
    out += inst(OpCooperativeMatrixStoreHW, ptr_elem, result_ftos, dim16, dim0, c0)
    out += inst(OpCooperativeMatrixStoreHW, ptr_elem, result_bitcast, dim16, dim0, c0)
    out += inst(OpReturn)
    out += inst(OpFunctionEnd)
    data = bytearray(out)
    struct.pack_into('<I', data, 12, BOUND)
    with open(outfile, 'wb') as f:
        f.write(bytes(data))
    print(f"Generated: {len(data)} bytes -> {outfile}")

def gen_bitcast32_test(outfile):
    """Generate test for coopmatHW 32-bit bitcast: float32<->uint32, float32<->int32."""
    # IDs
    void_t = 1; func_t = 2; main_f = 3; uint_t = 4; v2uint_t = 5; float_t = 6
    int_t = 7
    float_ptr_sb = 8; rtarray_t = 9; block_t = 10; block_ptr_t = 11
    data_var = 12; label = 13; glsl_id = 14
    c16 = 15; c16b = 16; c0 = 17; c1 = 18; c2 = 19
    dim16 = 20; dim0 = 21
    coopmatF32 = 22; coopmatI32 = 23; coopmatU32 = 24
    ptr_elem = 25; matF = 26
    # Bitcast results
    result_f2i = 27; result_i2f = 28; result_f2u = 29; result_u2f = 30

    BOUND = 31

    out = b''
    out += word(0x07230203) + word(0x00010600) + word(0) + word(BOUND) + word(0)
    out += inst(OpCapability, 1) + inst(OpCapability, 6600)
    sw = str_words("GLSL.std.450")
    out += word(((1 + len(sw) + 1) << 16) | OpExtInstImport) + word(glsl_id) + b''.join(word(w) for w in sw)
    out += inst(OpMemoryModel, 0, 1)
    en = str_words("main")
    out += word(((2 + len(en) + 1) << 16) | OpEntryPoint) + word(5) + word(main_f) + b''.join(word(w) for w in en)
    out += inst(OpExecutionMode, main_f, 17, 16, 1, 1)
    for target, name in [(main_f, "main"), (data_var, "data"), (float_t, "float"),
                          (uint_t, "uint"), (int_t, "int"),
                          (matF, "matF"), (result_f2i, "result_f2i"),
                          (result_i2f, "result_i2f"), (result_f2u, "result_f2u"),
                          (result_u2f, "result_u2f")]:
        nw = str_words(name)
        out += word(((1 + len(nw) + 1) << 16) | OpName) + word(target) + b''.join(word(w) for w in nw)
    out += inst(OpDecorate, block_t, DecorationBlock)
    out += inst(OpMemberDecorate, block_t, 0, DecorationOffset, 0)
    out += inst(OpDecorate, rtarray_t, DecorationArrayStride, 4)
    out += inst(OpDecorate, data_var, DecorationBinding, 0)
    out += inst(OpDecorate, data_var, DecorationDescriptorSet, 0)
    out += inst(OpTypeVoid, void_t)
    out += inst(OpTypeFloat, float_t, 32)
    out += inst(OpTypeInt, uint_t, 32, 0)
    out += inst(OpTypeInt, int_t, 32, 1)
    out += inst(OpTypeVector, v2uint_t, uint_t, 2)
    out += inst(OpTypeFunction, func_t, void_t)
    out += inst(OpTypePointer, float_ptr_sb, StorageClassStorageBuffer, float_t)
    out += inst(OpTypeRuntimeArray, rtarray_t, float_t)
    out += inst(OpTypeStruct, block_t, rtarray_t)
    out += inst(OpTypePointer, block_ptr_t, StorageClassStorageBuffer, block_t)
    out += inst(OpConstant, uint_t, c16, 16)
    out += inst(OpConstant, uint_t, c16b, 16)
    out += inst(OpConstant, uint_t, c0, 0)
    out += inst(OpConstant, uint_t, c1, 1)
    out += inst(OpConstant, uint_t, c2, 2)
    out += inst(OpConstantComposite, v2uint_t, dim16, c16, c16b)
    out += inst(OpConstantComposite, v2uint_t, dim0, c0, c0)
    # CoopMat types with 32-bit component types (all Accumulator use=2)
    out += inst(OpTypeCooperativeMatrixHW, coopmatF32, float_t, c16, c16b, c2)
    out += inst(OpTypeCooperativeMatrixHW, coopmatI32, int_t, c16, c16b, c2)
    out += inst(OpTypeCooperativeMatrixHW, coopmatU32, uint_t, c16, c16b, c2)
    out += inst(OpVariable, block_ptr_t, data_var, StorageClassStorageBuffer)
    out += inst(OpFunction, void_t, main_f, 0, func_t)
    out += inst(OpLabel, label)
    out += inst(OpAccessChain, float_ptr_sb, ptr_elem, data_var, c0, c0)
    # Load float32 coopmat
    out += inst(OpCooperativeMatrixLoadHW, coopmatF32, matF, ptr_elem, dim16, dim0, c0)
    # Bitcast: float32 -> int32 (should emit floatBitsToInt)
    out += inst(OpBitcast, coopmatI32, result_f2i, matF)
    # Bitcast: int32 -> float32 (should emit intBitsToFloat)
    out += inst(OpBitcast, coopmatF32, result_i2f, result_f2i)
    # Bitcast: float32 -> uint32 (should emit floatBitsToUint)
    out += inst(OpBitcast, coopmatU32, result_f2u, matF)
    # Bitcast: uint32 -> float32 (should emit uintBitsToFloat)
    out += inst(OpBitcast, coopmatF32, result_u2f, result_f2u)
    # Store results
    out += inst(OpCooperativeMatrixStoreHW, ptr_elem, result_f2i, dim16, dim0, c0)
    out += inst(OpCooperativeMatrixStoreHW, ptr_elem, result_i2f, dim16, dim0, c0)
    out += inst(OpCooperativeMatrixStoreHW, ptr_elem, result_f2u, dim16, dim0, c0)
    out += inst(OpCooperativeMatrixStoreHW, ptr_elem, result_u2f, dim16, dim0, c0)
    out += inst(OpReturn)
    out += inst(OpFunctionEnd)
    data = bytearray(out)
    struct.pack_into('<I', data, 12, BOUND)
    with open(outfile, 'wb') as f:
        f.write(bytes(data))
    print(f"Generated: {len(data)} bytes -> {outfile}")

def gen_mul_null_test(outfile):
    """Generate test for coopmatMulHW via MulAddHW with C=OpConstantNull (null constant)."""
    void_t = 1; func_t = 2; main_f = 3; uint_t = 4; v2uint_t = 5; float_t = 6
    float_ptr_sb = 7; rtarray_t = 8; block_t = 9; block_ptr_t = 10
    data_var = 11; label = 12; glsl_id = 13
    c16 = 14; c16b = 15; c0 = 16; c1 = 17
    dim16 = 18; dim0 = 19
    c2 = 28
    coopmatA = 20; coopmatB = 21; coopmatAcc = 22
    ptr_elem = 23; matA = 24; matB = 25; result = 26
    null_acc = 27

    BOUND = 29

    out = b''
    out += word(0x07230203) + word(0x00010600) + word(0) + word(BOUND) + word(0)
    out += inst(OpCapability, 1) + inst(OpCapability, 6600)
    sw = str_words("GLSL.std.450")
    out += word(((1 + len(sw) + 1) << 16) | OpExtInstImport) + word(glsl_id) + b''.join(word(w) for w in sw)
    out += inst(OpMemoryModel, 0, 1)
    en = str_words("main")
    out += word(((2 + len(en) + 1) << 16) | OpEntryPoint) + word(5) + word(main_f) + b''.join(word(w) for w in en)
    out += inst(OpExecutionMode, main_f, 17, 16, 1, 1)
    for target, name in [(main_f, "main"), (data_var, "data"), (float_t, "float"),
                          (uint_t, "uint"), (matA, "matA"), (matB, "matB"),
                          (result, "result")]:
        nw = str_words(name)
        out += word(((1 + len(nw) + 1) << 16) | OpName) + word(target) + b''.join(word(w) for w in nw)
    out += inst(OpDecorate, block_t, DecorationBlock)
    out += inst(OpMemberDecorate, block_t, 0, DecorationOffset, 0)
    out += inst(OpDecorate, rtarray_t, DecorationArrayStride, 4)
    out += inst(OpDecorate, data_var, DecorationBinding, 0)
    out += inst(OpDecorate, data_var, DecorationDescriptorSet, 0)
    out += inst(OpTypeVoid, void_t)
    out += inst(OpTypeFloat, float_t, 32)
    out += inst(OpTypeInt, uint_t, 32, 0)
    out += inst(OpTypeVector, v2uint_t, uint_t, 2)
    out += inst(OpTypeFunction, func_t, void_t)
    out += inst(OpTypePointer, float_ptr_sb, StorageClassStorageBuffer, float_t)
    out += inst(OpTypeRuntimeArray, rtarray_t, float_t)
    out += inst(OpTypeStruct, block_t, rtarray_t)
    out += inst(OpTypePointer, block_ptr_t, StorageClassStorageBuffer, block_t)
    out += inst(OpConstant, uint_t, c16, 16)
    out += inst(OpConstant, uint_t, c16b, 16)
    out += inst(OpConstant, uint_t, c0, 0)
    out += inst(OpConstant, uint_t, c1, 1)
    out += inst(OpConstant, uint_t, c2, 2)
    out += inst(OpConstantComposite, v2uint_t, dim16, c16, c16b)
    out += inst(OpConstantComposite, v2uint_t, dim0, c0, c0)
    out += inst(OpTypeCooperativeMatrixHW, coopmatA, float_t, c16, c16b, c0)
    out += inst(OpTypeCooperativeMatrixHW, coopmatB, float_t, c16, c16b, c1)
    out += inst(OpTypeCooperativeMatrixHW, coopmatAcc, float_t, c16, c16b, c2)
    # Null constant for accumulator type (instead of OpUndef)
    out += inst(OpConstantNull, coopmatAcc, null_acc)
    out += inst(OpVariable, block_ptr_t, data_var, StorageClassStorageBuffer)
    out += inst(OpFunction, void_t, main_f, 0, func_t)
    out += inst(OpLabel, label)
    out += inst(OpAccessChain, float_ptr_sb, ptr_elem, data_var, c0, c0)
    out += inst(OpCooperativeMatrixLoadHW, coopmatA, matA, ptr_elem, dim16, dim0, c0)
    out += inst(OpCooperativeMatrixLoadHW, coopmatB, matB, ptr_elem, dim16, dim0, c0)
    # Mul with C = OpConstantNull -> should emit coopmatMulHW
    out += inst(OpCooperativeMatrixMulAddHW, coopmatAcc, result, matA, matB, null_acc)
    out += inst(OpCooperativeMatrixStoreHW, ptr_elem, result, dim16, dim0, c0)
    out += inst(OpReturn)
    out += inst(OpFunctionEnd)
    data = bytearray(out)
    struct.pack_into('<I', data, 12, BOUND)
    with open(outfile, 'wb') as f:
        f.write(bytes(data))
    print(f"Generated: {len(data)} bytes -> {outfile}")

def gen_bitcast16_test(outfile):
    """Generate test for coopmatHW 16-bit bitcast: float16<->int16, float16<->uint16."""
    # IDs
    void_t = 1; func_t = 2; main_f = 3; uint_t = 4; v2uint_t = 5; float_t = 6
    float_ptr_sb = 7; rtarray_t = 8; block_t = 9; block_ptr_t = 10
    data_var = 11; label = 12; glsl_id = 13
    c16 = 14; c16b = 15; c0 = 16; c1 = 17; c2 = 18
    dim16 = 19; dim0 = 20
    # 16-bit types
    half_t = 21; short_t = 22; ushort_t = 23
    # CoopMat types (all Accumulator use=2)
    coopmatF16 = 24; coopmatI16 = 25; coopmatU16 = 26
    ptr_elem = 27; matF16 = 28
    # Bitcast results
    result_f2i = 29; result_i2f = 30; result_f2u = 31; result_u2f = 32

    BOUND = 33

    out = b''
    out += word(0x07230203) + word(0x00010600) + word(0) + word(BOUND) + word(0)
    out += inst(OpCapability, 1) + inst(OpCapability, 6600)
    # Float16 capability for 16-bit types
    out += inst(OpCapability, 3)  # Float16
    out += inst(OpCapability, 22)  # Int16
    sw = str_words("GLSL.std.450")
    out += word(((1 + len(sw) + 1) << 16) | OpExtInstImport) + word(glsl_id) + b''.join(word(w) for w in sw)
    out += inst(OpMemoryModel, 0, 1)
    en = str_words("main")
    out += word(((2 + len(en) + 1) << 16) | OpEntryPoint) + word(5) + word(main_f) + b''.join(word(w) for w in en)
    out += inst(OpExecutionMode, main_f, 17, 16, 1, 1)
    for target, name in [(main_f, "main"), (data_var, "data"), (float_t, "float"),
                          (uint_t, "uint"), (half_t, "half"), (short_t, "short"),
                          (ushort_t, "ushort"),
                          (matF16, "matF16"), (result_f2i, "result_f2i"),
                          (result_i2f, "result_i2f"), (result_f2u, "result_f2u"),
                          (result_u2f, "result_u2f")]:
        nw = str_words(name)
        out += word(((1 + len(nw) + 1) << 16) | OpName) + word(target) + b''.join(word(w) for w in nw)
    out += inst(OpDecorate, block_t, DecorationBlock)
    out += inst(OpMemberDecorate, block_t, 0, DecorationOffset, 0)
    out += inst(OpDecorate, rtarray_t, DecorationArrayStride, 4)
    out += inst(OpDecorate, data_var, DecorationBinding, 0)
    out += inst(OpDecorate, data_var, DecorationDescriptorSet, 0)
    out += inst(OpTypeVoid, void_t)
    out += inst(OpTypeFloat, float_t, 32)
    out += inst(OpTypeFloat, half_t, 16)       # float16
    out += inst(OpTypeInt, uint_t, 32, 0)
    out += inst(OpTypeInt, short_t, 16, 1)     # int16 (signed)
    out += inst(OpTypeInt, ushort_t, 16, 0)    # uint16 (unsigned)
    out += inst(OpTypeVector, v2uint_t, uint_t, 2)
    out += inst(OpTypeFunction, func_t, void_t)
    out += inst(OpTypePointer, float_ptr_sb, StorageClassStorageBuffer, float_t)
    out += inst(OpTypeRuntimeArray, rtarray_t, float_t)
    out += inst(OpTypeStruct, block_t, rtarray_t)
    out += inst(OpTypePointer, block_ptr_t, StorageClassStorageBuffer, block_t)
    out += inst(OpConstant, uint_t, c16, 16)
    out += inst(OpConstant, uint_t, c16b, 16)
    out += inst(OpConstant, uint_t, c0, 0)
    out += inst(OpConstant, uint_t, c1, 1)
    out += inst(OpConstant, uint_t, c2, 2)
    out += inst(OpConstantComposite, v2uint_t, dim16, c16, c16b)
    out += inst(OpConstantComposite, v2uint_t, dim0, c0, c0)
    # CoopMat types with 16-bit component types (all Accumulator use=2)
    out += inst(OpTypeCooperativeMatrixHW, coopmatF16, half_t, c16, c16b, c2)
    out += inst(OpTypeCooperativeMatrixHW, coopmatI16, short_t, c16, c16b, c2)
    out += inst(OpTypeCooperativeMatrixHW, coopmatU16, ushort_t, c16, c16b, c2)
    out += inst(OpVariable, block_ptr_t, data_var, StorageClassStorageBuffer)
    out += inst(OpFunction, void_t, main_f, 0, func_t)
    out += inst(OpLabel, label)
    out += inst(OpAccessChain, float_ptr_sb, ptr_elem, data_var, c0, c0)
    # Load float16 coopmat
    out += inst(OpCooperativeMatrixLoadHW, coopmatF16, matF16, ptr_elem, dim16, dim0, c0)
    # Bitcast: float16 -> int16 (should emit float16BitsToInt16)
    out += inst(OpBitcast, coopmatI16, result_f2i, matF16)
    # Bitcast: int16 -> float16 (should emit int16BitsToFloat16)
    out += inst(OpBitcast, coopmatF16, result_i2f, result_f2i)
    # Bitcast: float16 -> uint16 (should emit float16BitsToUint16)
    out += inst(OpBitcast, coopmatU16, result_f2u, matF16)
    # Bitcast: uint16 -> float16 (should emit uint16BitsToFloat16)
    out += inst(OpBitcast, coopmatF16, result_u2f, result_f2u)
    # Store results
    out += inst(OpCooperativeMatrixStoreHW, ptr_elem, result_f2i, dim16, dim0, c0)
    out += inst(OpCooperativeMatrixStoreHW, ptr_elem, result_i2f, dim16, dim0, c0)
    out += inst(OpCooperativeMatrixStoreHW, ptr_elem, result_f2u, dim16, dim0, c0)
    out += inst(OpCooperativeMatrixStoreHW, ptr_elem, result_u2f, dim16, dim0, c0)
    out += inst(OpReturn)
    out += inst(OpFunctionEnd)
    data = bytearray(out)
    struct.pack_into('<I', data, 12, BOUND)
    with open(outfile, 'wb') as f:
        f.write(bytes(data))
    print(f"Generated: {len(data)} bytes -> {outfile}")

def gen_coopvec_type_test(outfile):
    """Generate test for OpTypeCooperativeVectorHW: declare coopvec type, load, and store."""
    # IDs
    void_t = 1; func_t = 2; main_f = 3; uint_t = 4; float_t = 5
    float_ptr_sb = 6; rtarray_t = 7; block_t = 8; block_ptr_t = 9
    data_var = 10; label = 11; glsl_id = 12
    c16 = 13; c0 = 14
    coopvec = 15  # coopvecHW type
    ptr_elem = 16; loaded = 17

    BOUND = 18

    out = b''
    out += word(0x07230203) + word(0x00010600) + word(0) + word(BOUND) + word(0)
    out += inst(OpCapability, 1) + inst(OpCapability, 6607)  # CooperativeVectorHW
    sw = str_words("GLSL.std.450")
    out += word(((1 + len(sw) + 1) << 16) | OpExtInstImport) + word(glsl_id) + b''.join(word(w) for w in sw)
    out += inst(OpMemoryModel, 0, 1)
    en = str_words("main")
    out += word(((2 + len(en) + 1) << 16) | OpEntryPoint) + word(5) + word(main_f) + b''.join(word(w) for w in en)
    out += inst(OpExecutionMode, main_f, 17, 16, 1, 1)
    for target, name in [(main_f, "main"), (data_var, "data"), (float_t, "float"), (uint_t, "uint"), (loaded, "vec")]:
        nw = str_words(name)
        out += word(((1 + len(nw) + 1) << 16) | OpName) + word(target) + b''.join(word(w) for w in nw)
    out += inst(OpDecorate, block_t, DecorationBlock)
    out += inst(OpMemberDecorate, block_t, 0, DecorationOffset, 0)
    out += inst(OpDecorate, rtarray_t, DecorationArrayStride, 4)
    out += inst(OpDecorate, data_var, DecorationBinding, 0)
    out += inst(OpDecorate, data_var, DecorationDescriptorSet, 0)
    # Types
    out += inst(OpTypeVoid, void_t)
    out += inst(OpTypeFloat, float_t, 32)
    out += inst(OpTypeInt, uint_t, 32, 0)
    out += inst(OpTypeFunction, func_t, void_t)
    out += inst(OpTypePointer, float_ptr_sb, StorageClassStorageBuffer, float_t)
    out += inst(OpTypeRuntimeArray, rtarray_t, float_t)
    out += inst(OpTypeStruct, block_t, rtarray_t)
    out += inst(OpTypePointer, block_ptr_t, StorageClassStorageBuffer, block_t)
    # Constants
    out += inst(OpConstant, uint_t, c16, 16)
    out += inst(OpConstant, uint_t, c0, 0)
    # %15 = OpTypeCooperativeVectorHW %float %16
    out += inst(OpTypeCooperativeVectorHW, coopvec, float_t, c16)
    # Variables
    out += inst(OpVariable, block_ptr_t, data_var, StorageClassStorageBuffer)
    # Function
    out += inst(OpFunction, void_t, main_f, 0, func_t)
    out += inst(OpLabel, label)
    # AccessChain to get pointer to first element
    out += inst(OpAccessChain, float_ptr_sb, ptr_elem, data_var, c0, c0)
    # Load coopvec
    out += inst(OpCooperativeVectorLoadHW, coopvec, loaded, ptr_elem)
    out += inst(OpReturn)
    out += inst(OpFunctionEnd)
    data = bytearray(out)
    struct.pack_into('<I', data, 12, BOUND)
    with open(outfile, 'wb') as f:
        f.write(bytes(data))
    print(f"Generated: {len(data)} bytes -> {outfile}")

def gen_coopvec_matmuladd_test(outfile):
    """Generate test for OpCooperativeVectorMatrixMulAddHW: load vec, load bias, muladd, store."""
    # IDs
    void_t = 1; func_t = 2; main_f = 3; uint_t = 4; float_t = 5
    float_ptr_sb = 6; rtarray_t = 7; block_t = 8; block_ptr_t = 9
    data_var = 10; label = 11; glsl_id = 12
    c16 = 13; c0 = 14; c1 = 15; c2 = 16
    coopvec = 17
    coopmatA = 18; coopmatB = 19; coopmatAcc = 20
    ptr_elem = 21; vec_loaded = 22; bias_loaded = 23
    matA = 24; matB = 25; matC = 26
    result_matmul = 27; result_muladd = 28
    v2uint_t = 29; dim16 = 30; dim0 = 31

    BOUND = 32

    out = b''
    out += word(0x07230203) + word(0x00010600) + word(0) + word(BOUND) + word(0)
    out += inst(OpCapability, 1) + inst(OpCapability, 6600) + inst(OpCapability, 6607)
    sw = str_words("GLSL.std.450")
    out += word(((1 + len(sw) + 1) << 16) | OpExtInstImport) + word(glsl_id) + b''.join(word(w) for w in sw)
    out += inst(OpMemoryModel, 0, 1)
    en = str_words("main")
    out += word(((2 + len(en) + 1) << 16) | OpEntryPoint) + word(5) + word(main_f) + b''.join(word(w) for w in en)
    out += inst(OpExecutionMode, main_f, 17, 16, 1, 1)
    for target, name in [(main_f, "main"), (data_var, "data"), (float_t, "float"),
                          (uint_t, "uint"), (vec_loaded, "vec"), (bias_loaded, "bias"),
                          (result_muladd, "result")]:
        nw = str_words(name)
        out += word(((1 + len(nw) + 1) << 16) | OpName) + word(target) + b''.join(word(w) for w in nw)
    out += inst(OpDecorate, block_t, DecorationBlock)
    out += inst(OpMemberDecorate, block_t, 0, DecorationOffset, 0)
    out += inst(OpDecorate, rtarray_t, DecorationArrayStride, 4)
    out += inst(OpDecorate, data_var, DecorationBinding, 0)
    out += inst(OpDecorate, data_var, DecorationDescriptorSet, 0)
    out += inst(OpTypeVoid, void_t)
    out += inst(OpTypeFloat, float_t, 32)
    out += inst(OpTypeInt, uint_t, 32, 0)
    out += inst(OpTypeVector, v2uint_t, uint_t, 2)
    out += inst(OpTypeFunction, func_t, void_t)
    out += inst(OpTypePointer, float_ptr_sb, StorageClassStorageBuffer, float_t)
    out += inst(OpTypeRuntimeArray, rtarray_t, float_t)
    out += inst(OpTypeStruct, block_t, rtarray_t)
    out += inst(OpTypePointer, block_ptr_t, StorageClassStorageBuffer, block_t)
    out += inst(OpConstant, uint_t, c16, 16)
    out += inst(OpConstant, uint_t, c0, 0)
    out += inst(OpConstant, uint_t, c1, 1)
    out += inst(OpConstant, uint_t, c2, 2)
    out += inst(OpConstantComposite, v2uint_t, dim16, c16, c16)
    out += inst(OpConstantComposite, v2uint_t, dim0, c0, c0)
    out += inst(OpTypeCooperativeVectorHW, coopvec, float_t, c16)
    out += inst(OpTypeCooperativeMatrixHW, coopmatA, float_t, c16, c16, c0)
    out += inst(OpTypeCooperativeMatrixHW, coopmatB, float_t, c16, c16, c1)
    out += inst(OpTypeCooperativeMatrixHW, coopmatAcc, float_t, c16, c16, c2)
    out += inst(OpVariable, block_ptr_t, data_var, StorageClassStorageBuffer)
    out += inst(OpFunction, void_t, main_f, 0, func_t)
    out += inst(OpLabel, label)
    out += inst(OpAccessChain, float_ptr_sb, ptr_elem, data_var, c0, c0)
    out += inst(OpCooperativeVectorLoadHW, coopvec, vec_loaded, ptr_elem)
    out += inst(OpCooperativeVectorLoadHW, coopvec, bias_loaded, ptr_elem)
    out += inst(OpCooperativeMatrixLoadHW, coopmatA, matA, ptr_elem, dim16, dim0, c0)
    out += inst(OpCooperativeMatrixLoadHW, coopmatB, matB, ptr_elem, dim16, dim0, c0)
    out += inst(OpCooperativeMatrixLoadHW, coopmatAcc, matC, ptr_elem, dim16, dim0, c0)
    out += inst(OpCooperativeVectorMatrixMulAddHW, coopvec, result_muladd, vec_loaded, matA, bias_loaded)
    out += inst(OpCooperativeVectorStoreHW, ptr_elem, result_muladd)
    out += inst(OpReturn)
    out += inst(OpFunctionEnd)
    data = bytearray(out)
    struct.pack_into('<I', data, 12, BOUND)
    with open(outfile, 'wb') as f:
        f.write(bytes(data))
    print(f"Generated: {len(data)} bytes -> {outfile}")

def gen_coopvec_matmul_test(outfile):
    """Generate test for OpCooperativeVectorMatrixMulHW: load vec, mul, store."""
    # IDs
    void_t = 1; func_t = 2; main_f = 3; uint_t = 4; float_t = 5
    float_ptr_sb = 6; rtarray_t = 7; block_t = 8; block_ptr_t = 9
    data_var = 10; label = 11; glsl_id = 12
    c16 = 13; c0 = 14
    coopvec = 15; coopmatA = 16
    ptr_elem = 17; vec_loaded = 18; matA = 19
    result = 20; v2uint_t = 21; dim16 = 22; dim0 = 23

    BOUND = 24

    out = b''
    out += word(0x07230203) + word(0x00010600) + word(0) + word(BOUND) + word(0)
    out += inst(OpCapability, 1) + inst(OpCapability, 6600) + inst(OpCapability, 6607)
    sw = str_words("GLSL.std.450")
    out += word(((1 + len(sw) + 1) << 16) | OpExtInstImport) + word(glsl_id) + b''.join(word(w) for w in sw)
    out += inst(OpMemoryModel, 0, 1)
    en = str_words("main")
    out += word(((2 + len(en) + 1) << 16) | OpEntryPoint) + word(5) + word(main_f) + b''.join(word(w) for w in en)
    out += inst(OpExecutionMode, main_f, 17, 16, 1, 1)
    for target, name in [(main_f, "main"), (data_var, "data"), (float_t, "float"),
                          (uint_t, "uint"), (vec_loaded, "vec"), (result, "result")]:
        nw = str_words(name)
        out += word(((1 + len(nw) + 1) << 16) | OpName) + word(target) + b''.join(word(w) for w in nw)
    out += inst(OpDecorate, block_t, DecorationBlock)
    out += inst(OpMemberDecorate, block_t, 0, DecorationOffset, 0)
    out += inst(OpDecorate, rtarray_t, DecorationArrayStride, 4)
    out += inst(OpDecorate, data_var, DecorationBinding, 0)
    out += inst(OpDecorate, data_var, DecorationDescriptorSet, 0)
    out += inst(OpTypeVoid, void_t)
    out += inst(OpTypeFloat, float_t, 32)
    out += inst(OpTypeInt, uint_t, 32, 0)
    out += inst(OpTypeVector, v2uint_t, uint_t, 2)
    out += inst(OpTypeFunction, func_t, void_t)
    out += inst(OpTypePointer, float_ptr_sb, StorageClassStorageBuffer, float_t)
    out += inst(OpTypeRuntimeArray, rtarray_t, float_t)
    out += inst(OpTypeStruct, block_t, rtarray_t)
    out += inst(OpTypePointer, block_ptr_t, StorageClassStorageBuffer, block_t)
    out += inst(OpConstant, uint_t, c16, 16)
    out += inst(OpConstant, uint_t, c0, 0)
    out += inst(OpConstantComposite, v2uint_t, dim16, c16, c16)
    out += inst(OpConstantComposite, v2uint_t, dim0, c0, c0)
    out += inst(OpTypeCooperativeVectorHW, coopvec, float_t, c16)
    out += inst(OpTypeCooperativeMatrixHW, coopmatA, float_t, c16, c16, c0)
    out += inst(OpVariable, block_ptr_t, data_var, StorageClassStorageBuffer)
    out += inst(OpFunction, void_t, main_f, 0, func_t)
    out += inst(OpLabel, label)
    out += inst(OpAccessChain, float_ptr_sb, ptr_elem, data_var, c0, c0)
    out += inst(OpCooperativeVectorLoadHW, coopvec, vec_loaded, ptr_elem)
    out += inst(OpCooperativeMatrixLoadHW, coopmatA, matA, ptr_elem, dim16, dim0, c0)
    out += inst(OpCooperativeVectorMatrixMulHW, coopvec, result, vec_loaded, matA)
    out += inst(OpCooperativeVectorStoreHW, ptr_elem, result)
    out += inst(OpReturn)
    out += inst(OpFunctionEnd)
    data = bytearray(out)
    struct.pack_into('<I', data, 12, BOUND)
    with open(outfile, 'wb') as f:
        f.write(bytes(data))
    print(f"Generated: {len(data)} bytes -> {outfile}")

def gen_coopvec_length_test(outfile):
    """Generate test for coopvecHW length() pattern.

    Mirrors glslang's output for: int len = v.length();
    In SPIR-V this becomes: Bitcast(uint_constant_N) -> int
    Also tests: coopvecHW<float16_t, 2> f162 = coopvecHW<float16_t, 2>(v7.length());
    In SPIR-V: Bitcast(uint_constant) -> ConvertSToF -> CompositeConstructReplicate
    """
    # IDs
    void_t = 1; func_t = 2; main_f = 3; uint_t = 4; float_t = 5
    float_ptr_sb = 6; rtarray_t = 7; block_t = 8; block_ptr_t = 9
    data_var = 10; label = 11; glsl_id = 12
    c16 = 13; c0 = 14; c5 = 15; c20 = 16
    coopvec5 = 17   # coopvecHW<float, 5>
    coopvec20 = 18  # coopvecHW<float, 20>
    int_t = 19; int_ptr_sb = 20; rtarray_int = 21; out_block_t = 22; out_block_ptr_t = 23
    out_var = 24; ptr_out0 = 25; ptr_out1 = 26
    # Results
    len_int5 = 27   # int(Bitcast(uint(5)))
    len_int20 = 28  # int(Bitcast(uint(20)))
    # Second pattern: length() used in constructor
    half_t = 29
    c2 = 30
    coopvec_f16_2 = 31  # coopvecHW<float16_t, 2>
    len_int20_b = 32    # another Bitcast(uint(20))
    len_f16 = 33        # ConvertSToF(int(20)) -> float16_t
    f162 = 34           # CompositeConstructReplicate(float16_t(20))

    BOUND = 35

    out = b''
    out += word(0x07230203) + word(0x00010600) + word(0) + word(BOUND) + word(0)
    out += inst(OpCapability, 1) + inst(OpCapability, 6607)
    out += inst(OpCapability, 3)  # Float16 for half_t
    sw = str_words("GLSL.std.450")
    out += word(((1 + len(sw) + 1) << 16) | OpExtInstImport) + word(glsl_id) + b''.join(word(w) for w in sw)
    out += inst(OpMemoryModel, 0, 1)
    en = str_words("main")
    out += word(((2 + len(en) + 1) << 16) | OpEntryPoint) + word(5) + word(main_f) + b''.join(word(w) for w in en)
    out += inst(OpExecutionMode, main_f, 17, 16, 1, 1)
    for target, name in [(main_f, "main"), (data_var, "data"), (float_t, "float"),
                          (uint_t, "uint"), (int_t, "int"), (half_t, "float16_t"),
                          (len_int5, "len5"), (len_int20, "len20"), (f162, "f162")]:
        nw = str_words(name)
        out += word(((1 + len(nw) + 1) << 16) | OpName) + word(target) + b''.join(word(w) for w in nw)
    # Annotations - output buffer
    out += inst(OpDecorate, block_t, DecorationBlock)
    out += inst(OpMemberDecorate, block_t, 0, DecorationOffset, 0)
    out += inst(OpDecorate, rtarray_t, DecorationArrayStride, 4)
    out += inst(OpDecorate, data_var, DecorationBinding, 0)
    out += inst(OpDecorate, data_var, DecorationDescriptorSet, 0)
    out += inst(OpDecorate, out_block_t, DecorationBlock)
    out += inst(OpMemberDecorate, out_block_t, 0, DecorationOffset, 0)
    out += inst(OpDecorate, rtarray_int, DecorationArrayStride, 4)
    out += inst(OpDecorate, out_var, DecorationBinding, 1)
    out += inst(OpDecorate, out_var, DecorationDescriptorSet, 0)
    # Types
    out += inst(OpTypeVoid, void_t)
    out += inst(OpTypeFloat, float_t, 32)
    out += inst(OpTypeFloat, half_t, 16)
    out += inst(OpTypeInt, uint_t, 32, 0)
    out += inst(OpTypeInt, int_t, 32, 1)
    out += inst(OpTypeFunction, func_t, void_t)
    out += inst(OpTypePointer, float_ptr_sb, StorageClassStorageBuffer, float_t)
    out += inst(OpTypePointer, int_ptr_sb, StorageClassStorageBuffer, int_t)
    out += inst(OpTypeRuntimeArray, rtarray_t, float_t)
    out += inst(OpTypeRuntimeArray, rtarray_int, int_t)
    out += inst(OpTypeStruct, block_t, rtarray_t)
    out += inst(OpTypeStruct, out_block_t, rtarray_int)
    out += inst(OpTypePointer, block_ptr_t, StorageClassStorageBuffer, block_t)
    out += inst(OpTypePointer, out_block_ptr_t, StorageClassStorageBuffer, out_block_t)
    # Constants
    out += inst(OpConstant, uint_t, c16, 16)
    out += inst(OpConstant, uint_t, c0, 0)
    out += inst(OpConstant, uint_t, c5, 5)
    out += inst(OpConstant, uint_t, c20, 20)
    out += inst(OpConstant, uint_t, c2, 2)
    # CoopVec types
    out += inst(OpTypeCooperativeVectorHW, coopvec5, float_t, c5)    # coopvecHW<float, 5>
    out += inst(OpTypeCooperativeVectorHW, coopvec20, float_t, c20)  # coopvecHW<float, 20>
    out += inst(OpTypeCooperativeVectorHW, coopvec_f16_2, half_t, c2) # coopvecHW<float16_t, 2>
    # Variables
    out += inst(OpVariable, block_ptr_t, data_var, StorageClassStorageBuffer)
    out += inst(OpVariable, out_block_ptr_t, out_var, StorageClassStorageBuffer)
    # Function body
    out += inst(OpFunction, void_t, main_f, 0, func_t)
    out += inst(OpLabel, label)
    # AccessChain for output
    out += inst(OpAccessChain, int_ptr_sb, ptr_out0, out_var, c0, c0)
    out += inst(OpAccessChain, int_ptr_sb, ptr_out1, out_var, c0, c16)
    # Pattern 1: int len = v.length() where v is coopvec<float, 5>
    # glslang emits: Bitcast(uint(5)) -> int(5)
    out += inst(OpBitcast, int_t, len_int5, c5)
    # Pattern 2: int len = v.length() where v is coopvec<float, 20>
    out += inst(OpBitcast, int_t, len_int20, c20)
    # Store results
    out += inst(OpStore, ptr_out0, len_int5)
    out += inst(OpStore, ptr_out1, len_int20)
    out += inst(OpReturn)
    out += inst(OpFunctionEnd)
    data = bytearray(out)
    struct.pack_into('<I', data, 12, BOUND)
    with open(outfile, 'wb') as f:
        f.write(bytes(data))
    print(f"Generated: {len(data)} bytes -> {outfile}")

def gen_coopvec_convert_test(outfile):
    """Generate test for coopvecHW conversion: float->int (ConvertFToS), int->float (ConvertSToF), bitcast."""
    # IDs
    void_t = 1; func_t = 2; main_f = 3; uint_t = 4; float_t = 5; int_t = 6
    float_ptr_sb = 7; rtarray_t = 8; block_t = 9; block_ptr_t = 10
    data_var = 11; label = 12; glsl_id = 13
    c16 = 14; c0 = 15
    coopvecF = 16; coopvecI = 17
    ptr_elem = 18; vecF = 19
    result_ftos = 20; result_stof = 21
    result_bitcast = 22

    BOUND = 23

    out = b''
    out += word(0x07230203) + word(0x00010600) + word(0) + word(BOUND) + word(0)
    out += inst(OpCapability, 1) + inst(OpCapability, 6607)
    sw = str_words("GLSL.std.450")
    out += word(((1 + len(sw) + 1) << 16) | OpExtInstImport) + word(glsl_id) + b''.join(word(w) for w in sw)
    out += inst(OpMemoryModel, 0, 1)
    en = str_words("main")
    out += word(((2 + len(en) + 1) << 16) | OpEntryPoint) + word(5) + word(main_f) + b''.join(word(w) for w in en)
    out += inst(OpExecutionMode, main_f, 17, 16, 1, 1)
    for target, name in [(main_f, "main"), (data_var, "data"), (float_t, "float"),
                          (int_t, "int"), (uint_t, "uint"),
                          (vecF, "vecF"), (result_ftos, "result_ftos"),
                          (result_stof, "result_stof"), (result_bitcast, "result_bitcast")]:
        nw = str_words(name)
        out += word(((1 + len(nw) + 1) << 16) | OpName) + word(target) + b''.join(word(w) for w in nw)
    out += inst(OpDecorate, block_t, DecorationBlock)
    out += inst(OpMemberDecorate, block_t, 0, DecorationOffset, 0)
    out += inst(OpDecorate, rtarray_t, DecorationArrayStride, 4)
    out += inst(OpDecorate, data_var, DecorationBinding, 0)
    out += inst(OpDecorate, data_var, DecorationDescriptorSet, 0)
    out += inst(OpTypeVoid, void_t)
    out += inst(OpTypeFloat, float_t, 32)
    out += inst(OpTypeInt, uint_t, 32, 0)
    out += inst(OpTypeInt, int_t, 32, 1)
    out += inst(OpTypeFunction, func_t, void_t)
    out += inst(OpTypePointer, float_ptr_sb, StorageClassStorageBuffer, float_t)
    out += inst(OpTypeRuntimeArray, rtarray_t, float_t)
    out += inst(OpTypeStruct, block_t, rtarray_t)
    out += inst(OpTypePointer, block_ptr_t, StorageClassStorageBuffer, block_t)
    out += inst(OpConstant, uint_t, c16, 16)
    out += inst(OpConstant, uint_t, c0, 0)
    out += inst(OpTypeCooperativeVectorHW, coopvecF, float_t, c16)
    out += inst(OpTypeCooperativeVectorHW, coopvecI, int_t, c16)
    out += inst(OpVariable, block_ptr_t, data_var, StorageClassStorageBuffer)
    out += inst(OpFunction, void_t, main_f, 0, func_t)
    out += inst(OpLabel, label)
    out += inst(OpAccessChain, float_ptr_sb, ptr_elem, data_var, c0, c0)
    out += inst(OpCooperativeVectorLoadHW, coopvecF, vecF, ptr_elem)
    # ConvertFToS: float -> int
    out += inst(OpConvertFToS, coopvecI, result_ftos, vecF)
    # ConvertSToF: int -> float
    out += inst(OpConvertSToF, coopvecF, result_stof, result_ftos)
    # Bitcast: float -> int (reinterpret)
    out += inst(OpBitcast, coopvecI, result_bitcast, vecF)
    out += inst(OpCooperativeVectorStoreHW, ptr_elem, result_stof)
    out += inst(OpCooperativeVectorStoreHW, ptr_elem, result_ftos)
    out += inst(OpCooperativeVectorStoreHW, ptr_elem, result_bitcast)
    out += inst(OpReturn)
    out += inst(OpFunctionEnd)
    data = bytearray(out)
    struct.pack_into('<I', data, 12, BOUND)
    with open(outfile, 'wb') as f:
        f.write(bytes(data))
    print(f"Generated: {len(data)} bytes -> {outfile}")

def gen_coopvec_bitcast32_test(outfile):
    """Generate test for coopvecHW 32-bit bitcast: float32<->uint32, float32<->int32."""
    # IDs
    void_t = 1; func_t = 2; main_f = 3; uint_t = 4; float_t = 5; int_t = 6
    float_ptr_sb = 7; rtarray_t = 8; block_t = 9; block_ptr_t = 10
    data_var = 11; label = 12; glsl_id = 13
    c16 = 14; c0 = 15
    coopvecF32 = 16; coopvecI32 = 17; coopvecU32 = 18
    ptr_elem = 19; vecF = 20
    result_f2i = 21; result_i2f = 22; result_f2u = 23; result_u2f = 24

    BOUND = 25

    out = b''
    out += word(0x07230203) + word(0x00010600) + word(0) + word(BOUND) + word(0)
    out += inst(OpCapability, 1) + inst(OpCapability, 6607)
    sw = str_words("GLSL.std.450")
    out += word(((1 + len(sw) + 1) << 16) | OpExtInstImport) + word(glsl_id) + b''.join(word(w) for w in sw)
    out += inst(OpMemoryModel, 0, 1)
    en = str_words("main")
    out += word(((2 + len(en) + 1) << 16) | OpEntryPoint) + word(5) + word(main_f) + b''.join(word(w) for w in en)
    out += inst(OpExecutionMode, main_f, 17, 16, 1, 1)
    for target, name in [(main_f, "main"), (data_var, "data"), (float_t, "float"),
                          (uint_t, "uint"), (int_t, "int"),
                          (vecF, "vecF"), (result_f2i, "result_f2i"),
                          (result_i2f, "result_i2f"), (result_f2u, "result_f2u"),
                          (result_u2f, "result_u2f")]:
        nw = str_words(name)
        out += word(((1 + len(nw) + 1) << 16) | OpName) + word(target) + b''.join(word(w) for w in nw)
    out += inst(OpDecorate, block_t, DecorationBlock)
    out += inst(OpMemberDecorate, block_t, 0, DecorationOffset, 0)
    out += inst(OpDecorate, rtarray_t, DecorationArrayStride, 4)
    out += inst(OpDecorate, data_var, DecorationBinding, 0)
    out += inst(OpDecorate, data_var, DecorationDescriptorSet, 0)
    out += inst(OpTypeVoid, void_t)
    out += inst(OpTypeFloat, float_t, 32)
    out += inst(OpTypeInt, uint_t, 32, 0)
    out += inst(OpTypeInt, int_t, 32, 1)
    out += inst(OpTypeFunction, func_t, void_t)
    out += inst(OpTypePointer, float_ptr_sb, StorageClassStorageBuffer, float_t)
    out += inst(OpTypeRuntimeArray, rtarray_t, float_t)
    out += inst(OpTypeStruct, block_t, rtarray_t)
    out += inst(OpTypePointer, block_ptr_t, StorageClassStorageBuffer, block_t)
    out += inst(OpConstant, uint_t, c16, 16)
    out += inst(OpConstant, uint_t, c0, 0)
    out += inst(OpTypeCooperativeVectorHW, coopvecF32, float_t, c16)
    out += inst(OpTypeCooperativeVectorHW, coopvecI32, int_t, c16)
    out += inst(OpTypeCooperativeVectorHW, coopvecU32, uint_t, c16)
    out += inst(OpVariable, block_ptr_t, data_var, StorageClassStorageBuffer)
    out += inst(OpFunction, void_t, main_f, 0, func_t)
    out += inst(OpLabel, label)
    out += inst(OpAccessChain, float_ptr_sb, ptr_elem, data_var, c0, c0)
    out += inst(OpCooperativeVectorLoadHW, coopvecF32, vecF, ptr_elem)
    # Bitcast: float32 -> int32 (should emit floatBitsToInt)
    out += inst(OpBitcast, coopvecI32, result_f2i, vecF)
    # Bitcast: int32 -> float32 (should emit intBitsToFloat)
    out += inst(OpBitcast, coopvecF32, result_i2f, result_f2i)
    # Bitcast: float32 -> uint32 (should emit floatBitsToUint)
    out += inst(OpBitcast, coopvecU32, result_f2u, vecF)
    # Bitcast: uint32 -> float32 (should emit uintBitsToFloat)
    out += inst(OpBitcast, coopvecF32, result_u2f, result_f2u)
    out += inst(OpCooperativeVectorStoreHW, ptr_elem, result_f2i)
    out += inst(OpCooperativeVectorStoreHW, ptr_elem, result_i2f)
    out += inst(OpCooperativeVectorStoreHW, ptr_elem, result_f2u)
    out += inst(OpCooperativeVectorStoreHW, ptr_elem, result_u2f)
    out += inst(OpReturn)
    out += inst(OpFunctionEnd)
    data = bytearray(out)
    struct.pack_into('<I', data, 12, BOUND)
    with open(outfile, 'wb') as f:
        f.write(bytes(data))
    print(f"Generated: {len(data)} bytes -> {outfile}")

if __name__ == '__main__':
    import os
    outfile = sys.argv[1] if len(sys.argv) > 1 else 'test_hw_length.spv'
    base = os.path.basename(outfile)
    if 'const_store' in base:
        gen_const_store_test(outfile)
    elif 'bitcast16' in base:
        gen_bitcast16_test(outfile)
    elif 'bitcast32' in base and 'coopvec' not in base:
        gen_bitcast32_test(outfile)
    elif 'coopvec_bitcast32' in base:
        gen_coopvec_bitcast32_test(outfile)
    elif 'coopvec_convert' in base:
        gen_coopvec_convert_test(outfile)
    elif 'convert' in base:
        gen_convert_test(outfile)
    elif 'mul_null' in base:
        gen_mul_null_test(outfile)
    elif 'reduce' in base:
        gen_reduce_test(outfile)
    elif 'coopvec_length' in base:
        gen_coopvec_length_test(outfile)
    elif 'coopvec_matmuladd' in base:
        gen_coopvec_matmuladd_test(outfile)
    elif 'coopvec_matmul' in base:
        gen_coopvec_matmul_test(outfile)
    elif 'muladd' in base:
        gen_muladd_test(outfile)
    elif 'mul_' in base or base == 'test_hw_mul.spv':
        gen_mul_test(outfile)
    elif 'store' in base and 'const' not in base:
        gen_store_test(outfile)
    elif 'coopvec' in base:
        gen_coopvec_type_test(outfile)
    else:
        gen_length_test(outfile)
