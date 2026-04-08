#!/usr/bin/env python3
"""
Generate a minimal valid SPIR-V binary for OpCooperativeMatrixLoadHW testing.
Uses a proper block struct with runtime array, matching standard SSBO patterns.
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
OpEntryPoint = 15; OpExecutionMode = 16; OpName = 5; OpMemberName = 6
OpDecorate = 71; OpMemberDecorate = 72; OpTypeVoid = 19; OpTypeFloat = 22
OpTypeInt = 21; OpTypeVector = 23; OpTypeFunction = 33; OpTypePointer = 32
OpTypeStruct = 30; OpTypeRuntimeArray = 29; OpTypeCooperativeMatrixHW = 6501
OpVariable = 59; OpFunction = 54; OpFunctionEnd = 56; OpLabel = 248
OpReturn = 253; OpConstant = 43; OpConstantComposite = 44; OpAccessChain = 65
OpCooperativeMatrixLoadHW = 6502

StorageClassStorageBuffer = 12
DecorationBlock = 2; DecorationBinding = 33; DecorationDescriptorSet = 34
DecorationArrayStride = 35; DecorationOffset = 35

# --- ID allocation ---
# Types
void_t = 1; func_t = 2; main_f = 3; uint_t = 4; v2uint_t = 5; float_t = 6
float_ptr_sb = 7;    # OpTypePointer StorageBuffer float (for AccessChain results)
rtarray_t = 8;       # OpTypeRuntimeArray float
block_t = 9;         # OpTypeStruct { rtarray }
block_ptr_t = 10;    # OpTypePointer StorageBuffer block
data_var = 11;       # OpVariable
label = 12
# Constants
c16 = 13; c16b = 14; c0 = 15; c1 = 16
dim16 = 17; dim0 = 18
# CoopMat types
coopmatA = 19; coopmatB = 20
# AccessChain result & load results
ptr_elem = 21; matA = 22; matB = 23
# ExtInstImport
glsl_id = 24
BOUND = 25

out = b''

# Header
out += word(0x07230203) + word(0x00010600) + word(0) + word(BOUND) + word(0)

# Capabilities
out += inst(OpCapability, 1)      # Shader
out += inst(OpCapability, 6600)   # CooperativeMatrixHW

# ExtInstImport
sw = str_words("GLSL.std.450")
out += word(((1 + len(sw) + 1) << 16) | OpExtInstImport) + word(glsl_id) + b''.join(word(w) for w in sw)

# MemoryModel Logical GLSL450
out += inst(OpMemoryModel, 0, 1)

# EntryPoint GLCompute
en = str_words("main")
out += word(((2 + len(en) + 1) << 16) | OpEntryPoint) + word(5) + word(main_f) + b''.join(word(w) for w in en)

# ExecutionMode LocalSize 16 1 1
out += inst(OpExecutionMode, main_f, 17, 16, 1, 1)

# Debug names
for target, name in [(main_f, "main"), (data_var, "data"), (float_t, "float"),
                      (uint_t, "uint"), (block_t, "Block"), (rtarray_t, "values")]:
    nw = str_words(name)
    out += word(((1 + len(nw) + 1) << 16) | OpName) + word(target) + b''.join(word(w) for w in nw)

# Member name: Block.values (optional, skip to avoid encoding issues)
# mn = str_words("values")
# out += word(((2 + len(mn)) << 16) | OpMemberName) + word(block_t) + word(0) + b''.join(word(w) for w in mn)

# --- Annotations ---
out += inst(OpDecorate, block_t, DecorationBlock)
out += inst(OpMemberDecorate, block_t, 0, DecorationOffset, 0)
out += inst(OpDecorate, rtarray_t, DecorationArrayStride, 4)
out += inst(OpDecorate, data_var, DecorationBinding, 0)
out += inst(OpDecorate, data_var, DecorationDescriptorSet, 0)

# --- Types ---
out += inst(OpTypeVoid, void_t)
out += inst(OpTypeFloat, float_t, 32)
out += inst(OpTypeInt, uint_t, 32, 0)
out += inst(OpTypeVector, v2uint_t, uint_t, 2)
out += inst(OpTypeFunction, func_t, void_t)
out += inst(OpTypePointer, float_ptr_sb, StorageClassStorageBuffer, float_t)
out += inst(OpTypeRuntimeArray, rtarray_t, float_t)
out += inst(OpTypeStruct, block_t, rtarray_t)
out += inst(OpTypePointer, block_ptr_t, StorageClassStorageBuffer, block_t)

# --- Constants (must come before variables) ---
out += inst(OpConstant, uint_t, c16, 16)
out += inst(OpConstant, uint_t, c16b, 16)
out += inst(OpConstant, uint_t, c0, 0)
out += inst(OpConstant, uint_t, c1, 1)
out += inst(OpConstantComposite, v2uint_t, dim16, c16, c16b)  # vec2(16, 16)
out += inst(OpConstantComposite, v2uint_t, dim0, c0, c0)      # vec2(0, 0)

# --- CoopMat types ---
out += inst(OpTypeCooperativeMatrixHW, coopmatA, float_t, c16, c16b, c0)  # MatrixA
out += inst(OpTypeCooperativeMatrixHW, coopmatB, float_t, c16, c16b, c1)  # MatrixB

# --- Variables (after all types and constants) ---
out += inst(OpVariable, block_ptr_t, data_var, StorageClassStorageBuffer)

# --- Function body ---
out += inst(OpFunction, void_t, main_f, 0, func_t)
out += inst(OpLabel, label)

# AccessChain: %ptr_elem = OpAccessChain %float_ptr_sb %data_var %c0 %c0
# (data.values[0] — index into struct member 0, then index 0 in the array)
out += inst(OpAccessChain, float_ptr_sb, ptr_elem, data_var, c0, c0)

# Load cooperative matrices: OpCooperativeMatrixLoadHW %result_type %result %ptr %shape %offset %layout
out += inst(OpCooperativeMatrixLoadHW, coopmatA, matA, ptr_elem, dim16, dim0, c0)
out += inst(OpCooperativeMatrixLoadHW, coopmatB, matB, ptr_elem, dim16, dim0, c1)

out += inst(OpReturn)
out += inst(OpFunctionEnd)

# Update bound
data = bytearray(out)
struct.pack_into('<I', data, 12, BOUND)

outfile = sys.argv[1] if len(sys.argv) > 1 else 'test_hw_load.spv'
with open(outfile, 'wb') as f:
    f.write(bytes(data))
print(f"Generated: {len(data)} bytes -> {outfile}")
