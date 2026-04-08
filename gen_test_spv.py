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
OpStore = 62; OpLoad = 61

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

    # Output buffer for length results
    uint_ptr_sb = 27; rtarray_uint = 28; out_block_t = 29; out_block_ptr_t = 30
    out_var = 31; ptr_out0 = 32; ptr_out1 = 33

    BOUND = 34

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
                          (uint_t, "uint"), (lenA, "lenA"), (lenB, "lenB"),
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
    out += inst(OpDecorate, rtarray_uint, DecorationArrayStride, 4)
    out += inst(OpDecorate, out_var, DecorationBinding, 1)
    out += inst(OpDecorate, out_var, DecorationDescriptorSet, 0)
    # Types
    out += inst(OpTypeVoid, void_t)
    out += inst(OpTypeFloat, float_t, 32)
    out += inst(OpTypeInt, uint_t, 32, 0)
    out += inst(OpTypeVector, v2uint_t, uint_t, 2)
    out += inst(OpTypeFunction, func_t, void_t)
    out += inst(OpTypePointer, float_ptr_sb, StorageClassStorageBuffer, float_t)
    out += inst(OpTypePointer, uint_ptr_sb, StorageClassStorageBuffer, uint_t)
    out += inst(OpTypeRuntimeArray, rtarray_t, float_t)
    out += inst(OpTypeRuntimeArray, rtarray_uint, uint_t)
    out += inst(OpTypeStruct, block_t, rtarray_t)
    out += inst(OpTypeStruct, out_block_t, rtarray_uint)
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
    out += inst(OpAccessChain, uint_ptr_sb, ptr_out0, out_var, c0, c0)
    out += inst(OpAccessChain, uint_ptr_sb, ptr_out1, out_var, c0, c1)
    # Load matrices
    out += inst(OpCooperativeMatrixLoadHW, coopmatA, matA, ptr_elem, dim16, dim0, c0)
    out += inst(OpCooperativeMatrixLoadHW, coopmatB, matB, ptr_elem, dim16, dim0, c1)
    # OpCooperativeMatrixLengthHW
    out += inst(OpCooperativeMatrixLengthHW, uint_t, lenA, coopmatA)
    out += inst(OpCooperativeMatrixLengthHW, uint_t, lenB, coopmatB)
    # Store length results to output buffer
    out += inst(OpStore, ptr_out0, lenA)
    out += inst(OpStore, ptr_out1, lenB)
    out += inst(OpReturn)
    out += inst(OpFunctionEnd)
    # Update bound
    data = bytearray(out)
    struct.pack_into('<I', data, 12, BOUND)
    with open(outfile, 'wb') as f:
        f.write(bytes(data))
    print(f"Generated: {len(data)} bytes -> {outfile}")

if __name__ == '__main__':
    outfile = sys.argv[1] if len(sys.argv) > 1 else 'test_hw_length.spv'
    gen_length_test(outfile)
