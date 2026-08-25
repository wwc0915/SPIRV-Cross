#version 450
#if defined(GL_AMD_gpu_shader_half_float)
#extension GL_AMD_gpu_shader_half_float : require
#elif defined(GL_NV_gpu_shader5)
#extension GL_NV_gpu_shader5 : require
#else
#error No extension available for FP16.
#endif
#extension GL_HW_neural_shader : require

#ifndef SPIRV_CROSS_CONSTANT_ID_0
#define SPIRV_CROSS_CONSTANT_ID_0 false
#endif
const bool specColMajor = SPIRV_CROSS_CONSTANT_ID_0;
const int _49 = int(specColMajor);

layout(binding = 0, std430) buffer Buf
{
    float16_t data[];
} buf;

void main()
{
    gl_Position = vec4(0.0);
    bool cond = gl_VertexID == 0;
    coopmatHW<float16_t, 16u, 16u> _42;
    coopMatLoadHW(_42, buf.data, ivec2(16), ivec2(0), gl_CooperativeMatrixLayoutRowMajorHW);
    coopmatHW<float16_t, 16u, 16u> tempArg = _42;
    coopmatHW<float16_t, 16u, 16u> A = tempArg;
    coopmatHW<float16_t, 16u, 16u> _50;
    coopMatLoadHW(_50, buf.data, ivec2(16), ivec2(0), specColMajor ? gl_CooperativeMatrixLayoutColumnMajorHW : gl_CooperativeMatrixLayoutRowMajorHW);
    coopmatHW<float16_t, 16u, 16u> tempArg_1 = _50;
    coopmatHW<float16_t, 16u, 16u> B = tempArg_1;
    coopmatHW<float16_t, 16u, 16u> _57;
    coopMatLoadHW(_57, buf.data, ivec2(16), ivec2(0), int(cond));
    coopmatHW<float16_t, 16u, 16u> tempArg_2 = _57;
    coopmatHW<float16_t, 16u, 16u> C = tempArg_2;
    coopMatStoreHW(C, buf.data, ivec2(16), ivec2(0), cond ? 0 : 1);
}

