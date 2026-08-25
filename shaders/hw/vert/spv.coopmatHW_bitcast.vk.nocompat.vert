#version 450 core
#extension GL_KHR_memory_scope_semantics : enable
#extension GL_HW_neural_shader : enable
#extension GL_EXT_shader_explicit_arithmetic_types : enable

void main()
{
    gl_Position = vec4(0.0);

    coopmatHW<float16_t, 16, 8> f16;
    coopmatHW<int16_t, 16, 8> i16;
    coopmatHW<uint16_t, 16, 8> u16;
    coopmatHW<float, 16, 8> f32;
    coopmatHW<int, 16, 8> i32;
    coopmatHW<uint, 16, 8> u32;

    i16 = float16BitsToInt16(f16);
    u16 = float16BitsToUint16(f16);
    u16 = halfBitsToUint16(f16);
    f16 = int16BitsToFloat16(i16);
    f16 = int16BitsToHalf(i16);
    f16 = uint16BitsToFloat16(u16);
    f16 = uint16BitsToHalf(u16);

    i32 = floatBitsToInt(f32);
    u32 = floatBitsToUint(f32);
    f32 = intBitsToFloat(i32);
    f32 = uintBitsToFloat(u32);
}
