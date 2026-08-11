#version 450
#if defined(GL_AMD_gpu_shader_half_float)
#extension GL_AMD_gpu_shader_half_float : require
#elif defined(GL_NV_gpu_shader5)
#extension GL_NV_gpu_shader5 : require
#else
#error No extension available for FP16.
#endif
#extension GL_HW_neural_shader : require

layout(binding = 0, std430) buffer Buf
{
    float16_t data[];
} buf;

layout(location = 0) out vec4 outColor;

void main()
{
    outColor = vec4(1.0);
    coopmatHW<float16_t, 16u, 8u> A = coopmatHW<float16_t, 16u, 8u>(float16_t(0.0));
    coopmatHW<float16_t, 8u, 8u> B = coopmatHW<float16_t, 8u, 8u>(float16_t(1.0));
    coopmatHW<float16_t, 8u, 8u> S = coopmatHW<float16_t, 8u, 8u>(float16_t(2.0));
    coopmatHW<float16_t, 16u, 8u> _49;
    coopMatLoadHW(_49, buf.data, ivec2(32, 64), ivec2(1, 2), gl_CooperativeMatrixLayoutRowMajorHW);
    coopmatHW<float16_t, 16u, 8u> tempArg = _49;
    coopmatHW<float16_t, 16u, 8u> C = tempArg;
    coopmatHW<float, 8u, 8u> _58;
    coopMatMulHW(_58, S, B);
    coopmatHW<float, 8u, 8u> tempArg_1 = _58;
    coopmatHW<float, 8u, 8u> M = tempArg_1;
    coopmatHW<float16_t, 16u, 8u> _65;
    coopMatMulAddHW(_65, A, B, C);
    coopmatHW<float16_t, 16u, 8u> tempArg_2 = _65;
    C = tempArg_2;
    coopmatHW<float16_t, 16u, 8u> _69 = coopMatReduceHW(C, gl_CooperativeMatrixReduceRowHW, gl_CooperativeMatrixReduceAddHW);
    coopmatHW<float16_t, 16u, 8u> R0 = coopmatHW<float16_t, 16u, 8u>(_69);
    coopmatHW<float16_t, 16u, 8u> _73 = coopMatReduceHW(C, gl_CooperativeMatrixReduceColumnHW, gl_CooperativeMatrixReduceMaxHW);
    coopmatHW<float16_t, 16u, 8u> R1 = coopmatHW<float16_t, 16u, 8u>(_73);
    coopMatStoreHW(C, buf.data, ivec2(32, 64), ivec2(3, 4), gl_CooperativeMatrixLayoutColumnMajorHW);
    int len = int(uint(coopmatHW<float16_t, 16u, 8u>(0).length())) + int(uint(coopmatHW<float, 8u, 8u>(0).length()));
    coopmatHW<float16_t, 16u, 8u> D = coopmatHW<float16_t, 16u, 8u>(C);
    C = coopmatHW<float16_t, 16u, 8u>(D);
    if (len == 0)
    {
        C = coopmatHW<float16_t, 16u, 8u>(float16_t(0.0));
    }
}

