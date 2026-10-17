vec4 sdf_@ID@(vec3 p){
    vec3 q = abs(p) - P_@ID@_0.xyz + P_@ID@_0.w;
    return vec4(length(max(q, 0.0)) + min(max(q.x, max(q.y, q.z)), 0.0) - P_@ID@_0.w, P_@ID@_1.xyz);
}
