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
OpTypeStruct = 30; OpTypeRuntimeArray = 29; OpTypeCooperativeMatrixHW = 6501
OpVariable = 59; OpFunction = 54; OpFunctionEnd = 56; OpLabel = 248
OpReturn = 253; OpConstant = 43; OpConstantComposite = 44; OpAccessChain = 65
OpCooperativeMatrixLoadHW = 6502; OpCooperativeMatrixLengthHW = 6500
OpCooperativeMatrixStoreHW = 6503; OpCooperativeMatrixMulAddHW = 6504
OpCooperativeMatrixReduceHW = 6505
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

if __name__ == '__main__':
    import os
    outfile = sys.argv[1] if len(sys.argv) > 1 else 'test_hw_length.spv'
    base = os.path.basename(outfile)
    if 'const_store' in base:
        gen_const_store_test(outfile)
    elif 'reduce' in base:
        gen_reduce_test(outfile)
    elif 'muladd' in base:
        gen_muladd_test(outfile)
    elif 'mul_' in base or base == 'test_hw_mul.spv':
        gen_mul_test(outfile)
    elif 'store' in base:
        gen_store_test(outfile)
    else:
        gen_length_test(outfile)
