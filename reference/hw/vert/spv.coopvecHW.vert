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
    coopvecHW<float, 5u> v = coopvecHW<float, 5u>(0.0);
    vec3 x = vec3(1.0);
    vec3 y = vec3(2.0);
    coopvecHW<float, 5u> v2 = coopvecHW<float, 5u>(x, y.xy);
    coopvecHW<float16_t, 5u> v3 = coopvecHW<float16_t, 5u>(v2);
    coopvecHW<float, 5u> v4 = v + v2;
    v4 = v - v2;
    v4 = v * v2;
    v4 = v / v2;
    float f = 0.0;
    v4 *= f;
    v4 *= 5.0;
    int len = int(5u);
    v4[0] = f;
    v4[4] = 5.0;
    coopvecHW<float16_t, 100u> v7h;
    coopmatHW<float16_t, 100u, 20u> m8;
    coopvecHW<float, 20u> _89;
    coopVecMatMulHW(_89, v7h, m8);
    coopvecHW<float, 20u> tempArg = _89;
    coopvecHW<float, 20u> v8 = tempArg;
    coopvecHW<int8_t, 100u> v9;
    coopmatHW<int8_t, 100u, 20u> m10;
    coopvecHW<int, 20u> _104;
    coopVecMatMulHW(_104, v9, m10);
    coopvecHW<int, 20u> tempArg_1 = _104;
    coopvecHW<int, 20u> v10 = tempArg_1;
    float16_t _113 = float16_t(int(100u));
    coopvecHW<float16_t, 2u> f162 = coopvecHW<float16_t, 2u>(_113);
    float16_t f16;
    coopvecHW<float16_t, 1u> f161 = coopvecHW<float16_t, 1u>(f16);
    coopvecHW<float16_t, 7u> v11;
    coopvecHW<float16_t, 7u> v12;
    v11 = max(v11, v12);
    v11 = min(v11, v12);
    v11 = step(v11, v12);
    coopvecHW<float16_t, 7u> v13;
    v11 = clamp(v11, v12, v13);
    v11 = -v11;
    v11 = exp(v11);
    v11 = log(v11);
    v11 = tanh(v11);
    v11 = atan(v11);
    v11 = fma(v11, v12, v13);
    coopvecHW<int16_t, 7u> s11;
    s11 = -s11;
    s11 = ~s11;
    coopvecHW<int16_t, 7u> s12;
    s11 += s12;
    s11 -= s12;
    s11 *= s12;
    s11 = (s11 / s12);
    s11 += s12;
    s11 -= s12;
    s11 *= s12;
    s11 = (s11 / s12);
    coopvecHW<uint16_t, 7u> u11;
    coopvecHW<uint16_t, 7u> u12;
    u11 = (min(u11, u12));
    u11 = (max(u11, u12));
    coopvecHW<uint16_t, 7u> u13;
    u11 = (clamp(u11, u12, u13));
    u11 = ~u11;
    u11 = (u11 >> u12);
    u11 = u11 << u12;
    u11 |= u12;
    u11 &= u12;
    u11 ^= u12;
    u11 += u12;
    u11 -= u12;
    u11 *= u12;
    u11 = (u11 / u12);
    u11 = (u11 >> u12);
    u11 = u11 << u12;
    u11 |= u12;
    u11 &= u12;
    u11 ^= u12;
    u11 += u12;
    u11 -= u12;
    u11 *= u12;
    u11 = (u11 / u12);
    s11 = (s11 >> s12);
    s11 = s11 << s12;
    s11 |= s12;
    s11 &= s12;
    s11 ^= s12;
    s11 = (s11 >> s12);
    s11 = s11 << s12;
    s11 |= s12;
    s11 &= s12;
    s11 ^= s12;
    coopvecHW<float, 20u> v8bias;
    coopvecHW<float, 20u> _295;
    coopVecMatMulAddHW(_295, v7h, m8, v8bias);
    coopvecHW<float, 20u> tempArg_2 = _295;
    v8 = tempArg_2;
    coopvecHW<int, 20u> v10bias;
    coopvecHW<int, 20u> _302;
    coopVecMatMulAddHW(_302, v9, m10, v10bias);
    coopvecHW<int, 20u> tempArg_3 = _302;
    v10 = tempArg_3;
    coopvecHW<float, 5u> _304 = v;
    coopvecHW<float, 5u> _305 = v;
    coopvecHW<float, 5u> _306 = _305 + _304;
    v = _306;
    f += _306[len];
}

