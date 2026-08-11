#version 450
#if defined(GL_AMD_gpu_shader_half_float)
#extension GL_AMD_gpu_shader_half_float : require
#elif defined(GL_NV_gpu_shader5)
#extension GL_NV_gpu_shader5 : require
#else
#error No extension available for FP16.
#endif
#if defined(GL_EXT_shader_explicit_arithmetic_types_int8)
#extension GL_EXT_shader_explicit_arithmetic_types_int8 : require
#elif defined(GL_NV_gpu_shader5)
#extension GL_NV_gpu_shader5 : require
#else
#error No extension available for Int8.
#endif
#if defined(GL_EXT_shader_explicit_arithmetic_types_int16)
#extension GL_EXT_shader_explicit_arithmetic_types_int16 : require
#elif defined(GL_AMD_gpu_shader_int16)
#extension GL_AMD_gpu_shader_int16 : require
#elif defined(GL_NV_gpu_shader5)
#extension GL_NV_gpu_shader5 : require
#else
#error No extension available for Int16.
#endif
#extension GL_HW_neural_shader : require

layout(binding = 0, std430) buffer BufF16
{
    float16_t data[];
} bufF16;

layout(binding = 1, std430) buffer BufI8
{
    int8_t data[];
} bufI8;

layout(binding = 2, std430) buffer BufU16
{
    uint16_t data[];
} bufU16;

layout(location = 0) out vec4 outColor;

