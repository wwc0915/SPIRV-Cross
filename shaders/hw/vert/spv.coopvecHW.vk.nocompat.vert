#version 450 core
#extension GL_KHR_memory_scope_semantics : enable
#extension GL_HW_neural_shader : enable
#extension GL_EXT_shader_explicit_arithmetic_types : enable

coopvecHW<float16_t, 1> foo(coopvecHW<float16_t, 1> x) { return x; }
coopvecHW<float16_t, 2> foo(coopvecHW<float16_t, 2> x) { return x; }

void main()
{
    gl_Position = vec4(0.0);

    coopvecHW<float, 5> v = coopvecHW<float, 5>(0.0);

    vec3 x = vec3(1.0), y = vec3(2.0);
    coopvecHW<float, 5> v2 = coopvecHW<float, 5>(x, y);

    coopvecHW<float16_t, 5> v3 = coopvecHW<float16_t, 5>(v2);
    coopvecHW<float, 5> v4;

    v4 = v + v2;
    v4 = v - v2;
    v4 = v * v2;
    v4 = v / v2;

    float f = 0.0;
    v4 *= f;
    v4 *= 5.0;

    int len = v4.length();
    v4[0] = f;
    v4[4] = 5.0;

    coopvecHW<float, 100> v7;
    coopvecHW<float, 20> v8;
    coopvecHW<float16_t, 100> v7h;
    coopvecHW<float, 20> v8bias;
    coopmatHW<float16_t, 100, 20> m8;
    coopVecMatMulHW(v8, v7h, m8);

    coopvecHW<int8_t, 100> v9;
    coopvecHW<int32_t, 20> v10;
    coopvecHW<int32_t, 20> v10bias;
    coopmatHW<int8_t, 100, 20> m10;
    coopVecMatMulHW(v10, v9, m10);

    coopvecHW<float16_t, 2> f162 = coopvecHW<float16_t, 2>(v7.length());

    float16_t f16;
    coopvecHW<float16_t, 1> f161 = coopvecHW<float16_t, 1>(f16);

    coopvecHW<float16_t, 7> v11, v12, v13;
    v11 = max(v11, v12);
    v11 = min(v11, v12);
    v11 = step(v11, v12);
    v11 = clamp(v11, v12, v13);
    v11 = -v11;
    v11 = exp(v11);
    v11 = log(v11);
    v11 = tanh(v11);
    v11 = atan(v11);
    v11 = fma(v11, v12, v13);

    coopvecHW<int16_t, 7> s11, s12;
    s11 = -s11;
    s11 = ~s11;
    s11 = s11 + s12;
    s11 = s11 - s12;
    s11 = s11 * s12;
    s11 = s11 / s12;
    s11 += s12;
    s11 -= s12;
    s11 *= s12;
    s11 /= s12;

    coopvecHW<uint16_t, 7> u11, u12, u13;
    u11 = min(u11, u12);
    u11 = max(u11, u12);
    u11 = clamp(u11, u12, u13);
    u11 = ~u11;
    u11 = u11 >> u12;
    u11 = u11 << u12;
    u11 = u11 | u12;
    u11 = u11 & u12;
    u11 = u11 ^ u12;
    u11 = u11 + u12;
    u11 = u11 - u12;
    u11 = u11 * u12;
    u11 = u11 / u12;
    u11 >>= u12;
    u11 <<= u12;
    u11 |= u12;
    u11 &= u12;
    u11 ^= u12;
    u11 += u12;
    u11 -= u12;
    u11 *= u12;
    u11 /= u12;

    s11 = s11 >> s12;
    s11 = s11 << s12;
    s11 = s11 | s12;
    s11 = s11 & s12;
    s11 = s11 ^ s12;
    s11 >>= s12;
    s11 <<= s12;
    s11 |= s12;
    s11 &= s12;
    s11 ^= s12;

    coopVecMatMulAddHW(v8, v7h, m8, v8bias);
    coopVecMatMulAddHW(v10, v9, m10, v10bias);

    f += (v += v)[len];
}
