#version 450 core
#extension GL_HW_neural_shader : enable
#extension GL_EXT_shader_explicit_arithmetic_types : enable

void main()
{
    gl_Position = vec4(0.0);

    coopvecHW<float16_t, 5> f16;
    coopvecHW<float, 5> f32;
    coopvecHW<int, 5> i32;
    coopvecHW<uint, 5> u32;
    coopvecHW<int16_t, 5> i16;
    coopvecHW<uint16_t, 5> u16;

    u32 = coopvecHW<uint, 5>(f16);
    i32 = coopvecHW<int, 5>(f16);
    i16 = coopvecHW<int16_t, 5>(f32);
    u16 = coopvecHW<uint16_t, 5>(f32);

    i32 = coopvecHW<int, 5>(u16);
    u32 = coopvecHW<uint, 5>(i16);

    f32 = coopvecHW<float, 5>(u16);
    f16 = coopvecHW<float16_t, 5>(i16);
    f16 = coopvecHW<float16_t, 5>(f32);
}