void main()
{
    outColor = vec4(1.0);
    coopmatHW<float16_t, 16u, 8u> _34;
    coopMatLoadHW(_34, bufF16.data, ivec2(16, 8), ivec2(1, 2), gl_CooperativeMatrixLayoutRowMajorHW);
    coopmatHW<float16_t, 16u, 8u> tempArg = _34;
    coopmatHW<float16_t, 16u, 8u> fA = tempArg;
    coopmatHW<float16_t, 8u, 8u> _45;
    coopMatLoadHW(_45, bufF16.data, ivec2(8), ivec2(3, 4), gl_CooperativeMatrixLayoutColumnMajorHW);
    coopmatHW<float16_t, 8u, 8u> tempArg_1 = _45;
    coopmatHW<float16_t, 8u, 8u> fB = tempArg_1;
    coopmatHW<float16_t, 16u, 8u> _55;
    coopMatLoadHW(_55, bufF16.data, ivec2(16, 8), ivec2(5, 6), gl_CooperativeMatrixLayoutRowMajorHW);
    coopmatHW<float16_t, 16u, 8u> tempArg_2 = _55;
    coopmatHW<float16_t, 16u, 8u> fC = tempArg_2;
    coopmatHW<float, 8u, 8u> _66;
    coopMatMulHW(_66, coopmatHW<float16_t, 8u, 8u>(fB), fB);
    coopmatHW<float, 8u, 8u> tempArg_3 = _66;
    coopmatHW<float, 8u, 8u> fMulR = tempArg_3;
    coopmatHW<float16_t, 16u, 8u> _73;
    coopMatMulAddHW(_73, fA, fB, fC);
    coopmatHW<float16_t, 16u, 8u> tempArg_4 = _73;
    fC = tempArg_4;
    coopmatHW<float16_t, 16u, 8u> _77 = coopMatReduceHW(fC, gl_CooperativeMatrixReduceRowHW, gl_CooperativeMatrixReduceAddHW);
    coopmatHW<float16_t, 16u, 8u> fR = coopmatHW<float16_t, 16u, 8u>(_77);
    coopMatStoreHW(fR, bufF16.data, ivec2(16, 8), ivec2(7, 8), gl_CooperativeMatrixLayoutColumnMajorHW);
    int lf = int(uint(coopmatHW<float16_t, 16u, 8u>(0).length())) + int(uint(coopmatHW<float, 8u, 8u>(0).length()));
    coopmatHW<int8_t, 16u, 8u> _103;
    coopMatLoadHW(_103, bufI8.data, ivec2(16, 8), ivec2(9, 10), gl_CooperativeMatrixLayoutRowMajorHW);
    coopmatHW<int8_t, 16u, 8u> tempArg_5 = _103;
    coopmatHW<int8_t, 16u, 8u> iA = tempArg_5;
    coopmatHW<int8_t, 8u, 16u> _114;
    coopMatLoadHW(_114, bufI8.data, ivec2(8, 16), ivec2(11, 12), gl_CooperativeMatrixLayoutColumnMajorHW);
    coopmatHW<int8_t, 8u, 16u> tempArg_6 = _114;
    coopmatHW<int8_t, 8u, 16u> iB = tempArg_6;
    coopmatHW<int8_t, 16u, 16u> _125;
    coopMatLoadHW(_125, bufI8.data, ivec2(16), ivec2(13, 14), gl_CooperativeMatrixLayoutRowMajorHW);
    coopmatHW<int8_t, 16u, 16u> tempArg_7 = _125;
    coopmatHW<int8_t, 16u, 16u> iC = tempArg_7;
    coopmatHW<int8_t, 16u, 16u> iOperand = coopmatHW<int8_t, 16u, 16u>(iC);
    coopmatHW<int, 16u, 16u> _141;
    coopMatMulHW(_141, iOperand, coopmatHW<int8_t, 16u, 16u>(iOperand));
    coopmatHW<int, 16u, 16u> tempArg_8 = _141;
    coopmatHW<int, 16u, 16u> iMulR = tempArg_8;
    coopmatHW<int8_t, 16u, 16u> _148;
    coopMatMulAddHW(_148, iA, iB, iC);
    coopmatHW<int8_t, 16u, 16u> tempArg_9 = _148;
    iC = tempArg_9;
    coopmatHW<int8_t, 16u, 16u> _152 = coopMatReduceHW(iC, gl_CooperativeMatrixReduceColumnHW, gl_CooperativeMatrixReduceMinHW);
    coopmatHW<int8_t, 16u, 16u> iR = coopmatHW<int8_t, 16u, 16u>(_152);
    coopMatStoreHW(iR, bufI8.data, ivec2(16), ivec2(15, 16), gl_CooperativeMatrixLayoutColumnMajorHW);
    int li = int(uint(coopmatHW<int8_t, 16u, 16u>(0).length())) + int(uint(coopmatHW<int, 16u, 16u>(0).length()));
    coopmatHW<uint16_t, 4u, 16u> _179;
    coopMatLoadHW(_179, bufU16.data, ivec2(4, 16), ivec2(17, 18), gl_CooperativeMatrixLayoutRowMajorHW);
    coopmatHW<uint16_t, 4u, 16u> tempArg_10 = _179;
    coopmatHW<uint16_t, 4u, 16u> uA = tempArg_10;
    coopmatHW<uint16_t, 16u, 4u> _190;
    coopMatLoadHW(_190, bufU16.data, ivec2(16, 4), ivec2(19, 20), gl_CooperativeMatrixLayoutColumnMajorHW);
    coopmatHW<uint16_t, 16u, 4u> tempArg_11 = _190;
    coopmatHW<uint16_t, 16u, 4u> uB = tempArg_11;
    coopmatHW<uint16_t, 4u, 4u> _201;
    coopMatLoadHW(_201, bufU16.data, ivec2(4), ivec2(21, 22), gl_CooperativeMatrixLayoutRowMajorHW);
    coopmatHW<uint16_t, 4u, 4u> tempArg_12 = _201;
    coopmatHW<uint16_t, 4u, 4u> uC = tempArg_12;
    coopmatHW<uint16_t, 4u, 4u> uOperand = coopmatHW<uint16_t, 4u, 4u>(uC);
    coopmatHW<uint, 4u, 4u> _217;
    coopMatMulHW(_217, uOperand, coopmatHW<uint16_t, 4u, 4u>(uOperand));
    coopmatHW<uint, 4u, 4u> tempArg_13 = _217;
    coopmatHW<uint, 4u, 4u> uMulR = tempArg_13;
    coopmatHW<uint16_t, 4u, 4u> _224;
    coopMatMulAddHW(_224, uA, uB, uC);
    coopmatHW<uint16_t, 4u, 4u> tempArg_14 = _224;
    uC = tempArg_14;
    coopmatHW<uint16_t, 4u, 4u> _228 = coopMatReduceHW(uC, gl_CooperativeMatrixReduceRowHW, gl_CooperativeMatrixReduceMaxHW);
    coopmatHW<uint16_t, 4u, 4u> uR = coopmatHW<uint16_t, 4u, 4u>(_228);
    coopMatStoreHW(uR, bufU16.data, ivec2(4), ivec2(23, 24), gl_CooperativeMatrixLayoutColumnMajorHW);
    int lu = int(uint(coopmatHW<uint16_t, 4u, 4u>(0).length())) + int(uint(coopmatHW<uint, 4u, 4u>(0).length()));
    if (((lf + li) + lu) == 0)
    {
        fC = coopmatHW<float16_t, 16u, 8u>(fR);
        iC = coopmatHW<int8_t, 16u, 16u>(iR);
        uC = coopmatHW<uint16_t, 4u, 4u>(uR);
    }
}

