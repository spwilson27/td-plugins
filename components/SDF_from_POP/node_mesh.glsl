// SDF_from_POP / mesh: trilinear lookup in the baked distance volume T_@ID@_v over the bounds T_@ID@_b
// (2x1 texture: min xyz, max xyz); the volume stores distance / band width. P_@ID@_0 = (resolution G, band in voxels).
// Outside the volume: distance to its box plus the (clamped) edge value, so rays still converge.
vec4 sdf_@ID@(vec3 p){
    vec3 bmin = texelFetch(T_@ID@_b, ivec2(0, 0), 0).xyz;
    vec3 bmax = texelFetch(T_@ID@_b, ivec2(1, 0), 0).xyz;
    vec3 sz = bmax - bmin;
    if (!(sz.x > 0.0 && sz.y > 0.0 && sz.z > 0.0)) return vec4(1e3, 0.8, 0.8, 0.8);   // nothing baked yet
    vec3 u = (p - bmin) / sz, q = clamp(u, 0.0, 1.0);
    vec4 s = textureLod(T_@ID@_v, q, 0.0);
    float bw = P_@ID@_0.y * min(sz.x, min(sz.y, sz.z)) / P_@ID@_0.x;
    return vec4(s.x * bw + length((u - q) * sz), s.yzw);
}
