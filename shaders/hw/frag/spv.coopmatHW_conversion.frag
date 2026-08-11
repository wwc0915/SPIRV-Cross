#version 450 core
#extension GL_KHR_memory_scope_semantics : enable
#extension GL_HW_neural_shader : enable
#extension GL_EXT_shader_explicit_arithmetic_types : enable

layout(location = 0) out vec4 outColor;

void main()
{
    outColor = vec4(1.0);

    coopmatHW<float16_t, 16, 8> f16;
    coopmatHW<float, 16, 8> f32;
    coopmatHW<int, 16, 8> i32;
    coopmatHW<uint, 16, 8> u32;
    coopmatHW<int16_t, 16, 8> i16;
    coopmatHW<uint16_t, 16, 8> u16;

    u32 = coopmatHW<uint, 16, 8>(f16);
    i32 = coopmatHW<int, 16, 8>(f16);
    i16 = coopmatHW<int16_t, 16, 8>(f32);
    u16 = coopmatHW<uint16_t, 16, 8>(f32);

    i32 = coopmatHW<int, 16, 8>(i16);
    u32 = coopmatHW<uint, 16, 8>(u16);

    f32 = coopmatHW<float, 16, 8>(u16);
    f16 = coopmatHW<float16_t, 16, 8>(i16);
    f16 = coopmatHW<float16_t, 16, 8>(f32);
}
