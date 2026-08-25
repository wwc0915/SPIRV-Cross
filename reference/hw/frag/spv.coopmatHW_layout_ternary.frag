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
const int _48 = int(specColMajor);

layout(binding = 0, std430) buffer Buf
{
    float16_t data[];
} buf;

layout(location = 0) out vec4 outColor;

void main()
{
    outColor = vec4(1.0);
    bool cond = gl_FragCoord.x > 0.0;
    coopmatHW<float16_t, 16u, 16u> _41;
    coopMatLoadHW(_41, buf.data, ivec2(16), ivec2(0), gl_CooperativeMatrixLayoutRowMajorHW);
    coopmatHW<float16_t, 16u, 16u> tempArg = _41;
    coopmatHW<float16_t, 16u, 16u> A = tempArg;
    coopmatHW<float16_t, 16u, 16u> _49;
    coopMatLoadHW(_49, buf.data, ivec2(16), ivec2(0), specColMajor ? gl_CooperativeMatrixLayoutColumnMajorHW : gl_CooperativeMatrixLayoutRowMajorHW);
    coopmatHW<float16_t, 16u, 16u> tempArg_1 = _49;
    coopmatHW<float16_t, 16u, 16u> B = tempArg_1;
    coopmatHW<float16_t, 16u, 16u> _56;
    coopMatLoadHW(_56, buf.data, ivec2(16), ivec2(0), int(cond));
    coopmatHW<float16_t, 16u, 16u> tempArg_2 = _56;
    coopmatHW<float16_t, 16u, 16u> C = tempArg_2;
    coopMatStoreHW(C, buf.data, ivec2(16), ivec2(0), cond ? 0 : 1);
}

