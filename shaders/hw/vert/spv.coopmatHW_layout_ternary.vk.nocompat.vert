#version 450 core
#extension GL_KHR_memory_scope_semantics : enable
#extension GL_HW_neural_shader : enable
#extension GL_EXT_shader_explicit_arithmetic_types : enable

layout(set = 0, binding = 0) buffer Buf {
    float16_t data[];
} buf;

layout(constant_id = 0) const bool specColMajor = false;

void main()
{
    gl_Position = vec4(0.0);

    const ivec2 shape = ivec2(16, 16);
    const ivec2 zeroOffset = ivec2(0, 0);
    bool cond = gl_VertexIndex == 0;

    coopmatHW<float16_t, 16, 16> A, B, C;

    coopMatLoadHW(A, buf.data, shape, zeroOffset, gl_CooperativeMatrixLayoutRowMajorHW);

    coopMatLoadHW(B, buf.data, shape, zeroOffset, specColMajor ? gl_CooperativeMatrixLayoutColumnMajorHW : gl_CooperativeMatrixLayoutRowMajorHW);

    coopMatLoadHW(C, buf.data, shape, zeroOffset, cond ? gl_CooperativeMatrixLayoutColumnMajorHW : gl_CooperativeMatrixLayoutRowMajorHW);

    coopMatStoreHW(C, buf.data, shape, zeroOffset, cond ? gl_CooperativeMatrixLayoutRowMajorHW : gl_CooperativeMatrixLayoutColumnMajorHW);
}
