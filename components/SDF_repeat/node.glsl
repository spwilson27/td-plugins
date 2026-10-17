vec4 sdf_@ID@(vec3 p){
    vec4 a = P_@ID@_0, b = P_@ID@_1, c = P_@ID@_2;
    int mode = int(a.w + 0.5);
    vec3 q = p; float cell = 0.0;
    if (mode == 2){                                 // polar (around an axis)
        int ax = int(c.y + 0.5);
        vec3 w = ax == 0 ? p.yxz : (ax == 1 ? p : p.xzy);
        float sec = 6.2831853 / max(c.x, 1.0);
        float ang = atan(w.z, w.x);
        float id = floor((ang + 0.5 * sec) / sec);
        ang -= id * sec;
        float r = length(w.xz);
        w = vec3(r * cos(ang), w.y, r * sin(ang));
        cell = id;
        q = ax == 0 ? w.yxz : (ax == 1 ? w : w.xzy);
    } else {                                        // grid: infinite (0) or limited to +-count cells (1)
        vec3 s = max(a.xyz, vec3(1e-4));
        vec3 on = step(vec3(1e-4), a.xyz);
        vec3 id = floor(p / s + 0.5);
        if (mode == 1) id = clamp(id, -b.xyz, b.xyz);
        id *= on;
        q = p - s * id;
        cell = dot(id, vec3(1.0, 7.3, 13.1));
    }
    vec4 r = @A@(q);
    float h = fract(sin(cell * 12.9898) * 43758.5453);
    r.yzw *= mix(1.0, 0.35 + 1.3 * h, b.w);
    return r;
}
