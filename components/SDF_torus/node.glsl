vec4 sdf_@ID@(vec3 p){
    int ax = int(P_@ID@_0.z + 0.5);
    vec3 q = ax == 0 ? p.yxz : (ax == 1 ? p : p.xzy);
    vec2 t = vec2(length(q.xz) - P_@ID@_0.x, q.y);
    return vec4(length(t) - P_@ID@_0.y, P_@ID@_1.xyz);
}
