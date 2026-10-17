vec4 sdf_@ID@(vec3 p){
    vec4 a = @A@(p), b = @B@(p);
    float k = P_@ID@_0.x;
    int op = int(P_@ID@_0.y + 0.5);
    float d; vec3 col;
    if (op == 0){                                   // union
        float h = k > 0.0 ? clamp(0.5 + 0.5 * (b.x - a.x) / k, 0.0, 1.0) : (a.x < b.x ? 1.0 : 0.0);
        d = mix(b.x, a.x, h) - k * h * (1.0 - h); col = mix(b.yzw, a.yzw, h);
    } else if (op == 1){                            // subtract B from A
        float h = k > 0.0 ? clamp(0.5 - 0.5 * (a.x + b.x) / k, 0.0, 1.0) : (a.x < -b.x ? 1.0 : 0.0);
        d = mix(a.x, -b.x, h) + k * h * (1.0 - h); col = mix(a.yzw, b.yzw, h * 0.0);
        if (k <= 0.0) d = max(a.x, -b.x);
    } else if (op == 2){                            // intersect
        float h = k > 0.0 ? clamp(0.5 - 0.5 * (b.x - a.x) / k, 0.0, 1.0) : (a.x > b.x ? 1.0 : 0.0);
        d = mix(b.x, a.x, h) + k * h * (1.0 - h); col = mix(b.yzw, a.yzw, h);
    } else {                                        // morph A -> B
        float t = P_@ID@_0.z;
        d = mix(a.x, b.x, t); col = mix(a.yzw, b.yzw, t);
    }
    return vec4(d, col);
}
