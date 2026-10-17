float hash12(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
// field texture: rg = direction*0.5+0.5, b = magnitude (0-1)
vec3 fieldAt(sampler2D f, vec2 uv){
    vec4 t = texture(f, clamp(uv, 0., 1.));
    vec2 d = t.xy * 2. - 1.;
    float l = length(d);
    d = l > 1e-4 ? d / l : vec2(0.);
    return vec3(d, t.z);
}
vec3 palette(float t){
    return 0.5 + 0.5*cos(6.28318*(t + vec3(0.0,0.33,0.67)));
}
