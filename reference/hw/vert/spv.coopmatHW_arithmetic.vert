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

void main()
{
    gl_Position = vec4(0.0);
    coopmatHW<float16_t, 16u, 8u> f16a;
    f16a = -f16a;
    coopmatHW<float16_t, 16u, 8u> f16b;
    f16a += f16b;
    f16a -= f16b;
    f16a *= f16b;
    f16a /= f16b;
    f16a += f16b;
    f16a -= f16b;
    f16a *= f16b;
    f16a /= f16b;
    coopmatHW<float, 8u, 16u> f32a;
    f32a = -f32a;
    coopmatHW<float, 8u, 16u> f32b;
    f32a += f32b;
    f32a -= f32b;
    f32a *= f32b;
    f32a /= f32b;
    f32a += f32b;
    f32a -= f32b;
    f32a *= f32b;
    f32a /= f32b;
    coopmatHW<int, 8u, 8u> i32a;
    i32a = -i32a;
    coopmatHW<int, 8u, 8u> i32b;
    i32a += i32b;
    i32a -= i32b;
    i32a *= i32b;
    i32a = (i32a / i32b);
    i32a += i32b;
    i32a -= i32b;
    i32a *= i32b;
    i32a = (i32a / i32b);
    coopmatHW<int8_t, 16u, 8u> i8a;
    i8a = -i8a;
    coopmatHW<int8_t, 16u, 8u> i8b;
    i8a += i8b;
    i8a -= i8b;
    i8a *= i8b;
    i8a = (i8a / i8b);
    i8a += i8b;
    i8a -= i8b;
    i8a *= i8b;
    i8a = (i8a / i8b);
    coopmatHW<int16_t, 16u, 16u> i16a;
    i16a = -i16a;
    coopmatHW<int16_t, 16u, 16u> i16b;
    i16a += i16b;
    i16a -= i16b;
    i16a *= i16b;
    i16a = (i16a / i16b);
    i16a += i16b;
    i16a -= i16b;
    i16a *= i16b;
    i16a = (i16a / i16b);
    coopmatHW<uint, 8u, 16u> u32a;
    u32a = -u32a;
    coopmatHW<uint, 8u, 16u> u32b;
    u32a += u32b;
    u32a -= u32b;
    u32a *= u32b;
    u32a = (u32a / u32b);
    u32a += u32b;
    u32a -= u32b;
    u32a *= u32b;
    u32a = (u32a / u32b);
    coopmatHW<uint8_t, 16u, 8u> u8a;
    u8a = -u8a;
    coopmatHW<uint8_t, 16u, 8u> u8b;
    u8a += u8b;
    u8a -= u8b;
    u8a *= u8b;
    u8a = (u8a / u8b);
    u8a += u8b;
    u8a -= u8b;
    u8a *= u8b;
    u8a = (u8a / u8b);
    coopmatHW<uint16_t, 4u, 16u> u16a;
    u16a = -u16a;
    coopmatHW<uint16_t, 4u, 16u> u16b;
    u16a += u16b;
    u16a -= u16b;
    u16a *= u16b;
    u16a = (u16a / u16b);
    u16a += u16b;
    u16a -= u16b;
    u16a *= u16b;
    u16a = (u16a / u16b);
}

