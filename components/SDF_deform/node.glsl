float nz_@ID@(vec3 x){
    vec3 i = floor(x), f = fract(x); f = f * f * (3.0 - 2.0 * f);
    float n = 0.0;
    for (int k = 0; k < 8; k++){
        vec3 o = vec3(k & 1, (k >> 1) & 1, (k >> 2) & 1);
        vec3 c = i + o;
        float h = fract(sin(dot(c, vec3(127.1, 311.7, 74.7))) * 43758.5453);
        vec3 w = mix(1.0 - f, f, o);
        n += h * w.x * w.y * w.z;
    }
    return n;
}
vec4 sdf_@ID@(vec3 p){
    int mode = int(P_@ID@_0.x + 0.5);
    float k = P_@ID@_0.y;
    int ax = int(P_@ID@_0.w + 0.5);
    vec3 q = p;
    if (mode == 0 || mode == 1){
        vec3 w = ax == 0 ? p.yxz : (ax == 1 ? p : p.xzy);
        float ang = mode == 0 ? k * w.y : k * w.x;
        float cs = cos(ang), sn = sin(ang);
        if (mode == 0) w.xz = mat2(cs, -sn, sn, cs) * w.xz; else w.xy = mat2(cs, -sn, sn, cs) * w.xy;
        q = ax == 0 ? w.yxz : (ax == 1 ? w : w.xzy);
        vec4 r = @A@(q);
        r.x /= 1.0 + 0.45 * abs(k);
        return r;
    }
    vec4 r = @A@(p);
    if (mode == 2) r.x = (r.x + k * (nz_@ID@(p * P_@ID@_0.z + P_@ID@_1.xyz) - 0.5) * 2.0) * 0.8;
    else if (mode == 3) r.x -= k;
    else r.x = abs(r.x) - k;
    return r;
}
