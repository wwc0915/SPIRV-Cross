#version 450
#if defined(GL_EXT_shader_explicit_arithmetic_types_int16)
#extension GL_EXT_shader_explicit_arithmetic_types_int16 : require
#elif defined(GL_AMD_gpu_shader_int16)
#extension GL_AMD_gpu_shader_int16 : require
#elif defined(GL_NV_gpu_shader5)
#extension GL_NV_gpu_shader5 : require
#else
#error No extension available for Int16.
#endif
#if defined(GL_AMD_gpu_shader_half_float)
#extension GL_AMD_gpu_shader_half_float : require
#elif defined(GL_NV_gpu_shader5)
#extension GL_NV_gpu_shader5 : require
#else
#error No extension available for FP16.
#endif
#extension GL_HW_neural_shader : require

void main()
{
    gl_Position = vec4(0.0);
    coopmatHW<float16_t, 16u, 8u> f16;
    coopmatHW<int16_t, 16u, 8u> i16 = float16BitsToInt16(f16);
    coopmatHW<uint16_t, 16u, 8u> u16 = float16BitsToUint16(f16);
    u16 = float16BitsToUint16(f16);
    f16 = int16BitsToFloat16(i16);
    f16 = int16BitsToFloat16(i16);
    f16 = uint16BitsToFloat16(u16);
    f16 = uint16BitsToFloat16(u16);
    coopmatHW<float, 16u, 8u> f32;
    coopmatHW<int, 16u, 8u> i32 = floatBitsToInt(f32);
    coopmatHW<uint, 16u, 8u> u32 = floatBitsToUint(f32);
    f32 = intBitsToFloat(i32);
    f32 = uintBitsToFloat(u32);
}

