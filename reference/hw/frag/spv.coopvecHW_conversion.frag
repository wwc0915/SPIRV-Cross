#version 450
#if defined(GL_AMD_gpu_shader_half_float)
#extension GL_AMD_gpu_shader_half_float : require
#elif defined(GL_NV_gpu_shader5)
#extension GL_NV_gpu_shader5 : require
#else
#error No extension available for FP16.
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

layout(location = 0) out vec4 outColor;

void main()
{
    outColor = vec4(1.0);
    coopvecHW<float16_t, 5u> f16;
    coopvecHW<uint, 5u> u32 = coopvecHW<uint, 5u>(f16);
    coopvecHW<int, 5u> i32 = coopvecHW<int, 5u>(f16);
    coopvecHW<float, 5u> f32;
    coopvecHW<int16_t, 5u> i16 = coopvecHW<int16_t, 5u>(f32);
    coopvecHW<uint16_t, 5u> u16 = coopvecHW<uint16_t, 5u>(f32);
    i32 = coopvecHW<int, 5u>(coopvecHW<uint, 5u>(u16));
    u32 = coopvecHW<uint, 5u>(coopvecHW<int, 5u>(i16));
    f32 = coopvecHW<float, 5u>(u16);
    f16 = coopvecHW<float16_t, 5u>(i16);
    f16 = coopvecHW<float16_t, 5u>(f32);
}

