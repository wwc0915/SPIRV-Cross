#version 450 core
#extension GL_KHR_memory_scope_semantics : enable
#extension GL_HW_neural_shader : enable
#extension GL_EXT_shader_explicit_arithmetic_types : enable

layout(location = 0) out vec4 outColor;

layout(set = 0, binding = 0) buffer BufF16 {
    float16_t data[];
} bufF16;

layout(set = 0, binding = 1) buffer BufI8 {
    int8_t data[];
} bufI8;

layout(set = 0, binding = 2) buffer BufU16 {
    uint16_t data[];
} bufU16;

void main()
{
    outColor = vec4(1.0);

    const ivec2 shape16x8 = ivec2(16, 8);
    const ivec2 shape8x8 = ivec2(8, 8);
    const ivec2 shape8x16 = ivec2(8, 16);
    const ivec2 shape16x16 = ivec2(16, 16);
    const ivec2 shape4x16 = ivec2(4, 16);
    const ivec2 shape16x4 = ivec2(16, 4);
    const ivec2 shape4x4 = ivec2(4, 4);

    coopmatHW<float16_t, 16, 8> fA, fC, fR;
    coopmatHW<float16_t, 8, 8> fB;
    coopmatHW<float, 8, 8> fMulR;

    coopMatLoadHW(fA, bufF16.data, shape16x8, ivec2(1, 2), gl_CooperativeMatrixLayoutRowMajorHW);
    coopMatLoadHW(fB, bufF16.data, shape8x8, ivec2(3, 4), gl_CooperativeMatrixLayoutColumnMajorHW);
    coopMatLoadHW(fC, bufF16.data, shape16x8, ivec2(5, 6), gl_CooperativeMatrixLayoutRowMajorHW);
    coopMatMulHW(fMulR, fB, fB);
    coopMatMulAddHW(fC, fA, fB, fC);
    fR = coopMatReduceHW(fC, gl_CooperativeMatrixReduceRowHW, gl_CooperativeMatrixReduceAddHW);
    coopMatStoreHW(fR, bufF16.data, shape16x8, ivec2(7, 8), gl_CooperativeMatrixLayoutColumnMajorHW);
    int lf = fR.length() + fMulR.length();

    coopmatHW<int8_t, 16, 8> iA;
    coopmatHW<int8_t, 8, 16> iB;
    coopmatHW<int8_t, 16, 16> iC, iOperand, iR;
    coopmatHW<int, 16, 16> iMulR;

    coopMatLoadHW(iA, bufI8.data, shape16x8, ivec2(9, 10), gl_CooperativeMatrixLayoutRowMajorHW);
    coopMatLoadHW(iB, bufI8.data, shape8x16, ivec2(11, 12), gl_CooperativeMatrixLayoutColumnMajorHW);
    coopMatLoadHW(iC, bufI8.data, shape16x16, ivec2(13, 14), gl_CooperativeMatrixLayoutRowMajorHW);
    iOperand = iC;
    coopMatMulHW(iMulR, iOperand, iOperand);
    coopMatMulAddHW(iC, iA, iB, iC);
    iR = coopMatReduceHW(iC, gl_CooperativeMatrixReduceColumnHW, gl_CooperativeMatrixReduceMinHW);
    coopMatStoreHW(iR, bufI8.data, shape16x16, ivec2(15, 16), gl_CooperativeMatrixLayoutColumnMajorHW);
    int li = iR.length() + iMulR.length();

    coopmatHW<uint16_t, 4, 16> uA;
    coopmatHW<uint16_t, 16, 4> uB;
    coopmatHW<uint16_t, 4, 4> uC, uOperand, uR;
    coopmatHW<uint, 4, 4> uMulR;

    coopMatLoadHW(uA, bufU16.data, shape4x16, ivec2(17, 18), gl_CooperativeMatrixLayoutRowMajorHW);
    coopMatLoadHW(uB, bufU16.data, shape16x4, ivec2(19, 20), gl_CooperativeMatrixLayoutColumnMajorHW);
    coopMatLoadHW(uC, bufU16.data, shape4x4, ivec2(21, 22), gl_CooperativeMatrixLayoutRowMajorHW);
    uOperand = uC;
    coopMatMulHW(uMulR, uOperand, uOperand);
    coopMatMulAddHW(uC, uA, uB, uC);
    uR = coopMatReduceHW(uC, gl_CooperativeMatrixReduceRowHW, gl_CooperativeMatrixReduceMaxHW);
    coopMatStoreHW(uR, bufU16.data, shape4x4, ivec2(23, 24), gl_CooperativeMatrixLayoutColumnMajorHW);
    int lu = uR.length() + uMulR.length();

    if (lf + li + lu == 0) {
        fC = fR;
        iC = iR;
        uC = uR;
    }
}
